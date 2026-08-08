import os
from pathlib import Path

os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
content = Path('scripts/widget_grafo.py').read_text(encoding='utf-8')

# Injeta debug no início do script WIDGET_JS_EXTRA
idx = content.find('WIDGET_JS_EXTRA')
if idx >= 0:
    script_start = content.find('<script>', idx)
    if script_start >= 0:
        inject_point = script_start + 8
        debug_code = '\n    // DEBUG LOG\n    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){\n      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: START");\n    }\n'
        content = content[:inject_point] + debug_code + content[inject_point:]
        
        # Debug antes do appendChild
        append_idx = content.find('document.body.appendChild(painel);')
        if append_idx >= 0:
            debug2 = '\n    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){\n      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: appending painel");\n    }\n'
            content = content[:append_idx] + debug2 + content[append_idx:]
            
            Path('scripts/widget_grafo.py').write_text(content, encoding='utf-8')
            print('Debug logs injetados com sucesso')
        else:
            print('appendChild NAO encontrado')
    else:
        print('script tag NAO encontrado')
else:
    print('WIDGET_JS_EXTRA NAO encontrado')