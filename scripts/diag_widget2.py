import subprocess, sys, os, time

BASE = os.path.dirname(os.path.abspath(__file__))
w = subprocess.Popen(
    [sys.executable, "-u", os.path.join(BASE, "widget_grafo.py")],
    stdout=open(os.path.join(BASE, "..", "docs", "w_out2.txt"), "wb"),
    stderr=open(os.path.join(BASE, "..", "docs", "w_err2.txt"), "wb"),
)
print("widget PID:", w.pid)
time.sleep(12)
alive = w.poll() is None
print("alive after 12s:", alive)
if not alive:
    print("exit code:", w.returncode)
w.terminate()
