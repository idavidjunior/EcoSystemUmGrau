import sys, os, time, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
env = dict(os.environ)
env["PYWEBVIEW_LOG"] = "DEBUG"
code = r'''
import sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview
win = webview.create_window("Probe", url="http://127.0.0.1:8096/teste_title.html",
    width=900, height=600, resizable=True)
webview.start()
'''
tmp = os.path.join(ROOT, "scripts", "dbg_title.py")
open(tmp, "w", encoding="utf-8").write(code)
serv = subprocess.Popen([sys.executable, "-m", "http.server", "8096", "--directory", os.path.join(ROOT, "docs")],
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
p = subprocess.Popen([sys.executable, "-u", tmp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)
print("PID", p.pid, flush=True)
time.sleep(8)
print("DONE")