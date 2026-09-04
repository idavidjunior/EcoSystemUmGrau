import http.server
import socketserver
import threading
import json
import sys
from pathlib import Path

DASHBOARD_HTML = Path(__file__).resolve().parent.parent / "Projetos" / "EcoDashboard" / "web" / "dashboard.html"
PORT = 8766


def _health_payload() -> dict:
    """Agrega o score unico de saude; fail-soft se o agregador falhar."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from health_aggregator import health_score
        return health_score()
    except Exception as e:
        return {"status": "ok", "dashboard": True, "score": None, "erro": str(e)}

class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/dashboard" or self.path == "/":
            try:
                html = DASHBOARD_HTML.read_text(encoding="utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(f"Erro: {e}".encode())
        elif self.path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(_health_payload(), ensure_ascii=False).encode())
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404")

    def log_message(self, format, *args):
        pass

def iniciar_dashboard():
    with socketserver.TCPServer(("0.0.0.0", PORT), Handler) as httpd:
        httpd.serve_forever()

if __name__ == "__main__":
    print(f"Dashboard HTTP rodando em http://localhost:{PORT}/dashboard")
    print(f"WebSocket bridge em ws://localhost:8765")
    t = threading.Thread(target=iniciar_dashboard, daemon=True)
    t.start()
    try:
        while True:
            import time; time.sleep(1)
    except KeyboardInterrupt:
        print("Encerrando...")
