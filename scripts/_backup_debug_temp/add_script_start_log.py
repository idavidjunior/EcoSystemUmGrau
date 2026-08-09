import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Find the WIDGET_JS_EXTRA script start and add immediate console.log
idx = None
for i, line in enumerate(lines):
    if '<script>' in line and 'WIDGET_JS_EXTRA' in lines[i-1]:
        idx = i
        break

if idx is not None:
    # Insert console.log right after <script>
    lines.insert(idx + 1, '    console.log(">>> WIDGET_JS_EXTRA SCRIPT STARTED");')
    lines.insert(idx + 2, '    console.log(">>> Document readyState:", document.readyState);')
    lines.insert(idx + 3, '    console.log(">>> pywebview:", window.pywebview);')
    lines.insert(idx + 4, '    console.log(">>> pywebview.api:", window.pywebview && window.pywebview.api);')
    
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('Immediate console.log added at script start')
else:
    print('Script tag not found')