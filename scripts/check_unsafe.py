import io, re
c = io.open('docs/grafo_widget.html', encoding='utf-8').read()
inline = re.findall(r'<script[^>]*>(.*?)</script>', c, re.S)
g = inline[2]  # script do grafo
print('tam inline grafo:', len(g))
for pat in ['</script>', '<script', '<!--', '-->', '</style>', '</html>', '\\u2028', '\\u2029']:
    i = g.find(pat)
    print(f'{pat!r}: {i}')
# procurar </script case-insensitive
i = re.search(r'</script>', g, re.I)
print('</script> re.I:', i.start() if i else -1)
# procurar < seguido de letra dentro (tag html acidental)
m = re.search(r'<[a-zA-Z][a-zA-Z0-9]*(?:\s[^>]*)?>', g)
print('tag acidental:', g[m.start()-40:m.end()+40] if m else 'nenhuma')
