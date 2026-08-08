import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a simple bridge test that doesn't depend on other code
idx = None
for i, line in enumerate(lines):
    if 'console.log(">>> WIDGET_JS_EXTRA SCRIPT STARTED");' in line:
        idx = i
        break

if idx is not None:
    test_code = [
        '    // Simple bridge accessibility test',
        '    try {',
        '      var hasPywebview = typeof window.pywebview !== "undefined";',
        '      var hasApi = hasPywebview && typeof window.pywebview.api !== "undefined";',
        '      var hasDebugLog = hasApi && typeof window.pywebview.api.debug_log === "function";',
        '      console.log(">>> Bridge check: pywebview=" + hasPywebview + ", api=" + hasApi + ", debug_log=" + hasDebugLog);',
        '      if(hasDebugLog){ window.pywebview.api.debug_log("BRIDGE_ACCESSIBLE"); }',
        '    } catch(e) { console.log(">>> BRIDGE CHECK ERROR:", e); }',
    ]
    for j, tc in enumerate(test_code):
        lines.insert(idx + 1 + j, '    ' + tc)
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('Bridge accessibility test added')
else:
    print('Insert point not found')