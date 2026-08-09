import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

# Fix the painel style to include top: 70px
old = """painel.style.cssText =
      'position:fixed;right:10px;z-index:9999;display:flex;' +
      'flex-direction:column;gap:8px;padding:8px 10px;border-radius:8px;' +
      'background:rgba(30,30,46,0.88);border:1px solid ' + cores.borda + ';' +
      'box-shadow:0 2px 10px rgba(0,0,0,0.5);';"""

new = """painel.style.cssText =
      'position:fixed;right:10px;top:70px;z-index:9999;display:flex;' +
      'flex-direction:column;gap:8px;padding:8px 10px;border-radius:8px;' +
      'background:rgba(30,30,46,0.88);border:1px solid ' + cores.borda + ';' +
      'box-shadow:0 2px 10px rgba(0,0,0,0.5);';"""

if old in content:
    content = content.replace(old, new)
    Path('scripts/widget_grafo.py').write_text(content, encoding='utf-8')
    print('Painel style fixed - added top: 70px')
else:
    print('Pattern not found')