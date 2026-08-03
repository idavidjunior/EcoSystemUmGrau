import subprocess, sys, os, time

BASE = os.path.dirname(os.path.abspath(__file__))
w = subprocess.Popen(
    [sys.executable, "-u", os.path.join(BASE, "widget_grafo.py")],
    stdout=open(os.path.join(BASE, "..", "docs", "w_out3.txt"), "wb"),
    stderr=open(os.path.join(BASE, "..", "docs", "w_err3.txt"), "wb"),
)
print("widget PID:", w.pid, flush=True)

geo = os.path.join(BASE, "..", "docs", "grafo_widget_geometria.json")
last = os.path.getmtime(geo) if os.path.exists(geo) else 0
for i in range(6):
    time.sleep(4)
    wv = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='msedgewebview2.exe'\" | Where-Object { $_.CommandLine -notmatch 'TeamViewer' } | Measure-Object | Select-Object -ExpandProperty Count"],
        capture_output=True, text=True)
    alive = w.poll() is None
    now = os.path.getmtime(geo) if os.path.exists(geo) else 0
    err = open(os.path.join(BASE, "..", "docs", "w_err3.txt"), "rb").read()[:200]
    print(f"t={4*(i+1)}s alive={alive} wv2={wv.stdout.strip()} geo_moved={now!=last} err={err!r}", flush=True)

w.terminate()
print("done", flush=True)
