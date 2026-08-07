"""Open widget, inject JS tests after init, capture results."""
import subprocess, sys, time, json, threading, os
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
HTML_PATH = BASE / 'docs' / 'grafo_widget.html'
LOG_PATH = BASE / 'docs' / 'widget_log.txt'
TEST_RESULT = BASE / 'docs' / 'widget_test_result.json'

# Clear previous results
if LOG_PATH.exists():
    LOG_PATH.unlink()
if TEST_RESULT.exists():
    TEST_RESULT.unlink()

# Force rebuild
print("[1] Rebuilding grafo html...")
subprocess.run([sys.executable, str(BASE/'scripts'/'generate-graph-html.py'), str(BASE/'docs'/'grafo.html')],
               capture_output=True, timeout=30)

import importlib.util
spec = importlib.util.spec_from_file_location('widget_grafo', str(BASE / 'scripts' / 'widget_grafo.py'))
mod = importlib.util.module_from_spec(spec)
sys.modules['widget_grafo'] = mod
spec.loader.exec_module(mod)

print("[2] Building widget view...")
view = mod._build_view()
print(f"    View: {view}")

# Read the generated HTML
content = open(HTML_PATH, 'r', encoding='utf-8').read()
print(f"    Size: {len(content)} bytes")

# Inject a self-test script right before </body>
test_js = """
<script>
(function(){
    var resultados = [];
    function report(nome, ok) {
        resultados.push({nome: nome, ok: ok});
        try { if (window.pywebview && window.pywebview.api) window.pywebview.api.debug_log('TEST:' + nome + '=' + (ok?'OK':'FAIL')); } catch(e){}
    }

    // Wait for everything to load
    var tentativas = 0;
    function verificar() {
        tentativas++;
        if (tentativas > 25) {
            report('timeout', false);
            salvar();
            return;
        }
        if (typeof nodes === 'undefined' || typeof network === 'undefined' || typeof destacar === 'undefined') {
            setTimeout(verificar, 200);
            return;
        }
        
        // Test 1: Filter buttons exist
        var botoesLG = document.querySelectorAll('.lg');
        report('botoes_lg_count', botoesLG.length >= 19);
        
        // Test 2: TEMAS object exists
        report('TEMAS_object', typeof TEMAS !== 'undefined' && TEMAS.neon && TEMAS.glow);
        
        // Test 3: aplicarTema function exists
        report('aplicarTema_fn', typeof aplicarTema === 'function');
        
        // Test pet plasticity {no: temaSel exists
        report('temaSel_exists', document.querySelector('select') !== null && 
               Array.from(document.querySelectorAll('option')).some(o => o.textContent.indexOf('Neon') > -1));
        
        // Test 5: Header functions
        report('header_min_present', document.getElementById('header') !== null);
        
        // Test 6: Click Bug button
        var btnBug = document.querySelector('.lg[data-filter="st"][data-value="resolvido"]') ||
                     document.querySelector('.lg[data-value="bugs"]');
        if (btnBug) {
            btnBug.click();
            setTimeout(function() {
                report('btn_bugs_click', typeof _destacado !== 'undefined' ? _destacado === true : false);
                salvar();
            }, 200);
        } else {
            report('btn_bugs_found', false);
            salvar();
        }
    }
    
    function salvar() {
        // Try to save results
        try {
            var json = JSON.stringify(resultados);
            if (window.pywebview && window.pywebview.api && window.pywebview.api.salvar_resultados) {
                window.pywebview.api.salvar_resultados(json);
            }
        } catch(e) {}
    }
    
    if (document.readyState === 'complete') {
        setTimeout(verificar, 500);
    } else {
        window.addEventListener('load', function(){ setTimeout(verificar, 500); });
    }
})();
</script>
"""
content_with_test = content.replace('</body>', test_js + '\n</body>', 1)
HTML_PATH.write_text(content_with_test, encoding='utf-8')

print("[3] Opening widget with test injection...")

# Add resave method to bridge
class TestBridge(mod.Bridge):
    def __init__(self):
        super().__init__()
        self.results = None
    
    def salvar_resultados(self, json_str):
        self.results = json_str
        TEST_RESULT.write_text(json_str, encoding='utf-8')
        print(f"    [BRIDGE] Results received: {json_str[:200]}")

import webview

geo = mod._carregar_geo()
w = int(geo.get('width', mod.DEFAULT_W))
h = int(geo.get('height', mod.DEFAULT_H))
x = geo.get('x')
y = geo.get('y')

bridge = TestBridge()
win = webview.create_window(
    mod.TITLE,
    url=str(view.resolve()),
    width=w, height=h,
    x=x, y=y,
    resizable=True,
    frameless=True,
    easy_drag=False,
    shadow=False,
    focus=False,
    js_api=bridge,
    background_color=mod.BG,
)
bridge._win = win

# pywebview precisa rodar na thread principal (GUI). Agendamos auto-destruicao
# em thread separada e iniciamos o loop GUI aqui (main thread).
def auto_fechar():
    import time as _t
    _t.sleep(15)
    try:
        webview.destroy_window(win)
    except Exception:
        pass

threading.Thread(target=auto_fechar, daemon=True).start()
webview.start(debug=False)

# Read results
if TEST_RESULT.exists():
    print("[5] Test results:", open(TEST_RESULT, encoding='utf-8').read())
else:
    print("[5] No result file generated")

# Read log
if LOG_PATH.exists():
    print("[6] Log:", open(LOG_PATH, encoding='utf-8').read()[:1000])
else:
    print("[6] No log file")