
import sys, os
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
import webview
import widget_grafo as wg

bridge = wg.Bridge()
win = webview.create_window(
    wg.TITLE,
    url=str(wg._build_view().resolve()),
    width=wg.DEFAULT_W, height=wg.DEFAULT_H,
    x=None, y=None,
    resizable=True, frameless=True, easy_drag=False, shadow=False, focus=False,
    js_api=bridge,
    background_color=wg.BG,
)
bridge._win = win

def loaded():
    print("[dbg] loaded disparou", flush=True)
    try:
        res = win.evaluate_js("""
          (function(){
            var out = {hasVis: typeof window.vis !== 'undefined',
                       hasNet: !!document.getElementById('net'),
                       netSize: document.getElementById('net') ? {w: document.getElementById('net').clientWidth, h: document.getElementById('net').clientHeight} : null,
                       pywebviewApi: !!(window.pywebview && window.pywebview.api)};
            if (window.network) {
              out.network = true;
              try { out.nosVisiveis = window.nodes.length; out.arestasVisiveis = window.edges.length; } catch(e){ out.errData = String(e); }
            } else {
              out.network = false;
            }
            return JSON.stringify(out);
          })();
        """)
        print("[dbg] JS STATE:", res, flush=True)
    except Exception as e:
        print("[dbg] evaluate_js erro:", repr(e), flush=True)

win.events.loaded += loaded

print("[dbg] start", flush=True)
webview.start(debug=True)
