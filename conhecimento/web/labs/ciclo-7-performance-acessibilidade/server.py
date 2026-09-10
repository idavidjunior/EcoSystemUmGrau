# Ciclo 7 — Performance e acessibilidade
# Micro-lab: servidor servindo duas versões de uma página real (antes/depois)
# para medição de Core Web Vitals (LCP/CLS/INP) com Playwright e checagens
# WCAG básicas. Evidência dos blocos J (performance) e D (UI/UX acessível).
# Uso: python server.py [:porta]   |   python test_performance.py
#
# Decisões: ThreadingHTTPServer stdlib (ADR-003); medição CWV via Playwright
# + PerformanceObserver (ADR-007); sem dependência JS de build.

import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_AQUI = os.path.dirname(os.path.abspath(__file__))
_ANTES = os.path.join(_AQUI, "index-antes.html")
_DEPOIS = os.path.join(_AQUI, "index-depois.html")
_HERO = os.path.join(_AQUI, "assets", "hero.svg")

# Atraso artificial na resposta da imagem hero. Duplicamos o cenário de rede
# lenta para que LCP/CLS sejam mensuráveis em loopback (rede local é rápida
# demais para produzir dados). Na versão 'depois' o preload dispara o
# download antes, então mesmo com o mesmo atraso o LCP melhora.
HERO_DELAY_S = 0.5


def ler_arquivo(path):
    with open(path, "rb") as f:
        return f.read()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, body, ctype):
        data = body if isinstance(body, bytes) else body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/antes"):
            self._send(200, ler_arquivo(_ANTES), "text/html; charset=utf-8")
        elif path == "/corrigida":
            self._send(200, ler_arquivo(_DEPOIS), "text/html; charset=utf-8")
        elif path == "/assets/hero.svg":
            time.sleep(HERO_DELAY_S)  # simula rede lenta para LCP mensurável
            self._send(200, ler_arquivo(_HERO), "image/svg+xml")
        elif path == "/api/health":
            self._send(200, '{"status":"ok"}', "application/json")
        else:
            self._send(404, '{"erro":"nao encontrado"}', "application/json")

    def log_message(self, *args):
        pass  # silencia log de acesso


def criar_servidor(porta=8097):
    return ThreadingHTTPServer(("127.0.0.1", porta), Handler)


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8097
    print("Ciclo 7 servidor em http://127.0.0.1:%d" % porta)
    print("Paginas: / (antes) e /corrigida")
    criar_servidor(porta).serve_forever()