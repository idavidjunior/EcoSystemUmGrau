import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a simple echo method with no parameters
idx = None
for i, line in enumerate(lines):
    if 'def ping(self) -> str:' in line:
        idx = i
        break

if idx is not None:
    # Find the end of the ping method
    end_idx = idx + 1
    while end_idx < len(lines) and (lines[end_idx].startswith('        ') or lines[end_idx].strip() == ''):
        end_idx += 1
    
    new_method = [
        '',
        '    def echo(self, msg: str) -> str:',
        '        """Echo test with parameter."""',
        '        print("[BRIDGE] echo called with: " + str(msg), flush=True)',
        '        return "ECHO: " + str(msg)',
        ''
    ]
    
    lines[end_idx:end_idx] = [l for l in ['', '    def echo(self, msg: str) -> str:', '        """Echo test with parameter."""', '        print("[BRIDGE] echo called with: " + str(msg), flush=True)', '        return "ECHO: " + str(msg)', ''] if l != ''] + ['']
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('echo method added')
else:
    print('ping not found')