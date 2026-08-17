"""Widget desktop do Cerebro Vivo - grafo do conhecimento em tempo real.

Janela flutuante (pywebview) com o grafo interativo. Sem bordas visuais, mas
MOVIDA livremente pelo desktop arrastando a barra superior (moldura discreta
#mk-drag) e REDIMENSIONADA pela alca do canto inferior direito (#mk-resize).
Os controles ficam na faixa inferior (#mk-controles), alternada pelo botao do
olho; a barra superior (#mk-topbar) guarda T (etiquetas), menu e reset.

A posicao e o tamanho sao persistidos em JSON (docs/grafo_widget_geometria.json)
e restaurados a cada execucao, inclusive apos reiniciar o computador.

Observa continuamente o vault (conhecimento/*.md). Quando algo muda,
re-gera docs/grafo.html, remonta docs/grafo_widget.html e recarrega a janela.

Dependencias: pip install pywebview

Uso:
  python scripts/widget_grafo.py
"""
import json
import subprocess
import sys
import threading
import time
import hashlib
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN_SCRIPT = BASE / 'scripts' / 'generate-graph-html.py'
OUTPUT_HTML = BASE / 'docs' / 'grafo.html'
CONHECIMENTO_DIR = BASE / 'conhecimento'
VIEW_COPY = BASE / 'docs' / 'grafo_widget.html'
GEO_FILE = BASE / 'docs' / 'grafo_widget_geometria.json'

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
        if width is not None: data['width'] = int(width)
        if height is not None: data['height'] = int(height)
        # (0,0) vindo do JS costuma ser posicao duvidosa (screenX/screenY nao
        # confiaveis no WebView2): ignora e mantem a ultima posicao conhecida.
        if not (x is not None and y is not None and int(x) == 0 and int(y) == 0):
            if x is not None: data['x'] = int(x)
            if y is not None: data['y'] = int(y)
        data = _clamp_geo(data)
        GEO_FILE.parent.mkdir(parents=True, exist_ok=True)
        GEO_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        return data

    def mover(self, x, y):
        if self._win is not None and hasattr(self._win, 'move'):
            try:
                self._win.move(int(x), int(y))
            except Exception:
                pass
        return {'x': int(x), 'y': int(y)}

    def redimensionar(self, width, height):
        if self._win is not None and hasattr(self._win, 'resize'):
            try:
                self._win.resize(max(MIN_W, int(width)), max(MIN_H, int(height)))
            except Exception:
                pass
        return {'width': int(width), 'height': int(height)}


def _screen_area():
    """Dimensoes da area de trabalho (monitor principal) em pixels, ou None."""
    try:
        import ctypes
        u = ctypes.windll.user32
        return int(u.GetSystemMetrics(0)), int(u.GetSystemMetrics(1))
    except Exception:
        return None


def _clamp_geo(data: dict) -> dict:
    """Garante que a janela caiba na tela e fique com pelo menos 80px visiveis."""
    w = int(data.get('width', DEFAULT_W))
    h = int(data.get('height', DEFAULT_H))
    x = data.get('x')
    y = data.get('y')
    area = _screen_area()
    if area:
        sw, sh = area
        if sw > 160 and sh > 120:
            w = max(MIN_W, min(int(w), sw))
            h = max(MIN_H, min(int(h), sh))
            if x is not None:
                x = int(x)
                if x > sw - 80: x = sw - 80
                if x < -(w - 80): x = 0
            if y is not None:
                y = int(y)
                if y > sh - 40: y = sh - 40
                if y < -(h - 40): y = 0
    return {'x': x, 'y': y, 'width': int(w), 'height': int(h)}


def _carregar_geo() -> dict:
    if not GEO_FILE.exists():
        return _clamp_geo({'x': None, 'y': None, 'width': DEFAULT_W, 'height': DEFAULT_H})
    try:
        raw = GEO_FILE.read_text(encoding='utf-8')
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}
    out = {'x': data.get('x'), 'y': data.get('y'), 'width': int(data.get('width', DEFAULT_W)), 'height': int(data.get('height', DEFAULT_H))}
    return _clamp_geo(out)


# External asset file paths
WIDGET_CSS_FILE = BASE / 'docs' / 'widget.css'
WIDGET_JS_FILE = BASE / 'docs' / 'widget.js'
WIDGET_EXTRA_JS_FILE = BASE / 'docs' / 'widget-extra.js'

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

    # Widget CSS (external file)
    src = _inject_into_head(src, '<link rel="stylesheet" href="widget.css">')

    # Widget JS (init controls) - external file
    src = _inject_into_head(src, '<script src="widget.js"></script>')

    # Extra widget UI - external file
    src = _inject_into_body(src, '<script src="widget-extra.js"></script>')

    VIEW_COPY.write_text(src, encoding='utf-8')
    return VIEW_COPY


_regen_lock = threading.Lock()


def _watcher(win, stop) -> None:
    """Observa o vault e regenera+recarrega quando algo muda.

    Antes, a mudanca era detectada pelo JS e o `window.location.reload()`
    recarregava um HTML estatico SEM regenerar o grafo (e ainda reiniciava o
    estado do polling a cada reload, causando reload em loop). Agora a
    regeneracao e o reload acontecem no Python: o grafo novo e de fato gerado.
    """
    last = _get_vault_version()
    while not stop.wait(POLL_MS / 1000.0):
        try:
            cur = _get_vault_version()
        except Exception:
            continue
        if cur == last or cur in ('empty', 'error'):
            continue
        last = cur
        with _regen_lock:
            try:
                if _build_view():
                    # Recarrega com ?rc=<ts> para a cascata neural ser disparada
                    # (o gerador le o rc e solta a cascata de pulso de vez).
                    win.evaluate_js("window.location.search = 'rc=' + Date.now();")
            except Exception:
                pass


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

    stop = threading.Event()
    threading.Thread(target=_watcher, args=(win, stop), daemon=True).start()

    try:
        webview.start(debug=False)
    finally:
        stop.set()
        _persistir_saida(win)
    return 0


if __name__ == '__main__':
    sys.exit(main())