"""Teste de fumaça do sandbox isolado (stdlib pura)."""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

from eco_sandbox import executar, docker_disponivel


def main():
    r1 = executar("")
    assert not r1.get("ok") and r1.get("modo") == "nenhum", r1
    r2 = executar("print(1)", linguagem="ruby")
    assert not r2.get("ok"), r2
    r3 = executar("print('sandbox-ok')", timeout=30)
    assert r3.get("ok") and "sandbox-ok" in r3.get("stdout", ""), r3
    assert r3.get("modo") in ("docker", "degradado"), r3
    r4 = executar("import subprocess; print(1)", timeout=30)
    if not docker_disponivel():
        assert not r4.get("ok") and r4.get("modo") == "degradado", r4
    from eco_client import EcoClient
    eco = EcoClient(base=BASE)
    r5 = eco.sandbox_executar("print('via-cliente')", timeout=30)
    assert r5.get("ok") and "via-cliente" in r5.get("stdout", ""), r5
    print("[OK] eco_sandbox fumaça passou (modo=%s)" % r3.get("modo"))


if __name__ == "__main__":
    main()
