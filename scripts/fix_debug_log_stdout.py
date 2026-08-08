import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Modify debug_log to always print to stdout
idx = None
for i, line in enumerate(lines):
    if 'def debug_log(self, msg: str) -> None:' in line:
        idx = i
        break

if idx is not None:
    # Find the end of the debug_log method
    end_idx = idx + 1
    while end_idx < len(lines) and (lines[end_idx].startswith('        ') or lines[end_idx].strip() == ''):
        end_idx += 1
    
    # Replace the method body
    new_method = [
        '    def debug_log(self, msg: str) -> None:',
        '        print("[DEBUG_BRIDGE] " + msg, flush=True)',
        '        try:',
        '            with open(BASE / "docs" / "widget_log.txt", "a", encoding="utf-8") as f:',
        '                f.write(f"{time.time():.0f} | {msg}\\n")',
        '        except Exception as e:',
        '            print("[DEBUG_BRIDGE ERROR] " + str(e), flush=True)',
        ''
    ]
    
    # Replace the method
    lines[idx:end_idx] = new_method
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('debug_log updated to always print to stdout')
else:
    print('debug_log not found')