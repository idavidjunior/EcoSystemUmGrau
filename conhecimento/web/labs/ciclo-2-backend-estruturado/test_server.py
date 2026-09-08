"""Teste de integração auto-contido do Ciclo 2 — Backend estruturado."""
import json
import threading
import urllib.error
import urllib.request

from server import start


def _request(method, url, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))


def _request_raw(method, url, raw):
    req = urllib.request.Request(url, data=raw, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
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
        s, b = _request("GET", f"{base}/")
        add("GET / raiz", s == 200 and b.get("nome") == "ciclo-2-mini-api")

        s, b = _request("GET", f"{base}/api/health")
        add("GET /api/health", s == 200 and b.get("status") == "ok")

        s, b = _request("GET", f"{base}/api/soma?a=2&b=3")
        add("GET /api/soma 2+3", s == 200 and b.get("soma") == 5)

        s, b = _request("GET", f"{base}/api/soma?a=x&b=1")
        add("GET /api/soma param inválido", s == 400 and "erro" in b)

        s, b = _request("GET", f"{base}/api/items")
        add("GET /api/items", s == 200 and b.get("itens"))

        s, b = _request("GET", f"{base}/api/items/7")
        add("GET /api/items/7", s == 200 and b.get("id") == 7)

        s, b = _request("GET", f"{base}/api/items/abc")
        add("GET /api/items/abc 404", s == 404 and "erro" in b)

        s, b = _request("POST", f"{base}/api/items", {"nome": "borracha"})
        add("POST /api/items 201", s == 201 and b.get("nome") == "borracha")

        s, b = _request("POST", f"{base}/api/items", {"sem": "nome"})
        add("POST sem nome 400", s == 400 and "erro" in b)

        s, b = _request_raw("POST", f"{base}/api/items", b"{quebrado")
        add("POST json inválido 400", s == 400 and "erro" in b)

        s, b = _request("DELETE", f"{base}/api/items/3")
        add("DELETE /api/items/3", s == 200 and b.get("deletado") == 3)

        s, b = _request("PUT", f"{base}/api/items/3")
        add("PUT /api/items/3 405", s == 405 and "erro" in b)

        s, b = _request("GET", f"{base}/api/nao-existe")
        add("GET rota inexistente 404", s == 404 and "erro" in b)

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