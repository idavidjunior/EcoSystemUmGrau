content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()

# Count WIDGET_JS_EXTRA injections
count = content.count('mountWidgetUI')
print('mountWidgetUI count:', count)

# Check for duplicate script blocks
count2 = content.count('window.__mkWidgetApi')
print('__mkWidgetApi count:', count2)

# Check if WIDGET_JS_EXTRA appears twice
marker = 'Botão do Olho DENTRO do painel inferior'
count3 = content.count(marker)
print('Eye in panel marker count:', count3)

# Check the end of the tick loop
idx = content.find('network.on(\'tick\'')
if idx >= 0:
    end_idx = content.find('});', idx)
    # Find the next }); after the first one
    end_idx2 = content.find('});', end_idx + 2)
    print('Tick loop length:', end_idx2 - idx)
    # Print last 200 chars of tick loop
    print('End of tick loop:', content[end_idx2-200:end_idx2+10])