import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

# Corrige o optional chaining ?.
content = content.replace(
    "(ev.reason||ev.reason?.message||'')",
    "(ev.reason||(ev.reason&&ev.reason.message)||'')"
)

Path('scripts/widget_grafo.py').write_text(content, encoding='utf-8')
print('Corrigido optional chaining')