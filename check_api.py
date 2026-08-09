content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()

# Find API_INJECT section
idx = content.find('window.__widgetApiPoll')
if idx >= 0:
    print(content[idx:idx+500])