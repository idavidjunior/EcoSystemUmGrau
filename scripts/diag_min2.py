import subprocess, sys, os, time, threading

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, ".."))

env = dict(os.environ)
env["PYWEBVIEW_LOG"] = "DEBUG"

code = r'''
import sys, os, time, threading
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview

url = "http://127.0.0.1:8092/teste_minimo.html"
win = webview.create_window("TesteMin2", url=url, width=600, height=400, resizable=True)

def medir(tag):
    try:
        res = win.evaluate_js("""
          JSON.stringify({
            canvas: document.querySelectorAll('#net canvas').length,
            passou: window.__passou__||'nao',
            erro: window.__erro__||'sem-erro',
            dset: typeof vis.DataSet
          })
        """)
        print("[debug] " + tag + ": " + res, flush=True)
    except Exception as e:
        print("[debug] " + tag + " eval erro: " + repr(e), flush=True)

def no_load():
    threading.Timer(3.0, lambda: medir("+3s")).start()
    threading.Timer(7.0, lambda: medir("+7s")).start()

win.events.loaded += no_load
print("[debug] start", flush=True)
webview.start()
'''

tmp = os.path.join(ROOT, "scripts", "dbg_min2.py")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(code)

serv = subprocess.Popen(
    [sys.executable, "-m", "http.server", "8092", "--directory", os.path.join(ROOT, "docs")],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
time.sleep(1)
w = subprocess.Popen([sys.executable, "-u", tmp], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
print("widget PID", w.pid, flush=True)
time.sleep(16)
print("alive", w.poll() is None, flush=True)
w.terminate()
try:
    out, err = w.communicate(timeout=10)
    print("--- stdout ---")
    print(out.decode("utf-8", errors="ignore") if out else "(vazio)")
    print("--- stderr ---")
    print(err.decode("utf-8", errors="ignore")[-1200:] if err else "(vazio)")
except Exception as e:
    print("comm err:", e)
serv.terminate()