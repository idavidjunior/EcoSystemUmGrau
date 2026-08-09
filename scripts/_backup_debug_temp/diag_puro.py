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

# carrega o grafo.html PURO (sem injecoes do widget, sem bridge)
url = "http://127.0.0.1:8091/grafo.html"
win = webview.create_window("TesteGrafoPuro", url=url, width=1200, height=800, resizable=True)

def medir(tag):
    try:
        res = win.evaluate_js("""
          JSON.stringify({
            canvas: document.querySelectorAll('#net canvas').length,
            netKids: document.getElementById('net') ? document.getElementById('net').childNodes.length : -1,
            passou: typeof window.__passou__
          })
        """)
        print("[debug] " + tag + ": " + res, flush=True)
    except Exception as e:
        print("[debug] " + tag + " eval erro: " + repr(e), flush=True)

def no_load():
    threading.Timer(3.0, lambda: medir("+3s")).start()
    threading.Timer(8.0, lambda: medir("+8s")).start()

win.events.loaded += no_load
print("[debug] start", flush=True)
webview.start()
'''

tmp = os.path.join(ROOT, "scripts", "dbg_puro.py")
with open(tmp, "w", encoding="utf-8") as f:
    f.write(code)

serv = subprocess.Popen(
    [sys.executable, "-m", "http.server", "8091", "--directory", os.path.join(ROOT, "docs")],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)
print("http.server PID", serv.pid, flush=True)
time.sleep(1)
w = subprocess.Popen([sys.executable, "-u", tmp], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
print("widget PID", w.pid, flush=True)
time.sleep(18)
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
serv.terminate()