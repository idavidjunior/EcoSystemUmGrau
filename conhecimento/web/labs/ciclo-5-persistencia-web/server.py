# Ciclo 5 — Persistência Web
# Micro-lab: sqlite3 puro (stdlib) sobre HTTP com migrations versionadas,
# transações atômicas e estado persistido em disco. Evidência do bloco G.
# Uso: python server.py [:porta] [:caminho_do_banco]   |   python test_persistencia.py
#
# Decisão: manter ThreadingHTTPServer stdlib (ADR-003) — sem dependência nova.
# sqlite3 é stdlib. Banco em data/app.db por padrão (criado no primeiro uso,
# com migrations aplicadas em ordem).

import json
import os
import sqlite3
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

_AQUI = os.path.dirname(os.path.abspath(__file__))
_INDEX = os.path.join(_AQUI, "index.html")

MIGRACOES = [
    # v1: criação inicial da tabela de notas
    """
    CREATE TABLE IF NOT EXISTS notas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        conteudo TEXT NOT NULL DEFAULT '',
        arquivada INTEGER NOT NULL DEFAULT 0,
        criada_em TEXT NOT NULL DEFAULT (datetime('now')),
        atualizada_em TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,
    # v2: índice de busca por título + flag de arquivado
    """
    CREATE INDEX IF NOT EXISTS idx_notas_titulo ON notas(titulo);
    """,
]


class Dashboard:
    """Fachada de persistência: aplica migrations, isola transações e
    garante escrita atômica (commit/rollback) — ponto único do Lab."""

    def __init__(self, caminho_db):
        self.caminho_db = caminho_db
        self._lock = threading.Lock()
        conn = self._nova_con_cabecalho()
        try:
            self._aplicar_migracoes(conn)
        finally:
            conn.close()

    def _nova_con_cabecalho(self):
        os.makedirs(os.path.dirname(self.caminho_db), exist_ok=True)
        conn = sqlite3.connect(self.caminho_db, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _versao_atual(self, conn):
        row = conn.execute("PRAGMA user_version").fetchone()
        return row[0] if row else 0

    def _aplicar_migracoes(self, conn):
        try:
            atual = self._versao_atual(conn)
            for i in range(atual, len(MIGRACOES)):
                conn.executescript(MIGRACOES[i])
                conn.execute(f"PRAGMA user_version={i + 1}")
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _con(self):
        return self._nova_con_cabecalho()

    def listar_notas(self, incluir_arquivadas=False):
        with self._lock:
            conn = self._con()
            try:
                sql = ("SELECT id, titulo, conteudo, criada_em, atualizada_em "
                       "FROM notas")
                if not incluir_arquivadas:
                    sql += " WHERE arquivada = 0"
                sql += " ORDER BY id DESC"
                rows = [dict(r) for r in conn.execute(sql).fetchall()]
                return rows
            finally:
                conn.close()

    def obter_nota(self, nota_id):
        with self._lock:
            conn = self._con()
            try:
                row = conn.execute(
                    "SELECT id, titulo, conteudo, criada_em, atualizada_em "
                    "FROM notas WHERE id = ?", (nota_id,)).fetchone()
                return dict(row) if row else None
            finally:
                conn.close()

    def criar_nota(self, titulo, conteudo=""):
        with self._lock:
            conn = self._con()
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
            conn = self._con()
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
            conn = self._con()
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
            conn = self._con()
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
            conn = self._con()
            try:
                total = conn.execute(
                    "SELECT COUNT(*) AS n FROM notas").fetchone()["n"]
                return {
                    "banco": os.path.basename(self.caminho_db),
                    "schema_version": self._versao_atual(conn),
                    "notas": total,
                    "arquivo": self.caminho_db,
                }
            finally:
                conn.close()


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, status, texto, ctype="text/html; charset=utf-8"):
        body = texto.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _erro(self, status, msg, **extra):
        payload = {"erro": msg}
        payload.update(extra)
        self._json(status, payload)

    def _rota(self):
        return self.path.split("?", 1)[0].rstrip("/") or "/"

    def _bonita(self):
        return {"pretty": "true"} in self.headers.get("Accept", "")

    def _ids(self, path):
        prefixo = "/api/notas/"
        if path.startswith(prefixo):
            v = path[len(prefixo):]
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
                try:
                    with open(_INDEX, "r", encoding="utf-8") as f:
                        return self._html(200, f.read())
                except OSError:
                    return self._erro(500, "index.html indisponivel")
            if path == "/api/health":
                return self._json(200, {
                    "status": "ok", "bloco": "G", "ciclo": 5,
                    "db": self.server.dashboard.estatisticas(),
                })
            if path == "/api/explode":
                raise RuntimeError("erro interno forcado")
            if path == "/api/notas":
                return self._json(200, {"notas": self.server.dashboard.listar_notas()})
            nota_id = self._ids(path)
            if nota_id is not None:
                nota = self.server.dashboard.obter_nota(nota_id)
                if nota is None:
                    return self._erro(404, "nota nao encontrada", id=nota_id)
                return self._json(200, nota)
            return self._erro(404, "recurso nao encontrado", url=self.path)
        except Exception as exc:
            return self._erro(500, f"erro interno do servidor: {exc}")

    def do_POST(self):
        try:
            path = self._rota()
            if path != "/api/notas":
                if path == "/api/notas/":
                    return self._erro(404, "recurso nao encontrado", url=self.path)
                return self._erro(404, "recurso nao encontrado", url=self.path)
            corpo = self._ler_corpo()
            if not isinstance(corpo, dict):
                return self._erro(400, "corpo JSON invalido")
            titulo = corpo.get("titulo")
            if not titulo or not str(titulo).strip():
                return self._erro(400, "campo titulo obrigatorio")
            nota_id = self.server.dashboard.criar_nota(
                str(titulo).strip(), str(corpo.get("conteudo", "") or ""))
            return self._json(201, {"id": nota_id, "mensagem": "nota criada"})
        except Exception as exc:
            return self._erro(500, f"erro interno do servidor: {exc}")

    def do_PUT(self):
        try:
            path = self._rota()
            nota_id = self._ids(path)
            if nota_id is None:
                return self._erro(404, "recurso nao encontrado", url=self.path)
            corpo = self._ler_corpo()
            if not isinstance(corpo, dict):
                return self._erro(400, "corpo JSON invalido")
            titulo = corpo.get("titulo")
            if titulo is not None and not str(titulo).strip():
                return self._erro(400, "campo titulo nao pode ser vazio")
            ok = self.server.dashboard.atualizar_nota(
                nota_id,
                titulo=str(titulo).strip() if titulo is not None else None,
                conteudo=corpo.get("conteudo"),
            )
            if not ok:
                return self._erro(404, "nota nao encontrada", id=nota_id)
            return self._json(200, {"ok": True, "id": nota_id})
        except Exception as exc:
            return self._erro(500, f"erro interno do servidor: {exc}")

    def do_PATCH(self):
        try:
            path = self._rota()
            nota_id = self._ids(path)
            if nota_id is None:
                return self._erro(404, "recurso nao encontrado", url=self.path)
            ok = self.server.dashboard.arquivar_nota(nota_id)
            if not ok:
                return self._erro(404, "nota nao encontrada", id=nota_id)
            return self._json(200, {"ok": True, "id": nota_id, "arquivada": True})
        except Exception as exc:
            return self._erro(500, f"erro interno do servidor: {exc}")

    def do_DELETE(self):
        try:
            path = self._rota()
            nota_id = self._ids(path)
            if nota_id is None:
                return self._erro(404, "recurso nao encontrado", url=self.path)
            ok = self.server.dashboard.excluir_nota(nota_id)
            if not ok:
                return self._erro(404, "nota nao encontrada", id=nota_id)
            return self._json(200, {"ok": True, "id": nota_id, "excluida": True})
        except Exception as exc:
            return self._erro(500, f"erro interno do servidor: {exc}")

    def log_message(self, *_args):
        pass


def start(porta=8095, caminho_db=None):
    if caminho_db is None:
        caminho_db = os.path.join(_AQUI, "data", "app.db")
    srv = ThreadingHTTPServer(("127.0.0.1", porta), Handler)
    srv.dashboard = Dashboard(caminho_db)
    return srv


def main():
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8095
    caminho_db = sys.argv[2] if len(sys.argv) > 2 else None
    srv = start(porta, caminho_db)
    print(f"persistencia web em http://127.0.0.1:{porta} "
          f"(db={srv.dashboard.caminho_db})", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()