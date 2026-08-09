import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add echo test in JavaScript
idx = None
for i, line in enumerate(lines):
    if 'console.log(">>> WIDGET_JS_EXTRA SCRIPT STARTED");' in line:
        idx = i
        break

if idx is not None:
    test_code = [
        '    // Test echo method',
        '    if(window.pywebview && window.pywebview.api && window.pywebview.api.echo){',
        '      console.log(">>> Testing echo...");',
        '      window.pywebview.api.echo("test123").then(function(v){',
        '        console.log(">>> echo() returned:", v);',
        '        if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){',
        '          window.pywebview.api.debug_log("ECHO_TEST: " + v);',
        '        }',
        '      }).catch(function(e){ console.log(">>> ECHO ERROR:", e); });',
        '    }',
    ]
    for j, tc in enumerate(test_code):
        lines.insert(idx + 1 + j, '    ' + tc)
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('Echo test added')
else:
    print('Insert point not found')