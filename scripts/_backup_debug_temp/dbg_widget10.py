
import sys, os, time, threading
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview
import widget_grafo as wg

bridge = wg.Bridge()
win = webview.create_window(
    wg.TITLE,
    url=str(wg._build_view().resolve()),
    width=1200, height=800,
    resizable=True, frameless=True, easy_drag=False, shadow=False, focus=False,
    js_api=bridge, background_color=wg.BG,
)
bridge._win = win

def medir(tag):
    try:
        res = win.evaluate_js("""
          JSON.stringify({
            canvas: document.querySelectorAll('#net canvas').length,
            visType: typeof vis,
            hasDataSet: typeof vis.DataSet,
            netDivChildren: document.getElementById('net').childNodes.length
          })
        """)
        print("[debug] " + tag + ": " + res, flush=True)
    except Exception as e:
        print("[debug] " + tag + " eval erro: " + repr(e), flush=True)

def no_load():
    threading.Timer(2.0, lambda: medir("+2s")).start()
    threading.Timer(6.0, lambda: medir("+6s")).start()
    threading.Timer(12.0, lambda: medir("+12s")).start()

win.events.loaded += no_load
print("[debug] start", flush=True)
webview.start()
