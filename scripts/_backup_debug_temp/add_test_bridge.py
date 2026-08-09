import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a simple Python-side test in the Bridge class
idx = None
for i, line in enumerate(lines):
    if 'def debug_log(self, msg: str) -> None:' in line:
        idx = i
        break

if idx is not None:
    # Add a test method after debug_log
    insert_idx = idx
    # Find the end of debug_log method
    while idx < len(lines) and (lines[idx].startswith('        ') or lines[idx].strip() == '' or 'def debug_log' in lines[idx]):
        idx += 1
    
    test_method = '''
    def test_bridge(self) -> str:
        """Test method to verify bridge is working."""
        print("[BRIDGE TEST] test_bridge called", flush=True)
        return "BRIDGE_OK"
'''
    lines.insert(idx, test_method)
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('test_bridge method added')
else:
    print('debug_log not found')