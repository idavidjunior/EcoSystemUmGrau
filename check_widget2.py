content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()
# Search for the old CSS rule
old_css = '#mk-painel-toggle { position: fixed; top: 12px; left: 10px'
if old_css in content:
    idx = content.index(old_css)
    print('OLD CSS FOUND at', idx)
    print(content[idx:idx+500])
else:
    print('OLD CSS NOT FOUND')

# Also check for body.appendChild(eye)
old_js = 'document.body.appendChild(eye)'
if old_js in content:
    idx = content.index(old_js)
    print('OLD JS FOUND at', idx)
    print(content[idx:idx+200])
else:
    print('OLD JS NOT FOUND')