content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()

# Check tick loop
idx = content.find('network.on(\'tick\'')
if idx >= 0:
    print('tick loop found at', idx)
    print(content[idx:idx+800])