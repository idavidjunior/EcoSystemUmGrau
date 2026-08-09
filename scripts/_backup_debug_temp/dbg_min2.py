
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
