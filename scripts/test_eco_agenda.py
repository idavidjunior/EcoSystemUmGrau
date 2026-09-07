"""Teste isolado da agenda (usa estado temporário, sem poluir o real)."""
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

import runtime_state
from eco_agenda import agendar, listar, cancelar, executar_vencidas


def main():
    real_state = runtime_state.STATE_FILE
    tmp = tempfile.mkdtemp(prefix="eco_agenda_teste_")
    try:
        runtime_state.STATE_FILE = os.path.join(tmp, "state.json")
        runtime_state.CHECKPOINTS_DIR = os.path.join(tmp, "checkpoints")
        r1 = agendar("", "nota")
        assert not r1.get("ok"), r1
        r2 = agendar("x", "shell-malicioso")
        assert not r2.get("ok"), r2
        passado = (datetime.now() - timedelta(seconds=5)).isoformat(timespec="seconds")
        r3 = agendar("nota teste", "nota", {"texto": "tick-ok"},
                     recorrencia="once", em=passado)
        assert r3.get("ok"), r3
        r4 = agendar("janela teste", "checkpoint", {"rotulo": "agenda-teste"},
                     recorrencia="janela", hora="09:00")
        assert r4.get("ok") and r4["tarefa"]["proxima"], r4
        r5 = agendar("intervalo teste", "pendencia", {"texto": "p-teste"},
                     recorrencia="intervalo", intervalo_s=3600)
        assert r5.get("ok"), r5
        r6 = agendar("curto", "nota", recorrencia="intervalo", intervalo_s=5)
        assert not r6.get("ok"), r6
        r7 = executar_vencidas()
        assert r7.get("ok"), r7
        nomes = [e["nome"] for e in r7["executadas"]]
        assert "nota teste" in nomes, r7
        estado = json.load(open(runtime_state.STATE_FILE, encoding="utf-8"))
        once = [t for t in estado["agendadas"] if t["nome"] == "nota teste"][0]
        assert not once["ativa"], once
        r8 = cancelar(r4["tarefa"]["id"])
        assert r8.get("ok") and not r8["tarefa"]["ativa"], r8
        r9 = executar_vencidas()
        assert r9.get("ok") and r9["executadas"] == [], r9
        print("[OK] eco_agenda isolada passou")
    finally:
        runtime_state.STATE_FILE = real_state
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
