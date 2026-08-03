"""Captura screenshot do widget e salva em docs/. Requer Pillow (opcional)."""
import subprocess, sys, os, time

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, ".."))

# inicia o widget
w = subprocess.Popen([sys.executable, "-u", os.path.join(BASE, "widget_grafo.py")],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print("widget PID", w.pid)
time.sleep(6)

# tenta achar a janela e capturar via win32 (se pywin32 disponivel)
try:
    import win32gui, win32ui, win32con
    import ctypes
    from PIL import Image
    found = []
    def enum(hwnd, l):
        if win32gui.IsWindowVisible(hwnd) and 'Cerebro' in win32gui.GetWindowText(hwnd):
            found.append(hwnd)
        return True
    win32gui.EnumWindows(enum, None)
    for hwnd in found:
        l, t, r, b = win32gui.GetWindowRect(hwnd)
        w_ = r - l; h_ = b - t
        hdc = win32gui.GetWindowDC(hwnd)
        dc = win32ui.CreateDCFromHandle(hdc)
        mem = dc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        bmp.CreateCompatibleBitmap(dc, w_, h_)
        mem.SelectObject(bmp)
        ctypes.windll.user32.PrintWindow(hwnd, mem.GetSafeHdc(), 3)
        bmp.SaveBitmapFile(mem, os.path.join(ROOT, 'docs', 'widget_screenshot.bmp'))
        print("screenshot salvo", hwnd, w_, 'x', h_)
        mem.DeleteDC(); dc.DeleteDC(); win32gui.ReleaseDC(hwnd, hdc)
except Exception as e:
    print("screenshot erro:", repr(e))

w.terminate()