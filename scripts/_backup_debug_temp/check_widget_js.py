import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

# Encontra o início e fim do WIDGET_JS_EXTRA
start = content.find('WIDGET_JS_EXTRA = """')
if start >= 0:
    # Encontra o fechamento
    end = content.find('"""', start + 20)
    if end >= 0:
        widget_js = content[start:end+3]
        print(f'WIDGET_JS_EXTRA length: {len(widget_js)}')
        print('--- Inicio ---')
        print(widget_js[:200])
        print('--- Fim ---')
        print(widget_js[-200:])
    else:
        print('Fechamento nao encontrado')
else:
    print('Inicio nao encontrado')