#!/usr/bin/env python3
# Script para modificar o widget_controle_jarvis.py

import re

with open('C:\\Users\\David Jr\\Documents\\Default Project\\EcoSystemUmGrau\\scripts\\widget_controle_jarvis.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Adicionar ATALHO_WINDOWS após GEO_FILE
geo_file_pattern = r'GEO_FILE = ROOT / "runtime" / "widget_controle_geometria\.json"'
geo_replacement = '''GEO_FILE = ROOT / "runtime" / "widget_controle_geometria.json"

# --- Atalho de inicialização automática ---
ATALHO_WINDOWS = ROOT / "runtime" / "jarvis_atalho.lnk"'''

content = re.sub(geo_file_pattern, geo_replacement, content, count=1)

# 2. Adicionar _minimizar function após _guardar_geo
minimize_func = '''
def _minimizar(win):
    try:
        win.evaluate_js("window.pywebview.minimize()")
    except Exception:
        pass'''

# Inserir após _guardar_geo
pattern_guardar = r'def _guardar_geo\(win\):.*?except Exception:.*?pass'
content = re.sub(pattern_guardar, minimize_func + '\n\n' + r'''def _guardar_geo(win):
    try:
        win.evaluate_js("""
          (function(){
            var x=window.screenX||0,y=window.screenY||0,w=window.innerWidth||0,h=window.innerHeight||0;
            window.pywebview=null;  /* noop de compat */
            localStorage.setItem('jarvis_geo', JSON.stringify({x:x,y:y,width:w,height:h});
          })();
        """)
    except Exception:
        pass''', content, flags=re.DOTALL)

# 3. Modificar applyState no HTML para mudar "Narrador Ativo" para "JARVIS ativo"
# e adicionar detalhes durante fala
old_applyState = """    var info=document.getElementById('info');
    if(s.tts_ativo){ info.textContent='🔊 FALANDO'; info.className='info falando'; }
    else if(s.narrador){ info.textContent='narrador ativo | online'; info.className='info'; }
    else { info.textContent='online (voz off)'; info.className='info'; }"""

new_applyState = """    var info=document.getElementById('info');
    if(s.tts_ativo){ info.textContent='🔊 FALANDO'; info.className='info falando';
      info.title='FALANDO: ' + (s.texto||''); }
    else if(s.ativo){ info.textContent='JARVIS ativo | online'; info.className='info';
      info.title='Ativo'; }
    else { info.textContent='online (voz off)'; info.className='info';
      info.title='Desativado'; }"""

content = content.replace(old_applyState, new_applyState)

# 4. Adicionar botão de minimizar no HTML toolbar
old_toolbar = '''<div class="topbar">
  <div style="display:flex;align-items:center;gap:4px;">
    <div class="drag" id="drag"></div><span>🎙️ Jarvis</span>
  </div>
  <div class="close" id="closeBtn">✕</div>
</div>'''

new_toolbar = '''<div class="topbar">
  <div style="display:flex;align-items:center;gap:4px;">
    <div class="drag" id="drag"></div><span>🎙️ Jarvis</span>
    <div class="minimize" id="minimizeBtn">_</div>
  </div>
  <div class="close" id="closeBtn">✕</div>
</div>'''

content = content.replace(old_toolbar, new_toolbar)

# 5. Adicionar handler de minimizar no JS
old_close = '''  document.getElementById('closeBtn').addEventListener('click', function(){ clickSet('close'); });'''

new_close = '''  document.getElementById('closeBtn').addEventListener('click', function(){ clickSet('close'); });
  document.getElementById('minimizeBtn').addEventListener('click', function(){
    window.pywebview.minimize();
  });'''

content = content.replace(old_close, new_close)

with open('C:\\Users\\David Jr\\Documents\\Default Project\\EcoSystemUmGrau\\scripts\\widget_controle_jarvis.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Modificações aplicadas com sucesso!')