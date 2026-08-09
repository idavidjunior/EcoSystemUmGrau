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


# External asset file paths
WIDGET_CSS_FILE = BASE / 'docs' / 'widget.css'
WIDGET_JS_FILE = BASE / 'docs' / 'widget.js'
WIDGET_EXTRA_JS_FILE = BASE / 'docs' / 'widget-extra.js'
API_INJECT_FILE = BASE / 'docs' / 'api-inject.js'
RESIZE_JS_FILE = BASE / 'docs' / 'resize.js'

def _read_asset(path: Path) -> str:
    """Read asset file, return empty string if not found."""
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return ''

# Load external assets
WIDGET_CSS = _read_asset(WIDGET_CSS_FILE)
WIDGET_JS = _read_asset(WIDGET_JS_FILE)
WIDGET_JS_EXTRA = _read_asset(WIDGET_EXTRA_JS_FILE)
API_INJECT = _read_asset(API_INJECT_FILE)
RESIZE_JS = _read_asset(RESIZE_JS_FILE)


def _persistir_saida(win) -> None:
    try:
        if hasattr(win, 'evaluate_js'):
            win.evaluate_js("""
              if(window.pywebview && window.pywebview.api){
                window.pywebview.api.guardar_geo(
                  Math.round(window.screenX||0), Math.round(window.screenY||0),
                  Math.round(window.innerWidth||0), Math.round(window.innerHeight||0));
              }
            """)
    except Exception:
        pass


def _regenerate() -> bool:
    try:
        r = subprocess.run([sys.executable, str(GEN_SCRIPT), str(OUTPUT_HTML)],
                           capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            return False
        return True
    except Exception:
        return False


def _inject_vendor_script(src: str) -> str:
    """Inject vendor script reference (not inline)."""
    VENDOR = BASE / 'docs' / 'vendor' / 'vis-network.min.js'
    if VENDOR.exists():
        src = src.replace(
            '<script src="vendor/vis-network.min.js"></script>',
            '<script src="vendor/vis-network.min.js"></script>'
        )
    else:
        src = src.replace(
            '<script src="vendor/vis-network.min.js"></script>',
            '<script src="https://unpkg.com/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>'
        )
    return src


def _inject_into_head(src: str, injection: str) -> str:
    """Inject content before </head> tag, or append if not found."""
    if '</head>' in src:
        return src.replace('</head>', injection + '</head>', 1)
    return src + injection


def _inject_into_body(src: str, injection: str) -> str:
    """Inject content before </body> tag, or append if not found."""
    if '</body>' in src:
        return src.replace('</body>', injection + '</body>', 1)
    return src + injection


def _build_view() -> Path | None:
    # Sempre regenera para garantir HTML atualizado
    if not _regenerate():
        return None
    src = OUTPUT_HTML.read_text(encoding='utf-8')

    # Vendor script (external reference, not inlined)
    src = _inject_vendor_script(src)

    # Early error handler
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
    } catch(e){
      console.warn('[widget] debug_log error:', e);
    }
  }, true);
</script>
"""
    src = _inject_into_head(src, early_error)

    # Widget JS (init controls)
    src = _inject_into_head(src, WIDGET_JS)

    # Widget CSS
    src = _inject_into_head(src, '<style>' + WIDGET_CSS + '</style>')

    # API inject (polling)
    api_inject = API_INJECT.replace('%POLL_MS%', str(POLL_MS))
    src = _inject_into_head(src, api_inject)

    # Resize handler + extra widget UI
    src = _inject_into_body(src, RESIZE_JS + WIDGET_JS_EXTRA)

    VIEW_COPY.write_text(src, encoding='utf-8')
    return VIEW_COPY


def main() -> int:
    import webview

    view = _build_view()
    if not view:
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