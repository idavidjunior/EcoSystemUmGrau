content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()
checks = [
    ('OLD CSS should be ABSENT', '#mk-painel-toggle { position: fixed; top: 12px; left: 10px' in content),
    ('topBar left:12px present', 'left:12px' in content),
    ('OLD topBar left:52px should be ABSENT', '#mk-topbar { position: fixed; top: 10px; left: 52px' in content),
    ('eye inside panel JS present', 'panel.appendChild(eye)' in content),
    ('OLD body.appendChild(eye) should be ABSENT', 'document.body.appendChild(eye)' in content),
    ('API_INJECT hash handling present', 'resp.changed' in content),
    ('API_INJECT lastTs string present', "lastTs: ''" in content),
]
for name, found in checks:
    if 'ABSENT' in name:
        status = 'OK' if not found else 'FAIL'
    else:
        status = 'OK' if found else 'FAIL'
    print(status + ': ' + name + ' (found=' + str(found) + ')')