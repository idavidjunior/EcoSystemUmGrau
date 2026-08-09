
import sys, os, time, threading
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview

url = "http://127.0.0.1:8093/teste_plano.html"
win = webview.create_window("TestePlano", url=url, width=600, height=400, resizable=True)

def medir(tag):
    try:
        res = win.evaluate_js("JSON.stringify({passou:window.__passou__, erro:window.__erro__, errs:window.__erros__, canvas:document.querySelectorAll('#net canvas').length})")
        print("[debug] " + tag + ": " + res, flush=True)
    except Exception as e:
        print("[debug] " + tag + " eval erro: " + repr(e), flush=True)

def no_load():
    threading.Timer(4.0, lambda: medir("+4s")).start()
    threading.Timer(8.0, lambda: medir("+8s")).start()

win.events.loaded += no_load
print("[debug] start", flush=True)
webview.start()
