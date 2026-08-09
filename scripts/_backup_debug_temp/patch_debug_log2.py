import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

old = '''def debug_log(self, msg: str) -> None:
        try:
            with open(BASE / 'docs' / 'widget_log.txt', 'a', encoding='utf-8') as f:
                f.write(f'{time.time():.0f} | {msg}\n')
        except Exception:
            pass'''

new = '''def debug_log(self, msg: str) -> None:
        try:
            print('[DEBUG_BRIDGE] ' + msg, flush=True)
            with open(BASE / 'docs' / 'widget_log.txt', 'a', encoding='utf-8') as f:
                f.write(f'{time.time():.0f} | {msg}\n')
        except Exception as e:
            print('[DEBUG_BRIDGE ERROR] ' + str(e), flush=True)'''

if old in content:
    content = content.replace(old, new)
    Path('scripts/widget_grafo.py').write_text(content, encoding='utf-8')
    print('Substituido com sucesso')
else:
    print('Nao encontrado')