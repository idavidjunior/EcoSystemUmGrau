import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

idx = content.find('WIDGET_JS_EXTRA = """')
if idx >= 0:
    end_idx = content.find('"""', idx + 20)
    if end_idx >= 0:
        widget_js = content[idx:end_idx+3]
        Path('widget_js_extra_complete.js').write_text(widget_js, encoding='utf-8')
        print(f'WIDGET_JS_EXTRA length: {len(widget_js)}')
        print('Saved')
    else:
        print('End not found')
else:
    print('Start not found')