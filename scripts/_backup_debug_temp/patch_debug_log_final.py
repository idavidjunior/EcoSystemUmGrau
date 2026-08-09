import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

lines = content.split('\n')
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'def debug_log(self, msg: str) -> None:' in line:
        new_lines.append('    def debug_log(self, msg: str) -> None:')
        new_lines.append('        try:')
        new_lines.append("            print('[DEBUG_BRIDGE] ' + msg, flush=True)")
        new_lines.append("            with open(BASE / 'docs' / 'widget_log.txt', 'a', encoding='utf-8') as f:")
        new_lines.append("                f.write(f'{time.time():.0f} | {msg}\n')")
        new_lines.append('        except Exception as e:')
        new_lines.append("            print('[DEBUG_BRIDGE ERROR] ' + str(e), flush=True)")
        i += 1
        while i < len(lines) and (lines[i].startswith('        ') or lines[i].strip() == ''):
            i += 1
        continue
    new_lines.append(line)
    i += 1

new_content = '\n'.join(new_lines)
Path('scripts/widget_grafo.py').write_text(new_content, encoding='utf-8')
print('Substituido via line-by-line')