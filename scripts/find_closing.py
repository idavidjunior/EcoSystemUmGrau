import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Find the closing """ of WIDGET_JS_EXTRA
for i in range(358, 890):
    if '"""' in lines[i] and i > 358:
        print('Line {}: {}'.format(i+1, lines[i]))
        # Show context
        for j in range(max(0, i-5), min(len(lines), i+5)):
            print('{}: {}'.format(j+1, lines[j]))
        break