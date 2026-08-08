"""Widget desktop do Cerebro Vivo - grafo do conhecimento em tempo real.

Janela flutuante (pywebview) com o grafo interativo. Sem bordas visuais, mas
MOVIDA livremente pelo desktop arrastando a barra superior (moldura discreta)
e REDIMENSIONADA pela alca do canto inferior direito (aparece junto aos
controles). Os controles ficam ocultos por padrao; ao clicar com o botao
DIREITO do mouse a barra de controles (header/legenda) aparece/reaparece.

A posicao e o tamanho sao persistidos em JSON (docs/grafo_widget_geometria.json)
e restaurados a cada execucao, inclusive apos reiniciar o computador.

Observa continuamente as fontes do conhecimento (knowledge_graph.json +
conhecimento/*). Quando algo muda, re-gera docs/grafo.html e recarrega.

Dependencias: pip install pywebview

Uso:
  python scripts/widget_grafo.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN_SCRIPT = BASE / 'scripts' / 'generate-graph-html.py'
OUTPUT_HTML = BASE / 'docs' / 'grafo.html'
KNOWLEDGE_GRAPH = BASE / 'ler-runtime' / 'knowledge' / 'knowledge_graph.json'
CONHECIMENTO_DIR = BASE / 'conhecimento'
VIEW_COPY = BASE / 'docs' / 'grafo_widget.html'
GEO_FILE = BASE / 'docs' / 'grafo_widget_geometria.json'
ORB_FILE = BASE / 'docs' / 'grafo_widget_orbGrafo.json'

POLL_MS = 10000
TITLE = 'Cerebro Vivo'
BG = '#1e1e2e'
DEFAULT_W, DEFAULT_H = 1280, 800
MIN_W, MIN_H = 400, 300

WIDGET_CSS = """
  #header { transition: opacity .25s ease; position: relative; z-index: 10000; }
  body.desktop #header { opacity: 1; }
  #painel { display: none !important; }
  #wrap { display: flex; height: 100vh; }
  #net { flex: 1; height: 100vh !important; width: 100% !important; }
  body { margin: 0; width: 100vw; height: 100vh; overflow: hidden; background: #1e1e2e; }
  #mk-drag { position: fixed; left: 0; top: 0; width: 100%; height: 16px;
             cursor: grab; z-index: 10001; background: rgba(203,166,247,0.08);
             pointer-events: auto; }
  #mk-drag:active { cursor: grabbing; background: rgba(203,166,247,0.15); }
  #mk-drag:hover { background: rgba(203,166,247,0.12); }
  #mk-resize { position: fixed; right: 0; bottom: 0; width: 18px; height: 18px;
               cursor: nwse-resize; display: block; z-index: 10001;
               background: rgba(203,166,247,0.15);
               border-top: 2px solid rgba(203,166,247,0.4);
               border-left: 2px solid rgba(203,166,247,0.4);
               pointer-events: auto; }
  #mk-resize:hover { background: rgba(203,166,247,0.35); }
  #mk-topbar { position: fixed; bottom: 12px; left: 50%; transform: translateX(-50%); z-index: 99998; display: flex; justify-content: center; align-items: center; flex-wrap: wrap; gap: 8px; pointer-events: auto; width: min(780px, calc(100vw - 96px)); padding: 8px 12px; border-radius: 12px; background: rgba(30,30,46,0.9); border: 1px solid #45475a; box-shadow: 0 6px 18px rgba(0,0,0,0.38); }
  #mk-topbar > * { flex: 0 0 auto; }
  #mk-topbar select,
  #mk-topbar input,
  #mk-topbar span,
  #mk-topbar div { box-sizing: border-box; }
  #mk-painel-toggle { position: fixed; bottom: 18px; left: 18px; top: auto; z-index: 99999; width: 30px; height: 30px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; background: #313244; border: 1px solid #45475a; color: #cba6f7; }
  /* Painel de controles: organizado em faixa inferior e visivel por padrao */
  #mk-controles { position: fixed; bottom: 12px; left: 50%; transform: translateX(-50%); z-index: 9999; display: flex !important; flex-direction: row; align-items: center; justify-content: center; flex-wrap: wrap; gap: 10px; padding: 8px 12px; border-radius: 12px; background: rgba(30,30,46,0.9); border: 1px solid #45475a; box-shadow: 0 6px 18px rgba(0,0,0,0.38); max-width: min(780px, calc(100vw - 96px)); width: min(780px, calc(100vw - 96px)); }
  #mk-controles > div,
  #mk-controles > select,
  #mk-controles > input { max-width: 100%; }
  @media (max-width: 760px) {
    #mk-topbar,
    #mk-controles { width: min(560px, calc(100vw - 74px)); max-width: calc(100vw - 74px); }
    #mk-painel-toggle { left: 12px; bottom: 12px; width: 28px; height: 28px; }
  }
  @media (max-width: 500px) {
    #mk-topbar,
    #mk-controles { width: min(310px, calc(100vw - 62px)); max-width: calc(100vw - 62px); gap: 6px; }
    #mk-controles { padding: 7px 8px; }
    #mk-controles input[type="range"] { width: 90px !important; }
  }
  """

API_INJECT = """
<script>
(function(){
  window.__widgetApiPoll = window.__widgetApiPoll || {
    lastTs: 0,
    tick: function(){
      try {
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.perguntar === 'function') {
          window.pywebview.api.perguntar(this.lastTs).then(function(resp){
            if (resp && resp.ts) this.lastTs = Number(resp.ts) || this.lastTs;
          }.bind(this)).catch(function() {});
        }
      } catch (e) {}
    }
  };
  setInterval(function(){ window.__widgetApiPoll.tick(); }, 1000);
})();
</script>
"""

RESIZE_JS = """
<script>
(function(){
  function ensureHandle(){
    var handle = document.getElementById('mk-resize');
    if (!handle) {
      handle = document.createElement('div');
      handle.id = 'mk-resize';
      document.body.appendChild(handle);
    }
    return handle;
  }
  function updateHandle(){
    var handle = ensureHandle();
    handle.style.position = 'fixed';
    handle.style.right = '0px';
    handle.style.bottom = '0px';
    handle.style.width = '18px';
    handle.style.height = '18px';
    handle.style.display = 'block';
    handle.style.zIndex = '10001';
    handle.style.cursor = 'nwse-resize';
    handle.style.background = 'rgba(203,166,247,0.15)';
    handle.style.borderTop = '2px solid rgba(203,166,247,0.4)';
    handle.style.borderLeft = '2px solid rgba(203,166,247,0.4)';
  }
  updateHandle();
  window.addEventListener('resize', updateHandle);
})();
</script>
"""

WIDGET_JS = """
<script>
  (function(){
    function initWidgetControls() {
      if (document.getElementById('mk-controles')) return;
      if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.test_bridge === 'function') {
        try {
          window.pywebview.api.test_bridge().catch(function() {});
        } catch (e) {}
      }
    }

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', initWidgetControls, { once: true });
    } else {
      initWidgetControls();
    }

    window.addEventListener('pywebviewready', initWidgetControls, { once: true });
  })();
</script>
"""


class Bridge:
    def __init__(self):
        self._win = None

    def versao(self):
        return 'Cerebro Vivo widget'

    def echo(self, value):
        return value

    def ping(self):
        return 'pong'

    def test_bridge(self):
        return 'OK'

    def debug_log(self, msg):
        print(f'[widget-bridge] {msg}', flush=True)
        return True

    def perguntar(self, last_ts=0):
        return {'ts': int(time.time() * 1000), 'last_ts': int(last_ts or 0)}

    def guardar_geo(self, x=None, y=None, width=None, height=None):
        data = _carregar_geo()
        if x is not None: data['x'] = int(x)
        if y is not None: data['y'] = int(y)
        if width is not None: data['width'] = int(width)
        if height is not None: data['height'] = int(height)
        GEO_FILE.parent.mkdir(parents=True, exist_ok=True)
        GEO_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        return data

    def guardar_orbGrafo(self, valor):
        try:
            ORB_FILE.parent.mkdir(parents=True, exist_ok=True)
            ORB_FILE.write_text(str(valor), encoding='utf-8')
        except Exception:
            pass
        return valor

    def redimensionar(self, width, height):
        if self._win is not None and hasattr(self._win, 'resize'):
            try:
                self._win.resize(int(width), int(height))
            except Exception:
                pass
        return {'width': int(width), 'height': int(height)}


def _carregar_geo() -> dict:
    if not GEO_FILE.exists():
        return {'x': None, 'y': None, 'width': DEFAULT_W, 'height': DEFAULT_H}
    try:
        raw = GEO_FILE.read_text(encoding='utf-8')
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}
    out = {'x': data.get('x'), 'y': data.get('y'), 'width': int(data.get('width', DEFAULT_W)), 'height': int(data.get('height', DEFAULT_H))}
    return out

WIDGET_JS_EXTRA = """
<script>
(function(){
  function mk(tag, styles) {
    var el = document.createElement(tag);
    if (styles) el.style.cssText = styles;
    return el;
  }

  function mountWidgetUI() {
    if (document.getElementById('mk-controles')) return;

    var cores = { fundo: '#1e1e2e', borda: '#45475a', destaque: '#cba6f7', texto: '#cdd6f4', texto2: '#a6adc8' };

    var topBar = mk('div');
    topBar.id = 'mk-topbar';
    topBar.style.cssText = 'position:fixed;top:10px;right:12px;left:52px;z-index:99998;display:flex;justify-content:flex-end;align-items:center;gap:6px;pointer-events:auto;';

    var eye = mk('div');
    eye.id = 'mk-painel-toggle';
    eye.title = 'Ocultar/mostrar painel';
    eye.textContent = '👁';
    eye.style.cssText = 'position:fixed;top:12px;left:10px;z-index:99999;width:30px;height:30px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;background:#313244;border:1px solid ' + cores.borda + ';color:' + cores.destaque + ';';

    var ctrl = mk('div');
    ctrl.id = 'mk-labels';
    ctrl.title = 'Alternar visibilidade das etiquetas';
    ctrl.textContent = 'T';
    ctrl.style.cssText = 'width:30px;height:30px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + cores.destaque + ';background:#313244;border:1px solid ' + cores.destaque + ';font-size:14px;';

    var menuBtn = mk('div');
    menuBtn.id = 'mk-menu-btn';
    menuBtn.title = 'Mostrar/ocultar menus';
    menuBtn.textContent = '☰';
    menuBtn.style.cssText = 'width:30px;height:30px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + cores.destaque + ';background:#313244;border:1px solid ' + cores.destaque + ';font-size:14px;';

    var resetBtn = mk('div');
    resetBtn.id = 'mk-btn-reset';
    resetBtn.title = 'Resetar preferências';
    resetBtn.textContent = '↺';
    resetBtn.style.cssText = 'width:30px;height:30px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + cores.destaque + ';background:#313244;border:1px solid ' + cores.destaque + ';font-size:14px;';

    var actions = mk('div');
    actions.style.cssText = 'display:flex;gap:6px;border:1px solid ' + cores.destaque + ';border-radius:6px;padding:4px;background:#313244;';
    actions.appendChild(ctrl);
    actions.appendChild(menuBtn);
    actions.appendChild(resetBtn);

    var topTheme = mk('select');
    topTheme.style.cssText = 'background:' + cores.fundo + ';color:' + cores.texto + ';border:1px solid ' + cores.borda + ';border-radius:4px;font-size:11px;padding:2px 4px;';
    [{ nome: 'Neon', valor: 'neon' }, { nome: 'Glow', valor: 'glow' }, { nome: 'Calmo', valor: 'calm' }, { nome: 'Padrao', valor: 'padrao' }].forEach(function(item){
      var opt = mk('option');
      opt.value = item.valor;
      opt.textContent = item.nome;
      topTheme.appendChild(opt);
    });
    topTheme.value = localStorage.getItem('temaGrafo') || 'glow';

    var themeWrap = mk('div');
    themeWrap.style.cssText = 'display:flex;align-items:center;gap:6px;';
    var themeLabel = mk('span');
    themeLabel.textContent = 'Tema';
    themeLabel.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';';
    themeWrap.appendChild(themeLabel);
    themeWrap.appendChild(topTheme);

    var speed = mk('input');
    speed.type = 'range'; speed.min = '0.25'; speed.max = '3'; speed.step = '0.05'; speed.value = localStorage.getItem('velGrafo') || '1';
    speed.style.cssText = 'width:110px;accent-color:' + cores.destaque + ';cursor:pointer;';
    var speedValue = mk('span');
    speedValue.textContent = 'x' + parseFloat(speed.value).toFixed(2);
    speedValue.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';min-width:34px;text-align:right;';
    speed.addEventListener('input', function(){
      speedValue.textContent = 'x' + parseFloat(speed.value).toFixed(2);
      localStorage.setItem('velGrafo', speed.value);
    });
    var speedWrap = mk('div');
    speedWrap.style.cssText = 'display:flex;align-items:center;gap:6px;';
    var speedLabel = mk('span');
    speedLabel.textContent = 'Velocidade';
    speedLabel.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';';
    speedWrap.appendChild(speedLabel);
    speedWrap.appendChild(speed);
    speedWrap.appendChild(speedValue);

    var orbit = mk('input');
    orbit.type = 'range'; orbit.min = '0'; orbit.max = '3'; orbit.step = '0.1'; orbit.value = localStorage.getItem('orbGrafo') || '1';
    orbit.style.cssText = 'width:110px;accent-color:' + cores.destaque + ';cursor:pointer;';
    var orbitValue = mk('span');
    orbitValue.textContent = 'x' + parseFloat(orbit.value).toFixed(1);
    orbitValue.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';min-width:34px;text-align:right;';
    orbit.addEventListener('input', function(){
      orbitValue.textContent = 'x' + parseFloat(orbit.value).toFixed(1);
      localStorage.setItem('orbGrafo', orbit.value);
    });
    var orbitWrap = mk('div');
    orbitWrap.style.cssText = 'display:flex;align-items:center;gap:6px;';
    var orbitLabel = mk('span');
    orbitLabel.textContent = 'Orbita';
    orbitLabel.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';';
    orbitWrap.appendChild(orbitLabel);
    orbitWrap.appendChild(orbit);
    orbitWrap.appendChild(orbitValue);

    var panel = mk('div');
    panel.id = 'mk-controles';
    panel.title = 'Controles do grafo';
    panel.style.cssText = 'position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:row;align-items:center;justify-content:center;flex-wrap:wrap;gap:10px;padding:8px 12px;border-radius:12px;background:rgba(30,30,46,0.9);border:1px solid ' + cores.borda + ';box-shadow:0 6px 18px rgba(0,0,0,0.38);';
    panel.appendChild(themeWrap);
    panel.appendChild(speedWrap);
    panel.appendChild(orbitWrap);
    panel.appendChild(actions);

    topBar.appendChild(actions);
    document.body.appendChild(topBar);
    document.body.appendChild(panel);
    document.body.appendChild(eye);

    var visible = true;
    eye.addEventListener('click', function(){
      visible = !visible;
      panel.style.display = visible ? 'flex' : 'none';
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', mountWidgetUI, { once: true });
  } else {
    mountWidgetUI();
  }

  window.addEventListener('pywebviewready', mountWidgetUI, { once: true });
})();
</script>
"""


def _persistir_saida(win) -> None:
    try:
        if hasattr(win, 'evaluate_js'):
            try:
                win.evaluate_js("""
                  if(window.pywebview && window.pywebview.api){
                    window.pywebview.api.guardar_geo(
                      Math.round(window.screenX||0), Math.round(window.screenY||0),
                      Math.round(window.innerWidth||0), Math.round(window.innerHeight||0));
                  }
                """)
            except Exception:
                pass
    except Exception:
        pass


def _regenerate() -> bool:
    print('[widget] Regenerando grafo...')
    try:
        r = subprocess.run([sys.executable, str(GEN_SCRIPT), str(OUTPUT_HTML)],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print('[widget] Erro ao gerar:')
            print((r.stderr or r.stdout or '').strip())
            return False
        print('[widget] Grafo atualizado.')
        return True
    except Exception as e:
        print(f'[widget] Falha na geracao: {e}')
        return False


def _build_view() -> Path | None:
    # Sempre regenera para garantir HTML atualizado
    if not _regenerate():
        return None
    src = OUTPUT_HTML.read_text(encoding='utf-8')

    VENDOR = BASE / 'docs' / 'vendor' / 'vis-network.min.js'
    if VENDOR.exists():
        vendor_js = VENDOR.read_text(encoding='utf-8')
        src = src.replace(
            '<script src="vendor/vis-network.min.js"></script>',
            '<script>' + vendor_js + '</script>'
        )
    else:
        src = src.replace(
            '<script src="vendor/vis-network.min.js"></script>',
            '<script src="https://unpkg.com/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>'
        )

    early_error = """
<script>
  window.__widgerrs = [];
  window.addEventListener('error', function(ev){
    var txt = (ev.message||'') + ' @ ' + (ev.lineno||'') + ':' + (ev.colno||'');
    window.__widgerrs.push(txt);
    try {
      if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
        window.pywebview.api.debug_log('ERRO-TARDE: ' + txt);
      }
    } catch(e){}
  }, true);
</script>
"""
    if '</head>' in src:
        src = src.replace('</head>', early_error + '</head>', 1)
    else:
        src = early_error + src

    if '</head>' in src:
        src = src.replace('</head>', WIDGET_JS + '</head>', 1)
    else:
        src += WIDGET_JS

    if '</head>' in src:
        src = src.replace('</head>', '<style>' + WIDGET_CSS + '</style></head>', 1)
    else:
        src += '<style>' + WIDGET_CSS + '</style>'

    api_inject = API_INJECT.replace('%POLL_MS%', str(POLL_MS))
    if '</head>' in src:
        src = src.replace('</head>', api_inject + '</head>', 1)
    else:
        src += api_inject

    if '</body>' in src:
        src = src.replace('</body>', RESIZE_JS + WIDGET_JS_EXTRA + '</body>', 1)
    else:
        src += RESIZE_JS + WIDGET_JS_EXTRA

    VIEW_COPY.write_text(src, encoding='utf-8')
    return VIEW_COPY


def main() -> int:
    print("[WIDGET] main() started", flush=True)
    import webview

    view = _build_view()
    if not view:
        print('[widget] Nao foi possivel obter o grafo.')
        return 1

    geo = _carregar_geo()
    w = int(geo.get('width', DEFAULT_W))
    h = int(geo.get('height', DEFAULT_H))
    x = geo.get('x')
    y = geo.get('y')

    bridge = Bridge()
    win = webview.create_window(
        TITLE,
        url=str(view.resolve()),
        width=w, height=h,
        x=x, y=y,
        resizable=True,
        frameless=True,
        easy_drag=False,
        shadow=False,
        focus=False,
        js_api=bridge,
        background_color=BG,
    )
    bridge._win = win

    try:
        webview.start(debug=False)
    finally:
        _persistir_saida(win)
    return 0


if __name__ == '__main__':
    sys.exit(main())
