#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Widget Tray — Ícone na bandeja do sistema (system tray) para controlar o Edge.

Uso:
    pythonw scripts/widget_tray.py

Funciona sem terminal. Clique direito no ícone -> menu de controle.
"""
import sys
import os
import json
import time
import threading
import subprocess
import tempfile
from pathlib import Path

import win32gui
import win32api
import win32con

# ─── Paths ───
BASE = Path(__file__).resolve().parent.parent
SCRIPTS = BASE / "scripts"
RUNTIME = BASE / "runtime"
UI = BASE / "www" / "index.html"

STATE_FILE = RUNTIME / "widget_state.json"
NARRACAO_CONTROLE = RUNTIME / "narracao_estado.json"
STOP_FLAG = RUNTIME / "parar_fala.flag"
PID_FILE = RUNTIME / "widget_tray.pid"

# ─── Estado ───
_voz_proc = None
_voz_lock = threading.Lock()
_sleep_timer = None
_icone_handle = None
_menu_handle = None
_hwnd = None
_class_atom = None

# ─── Utilitários ───
def _log(msg):
    try:
        with open(RUNTIME / "widget_tray.log", "a", buffering=1, encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass

def _salvar_estado(update):
    try:
        estado = {}
        if STATE_FILE.exists():
            estado = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        estado.update(update)
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(estado, ensure_ascii=False), encoding="utf-8")
        tmp.replace(STATE_FILE)
    except Exception:
        pass

def _ler_estado():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _narrador_pausar(pausar: bool):
    """Pausa/retoma narrador via arquivo de controle compartilhado."""
    try:
        estado = {"ativo": True, "pausado": False}
        if NARRACAO_CONTROLE.exists():
            estado = json.loads(NARRACAO_CONTROLE.read_text(encoding="utf-8"))
        estado["pausado"] = bool(pausar)
        if pausar:
            STOP_FLAG.write_text(str(int(time.time())), encoding="utf-8")
        tmp = NARRACAO_CONTROLE.with_suffix(".tmp")
        tmp.write_text(json.dumps(estado), encoding="utf-8")
        tmp.replace(NARRACAO_CONTROLE)
    except Exception:
        pass

def _servico_no_ar(nome_script):
    try:
        import psutil
        alvo = nome_script.lower()
        if not alvo.endswith(".py"):
            alvo += ".py"
        for p in psutil.process_iter(["pid", "cmdline"]):
            for tok in p.info["cmdline"] or []:
                if tok.lower().strip('"').endswith(alvo):
                    return True
    except Exception:
        pass
    return False

# ─── Controle de voz ───
def _voice_on():
    global _voz_proc
    _narrador_pausar(True)
    with _voz_lock:
        if _voz_proc and _voz_proc.poll() is None:
            return
        exe = sys.executable
        alvo = exe.replace("python.exe", "pythonw.exe")
        if os.path.exists(alvo):
            exe = alvo
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        log_f = open(RUNTIME / "dialogo_widget.log", "a", buffering=1, encoding="utf-8")
        _voz_proc = subprocess.Popen(
            [exe, "-u", str(SCRIPTS / "dialogo.py"), "--modo", "vad"],
            cwd=str(SCRIPTS),
            stdout=log_f,
            stderr=subprocess.STDOUT,
            creationflags=flags,
        )
    _salvar_estado({"voz": True})

def _voice_off():
    global _voz_proc
    with _voz_lock:
        if _voz_proc and _voz_proc.poll() is None:
            try:
                _voz_proc.terminate()
            except Exception:
                pass
        _voz_proc = None
    _narrador_pausar(False)
    _salvar_estado({"voz": False})

def _voice_toggle():
    est = _ler_estado()
    if est.get("voz"):
        _voice_off()
    else:
        _voice_on()

def _set_volume(valor):
    _salvar_estado({"volume": max(0, min(100, int(valor)))})

def _set_sleep(minutos):
    global _sleep_timer
    minutos = int(minutos)
    _salvar_estado({"sleep": minutos})
    if _sleep_timer:
        _sleep_timer.cancel()
        _sleep_timer = None
    if minutos > 0:
        _sleep_timer = threading.Timer(minutos * 60, _voice_off)
        _sleep_timer.daemon = True
        _sleep_timer.start()

def _parar_fala():
    try:
        STOP_FLAG.write_text(str(int(time.time())), encoding="utf-8")
    except Exception:
        pass

# ─── Janela oculta para receber mensagens ───
def _wnd_proc(hwnd, msg, wparam, lparam):
    _log(f"wnd_proc: hwnd={hwnd}, msg={msg}, wparam={wparam}, lparam={lparam}")
    try:
        if msg == win32con.WM_DESTROY:
            _log("WM_DESTROY received, posting quit")
            win32gui.PostQuitMessage(0)
            return 0
        elif msg == win32con.WM_USER + 1:
            # Tray icon message: lparam = mouse event, wparam = icon ID
            _log(f"Tray callback: lparam={lparam}")
            if lparam == win32con.WM_RBUTTONUP:
                _mostrar_menu(hwnd)
            elif lparam == win32con.WM_LBUTTONDBLCLK:
                _voice_toggle()
            return 0
        elif msg == win32con.WM_COMMAND:
            # Menu item selected: wparam = command ID
            _log(f"WM_COMMAND: wparam={wparam}")
            _processar_comando(wparam)
            return 0
    except Exception as e:
        _log(f"Exception in wnd_proc: {e}")
        import traceback
        _log(traceback.format_exc())
    return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)

def _registrar_classe():
    global _class_atom
    wc = win32gui.WNDCLASS()
    wc.lpfnWndProc = _wnd_proc
    wc.lpszClassName = "WidgetTrayClass"
    wc.hInstance = win32api.GetModuleHandle(None)
    _class_atom = win32gui.RegisterClass(wc)
    return _class_atom

def _criar_janela_oculta():
    global _hwnd
    _registrar_classe()
    _hwnd = win32gui.CreateWindow(
        "WidgetTrayClass",
        "WidgetTrayHidden",
        win32con.WS_OVERLAPPED,
        0, 0, 0, 0,
        0, 0,
        win32api.GetModuleHandle(None),
        None
    )
    return _hwnd

# ─── Ícone na bandeja ───
def _criar_icone():
    """Cria ícone padrão (quadrado colorido) se não houver .ico."""
    # Tenta carregar ícone do sistema
    try:
        ico_path = BASE / "www" / "icon.ico"
        if ico_path.exists():
            return win32gui.LoadImage(
                0, str(ico_path), win32con.IMAGE_ICON, 16, 16, win32con.LR_LOADFROMFILE
            )
    except Exception:
        pass
    # Fallback: ícone do sistema (aplicação padrão)
    try:
        return win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
    except Exception:
        pass
    # Último recurso: ícone de aviso
    try:
        return win32gui.LoadIcon(0, win32con.IDI_WARNING)
    except Exception:
        return 0

def _adicionar_icone_bandeja(hwnd, hicon):
    nid = (
        hwnd,
        1,  # uID
        win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
        win32con.WM_USER + 1,  # callback message
        hicon,
        "Edge — EcoSystemUmGrau"
    )
    win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
    return nid

def _remover_icone_bandeja(hwnd):
    try:
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (hwnd, 1))
    except Exception:
        pass

# ─── Menu de contexto ───
def _mostrar_menu(hwnd):
    global _menu_handle
    try:
        est = _ler_estado()
        voz_ligada = est.get("voz", False)
        volume = est.get("volume", 80)
        sleep = est.get("sleep", 0)

        menu = win32gui.CreatePopupMenu()

        # Voice toggle
        win32gui.AppendMenu(menu, win32con.MF_STRING, 1001,
            ("Desligar voz" if voz_ligada else "Ligar voz"))
        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")

        # Volume submenu
        vol_menu = win32gui.CreatePopupMenu()
        for v in [0, 30, 50, 70, 80, 100]:
            flag = win32con.MF_STRING | (win32con.MF_CHECKED if volume == v else 0)
            win32gui.AppendMenu(vol_menu, flag, 2000 + v, f"{v}%")
        win32gui.AppendMenu(menu, win32con.MF_STRING | win32con.MF_POPUP, vol_menu, "Volume")

        # Sleep submenu
        sleep_menu = win32gui.CreatePopupMenu()
        for m in [0, 5, 15, 30, 60]:
            flag = win32con.MF_STRING | (win32con.MF_CHECKED if sleep == m else 0)
            win32gui.AppendMenu(sleep_menu, flag, 3000 + m, f"{m} min" if m else "Desativado")
        win32gui.AppendMenu(menu, win32con.MF_STRING | win32con.MF_POPUP, sleep_menu, "Timer sono")

        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")

        # Parar fala
        win32gui.AppendMenu(menu, win32con.MF_STRING, 4001, "Parar fala agora")

        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")

        # Status serviços
        narr = _servico_no_ar("narrador_desktop")
        tts = _servico_no_ar("tts_service")
        bridge = _servico_no_ar("jarvis_bridge")
        status_str = f"Narrador: {'ON' if narr else 'OFF'} | TTS: {'ON' if tts else 'OFF'} | Bridge: {'ON' if bridge else 'OFF'}"
        win32gui.AppendMenu(menu, win32con.MF_STRING | win32con.MF_GRAYED, 0, status_str)

        win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")

        # Sair
        win32gui.AppendMenu(menu, win32con.MF_STRING, 5001, "Sair")

        # Mostra menu na posição do cursor
        x, y = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(hwnd)
        win32gui.TrackPopupMenu(
            menu,
            win32con.TPM_RIGHTBUTTON | win32con.TPM_BOTTOMALIGN,
            x, y, 0, hwnd, None
        )
        win32gui.PostMessage(hwnd, win32con.WM_NULL, 0, 0)
        win32gui.DestroyMenu(menu)
    except Exception as e:
        _log(f"erro menu: {e}")

def _processar_comando(cmd_id):
    if cmd_id == 1001:  # Voice toggle
        _voice_toggle()
    elif 2000 <= cmd_id <= 2100:  # Volume
        _set_volume(cmd_id - 2000)
    elif 3000 <= cmd_id <= 3060:  # Sleep
        _set_sleep(cmd_id - 3000)
    elif cmd_id == 4001:  # Parar fala
        _parar_fala()
    elif cmd_id == 5001:  # Sair
        _cleanup()
        win32gui.PostQuitMessage(0)

# ─── Loop principal ───
def _message_loop():
    _log("message_loop started")
    iteration = 0
    while True:
        iteration += 1
        _log(f"iteration {iteration}: calling GetMessage")
        result = win32gui.GetMessage(None, 0, 0)
        _log(f"GetMessage result: {result}")
        if not result or result[0] == 0:
            _log("GetMessage returned 0, exiting loop")
            break
        # result = [1, (hwnd, message, wparam, lparam, time, pt)]
        try:
            win32gui.TranslateMessage(result[1])
            win32gui.DispatchMessage(result[1])
        except Exception as e:
            _log(f"Exception in message loop: {e}")
            import traceback
            _log(traceback.format_exc())
    _log("message_loop ended")

def _cleanup():
    global _voz_proc, _sleep_timer, _icone_handle
    _voice_off()
    if _sleep_timer:
        _sleep_timer.cancel()
    if _hwnd:
        _remover_icone_bandeja(_hwnd)
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass

def _instancia_unica():
    """Trava atômica via PID file."""
    import psutil
    me = str(os.getpid())
    for _ in range(2):
        try:
            fd = os.open(PID_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            # Verifica se outro widget_tray vivo existe
            for p in psutil.process_iter(["pid", "cmdline"]):
                if p.info["pid"] == os.getpid():
                    continue
                if any(
                    t.lower().strip('"').endswith("widget_tray.py")
                    for t in (p.info["cmdline"] or [])
                ):
                    os.close(fd)
                    PID_FILE.unlink()
                    return False
            os.write(fd, me.encode())
            os.close(fd)
            return True
        except FileExistsError:
            dono_vivo = False
            try:
                dono = int(PID_FILE.read_text().strip())
                p = psutil.Process(dono)
                if any(t.lower().endswith("widget_tray.py") for t in p.cmdline()):
                    dono_vivo = True
            except Exception:
                pass
            if dono_vivo:
                return False
            try:
                PID_FILE.unlink()
            except FileNotFoundError:
                pass
    return False

# ─── Entry point ───
def main():
    global _icone_handle, _hwnd

    if not _instancia_unica():
        _log("Widget Tray já está rodando.")
        return

    # Redireciona stdout/stderr para log (pythonw)
    if sys.stdout is None or sys.stderr is None:
        f = open(RUNTIME / "widget_tray.log", "a", buffering=1, encoding="utf-8")
        sys.stdout = f
        sys.stderr = f

    import faulthandler
    faulthandler.enable(file=sys.stderr)

    _log("boot")

    # Janela oculta
    _hwnd = _criar_janela_oculta()

    # Ícone na bandeja
    hicon = _criar_icone()
    _adicionar_icone_bandeja(_hwnd, hicon)

    _log("ícone na bandeja criado")

    # Loop de mensagens
    try:
        _message_loop()
    finally:
        _cleanup()

if __name__ == "__main__":
    main()