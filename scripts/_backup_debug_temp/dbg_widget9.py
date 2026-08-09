
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

def check_agora():
    # imediato, sem sleep
    try:
        res = win.evaluate_js("document.querySelectorAll('canvas').length + '|' + typeof vis")
        print("[debug] CANVAS+VIS:", res, flush=True)
    except Exception as e:
        print("[debug] eval erro imediato:", repr(e), flush=True)

win.events.loaded += check_agora
print("[debug] start", flush=True)
webview.start()
