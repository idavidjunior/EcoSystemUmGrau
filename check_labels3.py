content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()

# Check limpar() function
idx = content.find('function limpar()')
if idx >= 0:
    print('limpar() found at', idx)
    print(content[idx:idx+500])
    print('---')

# Check _fontLimpo
idx2 = content.find('_fontLimpo')
if idx2 >= 0:
    print('_fontLimpo found at', idx2)
    print(content[idx2:idx2+300])
    print('---')

# Check nodes initialization font size
idx3 = content.find('font:{ size:')
if idx3 >= 0:
    print('font init found at', idx3)
    print(content[idx3:idx3+200])
"