content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()

# Check label logic in tick loop
idx = content.find('_ajustarFontes')
if idx >= 0:
    print('_ajustarFontes found at', idx)
    print(content[idx:idx+500])
    print('---')

# Check setLabelVisibility in widget JS
idx2 = content.find('function setLabelVisibility')
if idx2 >= 0:
    print('setLabelVisibility found at', idx2)
    print(content[idx2:idx2+500])
"