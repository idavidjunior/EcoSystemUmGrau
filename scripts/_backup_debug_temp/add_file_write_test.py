import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a file write test in the JavaScript to verify execution
idx = None
for i, line in enumerate(lines):
    if 'console.log(">>> WIDGET_JS_EXTRA SCRIPT STARTED");' in line:
        idx = i
        break

if idx is not None:
    test_code = [
        '    // Write test file to verify JS execution',
        '    try {',
        '      fetch("test_js_execution.txt", {method: "POST", body: "JS_EXECUTED"});',
        '    } catch(e) { console.log(">>> FETCH ERROR:", e); }',
        '    console.log(">>> WIDGET_JS_EXTRA: About to call initWidgetControls");',
    ]
    insert_idx = None
    for i in range(len(lines)):
        if 'console.log(">>> WIDGET_JS_EXTRA SCRIPT STARTED");' in lines[i]:
            insert_idx = i + 1
            break
    
    if insert_idx is not None:
        for j, tc in enumerate(test_code):
            lines.insert(insert_idx + j, '    ' + tc)
        Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
        print('Test file write added')
    else:
        print('Insert point not found')
else:
    print('Start log not found')