import re

src = open('docs/grafo.html', encoding='utf-8').read()
print('tooltip estruturado (Categoria:):', 'Categoria:' in src)
print('separador ---:', '\\n---\\n' in src or "'---'" in src or '---' in src)
print('total de "Categoria:" em titulos:', src.count('Categoria:'))
print('descricao de categoria no botao:', 'Categoria: Padroes e convencoes' in src)
print('descricao de cluster no botao:', 'Cluster: Notas do projeto Android' in src)
print('title no botao Home:', 'Home: restaura a visao inicial' in src)
print('title no botao Limpar:', 'Limpar: remove o destaque atual' in src)
print('title no botao MCPs:', 'Dominio: destaca as notas cujas tags citam MCP' in src)
print('title no botao Conhecimento:', 'Dominio: destaca as notas que NAO sao de MCP' in src)
print('vis-tooltip css:', '.vis-tooltip' in src)
print('media query:', '@media (max-width: 720px)' in src)
