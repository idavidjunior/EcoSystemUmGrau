import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add error handling to initWidgetControls
idx = None
for i, line in enumerate(lines):
    if 'function initWidgetControls()' in line:
        idx = i
        break

if idx is not None:
    # Find the start of the function body
    body_start = idx + 1
    while body_start < len(lines) and '{' not in lines[body_start]:
        body_start += 1
    
    if body_start < len(lines):
        # Insert try-catch wrapper
        test_code = [
            '    try {',
        ]
        # Find the end of the function
        brace_count = 0
        end_idx = body_start
        while end_idx < len(lines):
            for ch in lines[end_idx]:
                if ch == '{': brace_count += 1
                elif ch == '}': brace_count -= 1
            if brace_count == 0:
                break
            end_idx += 1
        
        # Wrap the function body in try-catch
        lines.insert(body_start + 1, '      try {')
        lines.insert(end_idx + 2, '      } catch(e) { console.log(">>> initWidgetControls ERROR:", e); }')
        
        Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
        print('Error handling added to initWidgetControls')
    else:
        print('Function body not found')
else:
    print('initWidgetControls not found')