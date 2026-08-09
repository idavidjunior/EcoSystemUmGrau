import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

lines = content.split('\n')
print('Lines 355-400:')
for i in range(355, min(400, len(lines))):
    print('{}: {}'.format(i+1, lines[i]))