"""Validate JS in output HTML - simple count."""
c = open('docs/grafo_widget.html', encoding='utf-8').read()
for kw in ['mk-btn-3d', 'mk-btn-flash', 'mk-painel-toggle', 'mk-btn-reset', 
           '_toggle3D', '_toggleFlash', '_aplicarWaveIntensidade', 'flashNo',
           'localStorage.removeItem', 'painelToggle', 'btnReset', 'btn3D', 'btnFlash',
           'grupo3D', 'flashGroup']:
    print(f'  {kw}: {c.count(kw)}')

# Extract the last script block by finding the last </script>
last_script_end = c.rfind('</script>')
last_script_start = c.rfind('<script>', 0, last_script_end)
js = c[last_script_start+8:last_script_end]
print(f'\nLast script block: {len(js)} chars')
for kw in ['mk-btn-3d', 'mk-btn-flash', 'mk-painel-toggle', 'mk-btn-reset']:
    print(f'  {kw}: {js.count(kw)}')
    
# Save this for JS validation
open('docs/_test_widget_js.js', 'w', encoding='utf-8').write(js)
print('JS saved for validation')
