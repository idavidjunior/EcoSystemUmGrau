"""Teste do endurecimento da agenda (estado temporário, sem poluir o real)."""
import os
import sys
import tempfile
from datetime import datetime, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE, "scripts"))

import runtime_state
import eco_agenda
from eco_agenda import agendar, executar_vencidas, watchdog, _caminho_seguro


def main():
    real_state = runtime_state.STATE_FILE
    real_checks = runtime_state.CHECKPOINTS_DIR
    tmp = tempfile.mkdtemp(prefix="eco_agenda_dura_")
    eco_agenda.LOCK = os.path.join(tmp, "agenda.lock")
    eco_agenda.LOG = os.path.join(tmp, "agenda.log")
    eco_agenda.HEARTBEAT = os.path.join(tmp, "heartbeat.json")
    try:
        runtime_state.STATE_FILE = os.path.join(tmp, "state.json")
        runtime_state.CHECKPOINTS_DIR = os.path.join(tmp, "checkpoints")
        ok_c, _ = _caminho_seguro("scripts/eco_agenda.py")
        assert ok_c, "caminho interno deve passar"
        ok_e, _ = _caminho_seguro("../../Windows/System32/x.py")
        assert not ok_e, "escape com .. deve ser rejeitado"
        r0 = agendar("evil", "script", {"script": "../../evil.py"},
                     recorrencia="once",
                     em=(datetime.now() + timedelta(minutes=5)).isoformat())
        assert not r0.get("ok"), r0
        passado = (datetime.now() - timedelta(seconds=5)).isoformat(timespec="seconds")
        r1 = agendar("ok uma vez", "nota", {"texto": "dura-ok"},
                     recorrencia="once", em=passado)
        assert r1.get("ok") and r1["tarefa"]["estado"] == "pending", r1
        r2 = executar_vencidas()
        assert r2.get("ok") and len(r2["executadas"]) == 1, r2
        d = r2["executadas"][0]
        assert d["ok"] and d.get("dispatch"), d
        estado = eco_agenda._carregar()
        t1 = [t for t in estado["agendadas"] if t["nome"] == "ok uma vez"][0]
        assert t1["estado"] == "success" and not t1["ativa"], t1
        assert len(t1["disparos"]) == 1, t1
        orig = eco_agenda._rodar_acao
        chamadas = {"n": 0}

        def flaky(tarefa, timeout=None):
            chamadas["n"] += 1
            if chamadas["n"] == 1:
                return False, "timeout após 120s (simulado)"
            return True, "[OK] segunda tentativa"

        eco_agenda._rodar_acao = flaky
        try:
            r3 = agendar("flaky", "nota", {"texto": "retry"},
                         recorrencia="once", em=passado)
            assert r3.get("ok"), r3
            r4 = executar_vencidas()
            assert r4.get("ok"), r4
            estado = eco_agenda._carregar()
            tf = [t for t in estado["agendadas"] if t["nome"] == "flaky"][0]
            assert tf["estado"] == "failed" and tf["tentativa"] == 1, tf
            assert tf["ativa"], "aguarda retry com backoff"
            tf["proxima"] = passado
            eco_agenda._salvar(estado)
            r5 = executar_vencidas()
            assert r5.get("ok"), r5
            estado = eco_agenda._carregar()
            tf = [t for t in estado["agendadas"] if t["nome"] == "flaky"][0]
            assert tf["estado"] == "success" and tf["tentativa"] == 0, tf
        finally:
            eco_agenda._rodar_acao = orig
        r6 = agendar("orfa", "nota", {"texto": "crash"},
                     recorrencia="intervalo", intervalo_s=3600)
        estado = eco_agenda._carregar()
        to = [t for t in estado["agendadas"] if t["nome"] == "orfa"][0]
        to["estado"] = "running"
        to["running_inicio"] = (datetime.now() - timedelta(seconds=901)).isoformat()
        eco_agenda._salvar(estado)
        r7 = executar_vencidas()
        assert r7.get("ok"), r7
        estado = eco_agenda._carregar()
        to = [t for t in estado["agendadas"] if t["nome"] == "orfa"][0]
        assert to["estado"] == "failed" and "crash" in to["ultimo_motivo"], to
        w1 = watchdog(janela_s=600)
        assert w1.get("ok") and not w1.get("alerta"), w1
        w2 = watchdog(janela_s=0)
        assert w2.get("alerta"), w2
        print("[OK] eco_agenda endurecida passou")
    finally:
        runtime_state.STATE_FILE = real_state
        runtime_state.CHECKPOINTS_DIR = real_checks
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
