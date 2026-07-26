import subprocess, json, time, os, sys

PYTHONW = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
HELPER = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "status_check.py")
JSON_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "widget_status.json")
WATCHDOG_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "watchdog_recovery.json")

def run_hidden(args, **kw):
    kw.setdefault("capture_output", True)
    kw.setdefault("text", True)
    kw.setdefault("timeout", 30)
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0
    kw["startupinfo"] = si
    return subprocess.run(args, **kw)

while True:
    try:
        result = run_hidden([PYTHONW, HELPER, "all"])
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            # Merge watchdog recovery data
            try:
                with open(WATCHDOG_FILE) as wf:
                    wd = json.load(wf)
                    data["recovery"] = wd
            except:
                data["recovery"] = {"status": "no_watchdog", "message": "watchdog nao disponivel"}
            with open(JSON_FILE, "w") as f:
                json.dump(data, f)
    except:
        pass
    time.sleep(10)
