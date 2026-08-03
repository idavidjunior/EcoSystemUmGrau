import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
import subprocess
import pythonnet, clr
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import Screen
from System.Drawing import Bitmap, Graphics, Imaging, Color

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)

def capturar_regiao(x, y, w, h, nome):
    bmp = Bitmap(w, h)
    g = Graphics.FromImage(bmp)
    scr = Screen.PrimaryScreen
    g.CopyFromScreen(x, y, 0, 0, bmp.Size)
    g.Dispose()
    path = os.path.join(ROOT, "docs", nome)
    bmp.Save(path, Imaging.ImageFormat.Png)
    bmp.Dispose()
    return path

def analisar(path):
    bmp = Bitmap.FromFile(path)
    cores = {}
    step = 1
    for j in range(0, bmp.Height, step):
        for i in range(0, bmp.Width, step):
            px = bmp.GetPixel(i, j)
            r, gg, b = int(px.R), int(px.G), int(px.B)
            if r < 30 and gg < 30 and b < 30: continue
            def cls(r, g, b):
                if 60 < r < 100 and 100 < g < 140 and 150 < b < 180: return 'azul'
                if 225 < r < 255 and 130 < g < 160 and 30 < b < 60: return 'laranja'
                if 210 < r < 235 and 75 < g < 105 and 75 < b < 105: return 'vermelho'
                if 70 < r < 105 and 145 < g < 180 and 70 < b < 125: return 'verde'
                if 225 < r < 245 and 185 < g < 215 and 60 < b < 90: return 'amarelo'
                return 'outro'
            key = cls(r, gg, b)
            cores[key] = cores.get(key, 0) + 1
    bmp.Dispose()
    print("  cores:", dict(sorted(cores.items(), key=lambda kv: -kv[1])[:8]), flush=True)

# TESTE 1: widget com grafo real
print("=== TESTE 1: widget com grafo ===", flush=True)
env = dict(os.environ); env["PYWEBVIEW_LOG"] = "DEBUG"
code = r'''
import sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview, widget_grafo as wg
bridge = wg.Bridge()
win = webview.create_window(wg.TITLE, url=str(wg._build_view().resolve()),
    width=1280, height=750, x=100, y=100, resizable=True, frameless=True,
    easy_drag=False, shadow=False, focus=False, js_api=bridge, background_color=wg.BG)
bridge._win = win
webview.start()
'''
tmp = os.path.join(ROOT, "scripts", "dbg_keep3.py")
open(tmp, "w", encoding="utf-8").write(code)
p = subprocess.Popen([sys.executable, "-u", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
print("PID", p.pid, flush=True)
time.sleep(8)
capturar_regiao(100, 100, 1280, 750, "shot_grafo.png")
print("  analisando grafo:", flush=True)
analisar(os.path.join(ROOT, "docs", "shot_grafo.png"))
p.terminate()
p.wait(timeout=5)

# TESTE 2: widget com pagina BRANCA (controle)
print("=== TESTE 2: controle pagina branca ===", flush=True)
ctrl_html = os.path.join(ROOT, "docs", "_ctrl_branco.html")
open(ctrl_html, "w", encoding="utf-8").write("<html><body bgcolor='#181825'></body></html>")
code2 = 'import webview; w=webview.create_window("Ctrl", url="http://127.0.0.1:8095/_ctrl_branco.html", width=1280, height=750, x=100, y=100, frameless=True, resizable=True); webview.start()'
tmp2 = os.path.join(ROOT, "scripts", "dbg_ctrl.py")
open(tmp2, "w", encoding="utf-8").write(code2)
serv = subprocess.Popen([sys.executable, "-m", "http.server", "8095", "--directory", os.path.join(ROOT, "docs")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
p2 = subprocess.Popen([sys.executable, "-u", tmp2], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
print("PID ctrl", p2.pid, flush=True)
time.sleep(6)
capturar_regiao(100, 100, 1280, 750, "shot_ctrl.png")
print("  analisando controle:", flush=True)
analisar(os.path.join(ROOT, "docs", "shot_ctrl.png"))
p2.terminate(); serv.terminate()