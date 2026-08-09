import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a fetch to a test endpoint to verify JS execution
idx = None
for i, line in enumerate(lines):
    if 'console.log(">>> WIDGET_JS_EXTRA SCRIPT STARTED");' in line:
        idx = i
        break

if idx is not None:
    test_code = [
        '    // Write test file via fetch to /test endpoint',
        '    fetch("/test_js_exec", {method: "POST", body: "OK"}).then(function(){',
        '      console.log(">>> Test endpoint called");',
        '    }).catch(function(e){ console.log(">>> FETCH ERROR:", e); });',
    ]
    for j, tc in enumerate(test_code):
        lines.insert(idx + 1 + j, '    ' + tc)
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('Fetch test added')
else:
    print('Insert point not found')