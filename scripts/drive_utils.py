"""drive_utils.py — acesso local ao Google Drive via Composio.

Encapsula o fluxo Composio (tools/list -> search -> schemas -> multi_execute)
em comandos simples para os agentes do ecossistema usarem as pastas do Drive.

Uso (CLI):
  python scripts/drive_utils.py listar [folder_id]        # lista conteúdo de uma pasta (default: root)
  python scripts/drive_utils.py buscar "termo"             # busca arquivos por nome/termo
  python scripts/drive_utils.py ler <file_id>              # baixa o arquivo e exibe conteúdo de texto
  python scripts/drive_utils.py info <file_id>             # metadados do arquivo/pasta
  python scripts/drive_utils.py criar_pasta <nome> [pai]   # cria pasta no Drive
  python scripts/drive_utils.py mover <file_id> <pai>      # move arquivo para pasta
  python scripts/drive_utils.py renomear <file_id> <novo>  # renomeia arquivo/pasta
  python scripts/drive_utils.py estrutura [folder_id]      # árvore até 3 níveis
  python scripts/drive_utils.py sobre                       # informações da conta/quota

Importável: from drive_utils import listar_pasta, buscar_arquivos, ... (usa handle do mcp-composio-server).
"""
import json
import os
import sys
import importlib.util
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "mcp_composio", str(BASE / "scripts" / "mcp-composio-server.py")
)
_composio = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_composio)
_composio._load_dotenv()

COMPOSIO = _composio


def _executar(tools, passo):
    """Executa tools via COMPOSIO_MULTI_EXECUTE_TOOL e devolve lista de respostas."""
    req = {"jsonrpc": "2.0", "id": 1000, "method": "tools/call", "params": {
        "name": "COMPOSIO_MULTI_EXECUTE_TOOL",
        "arguments": {"tools": tools, "sync_response_to_workbench": False,
                      "thought": passo, "current_step": passo}
    }}
    r = COMPOSIO.handle(req)
    txt = r.get("result", {}).get("content", [{}])[0].get("text", "")
    try:
        obj = json.loads(txt)
        return obj.get("data", {}).get("results", [])
    except Exception:
        return [{"response": {"successful": False, "raw": txt[:400]}}]


def _primeiro_arquivo(results):
    for res in results:
        resp = res.get("response", {})
        if resp.get("successful"):
            return resp.get("data", {}).get("files") or resp.get("data_preview", {}).get("files") or []
    return []


def listar_pasta(folder_id="root"):
    """Lista conteúdo de uma pasta. Retorna lista de dicts (id, name, mimeType)."""
    tools = [{"tool_slug": "GOOGLEDRIVE_FIND_FILE",
              "arguments": {"q": f"'{folder_id}' in parents and trashed = false",
                            "fields": "files(id,name,mimeType,size,modifiedTime)", "pageSize": 1000}}]
    return _primeiro_arquivo(_executar(tools, "LISTANDO_PASTA"))


def buscar_arquivos(termo):
    """Busca arquivos/pastas por termo (nome). Retorna lista de dicts."""
    tools = [{"tool_slug": "GOOGLEDRIVE_FIND_FILE",
              "arguments": {"q": f"name contains '{termo}' and trashed = false",
                            "fields": "files(id,name,mimeType,size)", "pageSize": 100}}]
    return _primeiro_arquivo(_executar(tools, "BUSCANDO_ARQUIVO"))


def info_arquivo(file_id):
    """Metadados completos de um arquivo/pasta."""
    tools = [{"tool_slug": "GOOGLEDRIVE_GET_FILE_METADATA",
              "arguments": {"fileId": file_id, "fields": "*"}}]
    results = _executar(tools, "OBTENDO_METADADOS")
    for res in results:
        resp = res.get("response", {})
        if resp.get("successful"):
            return resp.get("data", {})
    return {}


def criar_pasta(nome, parent_id="root"):
    """Cria uma pasta. Retorna o ID criado."""
    tools = [{"tool_slug": "GOOGLEDRIVE_CREATE_FOLDER",
              "arguments": {"name": nome, "parent_id": parent_id}}]
    results = _executar(tools, "CRIANDO_PASTA")
    for res in results:
        resp = res.get("response", {})
        if resp.get("successful"):
            return resp.get("data", {}).get("id")
    return None


def mover_arquivo(file_id, destino_id):
    """Move arquivo para outra pasta. Retorna True em sucesso."""
    tools = [{"tool_slug": "GOOGLEDRIVE_MOVE_FILE",
              "arguments": {"file_id": file_id, "add_parents": destino_id, "remove_parents": "root"}}]
    results = _executar(tools, "MOVENDO_ARQUIVO")
    return any(res.get("response", {}).get("successful") for res in results)


def renomear(file_id, novo_nome):
    """Renomeia arquivo/pasta. Retorna True em sucesso."""
    tools = [{"tool_slug": "GOOGLEDRIVE_UPDATE_FILE_PUT",
              "arguments": {"fileId": file_id, "name": novo_nome}}]
    results = _executar(tools, "RENOMEANDO")
    return any(res.get("response", {}).get("successful") for res in results)


def ler_arquivo(file_id):
    """Baixa um arquivo e retorna (nome, mimeType, s3url) via GOOGLEDRIVE_DOWNLOAD_FILE."""
    tools = [{"tool_slug": "GOOGLEDRIVE_DOWNLOAD_FILE",
              "arguments": {"fileId": file_id}}]
    results = _executar(tools, "BAIXANDO_ARQUIVO")
    for res in results:
        resp = res.get("response", {})
        if resp.get("successful"):
            d = resp.get("data", {}) or resp.get("data_preview", {})
            return d
    return {}


def estrutura(folder_id="root", max_depth=3, _depth=0):
    """Árvore das pastas até max_depth níveis."""
    if _depth >= max_depth:
        return []
    saida = []
    itens = listar_pasta(folder_id)
    for it in itens:
        mime = it.get("mimeType", "")
        no = {"id": it.get("id"), "name": it.get("name"),
              "tipo": "pasta" if mime == "application/vnd.google-apps.folder" else "arquivo",
              "mime": mime}
        if no["tipo"] == "pasta":
            no["filhos"] = estrutura(it.get("id"), max_depth, _depth + 1)
        saida.append(no)
    return saida


def sobre():
    """Informações da conta/quota."""
    tools = [{"tool_slug": "GOOGLEDRIVE_GET_ABOUT", "arguments": {"fields": "*"}}]
    results = _executar(tools, "OBTENDO_INFOS")
    for res in results:
        resp = res.get("response", {})
        if resp.get("successful"):
            return resp.get("data", {}) or resp.get("data_preview", {})
    return {}


def _fmt_lista(itens):
    linhas = []
    for it in itens:
        mime = it.get("mimeType", "")
        tipo = "📁" if mime == "application/vnd.google-apps.folder" else "📄"
        tam = it.get("size")
        tam_s = f" {int(tam)}B" if tam else ""
        linhas.append(f"{tipo} {it.get('name')} [{it.get('id')}]{tam_s} ({mime.split('.')[-1]})")
    return "\n".join(linhas) if linhas else "(vazio)"


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    cmd = args[0]

    if cmd == "listar":
        fid = args[1] if len(args) > 1 else "root"
        print(_fmt_lista(listar_pasta(fid)))
    elif cmd == "buscar":
        termo = args[1]
        print(_fmt_lista(buscar_arquivos(termo)))
    elif cmd == "info":
        print(json.dumps(info_arquivo(args[1]), ensure_ascii=False, indent=1)[:3000])
    elif cmd == "criar_pasta":
        nome = args[1]
        pai = args[2] if len(args) > 2 else "root"
        nid = criar_pasta(nome, pai)
        print(f"[OK] Pasta criada: {nid}" if nid else "[ERRO] Não criou")
    elif cmd == "mover":
        ok = mover_arquivo(args[1], args[2])
        print("[OK] movido" if ok else "[ERRO] falha ao mover")
    elif cmd == "renomear":
        ok = renomear(args[1], args[2])
        print("[OK] renomeado" if ok else "[ERRO] falha ao renomear")
    elif cmd == "ler":
        print(json.dumps(ler_arquivo(args[1]), ensure_ascii=False, indent=1)[:3000])
    elif cmd == "estrutura":
        fid = args[1] if len(args) > 1 else "root"
        print(json.dumps(estrutura(fid), ensure_ascii=False, indent=1)[:5000])
    elif cmd == "sobre":
        print(json.dumps(sobre(), ensure_ascii=False, indent=1)[:2000])
    else:
        print(__doc__)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())