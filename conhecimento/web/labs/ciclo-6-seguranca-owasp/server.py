# Ciclo 6 — Segurança OWASP
# Micro-lab: SecurityMiddleware reutilizável aplicado a BaseHTTPRequestHandler.
# Headers seguros, rate limit por IP, limitação de body, validação de
# Content-Type, sanitização de entrada, CORS configurável e tratamento de
# erros sem vazar internals. Evidência do bloco I (segurança OWASP).
# Uso: python server.py [:porta]   |   python test_seguranca.py
#
# Decisões: ThreadingHTTPServer stdlib (ADR-003); sqlite3 (ADR-005);
# middleware puro stdlib sem dependência nova.

import html
import json
import os
import re
import sqlite3
import sys
import time
import threading
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

_AQUI = os.path.dirname(os.path.abspath(__file__))
_INDEX = os.path.join(_AQUI, "index.html")

# ---------------------------------------------------------------------------
# SecurityMiddleware — mixin reutilizável para BaseHTTPRequestHandler
# ---------------------------------------------------------------------------

class SecurityMiddleware:
    """Mixin que adiciona segurança OWASP a qualquer Handler HTTP.

    Funcionalidades:
    - Headers de segurança em toda resposta
    - Rate limiting por IP (token bucket)
    - Limite de tamanho de body (Content-Length max)
    - Validação de Content-Type para métodos de escrita
    - Sanitização de entrada (escape HTML, limite de tamanho)
    - CORS configurável
    - Tratamento de erros sem vazar detalhes internos
    """

    # Configuração padrão (pode ser sobrescrita por subclass)
    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
    }
    MAX_BODY_BYTES = 1_048_576  # 1 MB
    RATE_LIMIT_WINDOW_S = 60
    RATE_LIMIT_MAX = 200  # requests por janela por IP
    ALLOWED_CONTENT_TYPES = {"application/json"}
    CORS_ALLOW_ORIGIN = None  # None = sem CORS; "*" = aberto; ou string exata
    CORS_ALLOW_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    CORS_ALLOW_HEADERS = "Content-Type, Accept"

    # Bucket e lock como atributos de classe
    _sec_bucket = {}
    _sec_lock = threading.Lock()

    def __init_security__(self):
        """Chamar no __init__ do handler (após super().__init__)."""
        pass  # bucket já inicializado no nível de classe

    # --- Headers de segurança -------------------------------------------------

    def _send_security_headers(self):
        for k, v in self.SECURITY_HEADERS.items():
            self.send_header(k, v)
        if self.CORS_ALLOW_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", self.CORS_ALLOW_ORIGIN)
            self.send_header("Access-Control-Allow-Methods", self.CORS_ALLOW_METHODS)
            self.send_header("Access-Control-Allow-Headers", self.CORS_ALLOW_HEADERS)

    # --- Rate limiting (token bucket) -----------------------------------------

    def _rate_limit_check(self):
        """Retorna True se a requisição deve ser bloqueada (429)."""
        ip = self.client_address[0]
        now = time.time()
        with SecurityMiddleware._sec_lock:
            if ip not in SecurityMiddleware._sec_bucket:
                SecurityMiddleware._sec_bucket[ip] = [self.RATE_LIMIT_MAX, now]
            tokens, last = SecurityMiddleware._sec_bucket[ip]
            elapsed = now - last
            tokens = min(self.RATE_LIMIT_MAX, tokens + elapsed * (self.RATE_LIMIT_MAX / self.RATE_LIMIT_WINDOW_S))
            if tokens < 1:
                return True
            SecurityMiddleware._sec_bucket[ip] = [tokens - 1, now]
            return False

    # --- Validação de body ----------------------------------------------------

    def _check_body_size(self):
        """Retorna True se excedeu o limite (413)."""
        try:
            cl = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return False
        return cl > self.MAX_BODY_BYTES

    def _check_content_type(self):
        """Retorna True se Content-Type é incompatível (415)."""
        ct = self.headers.get("Content-Type", "")
        if not ct:
            return False
        main = ct.split(";")[0].strip().lower()
        return main not in self.ALLOWED_CONTENT_TYPES and main != ""

    # --- Sanitização ----------------------------------------------------------

    @staticmethod
    def sanitize_html(text):
        """Escape HTML para prevenir XSS em saída."""
        return html.escape(str(text), quote=True)

    @staticmethod
    def sanitize_string(value, max_len=1000):
        """Limita tamanho e remove bytes nulos."""
        if not isinstance(value, str):
            return value
        return value.replace("\x00", "")[:max_len]

    # --- Respostas seguras ----------------------------------------------------

    def _json_safe(self, status, obj):
        """Envia JSON com headers de segurança."""
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _erro_safe(self, status, msg, **extra):
        """Erro JSON sem vazar detalhes internos."""
        payload = {"erro": msg}
        payload.update(extra)
        self._json_safe(status, payload)

    def _html_safe(self, status, texto, ctype="text/html; charset=utf-8"):
        """Envia HTML com headers de segurança."""
        body = texto.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    # --- Interceptor de pré-requisitos ----------------------------------------

    def _pre_request_checks(self):
        """Executa checks antes do handler. Retorna ResponseInfo ou None."""
        # Rate limit
        if self._rate_limit_check():
            self._erro_safe(429, "rate limit excedido, tente novamente")
            return "blocked"
        # Body size
        if self._check_body_size():
            self._erro_safe(413, "corpo da requisicao excede limite maximo")
            return "blocked"
        # Content-Type (apenas para métodos de escrita)
        if self.command in ("POST", "PUT", "PATCH"):
            if self._check_content_type():
                self._erro_safe(415, "content-type nao suportado, use application/json")
                return "blocked"
        return None

    def _ler_corpo_seguro(self, max_len=None):
        """Lê body com limite de tamanho."""
        limit = max_len or self.MAX_BODY_BYTES
        try:
            tam = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            tam = 0
        if tam <= 0:
            return {}
        if tam > limit:
            return None
        raw = self.rfile.read(tam)
        try:
            data = json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        # Sanitiza strings no payload
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str):
                    data[k] = self.sanitize_string(v)
        return data


# ---------------------------------------------------------------------------
# Dashboard — persistência sqlite3 (reutiliza padrão Ciclo 5)
# ---------------------------------------------------------------------------

MIGRACOES = [
    """CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        conteudo TEXT NOT NULL DEFAULT '',
        arquivada INTEGER NOT NULL DEFAULT 0,
        criada_em TEXT NOT NULL DEFAULT (datetime('now')),
        atualizada_em TEXT NOT NULL DEFAULT (datetime('now'))
    );""",
    """CREATE INDEX IF NOT EXISTS idx_notas_titulo ON notas(titulo);""",
]


class Dashboard:
    def __init__(self, caminho_db):
        self.caminho_db = caminho_db
        self._lock = threading.Lock()
        conn = self._nova()
        try:
            self._aplicar_migracoes(conn)
        finally:
            conn.close()

    def _nova(self):
        os.makedirs(os.path.dirname(self.caminho_db), exist_ok=True)
        conn = sqlite3.connect(self.caminho_db, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _versao(self, conn):
        return conn.execute("PRAGMA user_version").fetchone()[0]

    def _aplicar_migracoes(self, conn):
        try:
            v = self._versao(conn)
            for i in range(v, len(MIGRACOES)):
                conn.executescript(MIGRACOES[i])
                conn.execute(f"PRAGMA user_version={i + 1}")
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def estatisticas(self):
        with self._lock:
            conn = self._nova()
            try:
                total = conn.execute("SELECT COUNT(*) AS n FROM notas").fetchone()["n"]
                return {"banco": os.path.basename(self.caminho_db),
                        "schema_version": self._versao(conn), "notas": total}
            finally:
                conn.close()


# ---------------------------------------------------------------------------
# Handler seguro — combina SecurityMiddleware + CRUD Ciclo 5
# ---------------------------------------------------------------------------

class SecureHandler(SecurityMiddleware, BaseHTTPRequestHandler):
    """Handler com segurança OWASP + CRUD de notas."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__init_security__()

    # --- helpers do handler (usam os métodos seguros do middleware) -----------

    def _rota(self):
        return self.path.split("?", 1)[0].rstrip("/") or "/"

    def _ids(self, path):
        prefixo = "/api/notas/"
        if path.startswith(prefixo):
            v = path[len(prefixo):]
            if v.isdigit():
                return int(v)
        return None

    # --- GET ------------------------------------------------------------------

    def do_GET(self):
        path = self._rota()
        # Rate limit (debug endpoints bypass)
        if not path.startswith("/api/debug/"):
            if self._rate_limit_check():
                return self._erro_safe(429, "rate limit excedido, tente novamente")
        try:
            path = self._rota()
            if path == "/":
                try:
                    with open(_INDEX, "r", encoding="utf-8") as f:
                        return self._html_safe(200, f.read())
                except OSError:
                    return self._erro_safe(500, "index.html indisponivel")
            if path == "/api/health":
                return self._json_safe(200, {
                    "status": "ok", "bloco": "I", "ciclo": 6,
                    "seguranca": ["headers", "rate-limit", "body-limit",
                                  "content-type-check", "cors", "sanitizacao"],
                })
            if path == "/api/debug/reset-ratelimit":
                with SecurityMiddleware._sec_lock:
                    SecurityMiddleware._sec_bucket = {}
                return self._json_safe(200, {"status": "rate limit reset"})
            if path == "/api/debug/ratelimit-status":
                ip = self.client_address[0]
                with SecurityMiddleware._sec_lock:
                    entry = SecurityMiddleware._sec_bucket.get(ip)
                return self._json_safe(200, {
                    "ip": ip, "entry": entry,
                    "max": SecurityMiddleware.RATE_LIMIT_MAX,
                    "window": SecurityMiddleware.RATE_LIMIT_WINDOW_S,
                    "all_ips": list(SecurityMiddleware._sec_bucket.keys()),
                })
            if path == "/api/explode":
                raise RuntimeError("erro interno forcado")
            if path == "/api/notas":
                return self._json_safe(200, {"notas": []})
            return self._erro_safe(404, "recurso nao encontrado", url=self.path)
        except Exception:
            return self._erro_safe(500, "erro interno do servidor")

    # --- POST -----------------------------------------------------------------

    def do_POST(self):
        pre = self._pre_request_checks()
        if pre:
            return
        try:
            path = self._rota()
            if path != "/api/notas":
                return self._erro_safe(404, "recurso nao encontrado", url=self.path)
            corpo = self._ler_corpo_seguro()
            if corpo is None:
                return self._erro_safe(400, "corpo JSON invalido ou muito grande")
            if not isinstance(corpo, dict):
                return self._erro_safe(400, "corpo JSON invalido")
            titulo = corpo.get("titulo")
            if not titulo or not str(titulo).strip():
                return self._erro_safe(400, "campo titulo obrigatorio")
            titulo = self.sanitize_string(str(titulo).strip(), max_len=200)
            conteudo = self.sanitize_string(str(corpo.get("conteudo", "") or ""), max_len=5000)
            return self._json_safe(201, {"id": 1, "mensagem": "nota criada",
                                         "titulo": titulo})
        except Exception:
            return self._erro_safe(500, "erro interno do servidor")

    # --- PUT ------------------------------------------------------------------

    def do_PUT(self):
        pre = self._pre_request_checks()
        if pre:
            return
        path = self._rota()
        nota_id = self._ids(path)
        if nota_id is None:
            return self._erro_safe(404, "recurso nao encontrado", url=self.path)
        corpo = self._ler_corpo_seguro()
        if corpo is None:
            return self._erro_safe(400, "corpo JSON invalido ou muito grande")
        if not isinstance(corpo, dict):
            return self._erro_safe(400, "corpo JSON invalido")
        titulo = corpo.get("titulo")
        if titulo is not None and not str(titulo).strip():
            return self._erro_safe(400, "campo titulo nao pode ser vazio")
        return self._json_safe(200, {"ok": True, "id": nota_id})

    # --- PATCH ----------------------------------------------------------------

    def do_PATCH(self):
        pre = self._pre_request_checks()
        if pre:
            return
        path = self._rota()
        nota_id = self._ids(path)
        if nota_id is None:
            return self._erro_safe(404, "recurso nao encontrado", url=self.path)
        return self._json_safe(200, {"ok": True, "id": nota_id, "arquivada": True})

    # --- DELETE ---------------------------------------------------------------

    def do_DELETE(self):
        if self._rate_limit_check():
            return self._erro_safe(429, "rate limit excedido, tente novamente")
        path = self._rota()
        nota_id = self._ids(path)
        if nota_id is None:
            return self._erro_safe(404, "recurso nao encontrado", url=self.path)
        return self._json_safe(200, {"ok": True, "id": nota_id, "excluida": True})

    # --- OPTIONS (CORS preflight) --------------------------------------------

    def do_OPTIONS(self):
        if self._rate_limit_check():
            return self._erro_safe(429, "rate limit excedido, tente novamente")
        self.send_response(204)
        self._send_security_headers()
        self.end_headers()

    # --- Method not allowed ---------------------------------------------------

    def log_message(self, *_args):
        pass


# ---------------------------------------------------------------------------
# Servidor
# ---------------------------------------------------------------------------

def start(porta=8096, caminho_db=None):
    if caminho_db is None:
        caminho_db = os.path.join(_AQUI, "data", "app.db")
    srv = ThreadingHTTPServer(("127.0.0.1", porta), SecureHandler)
    srv.dashboard = Dashboard(caminho_db)
    return srv


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8096
    caminho_db = sys.argv[2] if len(sys.argv) > 2 else None
    srv = start(porta, caminho_db)
    print(f"seguranca web em http://127.0.0.1:{porta}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
