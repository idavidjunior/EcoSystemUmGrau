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
import hashlib
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

# Cache de versão do vault para evitar recalcular a cada poll
_vault_version_cache = {'hash': None, 'mtime': 0}

def _compute_vault_hash() -> str:
    """Calcula hash MD5 dos mtimes de todos .md em conhecimento/.
    Só muda quando arquivos .md reais são modificados (ignora cluster_mapper.json etc)."""
    try:
        md_files = list(CONHECIMENTO_DIR.rglob('*.md'))
        if not md_files:
            return 'empty'
        # Usa mtime + size para detectar mudanças rápidas sem ler conteúdo
        parts = []
        for f in sorted(md_files):
            try:
                st = f.stat()
                parts.append(f'{f.name}:{int(st.st_mtime)}:{st.st_size}')
            except OSError:
                pass
        return hashlib.md5('|'.join(parts).encode()).hexdigest()[:16]
    except Exception:
        return 'error'

def _get_vault_version() -> str:
    """Retorna hash do vault, com cache de 2s para não saturar I/O."""
    global _vault_version_cache
    now = time.time()
    if now - _vault_version_cache['mtime'] > 2:
        _vault_version_cache['hash'] = _compute_vault_hash()
        _vault_version_cache['mtime'] = now
    return _vault_version_cache['hash']


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
        """Retorna versão do vault. Só muda ts se hash dos .md mudou."""
        vault_hash = _get_vault_version()
        # last_ts vem do JS como string do hash anterior
        last_hash = str(last_ts or '')
        if vault_hash != last_hash:
            return {'ts': vault_hash, 'last_ts': last_hash, 'changed': True}
        return {'ts': vault_hash, 'last_ts': last_hash, 'changed': False}

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
  #mk-topbar { position: fixed; top: 10px; left: 12px; right: auto; z-index: 99998; display: flex; justify-content: flex-start; align-items: center; flex-wrap: wrap; gap: 4px; pointer-events: auto; width: min(220px, calc(100vw - 90px)); padding: 4px 6px; border-radius: 8px; background: rgba(24, 24, 37, 0.82); border: 1px solid rgba(145, 160, 198, 0.2); box-shadow: 0 8px 22px rgba(0,0,0,0.32); backdrop-filter: blur(6px); }
  #mk-topbar > * { flex: 0 0 auto; }
  #mk-topbar select,
  #mk-topbar input,
  #mk-topbar span,
  #mk-topbar div { box-sizing: border-box; }
  /* mk-painel-toggle (olho) é criado dentro do #mk-controles pelo JS, não precisa CSS fixo aqui */
  /* Painel de controles: organizado em faixa inferior e visivel por padrao */
  #mk-controles { position: fixed; bottom: 12px; left: 50%; transform: translateX(-50%); z-index: 9999; display: flex; flex-direction: row; align-items: center; justify-content: center; flex-wrap: wrap; gap: 8px; padding: 8px 12px; border-radius: 10px; background: rgba(24, 24, 37, 0.82); border: 1px solid rgba(145, 160, 198, 0.2); box-shadow: 0 8px 22px rgba(0,0,0,0.32); backdrop-filter: blur(6px); max-width: min(760px, calc(100vw - 110px)); width: min(760px, calc(100vw - 110px)); }
  #mk-controles > div,
  #mk-controles > select,
  #mk-controles > input { max-width: 100%; }
  #mk-controles > div,
  #mk-controles > select,
  #mk-controles > input,
  #mk-controles > span { border-radius: 6px; }
  @media (max-width: 760px) {
    #mk-topbar,
    #mk-controles { width: min(560px, calc(100vw - 70px)); max-width: calc(100vw - 70px); }
  }
  @media (max-width: 500px) {
    #mk-topbar,
    #mk-controles { width: min(300px, calc(100vw - 56px)); max-width: calc(100vw - 56px); gap: 5px; }
    #mk-controles { padding: 7px 8px; }
    #mk-controles input[type="range"] { width: 90px !important; }
  }
  """

API_INJECT = """
<script>
(function(){
  window.__widgetApiPoll = window.__widgetApiPoll || {
    lastTs: '',
    tick: function(){
      try {
        if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.perguntar === 'function') {
          window.pywebview.api.perguntar(this.lastTs).then(function(resp){
            if (resp && resp.ts) {
              this.lastTs = resp.ts;
              if (resp.changed) {
                // Vault mudou: recarrega a página para regenerar o grafo
                window.location.reload();
              }
            }
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

    // ===== BARRA SUPERIOR (topBar) =====
    var topBar = mk('div');
    topBar.id = 'mk-topbar';
    topBar.style.cssText = 'position:fixed;top:10px;left:12px;right:auto;z-index:99998;display:flex;align-items:center;gap:4px;pointer-events:auto;';

    var ctrl = mk('div');
    ctrl.id = 'mk-labels';
    ctrl.title = 'Alternar visibilidade das etiquetas';
    ctrl.textContent = 'T';
    ctrl.style.cssText = 'width:22px;height:22px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + cores.destaque + ';background:#313244;border:1px solid ' + cores.destaque + ';font-size:11px;';

    var menuBtn = mk('div');
    menuBtn.id = 'mk-menu-btn';
    menuBtn.title = 'Mostrar/ocultar menus (barra superior)';
    menuBtn.textContent = '☰';
    menuBtn.style.cssText = 'width:22px;height:22px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + cores.destaque + ';background:#313244;border:1px solid ' + cores.destaque + ';font-size:11px;';

    var resetBtn = mk('div');
    resetBtn.id = 'mk-btn-reset';
    resetBtn.title = 'Resetar preferências';
    resetBtn.textContent = '↺';
    resetBtn.style.cssText = 'width:22px;height:22px;border-radius:6px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:' + cores.destaque + ';background:#313244;border:1px solid ' + cores.destaque + ';font-size:11px;';

    var actions = mk('div');
    actions.style.cssText = 'display:flex;gap:4px;border:1px solid ' + cores.destaque + ';border-radius:6px;padding:2px 4px;background:#313244;';
    actions.appendChild(ctrl);
    actions.appendChild(menuBtn);
    actions.appendChild(resetBtn);
    topBar.appendChild(actions);

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

    // ===== PAINEL INFERIOR (mk-controles) =====
    var panel = mk('div');
    panel.id = 'mk-controles';
    panel.title = 'Controles do grafo';
    panel.style.cssText = 'position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:9999;display:flex;flex-direction:row;align-items:center;justify-content:center;flex-wrap:wrap;gap:8px;padding:8px 12px;border-radius:10px;background:rgba(24,24,37,0.82);border:1px solid rgba(145, 160, 198, 0.2);box-shadow:0 8px 22px rgba(0,0,0,0.32);backdrop-filter:blur(6px);';
    panel.appendChild(themeWrap);
    panel.appendChild(speedWrap);
    panel.appendChild(orbitWrap);

    // Botão do Olho DENTRO do painel inferior (único controle de visibilidade global da área)
    var eye = mk('div');
    eye.id = 'mk-painel-toggle';
    eye.title = 'Ocultar/mostrar painel de controles';
    eye.textContent = '👁';
    eye.style.cssText = 'width:28px;height:28px;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;background:#313244;border:1px solid ' + cores.destaque + ';color:' + cores.destaque + ';font-size:13px;box-shadow:0 4px 12px rgba(0,0,0,0.22);transition:transform .12s ease, box-shadow .12s ease, background .12s ease;flex-shrink:0;';
    panel.appendChild(eye);

    document.body.appendChild(topBar);
    document.body.appendChild(panel);

    // ===== FUNÇÕES =====
    function setLabelVisibility(visible) {
      var hidden = !visible;
      localStorage.setItem('labelsOcultos', hidden ? 'true' : 'false');
      try {
        if (typeof network !== 'undefined' && network) {
          var nodeSet = null;
          if (network.body && network.body.data && network.body.data.nodes && typeof network.body.data.nodes.get === 'function') {
            nodeSet = network.body.data.nodes;
          } else if (network.body && network.body.nodes && typeof network.body.nodes.get === 'function') {
            nodeSet = network.body.nodes;
          } else if (typeof nodes !== 'undefined' && nodes && typeof nodes.get === 'function') {
            nodeSet = nodes;
          }

          if (nodeSet && typeof nodeSet.get === 'function') {
            if (!window.__mkLabelBase) window.__mkLabelBase = {};
            var currentNodes = nodeSet.get();
            var payload = currentNodes.map(function(n) {
              if (!n || typeof n.id === 'undefined') return null;
              if (typeof window.__mkLabelBase[n.id] !== 'number' || window.__mkLabelBase[n.id] <= 0) {
                window.__mkLabelBase[n.id] = (n.font && typeof n.font.size === 'number' && n.font.size > 0) ? n.font.size : 13;
              }
              return {
                id: n.id,
                font: Object.assign({}, n.font || {}, { size: hidden ? 0 : window.__mkLabelBase[n.id] })
              };
            }).filter(Boolean);

            if (payload.length) {
              try { nodeSet.update(payload); } catch (e) {}
            }
          }
          if (typeof network.redraw === 'function') network.redraw();
        }
      } catch (e) {}

      // Atualiza aparência do botão T
      ctrl.style.opacity = hidden ? '0.6' : '1';
      ctrl.style.borderColor = hidden ? '#7c7f93' : cores.destaque;
      ctrl.style.background = hidden ? '#2b2d3a' : '#313244';
      ctrl.title = visible ? 'Ocultar etiquetas' : 'Mostrar etiquetas';
    }

    function applyTheme(theme) {
      theme = theme || 'glow';
      localStorage.setItem('temaGrafo', theme);
      try {
        if (typeof window !== 'undefined') {
          window.__mkTemaAtual = theme;
          document.body.setAttribute('data-theme', theme);
        }
      } catch (e) {}
    }

    function resetWidgetState() {
      topTheme.value = 'glow';
      speed.value = '1';
      orbit.value = '1';
      localStorage.setItem('temaGrafo', 'glow');
      localStorage.setItem('velGrafo', '1');
      localStorage.setItem('orbGrafo', '1');
      localStorage.setItem('labelsOcultos', 'false');
      localStorage.setItem('painelGrafoVisivel', 'true');
      applyTheme('glow');
      setLabelVisibility(true);
      syncControlsPanel(true);
      speedValue.textContent = 'x1.00';
      orbitValue.textContent = 'x1.0';
      try {
        if (typeof _aplicarVelocidade === 'function') _aplicarVelocidade(1);
      } catch (e) {}
      try {
        if (typeof _aplicarOrbita === 'function') _aplicarOrbita(1);
      } catch (e) {}
      try {
        if (typeof network !== 'undefined' && network && network.fit) network.fit({ animation: true });
      } catch (e) {}
    }

    topTheme.addEventListener('change', function(){
      applyTheme(topTheme.value);
    });

    speed.addEventListener('input', function(){
      speedValue.textContent = 'x' + parseFloat(speed.value).toFixed(2);
      localStorage.setItem('velGrafo', speed.value);
      try {
        if (typeof _aplicarVelocidade === 'function') _aplicarVelocidade(parseFloat(speed.value));
      } catch (e) {}
    });

    orbit.addEventListener('input', function(){
      orbitValue.textContent = 'x' + parseFloat(orbit.value).toFixed(1);
      localStorage.setItem('orbGrafo', orbit.value);
      try {
        if (typeof _aplicarOrbita === 'function') _aplicarOrbita(parseFloat(orbit.value));
      } catch (e) {}
    });

    // Estado do painel inferior (controlado APENAS pelo botão do olho)
    var panelVisible = localStorage.getItem('painelGrafoVisivel') !== 'false';
    function syncControlsPanel(show) {
      panelVisible = !!show;
      panel.style.display = panelVisible ? 'flex' : 'none';
      panel.hidden = !panelVisible;
      panel.setAttribute('aria-hidden', String(!panelVisible));
      // Olho SEMPRE visível - só muda ícone/title
      eye.title = panelVisible ? 'Ocultar painel de controles' : 'Mostrar painel de controles';
      eye.textContent = panelVisible ? '👁' : '👁️';
      eye.style.background = panelVisible ? '#313244' : '#45475a';
      eye.style.boxShadow = panelVisible ? '0 4px 12px rgba(0,0,0,0.22)' : '0 0 0 2px rgba(203,166,247,0.2), 0 6px 14px rgba(0,0,0,0.24)';
      localStorage.setItem('painelGrafoVisivel', panelVisible ? 'true' : 'false');
    }

    syncControlsPanel(panelVisible);

    // ===== EVENT LISTENERS (estados independentes) =====
    
    // Olho: controla APENAS o painel inferior (mk-controles)
    eye.addEventListener('click', function(){
      syncControlsPanel(!panelVisible);
    });

    // Menu (☰): controla APENAS a barra superior (mk-topbar)
    menuBtn.addEventListener('click', function(){
      var isHidden = topBar.style.display === 'none';
      topBar.style.display = isHidden ? 'flex' : 'none';
      menuBtn.textContent = isHidden ? '☰' : '…';
      menuBtn.title = isHidden ? 'Mostrar barra superior' : 'Ocultar barra superior';
    });

    // Botão T: alterna etiquetas dos nós (independente)
    ctrl.addEventListener('click', function(){
      var shouldShow = localStorage.getItem('labelsOcultos') !== 'true';
      setLabelVisibility(shouldShow);
    });

    resetBtn.addEventListener('click', function(){
      resetWidgetState();
    });

    window.__mkWidgetApi = {
      applyTheme: applyTheme,
      setLabelVisibility: setLabelVisibility,
      resetWidgetState: resetWidgetState
    };

    applyTheme(topTheme.value);
    setLabelVisibility(localStorage.getItem('labelsOcultos') !== 'true');
    if (typeof _aplicarVelocidade === 'function') _aplicarVelocidade(parseFloat(speed.value));
    if (typeof _aplicarOrbita === 'function') _aplicarOrbita(parseFloat(orbit.value));
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
        webview.start(debug=True)
    finally:
        _persistir_saida(win)
    return 0


if __name__ == '__main__':
    sys.exit(main())