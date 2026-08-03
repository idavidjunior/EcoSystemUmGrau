import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
from widget_grafo import _build_view

v = _build_view()
content = v.read_text(encoding='utf-8')

idx = content.find('const network = new vis.Network')
if idx >= 0:
    script_start = content.rfind('<script>', 0, idx)
    script_end = content.find('</script>', idx)
    block = content[script_start:script_end+9]
    with open('C:\\Users\\David Jr\\Documents\\Default Project\\EcoSystemUmGrau\\network_block.txt', 'w', encoding='utf-8') as f:
        f.write(block)
    print('OK - block written to file')