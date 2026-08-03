import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
from widget_grafo import _build_view, _regenerate

_regenerate()
v = _build_view()
print('View:', v)
content = v.read_text(encoding='utf-8')
print('Tamanho HTML:', len(content), 'bytes')
print('vis.Network no inline:', 'vis.Network' in content)
print('CDN referencia:', 'unpkg' in content)
print('vendor src ref:', 'src="vendor/vis-network' in content)
