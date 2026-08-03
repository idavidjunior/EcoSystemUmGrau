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
    width=1280, height=800,
    resizable=True, frameless=True, easy_drag=False, shadow=False, focus=False,
    js_api=bridge, background_color=wg.BG,
)
bridge._win = win
print("[debug] widget com DevTools aberto (debug=True)", flush=True)
webview.start(debug=True)
'''

tmp = os.path.join(ROOT, "scripts", "dbg_devtools.py")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(code)

w = subprocess.Popen(
    [sys.executable, "-u", tmp],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
)
print("widget PID", w.pid, flush=True)
print("Deixando aberto 40s com DevTools...", flush=True)
time.sleep(40)
print("alive", w.poll() is None, flush=True)
w.terminate()
try:
    out, err = w.communicate(timeout=10)
    print("--- stderr (console) ---")
    print(err.decode("utf-8", errors="ignore")[-3000:] if err else "(vazio)")
except Exception as e:
    print("comm err:", e)