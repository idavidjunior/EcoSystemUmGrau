import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

print('Triple quotes:', content.count('"""'))

lines = content.split('\n')
for i, line in enumerate(lines):
    if 'WIDGET_JS_EXTRA' in line:
        print('Line {}: {}'.format(i, line.strip()))
    if 'def main' in line:
        print('main at line {}'.format(i))
    if '__name__' in line:
        print('main guard at line {}'.format(i))