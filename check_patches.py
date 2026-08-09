content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()

checks = [
    ('Single style block', content.count('<style>') == 1 and content.count('</style>') == 1),
    ('_getFontLimpo function', '_getFontLimpo' in content),
    ('limpar uses _getFontLimpo', '_getFontLimpo()' in content),
    ('Reduced base oscillation', '0.90 + 0.10 * Math.sin' in content),
    ('Reduced pulso amplitude', '0.03 + 0.06 * atv' in content),
    ('WIDGET_CSS in style', 'mk-controles' in content and content.index('mk-controles') < content.index('</style>') if 'mk-controles' in content and '</style>' in content else False),
    ('No duplicate mk-controles CSS', content.count('#mk-controles { position: fixed; bottom: 12px') == 1),
]

for name, result in checks:
    print(('OK' if result else 'FAIL') + ': ' + name)