import io, re, json
c = io.open('docs/grafo_widget.html', encoding='utf-8').read()
# contar nos no DataSet
m = re.search(r'const nodes = new vis\.DataSet\(\[(.*?)\]\);\s*\n\s*const edges', c, re.S)
if m:
    arr = m.group(1)
    n_nodes = arr.count('"id"')
    print('nos no grafo_widget.html:', n_nodes)
else:
    print('nodes DataSet NAO encontrado')
m2 = re.search(r'const edges = new vis\.DataSet\(\[(.*?)\]\)', c, re.S)
if m2:
    print('arestas:', m2.group(1).count('"from"'))
print('script vis presente:', 'vis-network.min.js' in c)
print('tam bytes:', len(c.encode('utf-8')))