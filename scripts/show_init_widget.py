import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

idx = content.rfind('WIDGET_JS_EXTRA')
if idx >= 0:
    idx2 = content.find('initWidgetControls', idx)
    if idx2 >= 0:
        print(content[idx2:idx2+2000])
    else:
        print('initWidgetControls not found')
else:
    print('WIDGET_JS_EXTRA not found')