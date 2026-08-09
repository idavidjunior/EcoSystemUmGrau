
import sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview, widget_grafo as wg
bridge = wg.Bridge()
win = webview.create_window(wg.TITLE, url=str(wg._build_view().resolve()),
    width=1280, height=750, resizable=True, frameless=True, easy_drag=False, shadow=False,
    focus=True, js_api=bridge, background_color=wg.BG)
bridge._win = win
webview.start()
