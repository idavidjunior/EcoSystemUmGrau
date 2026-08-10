#!/usr/bin/env python3
"""hotkey_pause_win32.py — Hotkey global Pause/Break via Windows API (RegisterHotKey).

Mais confiável que keyboard/pynput para processos em background.
"""

import json
import sys
import time
import winsound
import ctypes
import ctypes.wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

CONTROLE = ROOT / "runtime" / "narracao_estado.json"

# Windows API constants
WM_HOTKEY = 0x0312
MOD_NOREPEAT = 0x4000
VK_PAUSE = 0x13
VK_SCROLL = 0x91

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Para RegisterHotKey
RegisterHotKey = user32.RegisterHotKey
RegisterHotKey.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.INT, ctypes.wintypes.UINT, ctypes.wintypes.UINT]
RegisterHotKey.restype = ctypes.wintypes.BOOL

UnregisterHotKey = user32.UnregisterHotKey
UnregisterHotKey.argtypes = [ctypes.wintypes.HWND, ctypes.wintypes.INT]
UnregisterHotKey.restype = ctypes.wintypes.BOOL

GetMessageW = user32.GetMessageW
GetMessageW.argtypes = [ctypes.POINTER(ctypes.wintypes.MSG), ctypes.wintypes.HWND, ctypes.wintypes.UINT, ctypes.wintypes.UINT]
GetMessageW.restype = ctypes.wintypes.BOOL

TranslateMessage = user32.TranslateMessage
DispatchMessageW = user32.DispatchMessageW

KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002


def toggle_scroll_lock_led(aceso: bool):
    """Liga/desliga LED do Scroll Lock via keybd_event."""
    try:
        estado_atual = user32.GetKeyState(VK_SCROLL) & 1
        if (estado_atual == 1) != aceso:
            user32.keybd_event(VK_SCROLL, 0, KEYEVENTF_EXTENDEDKEY, 0)
            user32.keybd_event(VK_SCROLL, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)
    except Exception:
        pass


def beep_stop():
    try:
        winsound.Beep(400, 150)
    except Exception:
        pass


def beep_ativar():
    try:
        winsound.Beep(800, 100)
        winsound.Beep(1000, 100)
    except Exception:
        pass


def toast_notify(titulo: str, msg: str):
    """Toast nativo Windows 10/11 (opcional)."""
    try:
        from winrt.windows.ui.notifications import ToastNotificationManager, ToastTemplateType
        from winrt.windows.data.xml.dom import XmlDocument
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
    """Escreve STOP ECO + mata TTS ativo."""
    try:
        estado = {"ativo": False, "pausado": True}
        CONTROLE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CONTROLE.with_suffix(".tmp")
        tmp.write_text(json.dumps(estado), encoding="utf-8")
        tmp.replace(CONTROLE)
    except Exception as e:
        print(f"[hotkey] ERRO ao gravar controle: {e}")
        return

    # Mata TTS ativo
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
    toggle_scroll_lock_led(True)
    try:
        toast_notify("Jarvis", "STOP ECO — narração pausada")
    except Exception:
        pass
    print("[hotkey] STOP ECO executado (Pause/Break) — LED Scroll Lock ACESO")


def main():
    print("Hotkey global ativo: Pause/Break = STOP ECO (via Windows API)")
    print("  Scroll Lock LED: ACESO = pausado | APAGADO = ativo")
    print("  Beep grave = pausa | Beep agudo = ativar (via jarvis_audio.py on)")
    print("Pressione Ctrl+C no console para sair")

    # Cria janela oculta para receber WM_HOTKEY
    hwnd = user32.CreateWindowExW(
        0, "STATIC", "JarvisHotkeyWindow", 0,
        0, 0, 0, 0, 0, 0, kernel32.GetModuleHandleW(None), None
    )
    if not hwnd:
        print("ERRO: Falha ao criar janela oculta")
        return 1

    HOTKEY_ID = 1
    if not RegisterHotKey(hwnd, HOTKEY_ID, MOD_NOREPEAT, VK_PAUSE):
        error = kernel32.GetLastError()
        print(f"ERRO: RegisterHotKey falhou (código {error})")
        print("  Possíveis causas: tecla já registrada por outro app, ou sem permissão")
        return 1

    print("Hotkey Pause/Break registrada com sucesso (ID=1)")

    # Feedback inicial: LED reflete estado atual
    estado = ler_estado()
    pausado = estado.get("pausado", False) or not estado.get("ativo", True)
    toggle_scroll_lock_led(pausado)

    msg = ctypes.wintypes.MSG()
    try:
        while GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
            if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                gravar_parar()
            TranslateMessage(ctypes.byref(msg))
            DispatchMessageW(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        UnregisterHotKey(hwnd, HOTKEY_ID)
        user32.DestroyWindow(hwnd)
        print("\nHotkey encerrado")


def ler_estado():
    try:
        if CONTROLE.exists():
            return json.loads(CONTROLE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"ativo": True, "pausado": False}


if __name__ == "__main__":
    import json
    sys.exit(main())