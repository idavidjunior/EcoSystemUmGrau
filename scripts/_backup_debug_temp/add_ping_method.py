import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a simple echo method to test bridge
idx = None
for i, line in enumerate(lines):
    if 'def test_bridge(self) -> str:' in line:
        idx = i
        break

if idx is not None:
    # Find the end of the method
    end_idx = idx + 1
    while end_idx < len(lines) and (lines[end_idx].startswith('        ') or lines[end_idx].strip() == ''):
        end_idx += 1
    
    # Add a new method after test_bridge
    new_method = [
        '',
        '    def ping(self) -> str:',
        '        """Simple ping test."""',
        '        print("[BRIDGE] ping called", flush=True)',
        '        return "PONG"',
        ''
    ]
    
    lines[end_idx:end_idx] = [l for l in new_method if l != ''] + ['']
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('ping method added')
else:
    print('test_bridge not found')