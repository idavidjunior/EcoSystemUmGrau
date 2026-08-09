content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\scripts\widget_grafo.py', encoding='utf-8').read()
idx = content.find('WIDGET_CSS =')
if idx >= 0:
    end = content.find('"""', idx + 12)
    end = content.find('"""', end + 3)
    print(content[idx:end+3])