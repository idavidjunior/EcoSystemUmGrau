import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

if 'print("[WIDGET] main() started")' not in content:
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'def main()' in line:
            lines.insert(i + 1, '    print("[WIDGET] main() started", flush=True)')
            break
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('Print adicionado no main')
else:
    print('Ja existe')