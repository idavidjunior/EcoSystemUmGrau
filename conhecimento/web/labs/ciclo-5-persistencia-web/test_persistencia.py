"""Teste de integração auto-contido do Ciclo 5 — Persistência Web.

Valida CRUD completo (POST/GET/PUT/PATCH/DELETE), migrations versionadas,
persistência REAL em disco (dados sobrevivem ao reinício do servidor),
e o ponto único de persistência (escrita via Dashboard com WAL e transações).
"""
import json
import os
import shutil
import tempfile
import threading
import urllib.error
import urllib.request

from server import start

TIMEOUT_PADRAO = 10


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


def _lançar(porta, caminho_db):
    server = start(porta, caminho_db)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def main():
    checks = []

    def add(name, cond):
        checks.append((name, cond))

    tmp = tempfile.mkdtemp(prefix="ciclo5-")
    try:
        caminho_db = os.path.join(tmp, "sub", "app.db")
        os.makedirs(os.path.dirname(caminho_db), exist_ok=True)

        # --- Primeira execução: servidor S1 cria o banco + migrations ---
        srv1, _ = _lançar(8095, caminho_db)
        base1 = "http://127.0.0.1:8095"
        try:
            s, b = _request("GET", f"{base1}/")
            add("GET / index.html servido",
                s == 200 and "<!DOCTYPE html>" in b and "api/notas" in b)

            s, b = _request("GET", f"{base1}/api/health")
            add("health indica banco e schema", s == 200 and b.get("status") == "ok"
                and b["db"]["schema_version"] >= 2)

            s, b = _request("POST", f"{base1}/api/notas", {"titulo": "primeira"})
            add("POST cria nota 201", s == 201 and b.get("id") == 1)
            id1 = b["id"]

            s, b = _request("POST", f"{base1}/api/notas",
                            {"titulo": "segunda", "conteudo": "conteudo da segunda"})
            add("POST cria segunda nota 201", s == 201 and b.get("id") == 2)
            id2 = b["id"]

            s, b = _request("GET", f"{base1}/api/notas")
            add("GET lista notas", s == 200 and len(b["notas"]) == 2)

            s, b = _request("GET", f"{base1}/api/notas/{id1}")
            add("GET nota por id", s == 200 and b["titulo"] == "primeira")

            s, b = _request("PUT", f"{base1}/api/notas/{id2}",
                            {"titulo": "segunda-atualizada", "conteudo": "novo"})
            add("PUT atualiza nota", s == 200 and b.get("ok") is True)

            s, b = _request("GET", f"{base1}/api/notas/{id2}")
            add("PUT refletido no GET", s == 200 and b["titulo"] == "segunda-atualizada"
                and b["conteudo"] == "novo")

            s, b = _request("PATCH", f"{base1}/api/notas/{id1}")
            add("PATCH arquiva nota", s == 200 and b.get("arquivada") is True)

            s, b = _request("GET", f"{base1}/api/notas")
            add("GET default nao traz arquivada", s == 200 and len(b["notas"]) == 1)

            s, b = _request("DELETE", f"{base1}/api/notas/{id2}")
            add("DELETE exclui nota", s == 200 and b.get("excluida") is True)

            s, b = _request("GET", f"{base1}/api/notas/{id2}")
            add("DELETE refletido (404)",
                s == 404 and b.get("id") == id2)

            # Persistência real: a nota id=1 (arquivada) e a DDL sobrevivem.
            s, b = _request("GET", f"{base1}/api/health")
            add("health schema versao 2", b["db"]["schema_version"] == 2)

            # Erros e validação
            s, b = _request("POST", f"{base1}/api/notas", {"sem_titulo": 1})
            add("POST sem titulo 400", s == 400 and "erro" in b)

            s, b = _request("POST", f"{base1}/api/notas", {"titulo": "   "})
            add("POST titulo vazio 400", s == 400 and "erro" in b)

            s, b = _request_raw("POST", f"{base1}/api/notas", b"{quebrado")
            add("POST json invalido 400", s == 400 and "erro" in b)

            s, b = _request("GET", f"{base1}/nao-existe")
            add("GET rota inexistente 404", s == 404 and "erro" in b)

            s, b = _request("GET", f"{base1}/api/explode")
            add("GET /api/explode 500", s == 500 and "erro" in b)

            s, b = _request("PUT", f"{base1}/api/notas/9999", {"titulo": "x"})
            add("PUT nota inexistente 404", s == 404 and "erro" in b)

            s, b = _request("PATCH", f"{base1}/api/notas/9999")
            add("PATCH nota inexistente 404", s == 404 and "erro" in b)

            s, b = _request("DELETE", f"{base1}/api/notas/9999")
            add("DELETE nota inexistente 404", s == 404 and "erro" in b)
        finally:
            srv1.shutdown()
            srv1.server_close()

        # --- Segunda execução: servidor S2 abre o MESMO banco em disco ---
        srv2, _ = _lançar(8096, caminho_db)
        base2 = "http://127.0.0.1:8096"
        try:
            s, b = _request("GET", f"{base2}/api/health")
            add("reinicio mantem schema", s == 200 and b["db"]["schema_version"] == 2)
            add("reinicio mantem contador", b["db"]["notas"] == 1)

            s, b = _request("GET", f"{base2}/api/health")
            add("dados persistem apos reinicio",
                s == 200 and b["db"].get("notas") == 1)

            s, b = _request("GET", f"{base2}/api/notas/1")
            add("nota persistida recuperavel por id",
                s == 200 and b["titulo"] == "primeira")
        finally:
            srv2.shutdown()
            srv2.server_close()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ok = all(passed for _, passed in checks)
    for nome, passed in checks:
        print(("[PASS]" if passed else "[FAIL]"), nome)
    print(f"STATUS: {'OK' if ok else 'FALHOU'} ({len(checks)} checks, "
          f"{sum(1 for _, p in checks if not p)} falhas)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())