import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Insert closing brace for initWidgetControls before </script>
# Line 800 is </script> (index 799)
lines.insert(799, '  }')

content = '\n'.join(lines)
Path('scripts/widget_grafo.py').write_text(content, encoding='utf-8')
print('Closing brace added for initWidgetControls')