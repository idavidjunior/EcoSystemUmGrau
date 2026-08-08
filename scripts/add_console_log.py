import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add console.log test in initWidgetControls
idx = None
for i, line in enumerate(lines):
    if 'function initWidgetControls()' in line:
        idx = i
        break

if idx is not None:
    # Insert console.log after the debug_log call
    insert_idx = idx + 3  # after the debug_log line
    lines.insert(insert_idx, '    console.log("INIT WIDGET CONTROLS RUNNING");')
    lines.insert(insert_idx + 1, '    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){')
    lines.insert(insert_idx + 2, '      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: initWidgetControls CONSOLE LOG TEST");')
    lines.insert(insert_idx + 3, '    }')
    
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('console.log added to initWidgetControls')
else:
    print('initWidgetControls not found')