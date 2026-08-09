content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()
# Check for the full mountWidgetUI function
idx = content.find('function mountWidgetUI()')
if idx >= 0:
    end = content.find('})();', idx)
    if end < 0:
        end = idx + 5000
    with open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\debug_output.txt', 'w', encoding='utf-8') as f:
        f.write(content[idx:end+50])