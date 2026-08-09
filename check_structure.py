content = open(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\docs\grafo_widget.html', encoding='utf-8').read()

# Verify widget JS structure
checks = [
    ('mountWidgetUI once', content.count('function mountWidgetUI()') == 1),
    ('eye in panel', 'panel.appendChild(eye)' in content),
    ('topbar has T/menu/reset', 'actions.appendChild(ctrl)' in content and 'actions.appendChild(menuBtn)' in content and 'actions.appendChild(resetBtn)' in content),
    ('panel has theme/speed/orbit/eye', 'panel.appendChild(themeWrap)' in content and 'panel.appendChild(speedWrap)' in content and 'panel.appendChild(orbitWrap)' in content and 'panel.appendChild(eye)' in content),
    ('topbar left:12px', 'left:12px' in content),
    ('API_INJECT hash', 'resp.changed' in content),
]

for name, result in checks:
    print(('OK' if result else 'FAIL') + ': ' + name)