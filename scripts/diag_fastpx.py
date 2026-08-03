import sys, os, time, subprocess, threading
sys.stdout.reconfigure(encoding='utf-8')
import pythonnet, clr
clr.AddReference("System.Drawing")
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import Screen
from System.Drawing import Bitmap, Graphics, Imaging, Rectangle
import System
from System import Array, Byte

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

BLANK = os.path.join(ROOT, "docs", "_blank.html")
with open(BLANK, "w", encoding="utf-8") as f:
    f.write("<html><body style='background:#181825'></body></html>")

WIDGET_SCRIPT = (
    "import sys,os\n"
    "BASE=os.path.dirname(os.path.abspath(__file__))\n"
    "import sys as s; s.path.insert(0,BASE)\n"
    "import webview\n"
    "win=webview.create_window('W', url=URL, width=W, height=H, x=X, y=Y, resizable=True, frameless=True)\n"
    "webview.start()\n"
)

def start_widget(port, path, x, y, w, h):
    serv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--directory", os.path.join(ROOT, "docs")],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    script = WIDGET_SCRIPT.replace("URL", "http://127.0.0.1:%d/%s" % (port, path))
    script = script.replace("W", str(w)).replace("H", str(h)).replace("X", str(x)).replace("Y", str(y))
    tmp = os.path.join(ROOT, "scripts", "_wtmp.py")
    open(tmp, "w", encoding="utf-8").write(script)
    p = subprocess.Popen([sys.executable, "-u", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(7)
    return p, serv

def capture(x, y, w, h):
    bmp = Bitmap(w, h)
    g = Graphics.FromImage(bmp)
    g.CopyFromScreen(x, y, 0, 0, bmp.Size)
    g.Dispose()
    path = os.path.join(ROOT, "docs", "shot_region.png")
    bmp.Save(path, Imaging.ImageFormat.Png)
    # LockBits
    bmp2 = Bitmap.FromFile(path)
    rect = Rectangle(0, 0, bmp2.Width, bmp2.Height)
    data = bmp2.LockBits(rect, Imaging.ImageLockMode.ReadOnly, Imaging.PixelFormat.Format32bppRgb)
    buf = Array[Byte](data.Stride * bmp2.Height)
    System.Runtime.InteropServices.Marshal.Copy(data.Scan0, buf, 0, len(buf))
    bmp2.UnlockBits(data)
    nonblack = 0; colored = 0; sample = 0
    for i in range(0, len(buf), 16):  # sample every 16th para rapidez
        b = buf[i]; g_ = buf[i+1]; r = buf[i+2]
        sample += 1
        if not (r < 35 and g_ < 35 and b < 35):
            nonblack += 1
        if abs(int(r)-int(g_)) > 8 or abs(int(g_)-int(b)) > 8 or abs(int(r)-int(b)) > 8:
            colored += 1
    bmp2.Dispose()
    return nonblack, colored, sample

print("=== MINIMAL (3 nos) no widget ===", flush=True)
p, serv = start_widget(8098, "teste_minimo.html", 100, 100, 900, 600)
nb, col, n = capture(100, 100, 900, 600)
print(f"  nonblack={nb} colored={col} sampled={n}", flush=True)
p.terminate(); serv.terminate()

print("=== BLANK (controle) no widget ===", flush=True)
p2, serv2 = start_widget(8099, "_blank.html", 100, 100, 900, 600)
nb2, col2, n2 = capture(100, 100, 900, 600)
print(f"  nonblack={nb2} colored={col2} sampled={n2}", flush=True)
p2.terminate(); serv2.terminate()

print("CONCLUSAO:", flush=True)
print("  minimal colored >> blank colored -> renderizou", flush=True)
print("  minimal ~= blank -> NAO renderizou (problema WebView2/vis-network)", flush=True)
from System import GC
GC.Collect()