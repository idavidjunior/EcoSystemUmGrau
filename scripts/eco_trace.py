"""Costura de evolução para tracing — desligada por padrão.

NÃO é o tracing completo (ver specs/eco-tracing.spec.md).
É o ponto de encaixe: API estável que hoje não faz nada
e amanhã pluga o coletor sem mexer nos chamadores.

Uso futuro:
    from eco_trace import trace, span
    t = trace("minha-tarefa")
    with span(t, "etapa-lenta"):
        ...trabalho...

Ligar o rascunho local: ECO_TRACE=1 (grava runtime/traces/).
100% stdlib. Overhead zero quando desligada.
"""

import json
import os
import sys
import time
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
SCRIPTS = os.path.join(BASE, "scripts")
RUNTIME = os.path.join(BASE, "runtime")
TRACES_DIR = os.path.join(RUNTIME, "traces")
TETO_BYTES = 50 * 1024 * 1024
ATRIBUTO_MAX = 2000


def _ligada():
    return os.environ.get("ECO_TRACE", "0") == "1"


def _ok(**campos):
    out = {"ok": True}
    out.update(campos)
    return out


def _redigir(valor):
    try:
        from memory_engine import redigir_sensivel
        return redigir_sensivel(str(valor))[:ATRIBUTO_MAX]
    except Exception:
        return str(valor)[:ATRIBUTO_MAX]


def _gravar(linha):
    try:
        os.makedirs(TRACES_DIR, exist_ok=True)
        total = sum(f.stat().st_size for f in Path(TRACES_DIR).glob("*.jsonl"))
        if total > TETO_BYTES:
            return
        dia = datetime.now().strftime("%Y-%m-%d")
        with open(os.path.join(TRACES_DIR, "%s.jsonl" % dia), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps(linha, ensure_ascii=False)[:4000] + "\n")
    except Exception:
        pass


def trace(nome, atributos=None):
    """Abre um trace; desligada retorna só ids sem gravar."""
    t = {"trace_id": uuid.uuid4().hex[:16], "nome": nome,
         "inicio": time.time()}
    if _ligada():
        _gravar({"tipo": "trace-inicio", "trace_id": t["trace_id"],
                 "nome": _redigir(nome),
                 "atributos": {k: _redigir(v) for k, v in
                               (atributos or {}).items()}})
    return _ok(**t)


@contextmanager
def span(trace_info, nome, atributos=None, pai=None):
    """Contexto de span com duração medida e falha suave."""
    s = {"span_id": uuid.uuid4().hex[:8],
         "trace_id": (trace_info or {}).get("trace_id", ""),
         "nome": nome, "inicio": time.time()}
    try:
        yield s
        erro = ""
    except Exception as e:
        erro = str(e)
        raise
    finally:
        if _ligada():
            dur = round(time.time() - s["inicio"], 3)
            _gravar({"tipo": "span-fim", "trace_id": s["trace_id"],
                     "span_id": s["span_id"], "nome": _redigir(nome),
                     "duracao_s": dur, "erro": _redigir(erro),
                     "pai": pai or ""})


def finalizar(trace_info, ok=True, motivo=""):
    """Fecha o trace com resultado resumido."""
    try:
        if _ligada() and trace_info:
            dur = round(time.time() - trace_info.get("inicio", time.time()), 3)
            _gravar({"tipo": "trace-fim",
                     "trace_id": trace_info.get("trace_id", ""),
                     "ok": bool(ok), "duracao_s": dur,
                     "motivo": _redigir(motivo)})
    except Exception:
        pass
    return _ok()
