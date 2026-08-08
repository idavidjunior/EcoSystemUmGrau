import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

# Mostra o final do WIDGET_JS_EXTRA
idx = content.rfind('WIDGET_JS_EXTRA')
if idx >= 0:
    # Procura o fechamento da string tripla
    end_idx = content.find('"""', idx + 20)
    if end_idx >= 0:
        print(content[idx:end_idx+3])
    else:
        print('Fechamento nao encontrado')