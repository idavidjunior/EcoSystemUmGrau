
import sys, os, time, threading
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview
win = webview.create_window("TF", url="http://127.0.0.1:8094/teste_foco.html", width=700, height=500, resizable=True)
def M(tag):
    try:
        r = win.evaluate_js("JSON.stringify({ok:typeof window.__ok__, jsErr:window.__jsErr__, ms:window.__t1__?window.__t1__-window.__t0__:0, canvas:document.querySelectorAll('#net canvas').length})")
        print("[debug]" + tag + ": " + r, flush=True)
    except Exception as e:
        print("[debug]" + tag + " E: " + repr(e), flush=True)
def onload():
    threading.Timer(3.0, lambda: M("+3s")).start()
    threading.Timer(8.0, lambda: M("+8s")).start()
win.events.loaded += onload
webview.start()
