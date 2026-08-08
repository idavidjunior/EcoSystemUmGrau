import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Change initWidgetControls to wait for pywebviewready
idx = None
for i, line in enumerate(lines):
    if 'if (document.readyState === "loading")' in line:
        idx = i
        break

if idx is not None:
    # Replace the DOMContentLoaded logic with pywebviewready
    old_block = '''  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initWidgetControls);
  } else {
    initWidgetControls();
  }'''
    
    new_block = '''  // Wait for pywebviewready to ensure bridge is ready
  if (window.pywebview && window.pywebview.api) {
    initWidgetControls();
  } else {
    window.addEventListener("pywebviewready", initWidgetControls);
  }'''
    
    content = content.replace(old_block, new_block)
    Path('scripts/widget_grafo.py').write_text(content, encoding='utf-8')
    print('Changed to pywebviewready')
else:
    print('Block not found')