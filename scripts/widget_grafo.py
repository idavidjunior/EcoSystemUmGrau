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

POLL_MS = 2000
TITLE = 'Cerebro Vivo'
BG = '#1e1e2e'
DEFAULT_W, DEFAULT_H = 1280, 800
MIN_W, MIN_H = 400, 300

# CSS + JS de widget: oculta o header (controles); clique direito alterna a
# classe 'desktop' no body que revela os controles; alca de resize no canto.
# Funciona com o layout original (flexbox: header + wrap[net + painel])
WIDGET_CSS = """
  /* Esconde header por padrão; clique direito (body.desktop) revela */
  #header { transition: opacity .25s ease; opacity: 0; pointer-events: none; height: 0; overflow: hidden; }
  body.desktop #header { opacity: 1; pointer-events: auto; height: auto; overflow: visible; }

  /* Wrapper flex original mantém-se; só escondemos o painel lateral */
  #painel { display: none !important; }
  #wrap { display: flex; height: 100vh; }
  #net { flex: 1; height: 100vh !important; width: 100% !important; }
  body { margin: 0; width: 100vw; height: 100vh; overflow: hidden; background: #1e1e2e; }

  /* Moldura fina para arrastar a janela (sempre visível, discreta) */
  #mk-drag { position: fixed; left: 0; top: 0; width: 100%; height: 16px;
             cursor: grab; z-index: 9999; background: transparent; }
  #mk-drag:active { cursor: grabbing; }

  /* Alça de resize no canto inferior direito */
  #mk-resize { position: fixed; right: 0; bottom: 0; width: 18px; height: 18px;
               cursor: nwse-resize; display: none; z-index: 9999; }
  body.desktop #mk-resize { display: block; }
"""

WIDGET_JS = """
<script>
  document.addEventListener('contextmenu', function(e){
    e.preventDefault();
    document.body.classList.toggle('desktop');
  }, false);
</script>
"""

RESIZE_JS = """
<script>
  (function(){
    /* --- moldura de arrasto (move a janela pelo desktop) --- */
    var bar = document.createElement('div');
    bar.id = 'mk-drag';
    bar.title = 'Arraste para mover';
    document.body.appendChild(bar);
    var rx=0, ry=0, sx=0, sy=0, drag=false;
    bar.addEventListener('mousedown', function(e){
      e.preventDefault(); e.stopPropagation();
      sx=e.screenX; sy=e.screenY;
      rx=(window.screenX||0); ry=(window.screenY||0);
      drag=true;
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
    function onMove(e){
      if(!drag) return;
      var nx = rx + (e.screenX - sx);
      var ny = ry + (e.screenY - sy);
      if(window.pywebview && window.pywebview.api){
        window.pywebview.api.mover(Math.round(nx), Math.round(ny));
      }
    }
    function onUp(){
      drag=false;
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      report();
    }

    /* --- alca de resize (canto inferior direito) --- */
    var grip = document.createElement('div');
    grip.id = 'mk-resize';
    grip.title = 'Arraste para redimensionar';
    document.body.appendChild(grip);
    var startX=0, startY=0, startW=innerWidth, startH=innerHeight, ar=null;
    grip.addEventListener('mousedown', function(e){
      e.preventDefault(); e.stopPropagation();
      startX=e.screenX; startY=e.screenY; startW=innerWidth; startH=innerHeight;
      ar = true;
      document.addEventListener('mousemove', onRm);
      document.addEventListener('mouseup', onRu);
    });
    function onRm(e){
      if(!ar) return;
      var w = startW + (e.screenX - startX);
      var h = startH + (e.screenY - startY);
      if(window.pywebview && window.pywebview.api){
        window.pywebview.api.redimensionar(Math.round(w), Math.round(h));
      }
    }
    function onRu(){ ar=false; document.removeEventListener('mousemove', onRm);
      document.removeEventListener('mouseup', onRu); report(); }

    /* reporta a geometria via JS (nao acessa win.native -> evita recursao) */
    function report(){
      if(window.pywebview && window.pywebview.api){
        try {
          window.pywebview.api.guardar_geo(
            Math.round(window.screenX||0), Math.round(window.screenY||0),
            Math.round(window.innerWidth||0), Math.round(window.innerHeight||0));
        } catch(e){}
      }
    }
    window.addEventListener('pywebviewready', report);
    window.addEventListener('resize', report);
  })();
</script>
"""

API_INJECT = """
<script>
(function(){
  // Diagnostico: captura erros JS e grava via bridge (arquivo widget_log.txt)
  function log(msg){
    try {
      if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
        window.pywebview.api.debug_log(msg);
      }
    } catch(e){}
  }

  window.addEventListener('error', function(ev){
    log('ERRO: ' + String(ev.message||'') + ' @ ' + (ev.filename||'') + ':' + (ev.lineno||''));
    log('vis carregado? ' + (typeof vis !== 'undefined'));
    var netEl = document.getElementById('net');
    if(netEl){ log('net size: ' + netEl.clientWidth + 'x' + netEl.clientHeight); }
  });

  // Diagnostico imediato apos carregamento
  setTimeout(function(){
    log('DIAG: vis carregado? ' + (typeof vis !== 'undefined'));
    var netEl = document.getElementById('net');
    if(netEl){
      log('DIAG: container net existe: true');
      log('DIAG: net size: ' + netEl.clientWidth + 'x' + netEl.clientHeight);
      log('DIAG: net display: ' + getComputedStyle(netEl).display);
      log('DIAG: net visibility: ' + getComputedStyle(netEl).visibility);
    } else {
      log('DIAG: container net nao encontrado');
    }
  }, 500);

  // Diagnostico do network apos inicializacao - verifica canvas
  setTimeout(function(){
    var netEl = document.getElementById('net');
    if(netEl){
      var canvas = netEl.querySelector('canvas');
      if(canvas){
        log('DIAG: canvas existe: true, size: ' + canvas.width + 'x' + canvas.height);
        log('DIAG: canvas style: ' + canvas.style.cssText);
      } else {
        log('DIAG: canvas NAO encontrado dentro de #net');
        log('DIAG: #net innerHTML: ' + netEl.innerHTML.substring(0, 200));
      }
      // Tenta acessar network via vis instance (se exposto globalmente ou via dados)
      // vis-network guarda referencia no container dataset ou no elemento
      if(netEl.network){
        log('DIAG: netEl.network existe');
      } else {
        log('DIAG: netEl.network nao exposto');
      }
    }
  }, 3000);

  var lastVer = null;
  var rodou = false;
  function checar(){
    try {
      window.pywebview.api.versao().then(function(v){
        if(!rodou){ rodou = true; lastVer = v; return; }
        if(v !== lastVer){
          lastVer = v;
          var u = new URL(window.location.href);
          u.searchParams.set('v', v);
          u.searchParams.set('rc', String(Date.now()));
          window.pywebview.api.regenerar().then(function(){
            window.location.href = u.toString();
          });
        }
      });
    } catch(e){}
  }
  if(window.pywebview && window.pywebview.api){ checar(); }
  window.addEventListener('pywebviewready', checar);
  setInterval(checar, %POLL_MS%);
})();
</script>
"""


def _carregar_geo() -> dict:
    try:
        if GEO_FILE.exists():
            g = json.loads(GEO_FILE.read_text(encoding='utf-8'))
            # Rejeita geometrias degeneradas (ex.: janela de 384x100 salva por
            # report() prematuro/errado) para a janela nunca abrir invisivel.
            w = int(g.get('width', 0))
            h = int(g.get('height', 0))
            if w >= MIN_W and h >= MIN_H:
                return g
            return {'x': g.get('x'), 'y': g.get('y'),
                    'width': DEFAULT_W, 'height': DEFAULT_H}
    except Exception:
        pass
    return {}


class Bridge:
    """Ponte JS (window.pywebview.api) -> Python."""
    def __init__(self):
        self._win = None

    def versao(self) -> str:
        return _versao()

    def debug_log(self, msg: str) -> None:
        try:
            with open(BASE / 'docs' / 'widget_log.txt', 'a', encoding='utf-8') as f:
                f.write(f'{time.time():.0f} | {msg}\n')
        except Exception:
            pass

    def regenerar(self) -> str:
        """Regenera docs/grafo.html (a partir do vault) e reaplica o CSS/JS do
        widget em docs/grafo_widget.html. Chamado pelo JS quando versao muda —
        garante que o widget sempre espelhe o vault Obsidian vivo."""
        ok = _regenerate()
        if ok:
            view = _build_view()
            return str(view) if view else ''
        return ''

    def redimensionar(self, w: int, h: int) -> None:
        if not self._win:
            return
        try:
            self._win.resize(int(w), int(h))
        except Exception as e:
            print(f'[widget] resize: {e}')

    def mover(self, x: int, y: int) -> None:
        if not self._win:
            return
        try:
            self._win.move(int(x), int(y))
        except Exception as e:
            print(f'[widget] mover: {e}')

    def guardar_geo(self, x: int, y: int, w: int, h: int) -> None:
        """Recebe a geometria reportada pelo JS e a persiste. NAO le win.native
        aqui para evitar a recursao infinita do pywebview em Windows."""
        try:
            w = int(w); h = int(h)
            if w < MIN_W or h < MIN_H:
                return  # ignora geometria degenerada (nao corrompe o arquivo)
            _salvar_geo({'x': int(x), 'y': int(y), 'width': w, 'height': h})
        except Exception:
            pass

    def toggle_labels(self) -> None:
        """Alterna visibilidade das labels (semelhante ao current-mode da legend)"""
        if not self._win:
            return
        try:
            # JS para alternar visibilidade da propriedade font.size para 0 ou 11
            self._win.evaluate_js("""
                const atual = nodes.get();
                const atualizacoes = atual.map(n => ({
                    id: n.id,
                    font: { ...n.font, size: (n.font.size === 0 ? 11 : 0) }
                }));
                nodes.update(atualizacoes);
                localStorage.setItem('labelsOcultos', (atual[0].font.size === 0 ? 'true' : 'false'));
            """)
        except Exception as e:
            print(f'[widget] toggle_labels: {e}')

    def limpar_labels(self) -> None:
        """Zera para visibilidade (tamanho da fonte 11)"""
        if not self._win:
            return
        try:
            self._win.evaluate_js("""
                const atual = nodes.get();
                const atualizacoes = atual.map(n => ({
                    id: n.id,
                    font: { ...n.font, size: 11 }
                }));
                nodes.update(atualizacoes);
                localStorage.setItem('labelsOcultos', 'false');
            """)
        except Exception as e:
            print(f'[widget] limpar_labels: {e}')

    def restore_initial_state(self) -> None:
        """Restaura o estado inicial do grafo após uma atualização"""
        if not self._win:
            return
        try:
            self._win.evaluate_js("""
                // Após a estabilização, restaura as posições e zoom originais
                if (typeof guardaInicial === 'function') {
                    guardaInicial();
                }
                // Garante que as labels estão ocultas por padrão
                const atual = nodes.get();
                const atualizacoes = atual.map(n => ({
                    id: n.id,
                    font: { ...n.font, size: 0 }
                }));
                nodes.update(atualizacoes);
                localStorage.setItem('labelsOcultos', 'true');
            """)
        except Exception as e:
            print(f'[widget] restore_initial_state: {e}')

    def update_labels_on_reload(self) -> None:
        """Atualiza as labels após um reload do grafo"""
        if not self._win:
            return
        try:
            self._win.evaluate_js("""
                // Durante uma atualização, mantém o estado de visibilidade das labels
                const labelsOcultos = localStorage.getItem('labelsOcultos') === 'true';
                const atual = nodes.get();
                const atualizacoes = atual.map(n => ({
                    id: n.id,
                    font: { ...n.font, size: labelsOcultos ? 0 : 11 }
                }));
                nodes.update(atualizacoes);
            """)
        except Exception as e:
            print(f'[widget] update_labels_on_reload: {e}')


WIDGET_JS_EXTRA = """
<script>
  (function(){
    // Adiciona controle de toggle para ocultar/mostrar labels
    var ctrl = document.createElement('div');
    ctrl.id = 'mk-labels';
    ctrl.title = 'Alternar visibilidade das etiquetas';
    ctrl.style.position = 'fixed';
    ctrl.style.left = '10px';
    ctrl.style.top = '40px';
    ctrl.style.width = '28px';
    ctrl.style.height = '28px';
    ctrl.style.background = '#1e1e2e';
    ctrl.style.border = '1px solid #313244';
    ctrl.style.borderRadius = '4px';
    ctrl.style.cursor = 'pointer';
    ctrl.style.zIndex = '9999';
    ctrl.style.display = 'flex';
    ctrl.style.alignItems = 'center';
    ctrl.style.justifyContent = 'center';
    ctrl.style.fontSize = '16px';
    ctrl.innerHTML = 'T';
    ctrl.onmousedown = function(e) {
      e.preventDefault(); e.stopPropagation();
      if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.toggle_labels();
      }
    };
    document.body.appendChild(ctrl);

    // Estado inicial: carrega da localStorage, se nao houver, assume visivel
    window.addEventListener('pywebviewready', function() {
      var labelsOcultos = localStorage.getItem('labelsOcultos');
      if (labelsOcultos === 'true') {
        if (window.pywebview && window.pywebview.api) {
          window.pywebview.api.limpar_labels();
        }
      }
    });
  })();
</script>
"""


def _salvar_geo(data: dict) -> None:
    try:
        GEO_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                            encoding='utf-8')
    except Exception:
        pass


def _mtime_ns(path: Path) -> int:
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return 0


def _versao() -> str:
    v = [_mtime_ns(KNOWLEDGE_GRAPH)]
    late = 0
    if CONHECIMENTO_DIR.is_dir():
        for p in CONHECIMENTO_DIR.rglob('*'):
            if p.is_file():
                late = max(late, _mtime_ns(p))
    v.append(late)
    v.append(_mtime_ns(OUTPUT_HTML))
    return '-'.join(str(x) for x in v)


class Bridge:
    """Ponte JS (window.pywebview.api) -> Python."""
    def __init__(self):
        # _win e privado: pywebview itera dir(js_api) expoe atributos publicos e
        # tenta serializar objetos nao-callable -> o Window nativo causa recursao
        # infinita em win.native (erro COM UI thread) e quebra a injecao do bridge.
        self._win = None

    def versao(self) -> str:
        return _versao()

    def debug_log(self, msg: str) -> None:
        try:
            with open(BASE / 'docs' / 'widget_log.txt', 'a', encoding='utf-8') as f:
                f.write(f'{time.time():.0f} | {msg}\n')
        except Exception:
            pass

    def regenerar(self) -> str:
        """Regenera docs/grafo.html (a partir do vault) e reaplica o CSS/JS do
        widget em docs/grafo_widget.html. Chamado pelo JS quando versao muda —
        garante que o widget sempre espelhe o vault Obsidian vivo."""
        ok = _regenerate()
        if ok:
            view = _build_view()
            return str(view) if view else ''
        return ''

    def redimensionar(self, w: int, h: int) -> None:
        if not self._win:
            return
        try:
            self._win.resize(int(w), int(h))
        except Exception as e:
            print(f'[widget] resize: {e}')

    def mover(self, x: int, y: int) -> None:
        if not self._win:
            return
        try:
            self._win.move(int(x), int(y))
        except Exception as e:
            print(f'[widget] mover: {e}')

    def guardar_geo(self, x: int, y: int, w: int, h: int) -> None:
        """Recebe a geometria reportada pelo JS e a persiste. NAO le win.native
        aqui para evitar a recursao infinita do pywebview em Windows Forms."""
        try:
            w = int(w); h = int(h)
            if w < MIN_W or h < MIN_H:
                return  # ignora geometria degenerada (nao corrompe o arquivo)
            _salvar_geo({'x': int(x), 'y': int(y), 'width': w, 'height': h})
        except Exception:
            pass


def _persistir_saida(win) -> None:
    """Salva a geometria no fechamento, sem ler win.native (evita recursao)."""
    try:
        # le via JS: dispara um console do bridge que grava no fechamento
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
    if not OUTPUT_HTML.exists():
        if not _regenerate():
            return None
    src = OUTPUT_HTML.read_text(encoding='utf-8')

    # Embute o vis-network inline (elimina dependencia de CDN/servidor local)
    VENDOR = BASE / 'docs' / 'vendor' / 'vis-network.min.js'
    if VENDOR.exists():
        vendor_js = VENDOR.read_text(encoding='utf-8')
        src = src.replace(
            '<script src="vendor/vis-network.min.js"></script>',
            '<script>' + vendor_js + '</script>'
        )
    else:
        # Fallback: CDN se o arquivo local nao existir
        src = src.replace(
            '<script src="vendor/vis-network.min.js"></script>',
            '<script src="https://unpkg.com/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>'
        )

    # Injeta diagnostico imediatamente apos a criacao do network, DENTRO do
    # mesmo <script> que declara `const network` (para acessar a variavel no
    # escopo do bloco). Erros sincronos do bloco principal nao sao capturados
    # por window.onerror tardio do API_INJECT.
    # Captura erros do bloco principal ANTES que ele rode: registra um
    # window.onerror no <head> (roda antes dos scripts do body), assim qualquer
    # erro sincrono/assincrono do bloco principal cai aqui.
    # Também injeta um marcador global que o bloco principal pode chamar.
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

    # Injetar o controle extra para ocultar labels e detectar flash momentaneo
    if '</body>' in src:
        src = src.replace('</body>', WIDGET_JS_EXTRA + '</body>', 1)
    else:
        src += WIDGET_JS_EXTRA

    VIEW_COPY.write_text(src, encoding='utf-8')
    return VIEW_COPY



def main() -> int:
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
        # URL via resolve(): usa HTTP server do pywebview (carrega recursos relativos
        # como vendor/vis-network.min.js). Com _win privado, o bridge funciona e
        # o evento loaded dispara (antes quebrava pela recursao de win.publico).
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