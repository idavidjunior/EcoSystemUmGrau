"""Final debug: clear cache, simulate rebuild_widget.py exactly."""
import sys, importlib.util, shutil
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Clear pycache
shutil.rmtree(str(BASE / 'scripts' / '__pycache__'), ignore_errors=True)
print("1. __pycache__ cleared")

# Simulate rebuild_widget.py
spec = importlib.util.spec_from_file_location('widget_grafo', str(BASE / 'scripts' / 'widget_grafo.py'))
mod = importlib.util.module_from_spec(spec)
sys.modules['widget_grafo'] = mod
spec.loader.exec_module(mod)
print(f"2. Module loaded: {mod.__file__}")
print(f"3. WIDGET_JS_EXTRA len: {len(mod.WIDGET_JS_EXTRA)}")
print(f"   mk-btn-3d: {mod.WIDGET_JS_EXTRA.count('mk-btn-3d')}")

result = mod._build_view()
content = result.read_text(encoding='utf-8')
print(f"4. _build_view output: {result}")
print(f"   mk-btn-3d: {content.count('mk-btn-3d')}")
print(f"   mk-painel-toggle: {content.count('mk-painel-toggle')}")
print(f"   btnReset: {content.count('btnReset')}")
