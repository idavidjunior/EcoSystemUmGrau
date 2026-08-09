import io, re
c = io.open('docs/grafo_widget.html', encoding='utf-8').read()
inline = re.findall(r'<script[^>]*>(.*?)</script>', c, re.S)
g = inline[2]
# procurar APIs possivelmente problematicas
for api in ['localStorage', 'sessionStorage', 'fetch(', 'XMLHttpRequest', 'requestAnimationFrame', 'setInterval', 'console.', 'navigator.', 'devicePixelRatio', 'matchMedia']:
    i = g.find(api)
    if i >= 0:
        print(f'{api}: @{i}')
# contexto do inicio do script (primeiros 3000 chars)
print('===== INICIO DO SCRIPT =====')
print(g[:1500])
