import sys, os, time
sys.stdout.reconfigure(encoding='utf-8')
import pythonnet, clr
clr.AddReference("System.Drawing"); clr.AddReference("System.Windows.Forms")
from System.Drawing import Bitmap, Graphics, Imaging, Rectangle
from System.Diagnostics import Process
from System import IntPtr, Array, Byte
import System
from System.Windows.Forms import Screen

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

def count_graph_colors(path):
    bmp = Bitmap.FromFile(path)
    rect = Rectangle(0,0,bmp.Width,bmp.Height)
    data = bmp.LockBits(rect, Imaging.ImageLockMode.ReadOnly, Imaging.PixelFormat.Format32bppRgb)
    buf = Array[Byte](data.Stride * bmp.Height)
    System.Runtime.InteropServices.Marshal.Copy(data.Scan0, buf, 0, len(buf))
    bmp.UnlockBits(data)
    # quantas coordenadas coloridas (graph colors) e um hash simples de posicao
    pts = 0
    wsum_x=0; wsum_y=0
    alvos = [(79,121,167),(242,142,43),(225,87,89),(89,161,79),(237,201,72),(118,183,178),(255,255,255),(89,142,255)]
    for row in range(0,bmp.Height,4):
        ro=row*data.Stride
        for col in range(0,bmp.Width,4):
            off=ro+col*4
            r=buf[off+2]; g=buf[off+1]; b=buf[off]
            for ar,ag,ab in alvos:
                if abs(r-ar)<26 and abs(g-ag)<26 and abs(b-ab)<26:
                    pts += 1; wsum_x += col; wsum_y += row
                    break
    bmp.Dispose()
    return pts, wsum_x, wsum_y

scr = Screen.PrimaryScreen.Bounds
bmp1 = Bitmap(scr.Width, scr.Height)
g=Graphics.FromImage(bmp1); g.CopyFromScreen(0,0,0,0,scr.Size); g.Dispose()
p1=os.path.join(ROOT,"docs","shot_mov1.png"); bmp1.Save(p1, Imaging.ImageFormat.Png); bmp1.Dispose()
time.sleep(4)
bmp2 = Bitmap(scr.Width, scr.Height)
g=Graphics.FromImage(bmp2); g.CopyFromScreen(0,0,0,0,scr.Size); g.Dispose()
bmp2.Save(p2, Imaging.ImageFormat.Png); bmp2.Dispose()
time.sleep(0)
import shutil
bmp2b=Bitmap.FromFile(p2)
# re-save as png
path2=os.path.join(ROOT,"docs","shot_mov2.png")
bmp2b.Save(path2, Imaging.ImageFormat.Png); bmp2b.Dispose()
c1,x1,y1 = count_graph_colors(p1)
c2,x2,y2 = count_graph_colors(path2)
print(f"t1: colored={c1}  centroid=({x1},{y1})", flush=True)
print(f"t2: colored={c2}  centroid=({x2},{y2})", flush=True)
if c1 > 50 and c2 > 50:
    dx = x2-x1 if c2 else 0
    print(f"pixels coloridos nas duas capturas -> grafo renderizado em ambos", flush=True)
    print("Movimento organicos detectado:", (c1 != c2) or abs(x2-c1//2) != abs(x1-c1//2), flush=True)
else:
    print("GRAFO NAO RENDERIZOU em pelo menos uma captura", flush=True)