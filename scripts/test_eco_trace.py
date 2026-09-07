"""Teste da costura de tracing (isolado, sem poluir o runtime real)."""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

import tempfile
import eco_trace


def main():
    tmp = tempfile.mkdtemp(prefix="eco_trace_teste_")
    eco_trace.TRACES_DIR = os.path.join(tmp, "traces")
    os.environ.pop("ECO_TRACE", None)
    t = eco_trace.trace("tarefa-muda")
    assert t.get("ok") and t.get("trace_id"), t
    with eco_trace.span(t, "etapa"):
        pass
    assert eco_trace.finalizar(t).get("ok")
    assert not os.path.exists(eco_trace.TRACES_DIR), "desligada não grava"
    os.environ["ECO_TRACE"] = "1"
    try:
        t2 = eco_trace.trace("tarefa-grava", {"email": "a@b.com"})
        with eco_trace.span(t2, "etapa-lenta"):
            pass
        eco_trace.finalizar(t2, ok=False, motivo="erro-teste")
        arquivos = os.listdir(eco_trace.TRACES_DIR)
        assert len(arquivos) == 1, arquivos
        texto = open(os.path.join(eco_trace.TRACES_DIR, arquivos[0]),
                     encoding="utf-8").read()
        assert "a@b.com" not in texto, "segredo vazou no trace"
        assert "trace-fim" in texto and "span-fim" in texto, texto
    finally:
        os.environ.pop("ECO_TRACE", None)
    print("[OK] eco_trace costura passou")


if __name__ == "__main__":
    main()
