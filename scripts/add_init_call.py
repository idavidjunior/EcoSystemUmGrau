import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

# Find the end of WIDGET_JS_EXTRA (before </script>""")
idx = content.find('</script>')
if idx >= 0:
    # Find the """ that closes the string
    end_idx = content.find('"""', idx)
    if end_idx >= 0:
        # Insert the initWidgetControls call before </script>
        insert_code = '''
  // Initialize widget controls when pywebview is ready
  if (window.pywebview && window.pywebview.api) {
    initWidgetControls();
  } else {
    window.addEventListener("pywebviewready", initWidgetControls);
  }
'''
        content = content[:idx] + insert_code + content[idx:]
        Path('scripts/widget_grafo.py').write_text(content, encoding='utf-8')
        print('initWidgetControls call added')
    else:
        print('End of string not found')
else:
    print('</script> not found')