# Ciclo 1 — Fundamentos Web
# Micro-lab: HTTP server stdlib + HTML responsivo + JSON.
# Objetivo: provar domínio de Fundamentos (bloco A/F) com evidência real.
# Uso: python server.py [:porta]  (serve / e /api/health)

import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from datetime import datetime, timezone

HTML = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Um Grau — Fundamento Web</title>
<style>
:root { color-scheme: dark; --bg:#1e1e2e; --tx:#cdd6f4; --tx3:#6c7086; --acc:#89b4fa; --in:#181825; --bdr:#45475a; }
body { font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--tx); max-width:40rem; margin:4rem auto; padding:0 1rem; }
h1 { color:var(--tx); }
a { color:var(--acc); }
pre { background:var(--in); color:var(--tx); border:1px solid var(--bdr); padding:.75rem; border-radius:.5rem; overflow:auto; }
</style>
</head>
<body>
<h1>Um Grau: fundamento web</h1>
<p>Servido por <code>http.server</code> da stdlib. JSON em <code>/api/health</code>.</p>
<pre id="saida">carregando…</pre>
<script>
fetch('/api/health')
  .then(r => r.json())
  .then(j => { document.getElementById('saida').textContent = JSON.stringify(j, null, 2); })
  .catch(e => { document.getElementById('saida').textContent = 'erro: ' + e.message; });
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/":
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path == "/api/health":
            self._json(200, {
                "status": "ok",
                "servidor": "http.server stdlib",
                "url": self.path,
                "tempo": datetime.now(timezone.utc).isoformat(),
            })
        else:
            self._json(404, {"erro": "nao encontrado", "url": self.path})

    def log_message(self, *_args):
        pass


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    srv = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    print(f"servidor em http://127.0.0.1:{porta}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()