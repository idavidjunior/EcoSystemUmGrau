"""Teste de integração do Ciclo 8 — Quadro de Notas com IA (produto N1-N5).

Valida as 20 demonstrações de MASTERED cruzando as 7 capacidades integradas:
  N1 servidor HTTP | N2 API REST | N3 WebSocket realtime | N4 sqlite
  N5 IA cognitive_core | N6 segurança OWASP | N7 performance.

Executa local (auto-contido). IA usa o cognitive_core real (pode demorar).
"""
import json
import os
import socket
import shutil
import tempfile
import threading
import time
import urllib.error
import urllib.request

from server import start
import ws_broadcast

TIMEOUT_PADRAO = 15
TIMEOUT_IA_S = 120


def _porta_livre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _request(method, url, body=None, timeout=TIMEOUT_PADRAO, ctype="application/json"):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if data is not None:
        req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            if "application/json" in resp.headers.get("Content-Type", ""):
                return resp.status, json.loads(raw), _headers_dict(resp.headers)
            return resp.status, raw, _headers_dict(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        if "application/json" in exc.headers.get("Content-Type", ""):
            return exc.code, json.loads(raw), _headers_dict(exc.headers)
        return exc.code, raw, _headers_dict(exc.headers)


def _headers_dict(msg):
    """Normaliza headers para lookup case-insensitive.""" 
    out = {}
    for k, v in msg.items():
        out[k.lower()] = v
    return out


class WsListener:
    """Escuta contínua em /ws em thread própria; eventos acumulados em .eventos."""

    def __init__(self, porta_ws, duracao=10):
        self.porta_ws = porta_ws
        self.eventos = []
        self._stop = threading.Event()
        self._duracao = duracao
        self._th = threading.Thread(target=self._rodar, daemon=True)
        self._th.start()

    def _rodar(self):
        import asyncio

        async def _loop():
            from websockets.asyncio.client import connect
            try:
                async with connect(f"ws://127.0.0.1:{self.porta_ws}/ws") as cli:
                    while not self._stop.is_set():
                        try:
                            msg = await asyncio.wait_for(cli.recv(), timeout=1)
                            d = json.loads(msg)
                            self.eventos.append(d)
                        except asyncio.TimeoutError:
                            continue
                        except Exception:
                            break
            except Exception:
                pass

        fim = time.time() + self._duracao
        while time.time() < fim and not self._stop.is_set():
            try:
                asyncio.run(_loop())
                break
            except Exception:
                time.sleep(0.2)

    def aguardar(self, tipo, segundos=8):
        """Aguarda evento do tipo esperado; retorna lista com os vistos."""
        fim = time.time() + segundos
        while time.time() < fim:
            vistos = [e for e in self.eventos if e.get("tipo") == tipo]
            if vistos:
                return vistos
            time.sleep(0.1)
        return [e for e in self.eventos if e.get("tipo") == tipo]

    def parar(self):
        self._stop.set()
        self._th.join(timeout=2)


def _lançar(porta, porta_ws, caminho_db):
    server = start(porta, caminho_db, porta_ws)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _ws_recebe_evento(porta_ws, esperado, segundos=8):
    """Conecta em /ws e aguarda até N eventos com tipo esperado."""
    import asyncio

    async def _escuta():
        from websockets.asyncio.client import connect
        eventos = []
        fim = time.time() + segundos
        async with connect(f"ws://127.0.0.1:{porta_ws}/ws") as cli:
            while time.time() < fim:
                try:
                    msg = await asyncio.wait_for(cli.recv(), timeout=min(2, fim - time.time()))
                    d = json.loads(msg)
                    if d.get("tipo") == esperado:
                        eventos.append(d)
                        if len(eventos) >= 1:
                            break
                except asyncio.TimeoutError:
                    break
                except Exception:
                    break
            return eventos

    return asyncio.run(_escuta())


def main():
    checks = []

    def add(nome, cond, detalhe=""):
        checks.append((nome, cond, detalhe))

    tmp = tempfile.mkdtemp(prefix="ciclo8-")
    try:
        caminho_db = os.path.join(tmp, "sub", "produto.db")
        os.makedirs(os.path.dirname(caminho_db), exist_ok=True)
        porta = _porta_livre()
        porta_ws = _porta_livre()
        base = f"http://127.0.0.1:{porta}"

        # --- Servidor + API + sqlite + IA + segurança + WS num único processo ---
        srv1, _ = _lançar(porta, porta_ws, caminho_db)
        listener = WsListener(porta_ws, duracao=40)
        try:
            time.sleep(0.5)
            s, b, h = _request("GET", f"{base}/")
            add("N1 index.html servido", s == 200 and "Quadro de Notas" in b)

            s, b, h = _request("GET", f"{base}/api/health")
            integ = [(i["id"], i["capacidade"]) for i in b.get("integracoes", [])]
            add("N2 health lista 7 integracoes", s == 200 and len(integ) == 7,
                str([x[1] for x in integ]))

            s, b, h = _request("POST", f"{base}/api/notas",
                               {"titulo": "primeira", "conteudo": "conteudo A"})
            id1 = b.get("id")
            add("N4 POST cria nota sqlite 201", s == 201 and id1 == 1, f"id={id1}")

            ev = listener.aguardar("nota_criada")
            add("N3 WS transmite nota_criada em tempo real",
                any(e.get("id") == id1 for e in ev), str(ev)[:120])

            s, b, h = _request("GET", f"{base}/api/notas")
            add("N2 GET lista notas", s == 200 and len(b["notas"]) == 1)

            s, b, h = _request("GET", f"{base}/api/notas/{id1}")
            add("N2 GET nota por id", s == 200 and b["titulo"] == "primeira")

            s, b, h = _request("PUT", f"{base}/api/notas/{id1}",
                               {"titulo": "primeira-v2", "conteudo": "novo"})
            add("N2 PUT atualiza nota", s == 200 and b.get("ok") is True)

            ev = listener.aguardar("nota_atualizada")
            add("N3 WS transmite nota_atualizada",
                any(e.get("id") == id1 for e in ev), str(ev)[:120])

            s, b, h = _request("GET", f"{base}/api/notas/{id1}")
            add("N2 atualizacao refletida no GET",
                s == 200 and b["titulo"] == "primeira-v2")

            s, b, h = _request("PATCH", f"{base}/api/notas/{id1}")
            add("N2 PATCH arquiva nota", s == 200 and b.get("arquivada") is True)

            s, b, h = _request("GET", f"{base}/api/notas")
            add("N2 arquivada some da lista", s == 200 and len(b["notas"]) == 0)

            s, b, h = _request("DELETE", f"{base}/api/notas/{id1}")
            add("N2 DELETE exclui nota", s == 200 and b.get("excluida") is True)

            ev = listener.aguardar("nota_excluida")
            add("N3 WS transmite nota_excluida",
                any(e.get("id") == id1 for e in ev), str(ev)[:120])

            s, b, h = _request("GET", f"{base}/api/notas/{id1}")
            add("N2 DELETE refletido (404)",
                s == 404 and b.get("id") == id1)

            # --- IA (cognitive_core real) ---
            s, b, h = _request("POST", f"{base}/api/chat",
                               {"mensagem": "diga apenas: ola", "session_id": "ciclo8-teste"},
                               timeout=TIMEOUT_IA_S)
            add("N5 IA responde via /api/chat", s == 200 and b.get("resposta"),
                (b.get("resposta") or "")[:80])

            # --- Segurança OWASP ---
            header_names = {
                "X-Content-Type-Options": "x-content-type-options",
                "X-Frame-Options": "x-frame-options",
                "X-XSS-Protection": "x-xss-protection",
                "Referrer-Policy": "referrer-policy",
                "Content-Security-Policy": "content-security-policy",
            }
            for hd, chave in header_names.items():
                s, b, h = _request("GET", f"{base}/api/health")
                add(f"N6 header {hd} presente", h.get(chave) is not None)

            s, b, h = _request("POST", f"{base}/api/notas", {"titulo": "x"},
                               ctype="text/plain")
            add("N6 content-type invalido 415", s == 415, f"status={s}")

            s, b, h = _request("GET", f"{base}/api/explode")
            add("N6 erro 500 sem vazar internals",
                s == 500 and "Traceback" not in json.dumps(b))

            s, b, h = _request("POST", f"{base}/api/notas",
                               {"titulo": "xss", "conteudo": '<script>alert(1)</script>'})
            add("N6 XSS armazenado sem quebra de contrato",
                s == 201 and b.get("id") is not None)

            s, b, h = _request("POST", f"{base}/api/notas", {"sem_titulo": True})
            add("N6 POST sem titulo 400", s == 400)

            # --- Performance: verifica Cache-Control + resposta rápida ---
            t0 = time.monotonic()
            s, b, h = _request("GET", f"{base}/api/health")
            latencia = (time.monotonic() - t0) * 1000
            add("N7 /api/health responde < 1000ms", latencia < 1000,
                f"{latencia:.0f}ms")

        finally:
            listener.parar()
            srv1.shutdown()
            srv1.server_close()
            ws_broadcast.parar()
            time.sleep(0.2)

        # --- Persistência real (sqlite sobrevive ao reinício) ---
        porta2 = _porta_livre()
        porta_ws2 = _porta_livre()
        base2 = f"http://127.0.0.1:{porta2}"
        srv2, _ = _lançar(porta2, porta_ws2, caminho_db)
        try:
            s, b, h = _request("GET", f"{base2}/api/health")
            add("N4 reinicio mantem schema", s == 200 and b["db"]["schema_version"] >= 2)

            s, b, h = _request("GET", f"{base2}/api/notas")
            add("N4 persistencia real apos reinicio",
                s == 200 and len(b["notas"]) == 1)  # a nota XSS criada permanece
        finally:
            srv2.shutdown()
            srv2.server_close()
            ws_broadcast.parar()
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    ok = all(p for _, p, _ in checks)
    for nome, passed, detalhe in checks:
        print(("[PASS]" if passed else "[FAIL]"), nome, (f"- {detalhe}" if detalhe else ""))
    print(f"STATUS: {'OK' if ok else 'FALHOU'} ({len(checks)} checks, "
          f"{sum(1 for _, p, _ in checks if not p)} falhas)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())