import sys
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts')
import widget_grafo
print('Módulo carregado de:', widget_grafo.__file__)
print('diag_marker no módulo:', 'diag_marker' in open(widget_grafo.__file__, encoding='utf-8').read())

# Verifica a lógica de build passo a passo
src = widget_grafo.OUTPUT_HTML.read_text(encoding='utf-8')
marker = 'const network = new vis.Network(container, { nodes, edges }, options);'
print('Marker count em OUTPUT_HTML:', src.count(marker))

v = widget_grafo._build_view()
content = v.read_text(encoding='utf-8')
print('DEPOIS de _build_view, NET: in:', 'NET: network existe' in content)
print('Tamanho:', len(content))
