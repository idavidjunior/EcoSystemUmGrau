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
    resizable=True, frameless=True, easy_drag=False, shadow=False, focus=False,
    js_api=bridge, background_color=wg.BG,
)
bridge._win = win

erros = []
def on_console(msg):
    erros.append(str(msg))

def check():
    time.sleep(1.0)
    # inject error catcher first
    win.evaluate_js("""
      window.__erros__ = [];
      window.addEventListener('error', function(e){ window.__erros__.push(String(e.message||e.error||e)); });
      try { window.__erros__.push('NETC=' + document.querySelectorAll('#net canvas').length); } catch(e){}
    """)
    time.sleep(6)
    res = win.evaluate_js("""
      JSON.stringify({
        canvas: document.querySelectorAll('#net canvas').length,
        ns: typeof nodes,
        errs: (window.__erros__||[]),
        childs: document.getElementById('net') ? document.getElementById('net').childNodes.length : -1
      })
    """)
    print("[debug] STATE:", res, flush=True)

def onclose():
    print("[debug] fechando", flush=True)

win.events.loaded += check
win.events.closed += onclose
print("[debug] start", flush=True)
webview.start()
'''

tmp = os.path.join(ROOT, "scripts", "dbg_widget7.py")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(code)

w = subprocess.Popen(
    [sys.executable, "-u", tmp],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
)
print("PID", w.pid, flush=True)
time.sleep(26)
print("alive", w.poll() is None, flush=True)
w.terminate()
try:
    out, err = w.communicate(timeout=10)
    print("--- stdout ---")
    print(out.decode("utf-8", errors="ignore") if out else "(vazio)")
    print("--- stderr ---")
    print(err.decode("utf-8", errors="ignore")[-3000:] if err else "(vazio)")
except Exception as e:
    print("comm err:", e)