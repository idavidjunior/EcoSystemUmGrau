import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')
lines = content.split('\n')

# Add a synchronous call to test_bridge at the end of WIDGET_JS_EXTRA to verify bridge works
idx = None
for i, line in enumerate(lines):
    if '</script>' in line and i > 0 and 'WIDGET_JS_EXTRA' in lines[i-1]:
        idx = i
        break

if idx is not None:
    test_code = '''
    // Sync bridge test
    if(window.pywebview && window.pywebview.api){
      console.log(">>> Testing bridge test_bridge...");
      window.pywebview.api.test_bridge().then(function(v){
        console.log(">>> test_bridge() returned:", v);
      }).catch(function(e){ console.log(">>> test_bridge ERROR:", e); });
    }
    // Call initWidgetControls now if bridge is ready
    if(window.pywebview && window.pywebview.api){
      console.log(">>> Calling initWidgetControls directly...");
      initWidgetControls();
    }
'''
    lines.insert(idx, test_code)
    Path('scripts/widget_grafo.py').write_text('\n'.join(lines), encoding='utf-8')
    print('Direct initWidgetControls call added')
else:
    print('Script end not found')