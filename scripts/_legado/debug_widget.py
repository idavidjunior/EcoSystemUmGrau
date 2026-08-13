import os, sys, time
os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
sys.path.insert(0, '.')

import webview
from scripts.widget_grafo import Bridge, _build_view

print("=== WIDGET STARTING ===", flush=True)
view = _build_view()
print(f"View: {view}", flush=True)

win = webview.create_window(
    "Cerebro Vivo",
    url=str(view.resolve()),
    width=1024, height=768,
    x=100, y=100,
    js_api=Bridge(),
    frameless=True,
    easy_drag=False,
    shadow=False,
    focus=False,
    background_color="#1e1e2e"
)
print("Window created", flush=True)

webview.start(debug=True)
print("Done")