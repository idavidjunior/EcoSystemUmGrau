import os
import re
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

# Usa regex para encontrar e substituir o método debug_log
pattern = r'def debug_log\(self, msg: str\) -> None:\s+try:\s+with open\(BASE / \'docs\' / \'widget_log\.txt\', \'a\', encoding=\'utf-8\'\) as f:\s+f\.write\(f\'\{time\.time\(\):\.0f\} \| \{msg\}\n\'\)\s+except Exception:\s+pass'

replacement = '''def debug_log(self, msg: str) -> None:
        try:
            print('[DEBUG_BRIDGE] ' + msg, flush=True)
            with open(BASE / 'docs' / 'widget_log.txt', 'a', encoding='utf-8') as f:
                f.write(f'{time.time():.0f} | {msg}\n')
        except Exception as e:
            print('[DEBUG_BRIDGE ERROR] ' + str(e), flush=True)'''

new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content != content:
    Path('scripts/widget_grafo.py').write_text(new_content, encoding='utf-8')
    print('Substituido com sucesso via regex')
else:
    print('Padrao nao encontrado')