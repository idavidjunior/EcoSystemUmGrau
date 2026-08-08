import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

# Corrige o f-string quebrado - substitui a linha problemática
content = content.replace(
    "f.write(f'{time.time():.0f} | {msg}\n')",
    "f.write(f'{time.time():.0f} | {msg}\\n')"
)

Path('scripts/widget_grafo.py').write_text(content, encoding='utf-8')
print('Corrigido f-string')