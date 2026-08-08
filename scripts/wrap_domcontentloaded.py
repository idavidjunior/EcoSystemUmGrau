import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

# Wrap WIDGET_JS_EXTRA em DOMContentLoaded
old = '''WIDGET_JS_EXTRA = """
<script>
    // DEBUG LOG
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: START");
    }

  (function(){'''

new = '''WIDGET_JS_EXTRA = """
<script>
    // DEBUG LOG
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: START");
    }

  function initWidgetControls() {
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: initWidgetControls called");
    }

  (function(){'''

if old in content:
    content = content.replace(old, new)
    
    old2 = '''    document.body.appendChild(painel)

    // ---- Bo'''
    new2 = '''    document.body.appendChild(painel)
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: painel appended");
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initWidgetControls);
  } else {
    initWidgetControls();
  }

  // ---- Bo'''
    content = content.replace(old2, new2)
    
    Path('scripts/widget_grafo.py').write_text(content, encoding='utf-8')
    print('DOMContentLoaded wrapper adicionado')
else:
    print('Padrao nao encontrado')