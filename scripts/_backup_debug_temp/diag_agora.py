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

def check_agora():
    # imediato, sem sleep
    try:
        res = win.evaluate_js("document.querySelectorAll('canvas').length + '|' + typeof vis")
        print("[debug] CANVAS+VIS:", res, flush=True)
    except Exception as e:
        print("[debug] eval erro imediato:", repr(e), flush=True)

win.events.loaded += check_agora
print("[debug] start", flush=True)
webview.start()
'''

tmp = os.path.join(ROOT, "scripts", "dbg_widget9.py")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(code)

w = subprocess.Popen(
    [sys.executable, "-u", tmp],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
)
print("PID", w.pid, flush=True)
time.sleep(20)
print("alive", w.poll() is None, flush=True)
w.terminate()
try:
    out, err = w.communicate(timeout=10)
    print("--- stdout ---")
    print(out.decode("utf-8", errors="ignore") if out else "(vazio)")
    print("--- stderr ---")
    print(err.decode("utf-8", errors="ignore")[-1500:] if err else "(vazio)")
except Exception as e:
    print("comm err:", e)