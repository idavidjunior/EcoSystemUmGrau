import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a simple console.log at the very start of WIDGET_JS_EXTRA to verify JS execution
idx = None
for i, line in enumerate(lines):
    if 'WIDGET_JS_EXTRA = """' in line:
        idx = i
        break

if idx is not None:
    # Find the first <script> tag after WIDGET_JS_EXTRA
    script_idx = None
    for i in range(idx, min(idx + 10, len(lines))):
        if '<script>' in lines[i]:
            script_idx = i
            break
    
    if script_idx is not None:
        # Insert console.log right after <script>
        lines.insert(script_idx + 1, '    console.log(">>> WIDGET_JS_EXTRA LOADED AND EXECUTING");')
        Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
        print('console.log added at start of WIDGET_JS_EXTRA')
    else:
        print('<script> not found')
else:
    print('WIDGET_JS_EXTRA not found')