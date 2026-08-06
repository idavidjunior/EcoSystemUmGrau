import subprocess, sys
from pathlib import Path
import importlib.util

BASE = Path(__file__).resolve().parent.parent

# Regenerate HTML
r = subprocess.run([sys.executable, str(BASE / 'scripts' / 'generate-graph-html.py'), str(BASE / 'docs' / 'grafo.html')], capture_output=True, text=True, timeout=30)
print('Regen:', r.returncode)

spec = importlib.util.spec_from_file_location('widget_grafo', str(BASE / 'scripts' / 'widget_grafo.py'))
mod = importlib.util.module_from_spec(spec)
sys.modules['widget_grafo'] = mod
spec.loader.exec_module(mod)

view = mod._build_view()
content = view.read_text(encoding='utf-8') if view else ''

pos_net = content.find('const network = new vis.Network(')
pos_bind = content.find(".querySelectorAll('.lg')")

print('network init byte:', pos_net)
print('.lg binding byte:', pos_bind)
print('BOTAO_FILTRO in content:', 'BOTAO_FILTRO' in content)
print('Binding AFTER network:', pos_bind > pos_net if pos_bind >= 0 else 'N/A')