#!/usr/bin/env python3
"""hotkey_pause.py — Hotkey global Pause/Break = STOP ECO.

Roda em background. Pressione Pause/Break para interromper fala atual + pausar narração.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

try:
    import keyboard
except ImportError:
    print("ERRO: pip install keyboard")
    sys.exit(1)

CONTROLE = ROOT / "runtime" / "narracao_estado.json"


def gravar_parar():
    """Escreve STOP ECO: ativo=false, pausado=true + mata TTS ativo."""
    try:
        estado = {"ativo": False, "pausado": True}
        CONTROLE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONTROLE.with_suffix(".tmp")
        tmp.write_text(json.dumps(estado), encoding="utf-8")
        tmp.replace(CONTROLE)
    except Exception as e:
        print(f"[hotkey] ERRO ao gravar controle: {e}")
        return

    # Mata processo TTS ativo (vox_audio.py falar)
    try:
        import subprocess
        saida = subprocess.run(["tasklist", "/FI", "IMAGENAME eq python.exe", "/NH"],
                               capture_output=True, text=True, timeout=10).stdout
        for linha in saida.splitlines():
            if "vox_audio.py" in linha and "falar" in linha:
                partes = linha.split()
                if len(partes) >= 2 and partes[1].isdigit():
                    pid = int(partes[1])
                    subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                                   capture_output=True, timeout=3)
                    print(f"[hotkey] TTS interrompido (PID {pid})")
    except Exception as e:
        print(f"[hotkey] ERRO ao matar TTS: {e}")

    print("[hotkey] STOP ECO executado (Pause/Break)")


def main():
    print("Hotkey ativo: Pause/Break = STOP ECO")
    print("Pressione Ctrl+C para sair")
    
    keyboard.add_hotkey("pause", gravar_parar, suppress=True)
    
    try:
        keyboard.wait()  # bloqueia até Ctrl+C
    except KeyboardInterrupt:
        pass
    finally:
        keyboard.unhook_all()
        print("\nHotkey encerrado")


if __name__ == "__main__":
    main()