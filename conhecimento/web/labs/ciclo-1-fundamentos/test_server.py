# Ciclo 1 — Teste de validação do micro-lab Fundamentos.
# Inicia o servidor em thread, faz requisições reais com httpx e valida.
# Sem kill de processo: encerra sozinho. Rodar: python test_server.py

import json
import threading
import time
import urllib.request

import httpx

import server  # noqa: E402  (mesmo diretório)

PORTA = 8091
BASE = f"http://127.0.0.1:{PORTA}"


def iniciar_servidor():
    srv = server.ThreadingHTTPServer(("127.0.0.1", PORTA), server.Handler)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    return srv


def testar():
    srv = iniciar_servidor()
    time.sleep(0.3)
    falhas = []

    try:
        html = httpx.get(f"{BASE}/", timeout=5)
        assert html.status_code == 200, f"/ status {html.status_code}"
        ct = html.headers.get("content-type", "")
        assert "text/html" in ct, f"/ content-type {ct}"
        assert "um grau" in html.text.lower(), "/ nao contem 'um grau'"

        health = httpx.get(f"{BASE}/api/health", timeout=5)
        assert health.status_code == 200, f"/api/health status {health.status_code}"
        dados = health.json()
        assert dados["status"] == "ok", f"status campo {dados}"
        assert dados["servidor"] == "http.server stdlib", dados
        assert "tempo" in dados, "sem campo tempo"

        js = httpx.get(f"{BASE}/script.js", timeout=5)
        assert js.status_code == 404, f"/script.js status {js.status_code}"
        assert js.json()["erro"] == "nao encontrado", js.text

        raw = urllib.request.urlopen(f"{BASE}/api/health", timeout=5)
        conteudo = json.loads(raw.read().decode("utf-8"))
        assert conteudo["status"] == "ok", "urllib health"

    except Exception as exc:  # noqa: BLE001
        falhas.append(f"{type(exc).__name__}: {exc}")

    srv.shutdown()
    srv.server_close()

    if falhas:
        print("FALHOU:")
        for f in falhas:
            print(" -", f)
        return 1
    print("OK: servidor stdlib, HTML, JSON, 404, urllib — tudo validado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(testar())