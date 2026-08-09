import sys
sys.stdout.reconfigure(encoding='utf-8')
import subprocess, os, time, threading
import pythonnet
import clr
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")
from System import Drawing
from System.Windows.Forms import Screen
from System.Drawing import Bitmap, Graphics, Imaging

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
env = dict(os.environ); env["PYWEBVIEW_LOG"] = "DEBUG"

code = r'''
import sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview, widget_grafo as wg
bridge = wg.Bridge()
win = webview.create_window(wg.TITLE, url=str(wg._build_view().resolve()),
    width=1280, height=750, x=100, y=100, resizable=True, frameless=True,
bridge._win = win
webview.start()
'''
tmp = os.path.join(ROOT, "scripts", "dbg_keep2.py")
open(tmp, "w", encoding="utf-8").write(code)

p = subprocess.Popen([sys.executable, "-u", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
print("widget PID", p.pid, flush=True)
time.sleep(8)

scr = Screen.PrimaryScreen; bounds = scr.Bounds
bmp = Bitmap(bounds.Width, bounds.Height)
g = Graphics.FromImage(bmp); g.CopyFromScreen(0,0,0,0, bounds.Size); g.Dispose()
bmp.Save(os.path.join(ROOT,"docs","shot_now.png"), Imaging.ImageFormat.Png)
bmp.Dispose()
print("screenshot salvo", flush=True)

bmp2 = Bitmap.FromFile(os.path.join(ROOT,"docs","shot_now.png"))
colored = 0; total = 0
step = 5
# regiao do widget: aprox width 1280 height 750, x y vies
for y in range(0, bmp2.Height, step):
    for x in range(0, bmp2.Width, step):
        px = bmp2.GetPixel(x,y); r,g,b = int(px.R),int(px.G),int(px.B)
        total += 1
        if (r<30 and g<30 and b<30): continue
        if abs(r-g)>10 or abs(g-b)>10 or abs(r-b)>10:
            colored += 1
# tambem contar cores especificas do grafico (#4e79a7 azul, #f28e2b laranja etc)
cores_alvo = [(79,121,167),(242,142,43),(225,89,89),(89,161,79),(118,183,178),(237,201,72)]
match_alvo = 0
bmp2.Dispose()
print(f"sampled={total} colored={colored} match_cores_alvo={match_alvo}", flush=True)
p.terminate()