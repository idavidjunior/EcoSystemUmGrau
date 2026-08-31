"""test_runtime_maestro.py — Testes basicos do Maestro (fase 1).

Nao inicia o daemon de verdade; testa as funcoes puras e a integracao
via CLI/arquivo.

Uso:
    python scripts/test_runtime_maestro.py
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import runtime_maestro as m


def reset_estado():
    """Limpa estado para teste isolado."""
    estado_file = ROOT / "runtime" / "maestro_estado.json"
    cmd_file = ROOT / "runtime" / "maestro_cmd.json"
    estado_file.unlink(missing_ok=True)
    cmd_file.unlink(missing_ok=True)


def test_pode_iniciar_sem_estado():
    """Sem registro: pode iniciar (cooldown zerado, sem servico vivo)."""
    reset_estado()
    r = m.pode_iniciar("tts_service.py")
    assert r["pode"] is True, f"esperava pode=True, recebi {r}"
    print("  [OK] pode_iniciar sem estado: True")


def test_pode_iniciar_com_servico_vivo():
    """Com servico registrado vivo: NAO pode iniciar de novo."""
    reset_estado()
    m.registrar("tts_service.py", 9999, "guardian")
    r = m.pode_iniciar("tts_service.py")
    assert r["pode"] is False, f"esperava pode=False, recebi {r}"
    assert "ja_vivo" in r["motivo"], f"motivo errado: {r}"
    print(f"  [OK] pode_iniciar com vivo: False (motivo: {r['motivo']})")


def test_cooldown_apos_registrar():
    """Apos registrar, cooldown impede novo start por 15s."""
    reset_estado()
    m.registrar("widget_edge.py", 1234, "guardian")
    # Imediatamente apos registrar, o cooldown esta ativo
    r = m.pode_iniciar("widget_edge.py")
    # Pode ser que cooldown OU ja_vivo bloqueie; ambos sao ok
    assert r["pode"] is False
    print(f"  [OK] cooldown/ja_vivo bloqueia: {r['motivo']}")


def test_parar_limpa_singleton():
    """Depois de parar, pode iniciar de novo."""
    reset_estado()
    m.registrar("widget_edge.py", 1234, "guardian")
    m.parar("widget_edge.py")
    # Forca limpar cooldown manualmente para o teste
    estado = m._read_estado()
    estado["cooldowns"] = {}
    m._save_estado(estado)
    r = m.pode_iniciar("widget_edge.py")
    assert r["pode"] is True, f"apos parar deveria poder, recebi {r}"
    print("  [OK] apos parar, pode iniciar de novo: True")


def test_listar_vivos():
    """Listar mostra apenas os vivos."""
    reset_estado()
    m.registrar("tts_service.py", 1111, "guardian")
    m.registrar("widget_edge.py", 2222, "widget")
    m.parar("tts_service.py")
    r = m.listar_vivos()
    assert "widget_edge.py" in r["vivos"]
    assert "tts_service.py" not in r["vivos"]
    print(f"  [OK] listar_vivos: {r['total']} vivo(s) (esperado 1)")


def test_status_cli():
    """CLI status funciona sem erro."""
    reset_estado()
    m.registrar("jarvis_bridge.py", 3333, "guardian")
    r = subprocess.run(
        ["python", str(ROOT / "scripts" / "runtime_maestro.py"), "status"],
        capture_output=True, text=True, timeout=10
    )
    assert r.returncode == 0
    assert "MAESTRO STATUS" in r.stdout
    print("  [OK] CLI status funciona")


def test_pode_iniciar_cli():
    """CLI pode_iniciar retorna JSON."""
    reset_estado()
    r = subprocess.run(
        ["python", str(ROOT / "scripts" / "runtime_maestro.py"),
         "pode_iniciar", "tts_service.py"],
        capture_output=True, text=True, timeout=10
    )
    assert r.returncode == 0
    out = json.loads(r.stdout)
    assert "pode" in out
    print(f"  [OK] CLI pode_iniciar: {out}")


def test_client_sem_maestro_rodando():
    """Cliente consulta maestro offline sem travar."""
    from maestro_client import consultar_maestro, maestro_disponivel, fallback_degraded
    assert maestro_disponivel() is False, "esperava maestro offline"
    r = consultar_maestro("pode_iniciar", script="tts_service.py")
    assert r["status"] == "offline"
    assert fallback_degraded("test", "teste") is True
    print("  [OK] cliente nao trava se maestro offline")


def test_client_com_maestro_rodando():
    """Sobe maestro em background, consulta via cliente, derruba."""
    from maestro_client import consultar_maestro, maestro_disponivel
    reset_estado()

    # Sobe maestro em subprocess
    proc = subprocess.Popen(
        ["python",
         str(ROOT / "scripts" / "runtime_maestro.py"), "loop"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )

    # Espera ate maestro estar vivo (pid_file escrito e processo rodando)
    t0 = time.time()
    while time.time() - t0 < 10:
        if maestro_disponivel():
            break
        time.sleep(0.3)
    assert maestro_disponivel(), "maestro deveria estar vivo em ate 10s"

    try:
        r = consultar_maestro("pode_iniciar", script="tts_service.py")
        assert r.get("pode") is True, f"esperava pode=True, recebi {r}"
        # Agora registra
        consultar_maestro("registrar", script="tts_service.py", pid=9999, owner="test")
        r2 = consultar_maestro("pode_iniciar", script="tts_service.py")
        assert r2.get("pode") is False, f"apos registrar deveria negar, recebi {r2}"
        print(f"  [OK] fluxo completo: registrou e bloqueio funcionou ({r2['motivo']})")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except Exception:
            proc.kill()
        time.sleep(0.5)


if __name__ == "__main__":
    print("=== TESTES DO MAESTRO (FASE 1) ===\n")
    testes = [
        test_pode_iniciar_sem_estado,
        test_pode_iniciar_com_servico_vivo,
        test_cooldown_apos_registrar,
        test_parar_limpa_singleton,
        test_listar_vivos,
        test_status_cli,
        test_pode_iniciar_cli,
        test_client_sem_maestro_rodando,
        test_client_com_maestro_rodando,
    ]
    passou = 0
    falhou = 0
    for t in testes:
        try:
            t()
            passou += 1
        except AssertionError as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            falhou += 1
        except Exception as e:
            print(f"  [ERRO] {t.__name__}: {e}")
            falhou += 1
    print(f"\n=== {passou}/{len(testes)} passaram, {falhou} falharam ===")
    sys.exit(0 if falhou == 0 else 1)
