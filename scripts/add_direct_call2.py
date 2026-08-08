import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

idx = content.find('</script>')
if idx >= 0:
    end_idx = content.find('"""', idx)
    if end_idx >= 0:
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
        content = content[:idx] + test_code + content[idx:]
        Path('scripts/widget_grafo.py').write_text(content, encoding='utf-8')
        print('Direct call added')
    else:
        print('End not found')
else:
    print('</script> not found')