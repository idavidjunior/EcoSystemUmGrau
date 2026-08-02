"""Widget desktop do Cerebro Vivo - grafo do conhecimento em tempo real.

Abre uma janela (pywebview / EdgeView) com o grafo interativo e observa
continuamente as fontes do conhecimento (knowledge_graph.json + conhecimento/*).
Quando algo muda, re-gera docs/grafo.html e recarrega a janela.

Recarregamento: o HTML recebe um pequeno bloco JS (bridge) que pergunta ao
lado Python via `webview.api.versao()` periodicamente. Se a versao das fontes
mudou, a pagina recarrega a si propria com cache-bypass.

Dependencias: pip install pywebview

Uso:
  python scripts/widget_grafo.py
"""
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
GEN_SCRIPT = BASE / 'scripts' / 'generate-graph-html.py'
OUTPUT_HTML = BASE / 'docs' / 'grafo.html'
KNOWLEDGE_GRAPH = BASE / 'ler-runtime' / 'knowledge' / 'knowledge_graph.json'
CONHECIMENTO_DIR = BASE / 'conhecimento'
VIEW_COPY = BASE / 'docs' / 'grafo_widget.html'

POLL_MS = 2000

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
          window.location.href = u.toString();
        }
      });
    } catch(e){ /* bridge ainda nao pronta */ }
  }
  if(window.pywebview && window.pywebview.api){ checar(); }
  window.addEventListener('pywebviewready', checar);
  setInterval(checar, %POLL_MS%);
</script>
"""


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
    def versao(self) -> str:
        return _versao()


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
    js = API_INJECT.replace('%POLL_MS%', str(POLL_MS))
    if '</body>' in src:
        src = src.replace('</body>', js, 1)
    else:
        src += js
    VIEW_COPY.write_text(src, encoding='utf-8')
    return VIEW_COPY


def main() -> int:
    import webview
    view = _build_view()
    if not view:
        print('[widget] Nao foi possivel obter o grafo.')
        return 1
    print(f'[widget] Abrindo {view}')
    win = webview.create_window(
        'Cerebro Vivo - Grafo do Conhecimento',
        url=str(view.resolve()),
        width=1280, height=800, resizable=True,
        js_api=Bridge(),
        background_color='#1e1e2e',
    )
    webview.start()
    return 0


if __name__ == '__main__':
    sys.exit(main())