"""Check if buttons are in the rebuilt output."""
c = open('docs/grafo_widget.html', encoding='utf-8').read()
for kw in ['mk-btn-3d', 'mk-btn-flash', 'mk-painel-toggle', 'mk-btn-reset', 'painelToggle', 'btn3D']:
    print(f'{kw}: {c.count(kw)}')
