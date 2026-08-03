
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

def no_load():
    # injeta catcher de erro global e forca re-execucao do script do grafo
    time.sleep(0.5)
    try:
        win.evaluate_js("""
          window.__erros__ = [];
          window.addEventListener('error', function(e){ window.__erros__.push(String(e.message||e.error||e)); });
        """)
    except Exception as e:
        print("[debug] injeta catcher erro:", repr(e), flush=True)
    threading.Timer(6.0, medir).start()

def medir():
    try:
        res = win.evaluate_js("JSON.stringify({errs:(window.__erros__||[]), canvas:document.querySelectorAll('#net canvas').length})")
        print("[debug] ERROS+CANVAS:", res, flush=True)
    except Exception as e:
        print("[debug] medir erro:", repr(e), flush=True)

win.events.loaded += no_load
print("[debug] start", flush=True)
webview.start()
