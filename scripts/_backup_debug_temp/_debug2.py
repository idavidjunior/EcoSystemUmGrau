"""Debug the path and module issue."""
import sys, shutil
from pathlib import Path

wg = Path('scripts/widget_grafo.py').resolve()
base = wg.parent.parent
view = base / 'docs' / 'grafo_widget.html'
print(f'VIEW_COPY would be: {view}')
print(f'grafo_widget.html exists: {view.exists()}')

shutil.rmtree(str(wg.parent / '__pycache__'), ignore_errors=True)
sys.path.insert(0, str(wg.parent))
import widget_grafo

print(f'WIDGET_JS_EXTRA len: {len(widget_grafo.WIDGET_JS_EXTRA)}')
print(f'mk-btn-3d count: {widget_grafo.WIDGET_JS_EXTRA.count("mk-btn-3d")}')
print(f'painelToggle count: {widget_grafo.WIDGET_JS_EXTRA.count("painelToggle")}')
print(f'VIEW_COPY: {widget_grafo.VIEW_COPY}')
print(f'VIEW_COPY exists: {widget_grafo.VIEW_COPY.exists()}')
print(f'BASE: {widget_grafo.BASE}')
print(f'OUTPUT_HTML: {widget_grafo.OUTPUT_HTML}')

# Now call _build_view
result = widget_grafo._build_view()
print(f'\n_build_view returned: {result}')
content = result.read_text(encoding='utf-8')
print(f'mk-btn-3d in output: {content.count("mk-btn-3d")}')
print(f'painelToggle in output: {content.count("painelToggle")}')
print(f'btnReset in output: {content.count("btnReset")}')
