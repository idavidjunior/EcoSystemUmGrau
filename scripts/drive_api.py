"""drive_api.py — cliente DIRETO da Google Drive API v3 (sem Composio).

Usa credenciais OAuth próprias (scripts/.env: GOOGLE_CLIENT_ID,
GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN) geradas por google_drive_auth.py.
Todas as chamadas vão direto a https://www.googleapis.com/drive/v3.

Substitui o drive_utils baseado em Composio com acesso 100% próprio.
Mesma interface: listar_pasta, buscar_arquivos, info_arquivo, criar_pasta,
mover_arquivo, renomear, ler_arquivo, estrutura, sobre, changes.

Uso CLI (idêntico ao drive_utils):
  python scripts/drive_api.py listar [folder_id]
  python scripts/drive_api.py buscar "termo"
  python scripts/drive_api.py info <id>
  python scripts/drive_api.py criar_pasta <nome> [pai]
  python scripts/drive_api.py mover <id> <destino>
  python scripts/drive_api.py renomear <id> <novo>
  python scripts/drive_api.py estrutura [folder_id]
  python scripts/drive_api.py sobre
"""
import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
AUTH = Path(__file__).resolve().parent / "google_drive_auth.py"

import importlib.util
_spec = importlib.util.spec_from_file_location("gdauth", str(AUTH))
_auth = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_auth)

API = "https://www.googleapis.com/drive/v3"


def _api(method, path, params=None, body=None):
    """Chamada autenticada à API v3. Levanta exceção em erro HTTP."""
    token = _auth.obter_access_token()
    if not token:
        raise RuntimeError("Sem refresh token. Rode: python scripts/google_drive_auth.py")
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read().decode("utf-8", "replace")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace") if e.fp else ""
        raise RuntimeError(f"HTTP {e.code}: {raw[:300]}")


# ---------- Funções (mesma interface do drive_utils) ----------

def listar_pasta(folder_id="root"):
    params = {"q": f"'{folder_id}' in parents and trashed = false",
              "fields": "files(id,name,mimeType,size,modifiedTime)",
              "pageSize": "1000", "pageToken": None}
    out = []
    while True:
        p = {k: v for k, v in params.items() if v is not None}
        data = _api("GET", "/files", p)
        out.extend(data.get("files", []))
        if not data.get("nextPageToken"):
            break
        params["pageToken"] = data["nextPageToken"]
    return out


def buscar_arquivos(termo):
    params = {"q": f"name contains '{termo}' and trashed = false",
              "fields": "files(id,name,mimeType,size)", "pageSize": "100"}
    data = _api("GET", "/files", params)
    return data.get("files", [])


def info_arquivo(file_id):
    return _api("GET", f"/files/{urllib.parse.quote(file_id)}",
                {"fields": "*", "supportsAllDrives": "true"})


def criar_pasta(nome, parent_id="root"):
    data = _api("POST", "/files",
                body={"name": nome, "mimeType": "application/vnd.google-apps.folder",
                      "parents": [parent_id]})
    return data.get("id")


def mover_arquivo(file_id, destino_id):
    info = _api("GET", f"/files/{urllib.parse.quote(file_id)}",
                {"fields": "parents", "supportsAllDrives": "true"})
    pais = info.get("parents", [])
    if destino_id not in pais:
        pais.append(destino_id)
    data = _api("PATCH", f"/files/{urllib.parse.quote(file_id)}",
                params={"supportsAllDrives": "true"},
                body={"addParents": destino_id,
                      "removeParents": ",".join(p for p in pais if p != destino_id)})
    return data.get("id") is not None


def renomear(file_id, novo_nome):
    data = _api("PATCH", f"/files/{urllib.parse.quote(file_id)}",
                params={"supportsAllDrives": "true"}, body={"name": novo_nome})
    return data.get("name") == novo_nome


def ler_arquivo(file_id):
    """Baixa arquivo para um arquivo local temp e devolve o caminho + metadados."""
    meta = info_arquivo(file_id)
    nome = meta.get("name", "arquivo")
    mime = meta.get("mimeType", "")
    import tempfile
    path = Path(tempfile.gettempdir()) / f"drive_{file_id[:12]}_{nome}"
    token = _auth.obter_access_token()
    req = urllib.request.Request(meta.get("downloadUrl") or f"{API}/files/{urllib.parse.quote(file_id)}?alt=media&supportsAllDrives=true")
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=120) as resp:
        path.write_bytes(resp.read())
    return {"nome": nome, "mimeType": mime, "path": str(path), "size": path.stat().st_size}


def estrutura(folder_id="root", max_depth=3, _depth=0):
    if _depth >= max_depth:
        return []
    saida = []
    for it in listar_pasta(folder_id):
        mime = it.get("mimeType", "")
        no = {"id": it.get("id"), "name": it.get("name"),
              "tipo": "pasta" if mime == "application/vnd.google-apps.folder" else "arquivo",
              "mime": mime}
        if no["tipo"] == "pasta":
            no["filhos"] = estrutura(it.get("id"), max_depth, _depth + 1)
        saida.append(no)
    return saida


def sobre():
    return _api("GET", "/about", {"fields": "user,storageQuota,maxImportSizes"})


def changes(token=None, include_removed=True):
    """Lista mudanças desde o token. Retorna (changes, novo_token)."""
    if not token:
        # Token inicial: usa o mais recente? Não é trivial sem startPageToken.
        # Usamos changes com página inicial vazia apenas se token informado.
        return [], None
    params = {"pageToken": token, "pageSize": "100", "includeRemoved": "true" if include_removed else "false"}
    data = _api("GET", "/changes", params)
    return data.get("changes", []), data.get("newStartPageToken")


def start_page_token():
    data = _api("GET", "/changes/startPageToken", {})
    return data.get("startPageToken")


# ---------- CLI ----------

def _fmt(itens):
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
    try:
        if cmd == "listar":
            print(_fmt(listar_pasta(args[1] if len(args) > 1 else "root")))
        elif cmd == "buscar":
            print(_fmt(buscar_arquivos(args[1])))
        elif cmd == "info":
            print(json.dumps(info_arquivo(args[1]), ensure_ascii=False, indent=1)[:3000])
        elif cmd == "criar_pasta":
            nid = criar_pasta(args[1], args[2] if len(args) > 2 else "root")
            print(f"[OK] Pasta criada: {nid}" if nid else "[ERRO]")
        elif cmd == "mover":
            print("[OK] movido" if mover_arquivo(args[1], args[2]) else "[ERRO]")
        elif cmd == "renomear":
            print("[OK] renomeado" if renomear(args[1], args[2]) else "[ERRO]")
        elif cmd == "ler":
            print(json.dumps(ler_arquivo(args[1]), ensure_ascii=False, indent=1)[:2000])
        elif cmd == "estrutura":
            print(json.dumps(estrutura(args[1] if len(args) > 1 else "root"), ensure_ascii=False, indent=1)[:5000])
        elif cmd == "sobre":
            print(json.dumps(sobre(), ensure_ascii=False, indent=1)[:2000])
        elif cmd == "token":
            print("startPageToken:", start_page_token())
        else:
            print(__doc__)
            return 1
    except Exception as e:
        print(f"[ERRO] {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())