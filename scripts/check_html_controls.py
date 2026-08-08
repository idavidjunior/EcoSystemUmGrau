import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
html = Path('docs/grafo_widget.html').read_text(encoding='utf-8')

checks = {
    'mk-controles': 'mk-controles' in html,
    'mk-painel-toggle': 'mk-painel-toggle' in html,
    'mk-btn-3d': 'mk-btn-3d' in html,
    'mk-btn-flash': 'mk-btn-flash' in html,
    'velSlider': 'velSlider' in html,
    'temaSel': 'temaSel' in html,
    'mk-drag': 'mk-drag' in html,
    'mk-resize': 'mk-resize' in html,
}

for k, v in checks.items():
    status = 'OK' if v else 'FALTA'
    print(status + ': ' + k)