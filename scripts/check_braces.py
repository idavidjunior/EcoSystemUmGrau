import os
import re
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
html = Path('docs/grafo_widget.html').read_text(encoding='utf-8')

scripts = re.findall(r'<script>\s*(.*?)\s*</script>', html, re.DOTALL)
for i, js in enumerate(scripts):
    if 'initWidgetControls' in js:
        print(f'Script {i} ({len(js)} chars)')
        lines = js.split('\n')
        # Mostra estrutura
        brace_count = 0
        for j, line in enumerate(lines):
            for ch in line:
                if ch == '{': brace_count += 1
                elif ch == '}': brace_count -= 1
            if brace_count != 0 and j > len(lines) - 20:
                print(f'  Line {j} (braces={brace_count}): {line.strip()[:80]}')
        
        print(f'Final brace count: {brace_count}')
        break