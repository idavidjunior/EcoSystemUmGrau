"""Regenerate grafo.html AND grafo_widget.html, then validate JSON."""
import subprocess, sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

# Step 1: Regenerate grafo.html from vault
print('Regenerating grafo.html...')
r = subprocess.run([sys.executable, str(BASE/'scripts'/'generate-graph-html.py'), str(BASE/'docs'/'grafo.html')],
                   capture_output=True, text=True, timeout=40)
print(r.stdout.strip())
if r.returncode != 0:
    print('STDERR:', r.stderr[:500])

# Step 2: Build the widget view (grafo_widget.html)
print('\nBuilding widget view...')
import importlib.util
spec = importlib.util.spec_from_file_location('widget_grafo', str(BASE / 'scripts' / 'widget_grafo.py'))
mod = importlib.util.module_from_spec(spec)
sys.modules['widget_grafo'] = mod
spec.loader.exec_module(mod)

view = mod._build_view()
print(f'Widget view: {view}' if view else 'Widget view: FAILED')

# Step 3: Check sessionsession is gone
if view:
    content = view.read_text(encoding='utf-8')
    count = content.count('sessionsession')
    print(f'\n"sessionsession" occurrences in widget HTML: {count}')
    
    if count == 0:
        print('CLEAN - No corrupted tags remain.')
    else:
        # Find remaining occurrences
        idx = 0
        while True:
            idx = content.find('sessionsession', idx)
            if idx == -1:
                break
            print(f'  Found at byte {idx}: ...{content[max(0,idx-40):idx+40]}...')
            idx += 1