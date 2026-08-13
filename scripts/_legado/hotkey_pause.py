#!/usr/bin/env python3
"""hotkey_pause.py — Hotkey global Pause/Break = STOP ECO.

Roda em background. Pressione Pause/Break para interromper fala atual + pausar narração.

Feedback visual/sonoro:
  - Scroll Lock LED: ACESO = pausado/desativado | APAGADO = ativo
  - Beep: grave = pausa/stop | agudo = reativar (via jarvis_audio.py on)
  - Toast Windows (opcional): notificação nativa
"""

import json
import sys
import time
import winsound
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

try:
    import keyboard
except ImportError:
    print("ERRO: pip install keyboard")
    sys.exit(1)

# Scroll Lock LED via Windows API
try:
    import ctypes
    user32 = ctypes.windll.user32
    VK_SCROLL = 0x91
    KEYEVENTF_EXTENDEDKEY = 0x0001
    KEYEVENTF_KEYUP = 0x0002
    HAS_SCROLL_LOCK = True
except Exception:
    HAS_SCROLL_LOCK = False

# Toast nativo Windows 10/11 (opcional)
try:
    from winrt.windows.ui.notifications import ToastNotificationManager, ToastTemplateType
    from winrt.windows.data.xml.dom import XmlDocument
    HAS_TOAST = True
except Exception:
    HAS_TOAST = False

CONTROLE = ROOT / "runtime" / "narracao_estado.json"


def toggle_scroll_lock_led(aceso: bool):
    """Liga/desliga LED do Scroll Lock."""
    if not HAS_SCROLL_LOCK:
        return
    try:
        # Verifica estado atual
        estado_atual = user32.GetKeyState(VK_SCROLL) & 1
        if (estado_atual == 1) != aceso:
            # Simula pressionar Scroll Lock para togglear
            user32.keybd_event(VK_SCROLL, 0, KEYEVENTF_EXTENDEDKEY, 0)
            user32.keybd_event(VK_SCROLL, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
    except Exception:
        pass


def beep_stop():
    """Beep grave = pausa/stop."""
    try:
        winsound.Beep(400, 150)  # 400Hz, 150ms
    except Exception:
        pass


def beep_ativar():
    """Beep agudo = ativar."""
    try:
        winsound.Beep(800, 100)
        winsound.Beep(1000, 100)
    except Exception:
        pass


def toast_notify(titulo: str, msg: str):
    """Toast nativo Windows 10/11."""
    if not HAS_TOAST:
        return
    try:
        tpl = ToastNotificationManager.get_template_content(ToastTemplateType.toast_text02)
        texts = tpl.get_elements_by_tag_name("text")
        texts[0].append_child(tpl.create_text_node(titulo))
        texts[1].append_child(tpl.create_text_node(msg))
        toast = ToastNotification(tpl)
        ToastNotificationManager.create_toast_notifier("Jarvis").show(toast)
    except Exception:
        pass


def ler_estado():
    try:
        if CONTROLE.exists():
            return json.loads(CONTROLE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"ativo": True, "pausado": False}


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

    # Feedback
    beep_stop()
    toggle_scroll_lock_led(True)  # LED ACESO = pausado
    toast_notify("Jarvis", "STOP ECO — narração pausada")
    print("[hotkey] STOP ECO executado (Pause/Break) — LED Scroll Lock ACESO")


def main():
    print("Hotkey ativo: Pause/Break = STOP ECO")
    print("  Scroll Lock LED: ACESO = pausado | APAGADO = ativo")
    print("  Beep grave = pausa | Beep agudo = ativar (via jarvis_audio.py on)")
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