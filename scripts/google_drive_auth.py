"""google_drive_auth.py — autoriza o ecossistema a acessar SEU Google Drive.

Fluxo OAuth 2.0 "loopback" (desktop app): abre um mini servidor local na
porta 8080, redireciona você ao Google para autorizar, captura o code e troca
por tokens. Ao final, salva o refresh_token em scripts/.env (segredo do
ecossistema). Depois disso, NENHUM intermediário (Composio) é necessário:
todas as chamadas vão direto a https://www.googleapis.com/drive/v3.

Pré-requisito (uma vez, ~10 min no Google Cloud Console):
  1. https://console.cloud.google.com -> criar projeto
  2. Habilitar "Google Drive API"
  3. OAuth consent screen: External, adicionar seu e-mail como test user
  4. Credenciais -> Criar credencial -> OAuth Client ID -> Desktop app
  5. Copiar Client ID e Client Secret

Uso:
  python scripts/google_drive_auth.py                    # autoriza e grava token
  python scripts/google_drive_auth.py --status           # mostra se há token
  python scripts/google_drive_auth.py --refresh          # força renovação do access token
"""
import argparse
import base64
import json
import os
import socket
import sys
import threading
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ENV_FILE = Path(__file__).resolve().parent / ".env"

AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPES = ["https://www.googleapis.com/auth/drive"]
REDIRECT_PORT = 8080
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/"


def _carregar_env():
    dados = {}
    if ENV_FILE.exists():
        for linha in ENV_FILE.read_text(encoding="utf-8-sig").splitlines():
            linha = linha.strip()
            if not linha or linha.startswith("#") or "=" not in linha:
                continue
            k, _, v = linha.partition("=")
            dados[k.strip()] = v.strip()
    return dados


def _salvar_env(novos):
    dados = _carregar_env()
    dados.update(novos)
    linhas = []
    for k, v in dados.items():
        linhas.append(f"{k}={v}")
    ENV_FILE.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def _get_client():
    dados = _carregar_env()
    cid = dados.get("GOOGLE_CLIENT_ID", "").strip()
    sec = dados.get("GOOGLE_CLIENT_SECRET", "").strip()
    return cid, sec


def _servidor_loopback():
    """Abre socket local para capturar o redirect do Google (loopback)."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("localhost", REDIRECT_PORT))
    srv.listen(1)
    resultado = {}

    def tratar():
        try:
            conn, _ = srv.accept()
            req = conn.recv(4096).decode("utf-8", "replace")
            linha = req.splitlines()[0] if req else ""
            partes = linha.split()
            if len(partes) >= 2:
                path = partes[1]
                if "?" in path:
                    qs = urllib.parse.parse_qs(path.split("?", 1)[1])
                    resultado["code"] = qs.get("code", [None])[0]
                    resultado["error"] = qs.get("error", [None])[0]
            body = ("<html><body><h3>Autorizado. Pode fechar esta aba.</h3></body></html>").encode()
            conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\nContent-Length: " +
                         str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body)
            conn.close()
        except Exception as e:
            resultado["erro_local"] = str(e)

    t = threading.Thread(target=tratar, daemon=True)
    t.start()
    return srv, resultado


def _trocar_code_por_token(code):
    body = urllib.parse.urlencode({
        "code": code,
        "client_id": _get_client()[0],
        "client_secret": _get_client()[1],
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def autorizar():
    cid, sec = _get_client()
    if not cid or not sec:
        print("[ERRO] GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET ausentes em scripts/.env.")
        print("Configure no Google Cloud Console e adicione-os ao .env.")
        return 1
    srv, resultado = _servidor_loopback()
    params = {
        "client_id": cid,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",
    }
    url = AUTH_URL + "?" + urllib.parse.urlencode(params)
    print("Abra no navegador (vou tentar abrir automaticamente):")
    print(url)
    print("\nAguardando autorização...")
    try:
        webbrowser.open(url)
    except Exception:
        pass
    srv.settimeout(180)
    try:
        srv.accept()
    except socket.timeout:
        print("[ERRO] Timeout aguardando autorização.")
        return 1
    try:
        t.join(timeout=10)
    except Exception:
        pass
    srv.close()
    code = resultado.get("code")
    if not code:
        print("[ERRO] Autorização negada ou falhou:", resultado)
        return 1
    tok = _trocar_code_por_token(code)
    if "refresh_token" not in tok:
        print("[ERRO] Sem refresh_token. Verifique se o consent screen tem teste autorizado.")
        print("Resposta:", json.dumps(tok, ensure_ascii=False)[:500])
        return 1
    _salvar_env({
        "GOOGLE_ACCESS_TOKEN": tok.get("access_token", ""),
        "GOOGLE_REFRESH_TOKEN": tok["refresh_token"],
        "GOOGLE_TOKEN_EXPIRES_AT": str(int(__import__("time").time()) + int(tok.get("expires_in", 3600))),
    })
    print("[OK] Autorizado! Refresh token salvo em scripts/.env.")
    print("O acesso ao Drive agora é direto, sem Composio.")
    return 0


def obter_access_token():
    """Renova o access token via refresh token se necessário. Usado pelo drive_api."""
    dados = _carregar_env()
    cid = dados.get("GOOGLE_CLIENT_ID", "")
    sec = dados.get("GOOGLE_CLIENT_SECRET", "")
    ref = dados.get("GOOGLE_REFRESH_TOKEN", "")
    if not (cid and sec and ref):
        return None
    agora = __import__("time").time()
    exp = dados.get("GOOGLE_TOKEN_EXPIRES_AT", "0")
    try:
        if float(exp) - agora > 60 and dados.get("GOOGLE_ACCESS_TOKEN"):
            return dados["GOOGLE_ACCESS_TOKEN"]
    except Exception:
        pass
    body = urllib.parse.urlencode({
        "client_id": cid,
        "client_secret": sec,
        "refresh_token": ref,
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=body)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            tok = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERRO] Falha ao renovar token: {e}")
        return None
    at = tok.get("access_token", "")
    if at:
        _salvar_env({
            "GOOGLE_ACCESS_TOKEN": at,
            "GOOGLE_TOKEN_EXPIRES_AT": str(int(agora) + int(tok.get("expires_in", 3600))),
        })
    return at


def status():
    dados = _carregar_env()
    if dados.get("GOOGLE_REFRESH_TOKEN"):
        print("Token: PRESENTE (acesso direto configurado)")
        print("Client ID:", (dados.get("GOOGLE_CLIENT_ID") or "?")[:20] + "...")
    else:
        print("Token: AUSENTE")
        print("Rode: python scripts/google_drive_auth.py")


def main():
    ap = argparse.ArgumentParser(description="Autoriza acesso direto ao Google Drive")
    ap.add_argument("--status", action="store_true", help="mostra estado do token")
    args = ap.parse_args()
    if args.status:
        status()
        return 0
    return autorizar()


if __name__ == "__main__":
    sys.exit(main())