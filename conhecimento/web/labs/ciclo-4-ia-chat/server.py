# Ciclo 4 — IA como Interface Web
# Micro-lab: endpoint POST que conversa com o cognitive_core real do ecossistema;
# chat simples em HTML/JS consumindo fetch. Evidência do bloco H (IA/LLM em web).
# Uso: python server.py [:porta]   |   python test_ia_chat.py

import json
import os
import sys

# Raiz do projeto (pai de scripts/) para importar o cognitive_core real.
_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from scripts.cognitive_core import process_user_input

_AQUI = os.path.dirname(os.path.abspath(__file__))
_INDEX = os.path.join(_AQUI, "index.html")

TIMEOUT_IA_S = 90  # process_user_input pode envolver LLM router/memória


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _erro(self, status, msg, **extra):
        payload = {"erro": msg}
        payload.update(extra)
        self._json(status, payload)

    def _html(self, status, texto, ctype="text/html; charset=utf-8"):
        body = texto.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _rota(self):
        return self.path.split("?", 1)[0].rstrip("/") or "/"

    def _ler_corpo(self):
        try:
            tam = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            tam = 0
        if tam <= 0:
            return {}
        try:
            return json.loads(self.rfile.read(tam).decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def do_GET(self):
        try:
            path = self._rota()
            if path == "/":
                try:
                    with open(_INDEX, "r", encoding="utf-8") as f:
                        return self._html(200, f.read())
                except OSError:
                    return self._erro(500, "index.html indisponivel")
            if path == "/api/health":
                return self._json(200, {"status": "ok", "bloco": "H", "ciclo": 4})
            if path == "/api/explode":
                raise RuntimeError("erro interno forcado")
            if path == "/api/chat":
                return self._erro(405, "metodo nao permitido (use POST)", url=self.path)
            return self._erro(404, "recurso nao encontrado", url=self.path)
        except Exception:
            return self._erro(500, "erro interno do servidor")

    def do_POST(self):
        try:
            path = self._rota()
            if path != "/api/chat":
                if path == "/api/intent":
                    return self._erro(405, "metodo nao permitido (use GET)", url=self.path)
                return self._erro(404, "recurso nao encontrado", url=self.path)
            corpo = self._ler_corpo()
            if not isinstance(corpo, dict):
                return self._erro(400, "corpo JSON invalido")
            mensagem = corpo.get("mensagem")
            if not mensagem or not str(mensagem).strip():
                return self._erro(400, "campo mensagem obrigatorio")
            session_id = corpo.get("session_id") or "ciclo4-web"
            contexto = corpo.get("contexto") or None
            resultado = process_user_input(
                str(mensagem),
                contexto=contexto,
                session_id=str(session_id),
            )
            if not isinstance(resultado, dict):
                return self._json(200, {"resposta": str(resultado)})
            return self._json(200, {
                "resposta": resultado.get("response", ""),
                "intent": (resultado.get("state") or {}).get("intent"),
                "summary": resultado.get("summary"),
            })
        except Exception as exc:
            return self._erro(500, f"erro interno do servidor: {exc}")

    def do_PUT(self):
        return self._erro(405, "metodo nao permitido", url=self.path)

    def do_PATCH(self):
        return self._erro(405, "metodo nao permitido", url=self.path)

    def log_message(self, *_args):
        pass


def start(porta=8094):
    return ThreadingHTTPServer(("127.0.0.1", porta), Handler)


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8094
    srv = start(porta)
    print(f"chat IA em http://127.0.0.1:{porta}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()