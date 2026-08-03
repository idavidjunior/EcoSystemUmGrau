import subprocess, sys, os, time

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, ".."))

env = dict(os.environ)
env["PYWEBVIEW_LOG"] = "DEBUG"

code = r'''
import sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview
import widget_grafo as wg

bridge = wg.Bridge()
win = webview.create_window(
    wg.TITLE,
    url=str(wg._build_view().resolve()),
    width=wg.DEFAULT_W, height=wg.DEFAULT_H,
    x=None, y=None,
    resizable=True, frameless=True, easy_drag=False, shadow=False, focus=False,
    js_api=bridge,
    background_color=wg.BG,
)
bridge._win = win

def loaded():
    print("[dbg] loaded disparou", flush=True)
    try:
        res = win.evaluate_js("""
          (function(){
            var out = {hasVis: typeof window.vis !== 'undefined',
                       hasNet: !!document.getElementById('net'),
                       netSize: document.getElementById('net') ? {w: document.getElementById('net').clientWidth, h: document.getElementById('net').clientHeight} : null,
                       pywebviewApi: !!(window.pywebview && window.pywebview.api)};
            if (window.network) {
              out.network = true;
              try { out.nosVisiveis = window.nodes.length; out.arestasVisiveis = window.edges.length; } catch(e){ out.errData = String(e); }
            } else {
              out.network = false;
            }
            return JSON.stringify(out);
          })();
        """)
        print("[dbg] JS STATE:", res, flush=True)
    except Exception as e:
        print("[dbg] evaluate_js erro:", repr(e), flush=True)

win.events.loaded += loaded

print("[dbg] start", flush=True)
webview.start(debug=True)
'''

tmp = os.path.join(ROOT, "scripts", "dbg_widget5.py")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(code)

w = subprocess.Popen(
    [sys.executable, "-u", tmp],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
)
print("PID", w.pid, flush=True)
time.sleep(22)
print("alive", w.poll() is None, flush=True)
w.terminate()
try:
    out, err = w.communicate(timeout=10)
    print("--- stdout ---")
    print(out.decode("utf-8", errors="ignore") if out else "(vazio)")
    print("--- stderr (requests+console) ---")
    print(err.decode("utf-8", errors="ignore")[-4000:] if err else "(vazio)")
except Exception as e:
    print("comm err:", e)