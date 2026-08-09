import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a file write test in initWidgetControls that doesn't depend on bridge
idx = None
for i, line in enumerate(lines):
    if 'function initWidgetControls()' in line:
        idx = i
        break

if idx is not None:
    # Find the first line of the function body
    body_start = idx + 1
    while body_start < len(lines) and '{' not in lines[body_start]:
        body_start += 1
    
    test_code = [
        '      // File write test to verify initWidgetControls execution',
        '      try {',
        '        fetch("/initwidgetcontrols_test", {method: "POST", body: "initWidgetControls_called"});',
        '        console.log(">>> initWidgetControls: fetch test sent");',
        '      } catch(e) { console.log(">>> initWidgetControls fetch ERROR:", e); }',
    ]
    insert_idx = idx + 2  # after function declaration
    for j, tc in enumerate(test_code):
        lines.insert(body_start + 1 + j, tc)
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('initWidgetControls fetch test added')
else:
    print('initWidgetControls not found')