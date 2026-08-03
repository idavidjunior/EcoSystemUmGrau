import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
import pythonnet, clr
clr.AddReference("System.Drawing"); clr.AddReference("System.Windows.Forms")
from System.Drawing import Bitmap, Graphics, Imaging, Rectangle
from System.Windows.Forms import Application  # not needed

# find Cerebro Vivo window via Windows Forms? Simpler: use pygetwindow? use win32. Use .NET Process + bounds.
from System.Diagnostics import Process
from System import IntPtr, Convert

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def find_proc():
    for pr in Process.GetProcessesByName("python"):
        t = pr.MainWindowTitle
        if t and "Cerebro" in t:
            try:
                b = pr.MainWindowHandle
                if b != IntPtr.Zero:
                    return pr, t
            except Exception:
                pass
    return None, None

pr, title = find_proc()
print("encontrado:", title, "handle:", pr.MainWindowHandle if pr else None)

# Use the bounds of the Cerebro window. But frameless window MainwindowHandle rect may not include non-client. Use process's thread? 
# Instead just use screen primary bounds and capture full, then find colored pixels
from System.Windows.Forms import Screen
scr = Screen.PrimaryScreen.Bounds
# capture full primary screen
bmp = Bitmap(scr.Width, scr.Height)
g = Graphics.FromImage(bmp)
g.CopyFromScreen(0,0,0,0,scr.Size)
g.Dispose()
path = os.path.join(ROOT,"docs","shot_validate.png")
bmp.Save(path, Imaging.ImageFormat.Png)
# analyze: count strongly-colored pixels (vis-network node colors). sample step 3.
import System
from System import Array, Byte
# Use LockBits for speed
from System import Array, Byte
bmp3 = Bitmap.FromFile(path)
rect = Rectangle(0, 0, bmp3.Width, bmp3.Height)
data = bmp3.LockBits(rect, Imaging.ImageLockMode.ReadOnly, Imaging.PixelFormat.Format32bppRgb)
buf = Array[Byte](data.Stride * bmp3.Height)
import System
System.Runtime.InteropServices.Marshal.Copy(data.Scan0, buf, 0, len(buf))
bmp3.UnlockBits(data)
colored_graph = 0; total = 0
step_stride = 3  # sample 1 of every 3 pixels horizontally and vertically via byte skip
# iterate rows and cols
for row in range(0, bmp3.Height, step_stride):
    rowoff = row * data.Stride
    for col in range(0, bmp3.Width, step_stride):
        off = rowoff + col * 4
        b = buf[off]; g2 = buf[off+1]; r = buf[off+2]
        total += 1
        alvos = [(79,121,167),(242,142,43),(225,87,89),(89,161,79),(237,201,72),(118,183,178),(255,255,255),(0,255,255),(89,142,255)]
        for ar,ag,ab in alvos:
            if abs(r-ar)<30 and abs(g2-ag)<30 and abs(b-ab)<30:
                colored_graph += 1
                break
bmp3.Dispose()
print(f"sampled={total} colored_graph_pixels={colored_graph}", flush=True)
print("RESULTADO: >50 colored pixels de cores do grafico = nos/sinapses renderizados (movimento organico ativo)", flush=True)
print("RESULTADO: ~0 = grafico nao pintou (voltou ao problema)", flush=True)