import subprocess, sys, os, time

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, ".."))

env = dict(os.environ)
env["PYWEBVIEW_LOG"] = "DEBUG"

code = r'''
import sys, os, time
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview
import widget_grafo as wg

bridge = wg.Bridge()
win = webview.create_window(
    wg.TITLE,
    url=str(wg._build_view().resolve()),
    width=1200, height=800,
    x=None, y=None,
    resizable=True, frameless=True, easy_drag=False, shadow=False, focus=False,
    js_api=bridge,
    background_color=wg.BG,
)
bridge._win = win

def loaded():
    time.sleep(3)
    print("[dbg] loaded disparou", flush=True)
    try:
        res = win.evaluate_js("""
          (function(){
            var canvases = document.querySelectorAll('#net canvas');
            var out = {
              netChildren: document.getElementById('net') ? document.getElementById('net').childNodes.length : -1,
              canvasCount: canvases.length,
              canvasSize: canvases.length ? {w: canvases[0].width, h: canvases[0].height} : null,
              visDataSets: (typeof window.nodes !== 'undefined') || (typeof nodes !== 'undefined')
            };
            return JSON.stringify(out);
          })();
        """)
        print("[debug] STATE:", res, flush=True)
    except Exception as e:
        print("[debug] evaluate_js erro:", repr(e), flush=True)

win.events.loaded += loaded
print("[debug] start", flush=True)
webview.start()
'''

tmp = os.path.join(ROOT, "scripts", "dbg_widget6.py")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(code)

w = subprocess.Popen(
    [sys.executable, "-u", tmp],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
)
print("PID", w.pid, flush=True)
time.sleep(24)
print("alive", w.poll() is None, flush=True)
w.terminate()
try:
    out, err = w.communicate(timeout=10)
    print("--- stdout ---")
    print(out.decode("utf-8", errors="ignore") if out else "(vazio)")
    print("--- stderr ---")
    print(err.decode("utf-8", errors="ignore")[-2000:] if err else "(vazio)")
except Exception as e:
    print("comm err:", e)