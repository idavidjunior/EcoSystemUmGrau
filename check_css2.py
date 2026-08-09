content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()

# Find all #mk-controles CSS blocks
import re
for m in re.finditer(r'#mk-controles\s*\{', content):
    idx = m.start()
    print(f'--- #mk-controles at {idx} ---')
    print(content[idx:idx+300])
    print()