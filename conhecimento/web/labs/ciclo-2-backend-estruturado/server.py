# Ciclo 2 — Backend Estruturado
# Micro-lab: mini-API stdlib com rotas múltiplas, parâmetros, status codes
# corretos (200/201/400/404/405/500) e erros JSON consistentes.
# Objetivo: provar domínio de Backend estruturado (bloco F) com evidência real.
# Uso: python server.py [:porta]   |   python test_server.py

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROTAS_VALIDAS = {
    "/": {"GET"},
    "/api/health": {"GET"},
    "/api/soma": {"GET"},
    "/api/items": {"GET", "POST"},
    "/api/items/<id>": {"GET", "DELETE"},
    "/api/explode": {"GET"},
}


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

    def _rota(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        return path

    def _ids(self, path):
        if path.startswith("/api/items/"):
            v = path[len("/api/items/"):]
            if v.isdigit():
                return int(v)
        return None

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
                return self._json(200, {
                    "nome": "ciclo-2-mini-api",
                    "rotas": sorted(ROTAS_VALIDAS),
                    "docs": "GET /api/health | GET /api/explode | GET /api/soma?a=2&b=3 | GET/POST /api/items | GET/DELETE /api/items/<id>",
                })
            if path == "/api/health":
                return self._json(200, {"status": "ok", "bloco": "F", "ciclo": 2})
            if path == "/api/explode":
                raise RuntimeError("erro interno forcado")
            if path == "/api/soma":
                from urllib.parse import parse_qs, urlsplit
                qs = parse_qs(urlsplit(self.path).query)
                try:
                    a = int(qs.get("a", [""])[0])
                    b = int(qs.get("b", [""])[0])
                except (ValueError, IndexError):
                    return self._erro(400, "parametros a e b devem ser inteiros", url=self.path)
                return self._json(200, {"a": a, "b": b, "soma": a + b})
            if path == "/api/items":
                return self._json(200, {"itens": [1, 2, 3]})
            item = self._ids(path)
            if item is not None:
                return self._json(200, {"id": item, "nome": f"item-{item}"})
            return self._erro(404, "recurso nao encontrado", url=self.path)
        except Exception:
            return self._erro(500, "erro interno do servidor")

    def do_POST(self):
        path = self._rota()
        if path != "/api/items":
            return self._erro(404, "recurso nao encontrado", url=self.path)
        corpo = self._ler_corpo()
        if not isinstance(corpo, dict):
            return self._erro(400, "corpo JSON invalido")
        nome = corpo.get("nome")
        if not nome:
            return self._erro(400, "campo nome obrigatorio")
        return self._json(201, {"id": len(nome), "nome": nome})

    def do_DELETE(self):
        path = self._rota()
        item = self._ids(path)
        if item is None:
            return self._erro(404, "recurso nao encontrado", url=self.path)
        return self._json(200, {"deletado": item})

    def do_PUT(self):
        return self._erro(405, "metodo nao permitido", url=self.path)

    def do_PATCH(self):
        return self._erro(405, "metodo nao permitido", url=self.path)

    def log_message(self, *_args):
        pass


def start(porta=8092):
    return ThreadingHTTPServer(("127.0.0.1", porta), Handler)


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8092
    srv = start(porta)
    print(f"servidor em http://127.0.0.1:{porta}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()