import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Find the direct call block and add error handling
idx = None
for i, line in enumerate(lines):
    if 'Calling initWidgetControls directly' in line:
        idx = i
        break

if idx is not None:
    # Replace the block with error-handled version
    old = '''    if(window.pywebview && window.pywebview.api){
      console.log(">>> Calling initWidgetControls directly...");
      initWidgetControls();'''
    new = '''    try {
      if(window.pywebview && window.pywebview.api){
        console.log(">>> Calling initWidgetControls directly...");
        initWidgetControls();
      }
    } catch(e) {
      console.log(">>> ERROR calling initWidgetControls:", e);
    }'''
    
    content = content.replace(old, new)
    Path('scripts/widget_grafo.py').write_text(content, encoding='utf-8')
    print('Error handling added')
else:
    print('Block not found')