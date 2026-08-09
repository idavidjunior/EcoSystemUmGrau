import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add test_bridge call in initWidgetControls
idx = None
for i, line in enumerate(lines):
    if 'function initWidgetControls()' in line:
        idx = i
        break

if idx is not None:
    # Find the aggressive test block end
    insert_idx = None
    for i in range(idx, min(idx + 60, len(lines))):
        if 'WIDGET_JS_EXTRA: versao() returned' in lines[i]:
            insert_idx = i + 1
            break
    
    if insert_idx:
        test_lines = [
            '    // Test test_bridge method',
            '    try {',
            '      console.log(">>> Testing bridge test_bridge()...");',
            '      window.pywebview.api.test_bridge().then(function(v) {',
            '        console.log(">>> test_bridge() returned:", v);',
            '        if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){',
            '          window.pywebview.api.debug_log("WIDGET_JS_EXTRA: test_bridge() returned " + v);',
            '        }',
            '      }).catch(function(e) { console.log(">>> test_bridge() ERROR:", e); });',
            '    } catch(e) { console.log(">>> SYNC ERROR test_bridge:", e); }',
        ]
        for j, tl in enumerate(test_lines):
            lines.insert(insert_idx + j, '    ' + tl)
        Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
        print('test_bridge call added')
    else:
        print('Insert point not found')
else:
    print('initWidgetControls not found')