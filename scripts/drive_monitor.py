"""drive_monitor.py — vigia o Google Drive e reporta mudanças.

Usa a API incremental de changes do Google Drive via Composio:
  GOOGLEDRIVE_GET_CHANGES_START_PAGE_TOKEN -> checkpoint
  GOOGLEDRIVE_LIST_CHANGES (pageToken)     -> mudanças desde o checkpoint

Detecta: arquivos/pastas ADICIONADOS, REMOVIDOS e MODIFICADOS.
Persiste o checkpoint e um log de eventos em JSONL. Sempre regenerável;
nunca destrutivo (só leitura).

Uso:
  python scripts/drive_monitor.py init          # primeira vez: grava linha-base
  python scripts/drive_monitor.py check         # verifica mudanças desde o último token
  python scripts/drive_monitor.py status        # mostra estado atual e últimos eventos
"""
import json
import os
import sys
import time
import importlib.util
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "mcp_composio", str(BASE / "scripts" / "mcp-composio-server.py")
)
_composio = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_composio)
_composio._load_dotenv()

COMPOSIO = _composio
STATE = BASE / "runtime" / "drive_monitor.json"
LOG = BASE / "runtime" / "drive_monitor.log"


def _executar(tools, passo):
    req = {"jsonrpc": "2.0", "id": 2000, "method": "tools/call", "params": {
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
        return [{"response": {"successful": False, "raw": txt[:300]}}]


def _ler_estado():
    try:
        if STATE.exists():
            return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"token": None, "ultimo_check": None, "eventos_total": 0}


def _salvar_estado(estado):
    try:
        STATE.parent.mkdir(parents=True, exist_ok=True)
        tmp = STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps(estado, ensure_ascii=False), encoding="utf-8")
        tmp.replace(STATE)
    except Exception as e:
        print(f"[ERRO] não salvou estado: {e}")


def _log_evento(evento):
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        evento["ts"] = datetime.now().isoformat(timespec="seconds")
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    except Exception:
        pass


def obter_token_inicial():
    tools = [{"tool_slug": "GOOGLEDRIVE_GET_CHANGES_START_PAGE_TOKEN", "arguments": {}}]
    for res in _executar(tools, "OBTENDO_TOKEN_INICIAL"):
        resp = res.get("response", {})
        if resp.get("successful"):
            d = resp.get("data", {})
            tok = d.get("startPageToken")
            if tok:
                return str(tok)
    return None


def listar_changes(token, include_removed=True):
    """Retorna (changes, novo_token). changes = lista de dicts."""
    tools = [{"tool_slug": "GOOGLEDRIVE_LIST_CHANGES",
              "arguments": {"pageToken": token, "pageSize": 100,
                            "includeRemoved": include_removed}}]
    for res in _executar(tools, "LISTANDO_CHANGES"):
        resp = res.get("response", {})
        if resp.get("successful"):
            d = resp.get("data", {}) or resp.get("data_preview", {})
            changes = d.get("changes") or []
            novo = d.get("newStartPageToken")
            return changes, (str(novo) if novo else None)
    return [], None


def _classificar(c):
    """Classifica um change em evento legível."""
    removed = c.get("removed") or c.get("deleted") or False
    added = c.get("added") or False
    f = c.get("file") or {}
    fid = f.get("id") or c.get("fileId") or "?"
    nome = f.get("name") or c.get("fileId") or "?"
    mime = f.get("mimeType", "")
    tipo = "pasta" if mime == "application/vnd.google-apps.folder" else "arquivo"
    if removed:
        return {"tipo_evento": "removido", "id": fid, "nome": nome, "tipo": tipo}
    if added:
        return {"tipo_evento": "adicionado", "id": fid, "nome": nome, "tipo": tipo,
                "mime": mime, "size": f.get("size")}
    return {"tipo_evento": "modificado", "id": fid, "nome": nome, "tipo": tipo,
            "mime": mime, "size": f.get("size")}


def init():
    """Grava a linha-base: token inicial."""
    estado = _ler_estado()
    tok = estado.get("token") or obter_token_inicial()
    if not tok:
        print("[ERRO] não conseguiu token inicial")
        return 1
    estado["token"] = tok
    estado["ultimo_check"] = datetime.now().isoformat(timespec="seconds")
    estado["eventos_total"] = estado.get("eventos_total", 0)
    _salvar_estado(estado)
    print(f"[OK] Linha-base gravada. Token inicial: {tok}")
    return 0


def check():
    """Verifica mudanças desde o último token e atualiza o checkpoint."""
    estado = _ler_estado()
    tok = estado.get("token")
    if not tok:
        print("[INFO] Sem token. Rodando init primeiro...")
        if init() != 0:
            return 1
        estado = _ler_estado()
        tok = estado.get("token")
    changes, novo_tok = listar_changes(tok)
    eventos = [_classificar(c) for c in changes]
    for ev in eventos:
        _log_evento(ev)
        print(f"  [{ev['tipo_evento']}] {ev['tipo']}: {ev['nome']} ({ev['id']})")
    if novo_tok:
        estado["token"] = novo_tok
    estado["ultimo_check"] = datetime.now().isoformat(timespec="seconds")
    estado["eventos_total"] = estado.get("eventos_total", 0) + len(eventos)
    _salvar_estado(estado)
    print(f"\n[OK] Changes verificadas: {len(eventos)} evento(s) desde o último check.")
    return 0


def status():
    estado = _ler_estado()
    print("=== Monitor Google Drive ===")
    print(f"Token atual: {estado.get('token')}")
    print(f"Último check: {estado.get('ultimo_check')}")
    print(f"Eventos registrados: {estado.get('eventos_total')}")
    print()
    if LOG.exists():
        linhas = LOG.read_text(encoding="utf-8").strip().splitlines()
        print(f"Últimos eventos ({len(linhas)} no total):")
        for linha in linhas[-10:]:
            try:
                ev = json.loads(linha)
                print(f"  {ev.get('ts')} [{ev.get('tipo_evento')}] {ev.get('nome')} ({ev.get('id')})")
            except Exception:
                pass
    return 0


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "status"
    if cmd == "init":
        return init()
    if cmd == "check":
        return check()
    if cmd == "status":
        return status()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main())