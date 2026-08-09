import io, re

def script_srcs(path):
    c = io.open(path, encoding='utf-8').read()
    srcs = re.findall(r'<script[^>]*src=["\']([^"\']+)["\']', c)
    inline = re.findall(r'<script[^>]*>(.*?)</script>', c, re.S)
    return c, srcs, inline

orig_c, orig_srcs, orig_inline = script_srcs('docs/grafo.html')
w_c, w_srcs, w_inline = script_srcs('docs/grafo_widget.html')

print('=== grafo.html ===')
print('srcs:', orig_srcs)
print('inline count:', len(orig_inline))
print('inline lens:', [len(x) for x in orig_inline])

print()
print('=== grafo_widget.html ===')
print('srcs:', w_srcs)
print('inline count:', len(w_inline))
print('inline lens:', [len(x) for x in w_inline])

print()
print('=== nos nodes_js? ===')
for label, inline in [('orig', orig_inline), ('widget', w_inline)]:
    found = False
    for i, s in enumerate(inline):
        if 'new vis.DataSet' in s:
            found = True
            print(f'{label}: vis.DataSet no inline {i}')
    if not found:
        print(f'{label}: vis.DataSet NAO encontrado em nenhum inline!')

# checa se algum inline contem '</script>' ou '<' inesperado que pode quebrar parse
print()
print('=== procurando </script> dentro de inline (quebra de parse) ===')
for label, inline in [('orig', orig_inline), ('widget', w_inline)]:
    for i, s in enumerate(inline):
        if '</script>' in s:
            print(f'{label}: inline {i} CONTEM </script> interno (FALSO)!')
