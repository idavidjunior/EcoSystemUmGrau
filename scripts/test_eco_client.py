"""Teste de fumaça do cliente Python embutido (stdlib pura)."""
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

from eco_client import EcoClient


def main():
    eco = EcoClient(base=BASE)
    r1 = eco.check()
    assert isinstance(r1, dict) and "integridade" in r1, r1
    r2 = eco.status()
    assert r2.get("ok") and "estado" in r2, r2
    r3 = eco.memoria_buscar(texto="teste", limite=2)
    assert r3.get("ok") and "memorias" in r3, r3
    r4 = eco.contexto_carregar("")
    assert r4.get("ok") and r4.get("vazio"), r4
    r5 = eco.memoria_stats()
    assert isinstance(r5, dict), r5
    r6 = eco.checkpoint("teste-fumaca")
    assert r6.get("ok"), r6
    print("[OK] eco_client fumaça passou")


if __name__ == "__main__":
    main()
