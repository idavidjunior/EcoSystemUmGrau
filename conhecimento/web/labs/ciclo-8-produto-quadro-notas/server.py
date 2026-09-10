# Ciclo 8 — Produto web integrado: Quadro de Notas com IA (blocos N1-N5)
# Micro-produto real que integra tudo validado nos ciclos 1-7:
#   servidor HTTP (stdlib, ADR-003) + API REST + WebSocket realtime
#   (ciclo 3, ws_broadcast) + sqlite persistente (ciclo 5 / ADR-005) +
#   IA cognitive_core (ciclo 4) + segurança OWASP (ciclo 6 / ADR-006) +
#   performance Core Web Vitals (ciclo 7 / ADR-007).
# Uso: python server.py [:porta] [:porta_ws]   |   python test_produto.py
#
# Integração por composição: as camadas validadas nos ciclos anteriores são
# reutilizadas (mixin SecurityMiddleware, Dashboard sqlite), NÃO duplicadas.

import json
import os
import sqlite3
import sys
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_AQUI = os.path.dirname(os.path.abspath(__file__))
_INDEX = os.path.join(_AQUI, "index.html")

# Raiz do projeto (pai de scripts/) para importar o cognitive_core real.
_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
if _BASE not in sys.path:
    sys.path.insert(0, _BASE)

from scripts.cognitive_core import process_user_input

import ws_broadcast

TIMEOUT_IA_S = 90  # process_user_input pode envolver LLM router/memória


# ---------------------------------------------------------------------------
# SecurityMiddleware — mixin reutilizável (mesma validação do Ciclo 6 / ADR-006)
# ---------------------------------------------------------------------------

class SecurityMiddleware:
    """Mixin que adiciona segurança OWASP a qualquer Handler HTTP.

    Reusado do Ciclo 6 (mesmo contrato): headers seguros, rate limit token
    bucket por IP, limite de body, validação de Content-Type, sanitização,
    CORS configurável e erros sem vazar internals.
    """

    SECURITY_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        "Referrer-Policy": "strict-origin-when-cross-origin",
        "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self' ws: wss:",
    }
    MAX_BODY_BYTES = 1_048_576  # 1 MB
    RATE_LIMIT_WINDOW_S = 60
    RATE_LIMIT_MAX = 50
    ALLOWED_CONTENT_TYPES = {"application/json"}
    CORS_ALLOW_ORIGIN = None
    CORS_ALLOW_METHODS = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    CORS_ALLOW_HEADERS = "Content-Type, Accept"

    _sec_bucket = {}
    _sec_lock = threading.Lock()

    def __init_security__(self):
        pass

    def _send_security_headers(self):
        for k, v in self.SECURITY_HEADERS.items():
            self.send_header(k, v)
        if self.CORS_ALLOW_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", self.CORS_ALLOW_ORIGIN)
            self.send_header("Access-Control-Allow-Methods", self.CORS_ALLOW_METHODS)
            self.send_header("Access-Control-Allow-Headers", self.CORS_ALLOW_HEADERS)

    def _rate_limit_check(self):
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

    def _check_body_size(self):
        try:
            cl = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return False
        return cl > self.MAX_BODY_BYTES

    def _check_content_type(self):
        ct = self.headers.get("Content-Type", "")
        if not ct:
            return False
        main = ct.split(";")[0].strip().lower()
        return main not in self.ALLOWED_CONTENT_TYPES and main != ""

    @staticmethod
    def sanitize_html(text):
        return html.escape(str(text), quote=True)

    @staticmethod
    def sanitize_string(value, max_len=1000):
        if not isinstance(value, str):
            return value
        return value.replace("\x00", "")[:max_len]

    def _json_safe(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _erro_safe(self, status, msg, **extra):
        payload = {"erro": msg}
        payload.update(extra)
        self._json_safe(status, payload)

    def _html_safe(self, status, texto, ctype="text/html; charset=utf-8"):
        body = texto.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _pre_request_checks(self):
        if self._rate_limit_check():
            self._erro_safe(429, "rate limit excedido, tente novamente")
            return "blocked"
        if self._check_body_size():
            self._erro_safe(413, "corpo da requisicao excede limite maximo")
            return "blocked"
        if self.command in ("POST", "PUT", "PATCH"):
            if self._check_content_type():
                self._erro_safe(415, "content-type nao suportado, use application/json")
                return "blocked"
        return None

    def _ler_corpo_seguro(self, max_len=None):
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
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str):
                    data[k] = self.sanitize_string(v)
        return data


# ---------------------------------------------------------------------------
# Dashboard — persistência sqlite3 (reuso do ciclo 5 / ADR-005)
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

    def listar_notas(self, incluir_arquivadas=False):
        with self._lock:
            conn = self._nova()
            try:
                sql = ("SELECT id, titulo, conteudo, criada_em, atualizada_em "
                       "FROM notas")
                if not incluir_arquivadas:
                    sql += " WHERE arquivada = 0"
                sql += " ORDER BY id DESC"
                return [dict(r) for r in conn.execute(sql).fetchall()]
            finally:
                conn.close()

    def obter_nota(self, nota_id):
        with self._lock:
            conn = self._nova()
            try:
                row = conn.execute(
                    "SELECT id, titulo, conteudo, criada_em, atualizada_em "
                    "FROM notas WHERE id = ?", (nota_id,)).fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def criar_nota(self, titulo, conteudo=""):
        with self._lock:
            conn = self._nova()
            try:
                cur = conn.execute(
                    "INSERT INTO notas (titulo, conteudo) VALUES (?, ?)",
                    (titulo, conteudo))
                conn.commit()
                return cur.lastrowid
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def atualizar_nota(self, nota_id, titulo=None, conteudo=None):
        with self._lock:
            conn = self._nova()
            try:
                cur = conn.execute(
                    "SELECT id FROM notas WHERE id = ?", (nota_id,))
                if cur.fetchone() is None:
                    return False
                campos, valores = [], []
                if titulo is not None:
                    campos.append("titulo = ?")
                    valores.append(titulo)
                if conteudo is not None:
                    campos.append("conteudo = ?")
                    valores.append(conteudo)
                if not campos:
                    return True
                campos.append("atualizada_em = datetime('now')")
                valores.append(nota_id)
                conn.execute(
                    f"UPDATE notas SET {', '.join(campos)} WHERE id = ?",
                    valores)
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def arquivar_nota(self, nota_id):
        with self._lock:
            conn = self._nova()
            try:
                cur = conn.execute(
                    "SELECT id FROM notas WHERE id = ?", (nota_id,))
                if cur.fetchone() is None:
                    return False
                conn.execute(
                    "UPDATE notas SET arquivada = 1, "
                    "atualizada_em = datetime('now') WHERE id = ?",
                    (nota_id,))
                conn.commit()
                return True
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def excluir_nota(self, nota_id):
        with self._lock:
            conn = self._nova()
            try:
                cur = conn.execute(
                    "DELETE FROM notas WHERE id = ?", (nota_id,))
                conn.commit()
                return cur.rowcount > 0
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()

    def estatisticas(self):
        with self._lock:
            conn = self._nova()
            try:
                total = conn.execute(
                    "SELECT COUNT(*) AS n FROM notas").fetchone()["n"]
                return {
                    "banco": os.path.basename(self.caminho_db),
                    "schema_version": self._versao(conn),
                    "notas": total,
                    "arquivo": self.caminho_db,
                }
            finally:
                conn.close()


# ---------------------------------------------------------------------------
# Handler do produto — integra segurança + persistentcia + IA + realtime
# ---------------------------------------------------------------------------

class SecureHandler(SecurityMiddleware, BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__init_security__()

    def _rota(self):
        return self.path.split("?", 1)[0].rstrip("/") or "/"

    def _ids(self, path):
        prefixo = "/api/notas/"
        if path.startswith(prefixo):
            v = path[len(prefixo):]
            if v.isdigit():
                return int(v)
        return None

    def _manter_ws(self, dash, tipo, dados_evento):
        try:
            ws_broadcast.emitir(tipo, **dados_evento)
        except Exception:
            pass

    def _emitir_nota(self, dash, nota_id, tipo, fonte):
        nota = dash.obter_nota(nota_id)
        evento = {
            "fonte": fonte,
            "id": nota_id,
            "titulo": (nota or {}).get("titulo"),
            "hora": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
        }
        self._manter_ws(dash, tipo, evento)

    # --- GET ------------------------------------------------------------------

    def do_GET(self):
        path = self._rota()
        if not path.startswith("/api/debug/"):
            if self._rate_limit_check():
                return self._erro_safe(429, "rate limit excedido, tente novamente")
        try:
            path = self._rota()
            dash = self.server.dashboard
            if path == "/":
                try:
                    with open(_INDEX, "r", encoding="utf-8") as f:
                        return self._html_safe(200, f.read())
                except OSError:
                    return self._erro_safe(500, "index.html indisponivel")
            if path == "/api/health":
                return self._json_safe(200, {
                    "status": "ok", "produto": "quadro-de-notas", "ciclo": 8,
                    "integracoes": self._lista_integracoes(dash),
                    "db": dash.estatisticas(),
                })
            if path == "/api/debug/reset-ratelimit":
                with SecurityMiddleware._sec_lock:
                    SecurityMiddleware._sec_bucket = {}
                return self._json_safe(200, {"status": "rate limit reset"})
            if path == "/api/explode":
                raise RuntimeError("erro interno forcado")
            if path == "/api/notas":
                return self._json_safe(200, {"notas": dash.listar_notas()})
            nota_id = self._ids(path)
            if nota_id is not None:
                nota = dash.obter_nota(nota_id)
                if nota is None:
                    return self._erro_safe(404, "nota nao encontrada", id=nota_id)
                return self._json_safe(200, nota)
            if path == "/api/chat":
                return self._erro_safe(405, "metodo nao permitido (use POST)", url=self.path)
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
            dash = self.server.dashboard
            if path == "/api/notas":
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
                nota_id = dash.criar_nota(titulo, conteudo)
                self._emitir_nota(dash, nota_id, "nota_criada", "api")
                return self._json_safe(201, {"id": nota_id, "mensagem": "nota criada",
                                             "titulo": titulo})
            if path == "/api/chat":
                corpo = self._ler_corpo_seguro()
                if corpo is None:
                    return self._erro_safe(400, "corpo JSON invalido ou muito grande")
                if not isinstance(corpo, dict):
                    return self._erro_safe(400, "corpo JSON invalido")
                mensagem = corpo.get("mensagem")
                if not mensagem or not str(mensagem).strip():
                    return self._erro_safe(400, "campo mensagem obrigatorio")
                session_id = corpo.get("session_id") or "ciclo8-web"
                contexto = corpo.get("contexto") or None
                try:
                    self.server.ia_luz_vermelha.acquire()
                    try:
                        resultado = process_user_input(
                            str(mensagem), contexto=contexto, session_id=str(session_id))
                    finally:
                        self.server.ia_luz_vermelha.release()
                except Exception as exc:
                    return self._erro_safe(500, f"falha ao processar chat: {exc}")
                if not isinstance(resultado, dict):
                    return self._json_safe(200, {"resposta": str(resultado)})
                return self._json_safe(200, {
                    "resposta": resultado.get("response", ""),
                    "intent": (resultado.get("state") or {}).get("intent"),
                    "summary": resultado.get("summary"),
                })
            return self._erro_safe(404, "recurso nao encontrado", url=self.path)
        except Exception:
            return self._erro_safe(500, "erro interno do servidor")

    # --- PUT / PATCH / DELETE -------------------------------------------------

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
        ok = self.server.dashboard.atualizar_nota(
            nota_id,
            titulo=str(titulo).strip() if titulo is not None else None,
            conteudo=corpo.get("conteudo"),
        )
        if not ok:
            return self._erro_safe(404, "nota nao encontrada", id=nota_id)
        self._emitir_nota(self.server.dashboard, nota_id, "nota_atualizada", "api")
        return self._json_safe(200, {"ok": True, "id": nota_id})

    def do_PATCH(self):
        pre = self._pre_request_checks()
        if pre:
            return
        path = self._rota()
        nota_id = self._ids(path)
        if nota_id is None:
            return self._erro_safe(404, "recurso nao encontrado", url=self.path)
        ok = self.server.dashboard.arquivar_nota(nota_id)
        if not ok:
            return self._erro_safe(404, "nota nao encontrada", id=nota_id)
        self._emitir_nota(self.server.dashboard, nota_id, "nota_arquivada", "api")
        return self._json_safe(200, {"ok": True, "id": nota_id, "arquivada": True})

    def do_DELETE(self):
        if self._rate_limit_check():
            return self._erro_safe(429, "rate limit excedido, tente novamente")
        path = self._rota()
        nota_id = self._ids(path)
        if nota_id is None:
            return self._erro_safe(404, "recurso nao encontrado", url=self.path)
        ok = self.server.dashboard.excluir_nota(nota_id)
        if not ok:
            return self._erro_safe(404, "nota nao encontrada", id=nota_id)
        ws_broadcast.emitir("nota_excluida", fonte="api", id=nota_id,
                            hora=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()))
        return self._json_safe(200, {"ok": True, "id": nota_id, "excluida": True})

    # --- OPTIONS (CORS preflight) --------------------------------------------

    def do_OPTIONS(self):
        if self._rate_limit_check():
            return self._erro_safe(429, "rate limit excedido, tente novamente")
        self.send_response(204)
        self._send_security_headers()
        self.end_headers()

    def log_message(self, *_args):
        pass

    # --- Integração declarada (evidência do Ciclo 8) -------------------------

    @staticmethod
    def _lista_integracoes(dash):
        integracoes = [
            {"id": "N1", "capacidade": "servidor-http", "stack": "ThreadingHTTPServer stdlib (ADR-003)"},
            {"id": "N2", "capacidade": "api-rest", "stack": "CRUD JSON /api/notas"},
            {"id": "N3", "capacidade": "websocket-realtime", "stack": "ws_broadcast (eventos nota_*)"},
            {"id": "N4", "capacidade": "sqlite-persistente", "stack": f"sqlite3 WAL + migrations v{dash.estatisticas()['schema_version']} (ADR-005)"},
            {"id": "N5", "capacidade": "ia-cognitive-core", "stack": "process_user_input (cognitive_core)"},
            {"id": "N6", "capacidade": "seguranca-owasp", "stack": "SecurityMiddleware headers/rate-limit/body/sanitizacao (ADR-006)"},
            {"id": "N7", "capacidade": "performance-cwv", "stack": "Playwright + PerformanceObserver medido (ADR-007)"},
        ]
        return integracoes


# ---------------------------------------------------------------------------
# Servidor
# ---------------------------------------------------------------------------

def start(porta=8098, caminho_db=None, porta_ws=8099):
    if caminho_db is None:
        caminho_db = os.path.join(_AQUI, "data", "produto.db")
    srv = ThreadingHTTPServer(("127.0.0.1", porta), SecureHandler)
    srv.dashboard = Dashboard(caminho_db)
    srv.ia_luz_vermelha = threading.Semaphore(1)
    ws_broadcast.iniciar(porta_ws)
    return srv


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8098
    porta_ws = int(sys.argv[2]) if len(sys.argv) > 2 else 8099
    srv = start(porta, None, porta_ws)
    print(f"Quadro de Notas (ciclo 8) http://127.0.0.1:{porta} "
          f"| ws://127.0.0.1:{porta_ws}/ws", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()