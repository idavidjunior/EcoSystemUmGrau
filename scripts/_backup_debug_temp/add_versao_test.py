import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Find the initWidgetControls function and add a synchronous bridge test
idx = None
for i, line in enumerate(lines):
    if 'function initWidgetControls()' in line:
        idx = i
        break

if idx is not None:
    # Find the end of the debug_log test block
    insert_idx = idx + 10  # after the aggressive test block
    test_lines = [
        '    // Direct synchronous bridge test',
        '    try {',
        '      console.log(">>> Testing bridge versao()...");',
        '      window.pywebview.api.versao().then(function(v) {',
        '        console.log(">>> versao() returned:", v);',
        '        if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){',
        '          window.pywebview.api.debug_log("WIDGET_JS_EXTRA: versao() returned " + v);',
        '        }',
        '      }).catch(function(e) { console.log(">>> versao() ERROR:", e); });',
        '    } catch(e) { console.log(">>> SYNC ERROR:", e); }',
    ]
    
    # Find a good place to insert - after the aggressive test block
    insert_idx = None
    for i in range(idx, min(idx + 50, len(lines))):
        if 'WIDGET_JS_EXTRA: initWidgetControls CONSOLE LOG TEST' in lines[i]:
            insert_idx = i + 1
            break
    
    if insert_idx:
        for j, tl in enumerate(test_lines):
            lines.insert(insert_idx + j, '    ' + tl)
        Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
        print('Bridge test added')
    else:
        print('Insert point not found')
else:
    print('initWidgetControls not found')