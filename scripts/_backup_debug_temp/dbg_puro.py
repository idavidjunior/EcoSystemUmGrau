
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
