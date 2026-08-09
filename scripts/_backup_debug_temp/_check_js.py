"""Check if WIDGET_JS_EXTRA contains the new buttons."""
import importlib.util, sys

spec = importlib.util.spec_from_file_location('widget_grafo', 'scripts/widget_grafo.py')
mod = importlib.util.module_from_spec(spec)
sys.modules['widget_grafo'] = mod
spec.loader.exec_module(mod)

js = mod.WIDGET_JS_EXTRA
print("Len:", len(js))
for kw in ['grupo3D', 'btn3D', 'mk-btn-3d', 'painelToggle', 'btnReset', 'mk-btn-reset', 'mk-painel-toggle', 'flashGroup', 'btnFlash', 'mk-btn-flash']:
    print(f"  {kw}: {js.count(kw)}")
