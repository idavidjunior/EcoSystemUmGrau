import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add more aggressive test in initWidgetControls
idx = None
for i, line in enumerate(lines):
    if 'function initWidgetControls()' in line:
        idx = i
        break

if idx is not None:
    # Add multiple test logs
    test_lines = [
        '    console.log(">>> initWidgetControls START");',
        '    console.log(">>> pywebview:", window.pywebview);',
        '    console.log(">>> pywebview.api:", window.pywebview && window.pywebview.api);',
        '    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){',
        '      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: initWidgetControls BRIDGE TEST");',
        '    }',
        '    // Direct bridge test',
        '    if(window.pywebview && window.pywebview.api){',
        '      window.pywebview.api.versao().then(function(v){ console.log("versao:", v); });',
        '    }',
    ]
    
    insert_idx = idx + 3
    for j, tl in enumerate(test_lines):
        lines.insert(idx + 3 + j, '    ' + tl)
    
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('Aggressive test added')
else:
    print('initWidgetControls not found')