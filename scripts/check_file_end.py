import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

triple_quotes = content.count('"""')
print('Triple quotes count:', triple_quotes)

lines = content.split('\n')
print('--- Last 30 lines ---')
for line in lines[-30:]:
    print(line)