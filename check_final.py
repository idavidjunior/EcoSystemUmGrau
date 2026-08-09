content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()

# Check API_INJECT uses 10000ms
idx = content.find('setInterval(function(){ window.__widgetApiPoll.tick()')
if idx >= 0:
    print('POLL interval:', content[idx:idx+80])

# Check _getFontLimpo
idx2 = content.find('_getFontLimpo')
if idx2 >= 0:
    print('_getFontLimpo:', content[idx2:idx2+200])