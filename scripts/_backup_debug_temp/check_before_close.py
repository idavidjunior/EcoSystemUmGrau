import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Find the line with </script> before the closing """
for i in range(795, 802):
    print('{}: {}'.format(i+1, lines[i]))