import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a call counter to Bridge class
idx = None
for i, line in enumerate(lines):
    if 'class Bridge:' in line:
        idx = i
        break

if idx is not None:
    # Find the __init__ method
    init_idx = None
    for i in range(idx, min(idx + 20, len(lines))):
        if 'def __init__' in lines[i]:
            init_idx = i
            break
    
    if init_idx is not None:
        # Find the end of __init__
        end_idx = init_idx + 1
        while end_idx < len(lines) and (lines[end_idx].startswith('        ') or lines[end_idx].strip() == ''):
            end_idx += 1
        
        # Insert counter initialization
        lines.insert(end_idx, '        self._call_count = 0')
        
        # Add a get_call_count method
        method_code = '''
    def get_call_count(self) -> int:
        """Return the number of bridge calls made."""
        return self._call_count
'''
        lines.insert(end_idx + 1, '    def increment_call_count(self) -> None:')
        lines.insert(end_idx + 2, '        self._call_count += 1')
        lines.insert(end_idx + 3, '        print("[BRIDGE] Call count: " + str(self._call_count), flush=True)')
        
        for j, line in enumerate(['', '    def get_call_count(self) -> int:', '        return self._call_count', '']):
            lines.insert(end_idx + 4 + j, line)
        
        Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
        print('Call counter added to Bridge')
    else:
        print('__init__ not found')
else:
    print('Bridge class not found')