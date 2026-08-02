"""Widget desktop do Cerebro Vivo - grafo do conhecimento em tempo real.

Janela estilo "widget de area de trabalho" (estilo Rainmeter), sem bordas,
ancorada ATRAS das outras janelas, ficando "colada" no desktop como um
wallpaper vivo. Os controles ficam ocultos por padrao; ao clicar com o botao
DIREITO do mouse a barra de controles (header/legenda) aparece/reaparece.

A janela pode ser REDIMENSIONADA arrastando a alca no canto inferior direito
(visivel quando os controles aparecem) e MOVIDA arrastando a barra superior.
A geometria (posicao + tamanho) e persistida em JSON e restaurada no proximo
start.

Observa continuamente as fontes do conhecimento (knowledge_graph.json +
conhecimento/*). Quando algo muda, re-gera docs/grafo.html e recarrega.

Dependencias: pip install pywebview

Uso:
  python scripts/widget_grafo.py
"""
import ctypes
import json
import subprocess
import sys
import threading
import time
from ctypes import wintypes
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

# --- Win32 ------------------------------------------------------------------
HWND_BOTTOM = 1
SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
GWL_EXSTYLE = -20
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
_user32 = ctypes.WinDLL('user32', use_last_error=True)

# CSS + JS de widget: oculta o header (controles); clique direito alterna a
# classe 'desktop' no body que revela os controles; alca de resize no canto.
WIDGET_CSS = """
  #header { transition: opacity .25s ease; opacity: 0; pointer-events: none; }
  #wrap { position: fixed; inset: 0; }
  #net { height: 100vh !important; width: 100vw !important; }
  body { width:100vw; height:100vh; overflow:hidden; }
  body.desktop #header { opacity: 1; pointer-events: auto; }
  #mk-resize { position: fixed; right:0; bottom:0; width:18px; height:18px;
               cursor: nwse-resize; display:none; }
  body.desktop #mk-resize { display:block; }
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
    var grip = document.createElement('div');
    grip.id = 'mk-resize';
    grip.title = 'Arraste para redimensionar';
    document.body.appendChild(grip);
    var startX=0, startY=0, startW=innerWidth, startH=innerHeight, ar=null;
    grip.addEventListener('mousedown', function(e){
      e.preventDefault(); e.stopPropagation();
      startX=e.screenX; startY=e.screenY; startW=innerWidth; startH=innerHeight;
      ar = true;
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);
    });
    function onMove(e){
      if(!ar) return;
      var w = startW + (e.screenX - startX);
      var h = startH + (e.screenY - startY);
      if(window.pywebview && window.pywebview.api){
        window.pywebview.api.redimensionar(Math.round(w), Math.round(h));
      }
    }
    function onUp(){ ar=false; document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp); }
  })();
</script>
"""

API_INJECT = """
<script>
(function(){
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
          window.location.href = u.toString();
        }
      });
    } catch(e){ /* pywebview ainda nao pronto */ }
  }
  if(window.pywebview && window.pywebview.api){ checar(); }
  window.addEventListener('pywebviewready', checar);
  setInterval(checar, %POLL_MS%);
</script>
"""


def _carregar_geo() -> dict:
    try:
        if GEO_FILE.exists():
            return json.loads(GEO_FILE.read_text(encoding='utf-8'))
    except Exception:
        pass
    return {}


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
        self.win = None

    def versao(self) -> str:
        return _versao()

    def redimensionar(self, w: int, h: int) -> None:
        if not self.win:
            return
        try:
            self.win.resize(int(w), int(h))
        except Exception as e:
            print(f'[widget] resize: {e}')


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

    if '<style>' in src:
        src = src.replace('<style>', '<style>' + WIDGET_CSS, 1)
    else:
        src = '<style>' + WIDGET_CSS + '</style>' + src

    if '</head>' in src:
        src = src.replace('</head>', WIDGET_JS + '</head>', 1)
    else:
        src += WIDGET_JS

    if '</body>' in src:
        src = src.replace('</body>', RESIZE_JS, 1)
    else:
        src += RESIZE_JS

    js = API_INJECT.replace('%POLL_MS%', str(POLL_MS))
    if '</body>' in src:
        src = src.replace('</body>', js, 1)
    else:
        src += js

    VIEW_COPY.write_text(src, encoding='utf-8')
    return VIEW_COPY


def _find_hwnd_by_title(title: str, deadline: float = 12.0) -> int:
    start = time.time()
    while time.time() - start < deadline:
        hwnd = _user32.FindWindowW(None, title)
        if hwnd:
            return int(hwnd)
        found = []
        EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def _cb(h, _lp):
            ln = _user32.GetWindowTextLengthW(h)
            if ln:
                buf = ctypes.create_unicode_buffer(ln + 1)
                _user32.GetWindowTextW(h, buf, ln + 1)
                if title.lower() in buf.value.lower():
                    found.append(int(h))
            return True

        _user32.EnumWindows(EnumProc(_cb), 0)
        if found:
            return found[0]
        time.sleep(0.2)
    return 0


def _find_workerw() -> int:
    """Encontra uma janela 'WorkerW' (area de trabalho) via EnumWindows."""
    workers = []
    EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def _cb(h, _lp):
        cls = ctypes.create_unicode_buffer(64)
        _user32.GetClassNameW(h, cls, 64)
        if cls.value == 'WorkerW' and _user32.IsWindowVisible(h):
            workers.append(int(h))
        return True

    _user32.EnumWindows(EnumProc(_cb), 0)
    if workers:
        return workers[-1]
    w = _user32.FindWindowW('WorkerW', None)
    return int(w) if w else 0


def _anchor_to_desktop(hwnd: int) -> bool:
    """Torna a janela filha da area de trabalho (Progman/Worker), ficando
    atras dos icones, como um wallpaper. Retorna True se ancorado."""
    try:
        progman = _user32.FindWindowW('Progman', None)
        if not progman:
            return False
        _user32.SendMessageW(progman, 0x052C, 0xD, 0)
        worker = _find_workerw()
        if not worker:
            return False
        cur = int(_user32.GetParent(wintypes.HWND(hwnd)))
        if cur == worker:
            return True
        _user32.SetParent(wintypes.HWND(hwnd), wintypes.HWND(worker))
        _user32.ShowWindow(wintypes.HWND(hwnd), 5)
        return True
    except Exception as e:
        print(f'[widget] Ancoragem Progman/WorkerW falhou ({e}).')
        return False


def _keep_behind(hwnd: int) -> None:
    """Mantem a janela sempre no fundo e sem roubar foco/taskbar. Tenta
    ancorar ao desktop periodicamente ate conseguir (o WorkerW pode demorar)."""
    try:
        h = wintypes.HWND(hwnd)
        ex = _user32.GetWindowLongW(h, GWL_EXSTYLE)
        _user32.SetWindowLongW(h, GWL_EXSTYLE, ex | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE)
    except Exception:
        pass
    ancorado = False
    while True:
        try:
            h = wintypes.HWND(hwnd)
            if not ancorado:
                ancorado = _anchor_to_desktop(hwnd)
            _user32.SetWindowPos(h, HWND_BOTTOM, 0, 0, 0, 0,
                                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
        except Exception:
            pass
        time.sleep(1.0)


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

    def _pin():
        hwnd = _find_hwnd_by_title(TITLE)
        if hwnd:
            _keep_behind(hwnd)

    threading.Thread(target=_pin, daemon=True).start()

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
    bridge.win = win

    def _geo_watcher():
        """Persiste posicao+tamanho periodicamente e no fechamento."""
        last = None
        while True:
            try:
                cur = {k: getattr(win, k) for k in ('x', 'y', 'width', 'height')}
                if cur != last:
                    _salvar_geo(cur)
                    last = cur
            except Exception:
                pass
            time.sleep(1.0)

    threading.Thread(target=_geo_watcher, daemon=True).start()

    try:
        webview.start(debug=False)
    finally:
        try:
            _salvar_geo({k: getattr(win, k) for k in ('x', 'y', 'width', 'height')})
        except Exception:
            pass
        print('[widget] Fechado.')
    return 0


if __name__ == '__main__':
    sys.exit(main())