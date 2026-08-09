import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a simple test that doesn't depend on bridge
idx = None
for i, line in enumerate(lines):
    if 'console.log(">>> WIDGET_JS_EXTRA SCRIPT STARTED");' in line:
        idx = i
        break

if idx is not None:
    test_code = [
        '    // Test: write to localStorage and check',
        '    try {',
        '      localStorage.setItem("widget_js_test", Date.now().toString());',
        '      console.log(">>> localStorage write OK");',
        '    } catch(e) { console.log(">>> localStorage ERROR:", e); }',
        '    // Force initWidgetControls call with error handling',
        '    setTimeout(function(){',
        '      try {',
        '        console.log(">>> Timeout: calling initWidgetControls");',
        '        initWidgetControls();',
        '        console.log(">>> initWidgetControls returned");',
        '      } catch(e) { console.log(">>> initWidgetControls ERROR:", e); }',
        '    }, 100);',
    ]
    for j, tc in enumerate(test_code):
        lines.insert(idx + 1 + j, '    ' + tc)
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('Timeout init call added')
else:
    print('Insert point not found')