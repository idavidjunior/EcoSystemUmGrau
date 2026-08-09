import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a simple bridge call that writes a file
idx = None
for i, line in enumerate(lines):
    if 'console.log(">>> WIDGET_JS_EXTRA: About to call initWidgetControls");' in line:
        idx = i
        break

if idx is not None:
    test_code = [
        '    // Test bridge with file write',
        '    if(window.pywebview && window.pywebview.api){',
        '      console.log(">>> Testing bridge write_file...");',
        '      window.pywebview.api.debug_log("JS_BRIDGE_TEST: Widget JS executed");',
        '    }',
    ]
    for j, tc in enumerate(test_code):
        lines.insert(idx + 1 + j, '    ' + tc)
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('Bridge test added')
else:
    print('Insert point not found')