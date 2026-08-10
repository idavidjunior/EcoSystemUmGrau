"""jarvis_audio.py — liga e desliga a narração do Jarvis no desktop.

Palavras-gatilho da conversa:
  "Eco"                -> on   (ativa narração)
  "D Eco"/"Desativar Eco" -> off (pausa narração)

Mecanismo: grava runtime/narracao_estado.json ({"ativo": bool}). O narrador
(scripts/narrador_desktop.py) lê esse arquivo a cada loop e pausa sem ser
encerrado. "on" também garante que o processo do narrador esteja rodando.

Uso:
  python scripts/jarvis_audio.py on|off|status
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTROLE = ROOT / "runtime" / "narracao_estado.json"
PID_FILE = ROOT / "runtime" / "narrador.pid"
NARRADOR = ROOT / "scripts" / "narrador_desktop.py"


def gravar(ativo):
    try:
        CONTROLE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONTROLE.with_suffix(".tmp")
        tmp.write_text(json.dumps({"ativo": ativo}), encoding="utf-8")
        tmp.replace(CONTROLE)
    except Exception as e:
        print(f"ERRO ao gravar controle: {e}")
        return False
    return True


def narrador_rodando():
    try:
        if PID_FILE.exists():
            pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            saida = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                                   capture_output=True, text=True, timeout=20).stdout
            return str(pid) in saida
    except Exception:
        pass
    return False


def iniciar_narrador():
    if narrador_rodando():
        return True
    try:
        DETACHED = getattr(subprocess, "DETACHED_PROCESS", 0)
        proc = subprocess.Popen(
            [sys.executable, str(NARRADOR)],
            cwd=str(ROOT), creationflags=DETACHED | subprocess.CREATE_NEW_PROCESS_GROUP,
            close_fds=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        PID_FILE.write_text(str(proc.pid), encoding="utf-8")
        time.sleep(2)
        return True
    except Exception as e:
        print(f"ERRO ao iniciar narrador: {e}")
        return False


def cmd_on():
    if not gravar(True):
        return 1
    ok = iniciar_narrador()
    print("Narracao ATIVADA (Eco)." + ("" if ok else " (processo nao confirmado)"))
    return 0


def cmd_off():
    if not gravar(False):
        return 1
    print("Narracao PAUSADA (D Eco).")
    return 0


def cmd_status():
    try:
        ativo = json.loads(CONTROLE.read_text(encoding="utf-8")).get("ativo", True)
    except Exception:
        ativo = True
    print(f"narracao: {'ATIVA' if ativo else 'PAUSADA'} | processo narrador: {'rodando' if narrador_rodando() else 'parado'}")
    return 0


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("on", "off", "status"):
        print(__doc__)
        return 1
    return {"on": cmd_on, "off": cmd_off, "status": cmd_status}[sys.argv[1]]()


if __name__ == "__main__":
    sys.exit(main())
