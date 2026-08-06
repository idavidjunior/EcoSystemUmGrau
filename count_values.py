import re, pathlib, sys
txt = pathlib.Path('docs/grafo_widget.html').read_text(encoding='utf-8')
vals = re.findall(r'data-value="([^"]+)"', txt)
print('total:', len(vals))
print('unique:', len(set(vals)))
print('unique list:', sorted(set(vals)))