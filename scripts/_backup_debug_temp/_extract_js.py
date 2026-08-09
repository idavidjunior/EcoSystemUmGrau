"""Extract and validate JS from widget HTML using node."""
import re, subprocess

c = open('docs/grafo_widget.html', encoding='utf-8').read()

# Find the last <script> block (WIDGET_JS_EXTRA)
last_script_start = c.rfind('<script>')
last_script_end = c.rfind('</script>')
js = c[last_script_start+8:last_script_end]
open('docs/_test_final.js', 'w', encoding='utf-8').write(js)
print(f"JS extracted: {len(js)} chars")

# Check for key content
for kw in ['mk-btn-3d', 'mk-btn-flash', 'mk-painel-toggle', 'mk-btn-reset', '_toggle3D', 'flashNo']:
    print(f"  {kw}: {js.count(kw)}")
