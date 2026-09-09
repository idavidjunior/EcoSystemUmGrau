"""Teste de integração auto-contido do Ciclo 4 — IA como interface web.

Liga a um agente real (cognitive_core) via POST /api/chat e valida:
caminho feliz, intenção, corpo vazio, JSON inválido, método errado,
rota inexistente, erro interno, e a página HTML servida.
"""
import json
import threading
import urllib.error
import urllib.request

from server import start

TIMEOUT_PADRAO = 10
TIMEOUT_IA_S = 90  # process_user_input pode envolver LLM router/memória


def _request(method, url, body=None, timeout=TIMEOUT_PADRAO):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            ct = resp.headers.get("Content-Type", "")
            raw = resp.read().decode("utf-8")
            if "application/json" in ct:
                return resp.status, json.loads(raw)
            return resp.status, raw
    except urllib.error.HTTPError as exc:
        ct = exc.headers.get("Content-Type", "")
        raw = exc.read().decode("utf-8")
        if "application/json" in ct:
            return exc.code, json.loads(raw)
        return exc.code, raw


def _request_raw(method, url, raw):
    req = urllib.request.Request(url, data=raw, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_PADRAO) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def main():
    server = start()
    port = server.server_address[1]
    base = f"http://127.0.0.1:{port}"

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    checks = []

    def add(name, cond):
        checks.append((name, cond))

    try:
        # Página servida
        s, html = _request("GET", f"{base}/")
        add("GET / index.html", s == 200 and "<!DOCTYPE html>" in html and "fetch" in html)

        s, b = _request("GET", f"{base}/api/health")
        add("GET /api/health", s == 200 and b.get("status") == "ok")

        # Caminho feliz: agente real responde a conversa
        s, b = _request("POST", f"{base}/api/chat",
                        {"mensagem": "explique o que e um servidor HTTP"},
                        timeout=TIMEOUT_IA_S)
        add("POST /api/chat conversa real",
            s == 200 and isinstance(b.get("resposta"), str) and len(b["resposta"]) > 0)

        # Intenção refletida para uma pergunta
        s, b = _request("POST", f"{base}/api/chat",
                        {"mensagem": "defina arquetipo de software",
                         "session_id": "ciclo4-teste"},
                        timeout=TIMEOUT_IA_S)
        add("POST /api/chat session custom",
            s == 200 and isinstance(b.get("resposta"), str))

        # Corpo sem mensagem → 400
        s, b = _request("POST", f"{base}/api/chat", {"vazio": 1})
        add("POST sem mensagem 400", s == 400 and "erro" in b)

        # Mensagem vazia → 400
        s, b = _request("POST", f"{base}/api/chat", {"mensagem": "   "})
        add("POST mensagem vazia 400", s == 400 and "erro" in b)

        # JSON inválido → 400
        s, b = _request_raw("POST", f"{base}/api/chat", b"{quebrado")
        add("POST json inválido 400", s == 400 and "erro" in b)

        # GET no /api/chat → 405
        s, b = _request("GET", f"{base}/api/chat")
        add("GET /api/chat 405", s == 405 and "erro" in b)

        # Rota inexistente → 404
        s, b = _request("GET", f"{base}/nao-existe")
        add("GET rota inexistente 404", s == 404 and "erro" in b)

        # PUT → 405
        s, b = _request("PUT", f"{base}/api/chat")
        add("PUT /api/chat 405", s == 405 and "erro" in b)

        # Erro interno forçado → 500
        s, b = _request("GET", f"{base}/api/explode")
        add("GET /api/explode 500", s == 500 and "erro" in b)
    finally:
        server.shutdown()
        server.server_close()

    ok = all(passed for _, passed in checks)
    for name, passed in checks:
        print(("[PASS]" if passed else "[FAIL]"), name)
    print(f"STATUS: {'OK' if ok else 'FALHOU'} ({len(checks)} checks, {sum(1 for _, p in checks if not p)} falhas)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())