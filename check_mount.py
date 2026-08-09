content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()

# Find all mountWidgetUI occurrences
import re
for m in re.finditer(r'mountWidgetUI', content):
    idx = m.start()
    context = content[max(0,idx-50):idx+100]
    print(f'--- Found at {idx} ---')
    print(context)
    print()