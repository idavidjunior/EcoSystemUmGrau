from pathlib import Path
import re

content = Path(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html').read_text(encoding='utf-8')

# Check for data-filter on buttons
buttons = re.findall(r'<button class="lg".*?>', content)
print('Total .lg buttons found:', len(buttons))
for b in buttons[:5]:
    print(' ', b[:150])

print()
print('destacar function exists:', 'function destacar(' in content)
print('limpar function exists:', 'function limpar()' in content)
print('Binding chain exists:', 'document.querySelectorAll' in content and '.lg' in content)

# Check script blocks
script_blocks = content.count('</script>')
print()
print('Script close tags:', script_blocks)

# Check if network.on exists
idx = content.find('network.on(')
print('network.on() found at byte:', idx if idx >= 0 else 'NOT FOUND')

# Check for CSS hiding the legend
idx_legend = content.find('id="legend"')
idx_header = content.find('id="header"')
print('legend id at byte:', idx_legend)
print('header id at byte:', idx_header)