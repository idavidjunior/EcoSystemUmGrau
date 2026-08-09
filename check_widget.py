content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()
checks = [
    ('mk-painel-toggle CSS old', 'position: fixed; top: 12px; left: 10px' in content),
    ('topBar left:12px', 'left:12px' in content),
    ('topBar left:52px old', 'left:52px' in content),
    ('eye inside panel JS', 'panel.appendChild(eye)' in content),
    ('body.appendChild(eye) old', 'document.body.appendChild(eye)' in content),
    ('API_INJECT hash handling', 'resp.changed' in content),
    ('API_INJECT lastTs string', "lastTs: ''" in content),
]
for name, result in checks:
    print(('OK' if result else 'FAIL') + ': ' + name)