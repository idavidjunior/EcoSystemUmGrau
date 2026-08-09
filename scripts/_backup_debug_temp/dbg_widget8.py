
import sys, os, time
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

def check():
    time.sleep(8)
    try:
        res = win.evaluate_js("""
          JSON.stringify({
            canvas: document.querySelectorAll('#net canvas').length,
            visType: typeof vis,
            visKeys: Object.keys(vis).slice(0,30),
            errs: (window.__erros__||[])
          })
        """)
        print("[debug] STATE:", res, flush=True)
    except Exception as e:
        print("[debug] evaluate_js erro:", repr(e), flush=True)

# injeta catcher o mais cedo possivel (via before_load nao disponivel; aqui apos load)
def injeta_catcher():
    try:
        win.evaluate_js("""
          window.__erros__ = [];
          window.addEventListener('error', function(e){ window.__erros__.push(String(e.message||e.error)); });
        """)
    except Exception:
        pass
    check()

win.events.loaded += injeta_catcher
print("[debug] start", flush=True)
webview.start()
