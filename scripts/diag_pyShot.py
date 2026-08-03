"""Captura screenshot da tela inteira e analisa pixels coloridos na regiao do #net.
Usa System.Drawing via pythonnet (já usado antes)."""
import subprocess, sys, os, time

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)

# inicia o widget com pywebview focus (debug=False, janela visivel)
env = dict(os.environ); env["PYWEBVIEW_LOG"] = "DEBUG"
code = r'''
import sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview, widget_grafo as wg
bridge = wg.Bridge()
win = webview.create_window(wg.TITLE, url=str(wg._build_view().resolve()),
    width=1280, height=700, resizable=True, frameless=True, easy_drag=False, shadow=False, focus=False, js_api=bridge, background_color=wg.BG)
bridge._win = win
webview.start()
'''
tmp = os.path.join(ROOT, "scripts", "dbg_keep_open.py")
open(tmp, "w", encoding="utf-8").write(code)

p = subprocess.Popen([sys.executable, "-u", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
print("widget PID", p.pid, flush=True)
time.sleep(8)

# captura tela
try:
    import clr
    from System.Drawing import Bitmap, Graphics, Rectangle, Imaging
    from System.Windows.Forms import Screen
    scr = Screen.get_PrimaryScreen().Bounds
    sw, sh = scr.Width, scr.Height
    bmp = Bitmap(sw, sh)
    g = Graphics.FromImage(bmp)
    g.CopyFromScreen(0, 0, 0, 0, scr.Size)
    outp = os.path.join(ROOT, "docs", "shot_now.png")
    bmp.Save(outp, Imaging.ImageFormat.Png)
    g.Dispose(); bmp.Dispose()
    print("screenshot salvo", outp, sw, "x", sh, flush=True)
    # analisa: quantos pixels distintos de cores nao-preto?
    from System import Drawing
    bmp2 = Bitmap.FromFile(outp)
    cores = {}
    step = 6
    nonblack = 0; colored = 0
    for y in range(0, bmp2.Height, step):
        for x in range(0, bmp2.Width, step):
            px = bmp2.GetPixel(x, y)
            r,g,b = int(px.R), int(px.G), int(px.B)
            if not (r<30 and g<30 and b<30):
                nonblack += 1
            if abs(r-g)>15 or abs(g-b)>15 or abs(b-r)>15 or r>80 or g>80 or b>80:
                colored += 1
    bmp2.Dispose()
    print(f"pixel sampled (step={step}): nonblack={nonblack} colored={colored}", flush=True)
    print("CONCLUSAO: se colored muito >0, grafo renderizou; se ~0, nada renderizou", flush=True)
except Exception as e:
    import traceback; traceback.print_exc()
    print("dotnet screenshot erro:", repr(e), flush=True)

p.terminate()