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
  /* Painel de controles: sempre visivel por padrao, toggle via botao olho */
  #mk-controles { position: fixed; right: 10px; top: 70px; z-index: 9999; display: flex !important; flex-direction: column; gap: 8px; padding: 8px 10px; border-radius: 8px; background: rgba(30,30,46,0.88); border: 1px solid #45475a; box-shadow: 0 2px 10px rgba(0,0,0,0.5); }
  """

WIDGET_JS = """
<script>
  document.addEventListener('contextmenu', function(e){
    e.preventDefault();
    document.body.classList.toggle('desktop');
  }, false);

  // Initialize widget controls when pywebview is ready
  if (window.pywebview && window.pywebview.api) {
    initWidgetControls();
  } else {
    window.addEventListener("pywebviewready", initWidgetControls);
  }

    // Sync bridge test
    if(window.pywebview && window.pywebview.api){
      console.log(">>> Testing bridge test_bridge...");
      window.pywebview.api.test_bridge().then(function(v){
        console.log(">>> test_bridge() returned:", v);
      }).catch(function(e){ console.log(">>> test_bridge ERROR:", e); });
    }
    // Call initWidgetControls now if bridge is ready
    try {
      if(window.pywebview && window.pywebview.api){
        console.log(">>> Calling initWidgetControls directly...");
        initWidgetControls();
      }
    } catch(e) {
      console.log(">>> ERROR calling initWidgetControls:", e);
    }
    }
</script>
"""

RESIZE_JS = """
<script>
  (function(){
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
  function log(msg){
    try {
      if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
        window.pywebview.api.debug_log(msg);
      }
    } catch(e){}
  }
  window.addEventListener('error', function(ev){
    log('ERRO: ' + String(ev.message||'') + ' @ ' + (ev.filename||'') + ':' + (ev.lineno||''));
  });
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
            w = int(g.get('width', 0))
            h = int(g.get('height', 0))
            if w >= MIN_W and h >= MIN_H:
                return g
            return {'x': g.get('x'), 'y': g.get('y'),
                    'width': DEFAULT_W, 'height': DEFAULT_H}
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
        for p in CONHECIMENTO_DIR.rglob('*.md'):
            if p.is_file():
                late = max(late, _mtime_ns(p))
    v.append(late)
    return '-'.join(str(x) for x in v)


class Bridge:
    """Ponte JS (window.pywebview.api) -> Python."""
    def __init__(self):
        self._win = None

        self._call_count = 0
    def increment_call_count(self) -> None:
        self._call_count += 1
        print("[BRIDGE] Call count: " + str(self._call_count), flush=True)

    def get_call_count(self) -> int:
        return self._call_count

    def versao(self) -> str:
        return _versao()

    def debug_log(self, msg: str) -> None:
        msg_str = "[DEBUG_BRIDGE] " + str(msg)
        print(msg_str, flush=True)
        try:
            log_path = Path(r"C:/Users/David Jr/Documents/Default Project/EcoSystemUmGrau/docs/widget_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"{time.time():.0f} | {msg}\n")
        except Exception as e:
            print("[DEBUG_BRIDGE ERROR] " + str(e), flush=True)

    def test_bridge(self) -> str:
        """Test method to verify bridge is working."""
        print("[BRIDGE TEST] test_bridge called", flush=True)
        return "BRIDGE_OK"

    def regenerar(self) -> str:
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
        try:
            w = int(w); h = int(h)
            if w < MIN_W or h < MIN_H:
                return
            _salvar_geo({'x': int(x), 'y': int(y), 'width': w, 'height': h})
        except Exception:
            pass

    def guardar_orbGrafo(self, valor: float) -> None:
        """Salva orbGrafo no localStorage e escreve em arquivo para validacao."""
        try:
            if self._win and self._win.evaluate_js:
                self._win.evaluate_js(f"localStorage.setItem('orbGrafo', '{valor}');")
            ORB_FILE.write_text(f"{float(valor):.2f}", encoding='utf-8')
        except Exception as e:
            self.debug_log(f'[widget] Error saving orbGrafo: {e}')

    def verificar_llm(self, modelo: str, query: str) -> dict:
        """Verifica um unico LLM. Retorna {ok, saida, erro, modelo}."""
        t0 = time.time()
        try:
            import urllib.request, urllib.error
            req = urllib.request.Request(
                'https://opencode.ai/api/v1/chat/completions',
                data=json.dumps({
                    'model': modelo,
                    'messages': [{'role': 'user', 'content': query}],
                    'max_tokens': 256,
                }).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
                method='POST',
            )
            with urllib.request.urlopen(req, timeout=15) as r:
                data = json.loads(r.read().decode('utf-8'))
                saida = (data.get('choices') or [{}])[0].get('message', {}).get('content', '')
                return {'ok': True, 'modelo': modelo, 'saida': saida,
                        'ms': int((time.time() - t0) * 1000), 'erro': None}
        except Exception as e:
            return {'ok': False, 'modelo': modelo, 'saida': '',
                    'ms': int((time.time() - t0) * 1000), 'erro': str(e)}

    def processar_query_llm(self, query: str) -> dict:
        """Pipeline multi-LLM curado: tenta a cadeia ordenada por score real.

        Usa scripts/llm_feedback.py para registrar sucesso/falha e latencia
        de cada modelo, reordenando dinamicamente a cadeia. Modelos com falhas
        consecutivas sao penalizados no score.
        """
        import importlib.util
        fb_path = BASE / 'scripts' / 'llm_feedback.py'
        spec = importlib.util.spec_from_file_location('llm_feedback', fb_path)
        fb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fb)

        cadeia = fb.cadeia_ordenada()
        tentativas = []
        for modelo in cadeia:
            r = self.verificar_llm(modelo, query)
            tentativas.append(r)
            fb.registrar(modelo, r['ok'], r['ms'])
            self.debug_log(f"[llm] {modelo}: ok={r['ok']} ms={r['ms']} erro={r['erro']}")
            if r['ok']:
                return {'ok': True, 'modelo': modelo, 'saida': r['saida'],
                        'tentativas': tentativas, 'cadeia': cadeia}
        self.debug_log(f"[llm] todos os {len(cadeia)} modelos falharam para: {query[:80]}")
        return {'ok': False, 'modelo': None, 'saida': '',
                'tentativas': tentativas, 'cadeia': cadeia}

    def perguntar(self, query: str) -> str:
        """Ponto de entrada do widget para o pipeline multi-LLM.

        Chamado pelo frontend via window.pywebview.api.perguntar(texto).
        Retorna a resposta do primeiro LLM que responder com sucesso.
        """
        if not query or not query.strip():
            return json.dumps({'ok': False, 'erro': 'query vazia'})
        try:
            resultado = self.processar_query_llm(query.strip())
            self.debug_log(f"[llm] pergunta: {query[:80]} | ok={resultado['ok']} | modelo={resultado['modelo']}")
            return json.dumps(resultado, ensure_ascii=False)
        except Exception as e:
            self.debug_log(f"[llm] erro fatal: {e}")
            return json.dumps({'ok': False, 'erro': str(e)})

    def comando_grafo(self, ultimo_ts: int = 0) -> dict:
        try:
            f = BASE / 'docs' / 'comando_grafo.json'
            if not f.exists():
                return {}
            data = json.loads(f.read_text(encoding='utf-8'))
            ts = int(data.get('ts', 0))
            if ts <= int(ultimo_ts) or not data.get('filtro'):
                return {}
            return data
        except Exception as e:
            print(f'[widget] comando_grafo: {e}')
            return {}


WIDGET_JS_EXTRA = """
<script>
    console.log(">>> WIDGET_JS_EXTRA SCRIPT STARTED");
        // Test: write to localStorage and check
        try {
          localStorage.setItem("widget_js_test", Date.now().toString());
          console.log(">>> localStorage write OK");
        } catch(e) { console.log(">>> localStorage ERROR:", e); }
        // Force initWidgetControls call with error handling
        setTimeout(function(){
          try {
            console.log(">>> Timeout: calling initWidgetControls");
            initWidgetControls();
            console.log(">>> initWidgetControls returned");
          } catch(e) { console.log(">>> initWidgetControls ERROR:", e); }
        }, 100);
        // Write test file via fetch to /test endpoint
        fetch("/test_js_exec", {method: "POST", body: "OK"}).then(function(){
          console.log(">>> Test endpoint called");
        }).catch(function(e){ console.log(">>> FETCH ERROR:", e); });
        // Simple bridge accessibility test
        try {
          var hasPywebview = typeof window.pywebview !== "undefined";
          var hasApi = hasPywebview && typeof window.pywebview.api !== "undefined";
          var hasDebugLog = hasApi && typeof window.pywebview.api.debug_log === "function";
          console.log(">>> Bridge check: pywebview=" + hasPywebview + ", api=" + hasApi + ", debug_log=" + hasDebugLog);
          if(hasDebugLog){ window.pywebview.api.debug_log("BRIDGE_ACCESSIBLE"); }
        } catch(e) { console.log(">>> BRIDGE CHECK ERROR:", e); }
        // localStorage test
        try {
          localStorage.setItem("js_test_executed", "true");
          console.log(">>> localStorage test set");
        } catch(e) { console.log(">>> localStorage ERROR:", e); }
        // Alert to verify JS execution
        alert("JS EXECUTING - check this alert");
        // Write test file to verify JS execution
        try {
          fetch("test_js_execution.txt", {method: "POST", body: "JS_EXECUTED"});
        } catch(e) { console.log(">>> FETCH ERROR:", e); }
        console.log(">>> WIDGET_JS_EXTRA: About to call initWidgetControls");
        // Test bridge with file write
        if(window.pywebview && window.pywebview.api){
          console.log(">>> Testing bridge write_file...");
          window.pywebview.api.debug_log("JS_BRIDGE_TEST: Widget JS executed");
        }
    console.log(">>> Document readyState:", document.readyState);
    console.log(">>> pywebview:", window.pywebview);
    console.log(">>> pywebview.api:", window.pywebview && window.pywebview.api);
    console.log(">>> WIDGET_JS_EXTRA LOADED AND EXECUTING");
    // DEBUG LOG
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: START");
    }

  function initWidgetControls() {
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      try {
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: initWidgetControls called");
        console.log(">>> initWidgetControls START");
        console.log(">>> pywebview:", window.pywebview);
        console.log(">>> pywebview.api:", window.pywebview && window.pywebview.api);
        if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
          window.pywebview.api.debug_log("WIDGET_JS_EXTRA: initWidgetControls BRIDGE TEST");
        }
        // Direct bridge test
        if(window.pywebview && window.pywebview.api){
          window.pywebview.api.versao().then(function(v){ console.log("versao:", v); });
        }
    console.log("INIT WIDGET CONTROLS RUNNING");
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: initWidgetControls CONSOLE LOG TEST");
        // Direct synchronous bridge test
        try {
          console.log(">>> Testing bridge versao()...");
          window.pywebview.api.versao().then(function(v) {
            console.log(">>> versao() returned:", v);
            if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
              window.pywebview.api.debug_log("WIDGET_JS_EXTRA: versao() returned " + v);
        // Test test_bridge method
        try {
          console.log(">>> Testing bridge test_bridge()...");
          window.pywebview.api.test_bridge().then(function(v) {
            console.log(">>> test_bridge() returned:", v);
            if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
              window.pywebview.api.debug_log("WIDGET_JS_EXTRA: test_bridge() returned " + v);
            }
          }).catch(function(e) { console.log(">>> test_bridge() ERROR:", e); });
        } catch(e) { console.log(">>> SYNC ERROR test_bridge:", e); }
            }
          }).catch(function(e) { console.log(">>> versao() ERROR:", e); });
        } catch(e) { console.log(">>> SYNC ERROR:", e); }
    }
    }
      } catch(e) { console.log(">>> initWidgetControls ERROR:", e); }

  (function(){
    // ERROR HANDLER GLOBAL
    window.addEventListener('error', function(ev){
      if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
        window.pywebview.api.debug_log('JS_ERROR: ' + (ev.message||'') + ' @ ' + (ev.filename||'') + ':' + (ev.lineno||''));
      }
    });
    window.addEventListener('unhandledrejection', function(ev){
      if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
        window.pywebview.api.debug_log('UNHANDLED_REJECTION: ' + (ev.reason||(ev.reason&&ev.reason.message)||''));
      }
    });
    var cores = {
      fundo: '#1e1e2e', borda: '#45475a', destaque: '#cba6f7',
      texto: '#cdd6f4', texto2: '#a6adc8'
    };

    function mkEl(tag, st) {
      var el = document.createElement(tag);
      if (st) el.style.cssText = st;
      return el;
    }

    // ---- Slider de velocidade (0.25x .. 3x) ----
    var velSlider = mkEl('input');
    velSlider.type = 'range';
    velSlider.min = '0.25'; velSlider.max = '3'; velSlider.step = '0.05';
    velSlider.value = localStorage.getItem('velGrafo') || '1';
    velSlider.style.cssText = 'width:110px;accent-color:#cba6f7;cursor:pointer;';
    velSlider.title = 'Velocidade do movimento';
    velSlider.addEventListener('input', function(){
      var v = parseFloat(velSlider.value);
      localStorage.setItem('velGrafo', String(v));
      try { if (typeof _aplicarVelocidade === 'function') _aplicarVelocidade(v); }
      catch(e){}
      velLbl.textContent = 'x' + v.toFixed(2);
    });

    var velLbl = mkEl('span');
    velLbl.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';min-width:34px;text-align:right;';
    velLbl.textContent = 'x' + parseFloat(velSlider.value).toFixed(2);

    var velGroup = mkEl('div');
    velGroup.style.cssText = 'display:flex;align-items:center;gap:6px;';
    velGroup.appendChild(mkEl('span', 'font-size:10px;color:' + cores.texto2 + ';'));
    velGroup.firstChild.textContent = 'Velocidade';
    velGroup.appendChild(velSlider);
    velGroup.appendChild(velLbl);

    // ---- Slider de amplitude da deriva orbital (0 .. 3x) ----
    var orbSlider = mkEl('input');
    orbSlider.type = 'range';
    orbSlider.min = '0'; orbSlider.max = '3'; orbSlider.step = '0.1';
    orbSlider.value = localStorage.getItem('orbGrafo') || '1';
    orbSlider.style.cssText = 'width:110px;accent-color:#cba6f7;cursor:pointer;';
    orbSlider.title = 'Amplitude da flutuacao orbital';
    orbSlider.addEventListener('input', function(){
      var o = parseFloat(orbSlider.value);
      localStorage.setItem('orbGrafo', String(o));
      try { if (typeof _aplicarOrbita === 'function') _aplicarOrbita(o); }
      catch(e){}
      orbLbl.textContent = 'x' + o.toFixed(1);
      if (window.pywebview && window.pywebview.api && window.pywebview.api.guardar_orbGrafo) {
        try { window.pywebview.api.guardar_orbGrafo(o); } catch(e){}
      }
    });

    var orbLbl = mkEl('span');
    orbLbl.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';min-width:34px;text-align:right;';
    orbLbl.textContent = 'x' + parseFloat(orbSlider.value).toFixed(1);

    var orbGroup = mkEl('div');
    orbGroup.style.cssText = 'display:flex;align-items:center;gap:6px;';
    orbGroup.appendChild(mkEl('span', 'font-size:10px;color:' + cores.texto2 + ';'));
    orbGroup.firstChild.textContent = 'Orbita';
    orbGroup.appendChild(orbSlider);
    orbGroup.appendChild(orbLbl);

    // ---- Busca por palavra no grafo ----
    var buscaInput = mkEl('input');
    buscaInput.type = 'text';
    buscaInput.placeholder = 'Buscar no grafo...';
    buscaInput.style.cssText =
      'width:100%;background:' + cores.fundo + ';color:' + cores.texto + ';' +
      'border:1px solid ' + cores.borda + ';border-radius:4px;font-size:11px;' +
      'padding:4px 6px;box-sizing:border-box;';
    buscaInput.addEventListener('input', function(){
      var termo = buscaInput.value.trim();
      try {
        if (typeof destacar === 'function') {
          if (termo) destacar('txt', termo, cores.destaque);
          else if (typeof limpar === 'function') limpar();
        }
      } catch(e){}
    });
    var buscaGroup = mkEl('div');
    buscaGroup.style.cssText = 'display:flex;align-items:center;gap:6px;';
    buscaGroup.appendChild(mkEl('span', 'font-size:10px;color:' + cores.texto2 + ';'));
    buscaGroup.firstChild.textContent = 'Busca';
    buscaGroup.appendChild(buscaInput);

    // ---- Presets de tamanho do quadro ----
    var tamanhos = [
      { nome: 'Compacto',  w: 720,  h: 480 },
      { nome: 'Media',     w: 1024, h: 640 },
      { nome: 'Padrao',    w: 1280, h: 800 },
      { nome: 'Grande',    w: 1600, h: 1000 },
      { nome: 'Maxima',    w: 1920, h: 1200 },
    ];
    var tamSel = mkEl('select');
    tamSel.style.cssText =
      'background:' + cores.fundo + ';color:' + cores.texto + ';border:1px solid ' +
      cores.borda + ';border-radius:4px;font-size:11px;padding:2px 4px;cursor:pointer;';
    tamanhos.forEach(function(t){
      var op = mkEl('option');
      op.value = t.w + 'x' + t.h;
      op.textContent = t.nome + ' (' + t.w + 'x' + t.h + ')';
      tamSel.appendChild(op);
    });
    tamSel.addEventListener('change', function(){
      var wh = tamSel.value.split('x');
      localStorage.setItem('tamGrafo', tamSel.value);
      try {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.redimensionar) {
          window.pywebview.api.redimensionar(parseInt(wh[0],10), parseInt(wh[1],10));
        }
      } catch(e){}
    });
    var tamLbl = mkEl('span');
    tamLbl.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';';
    tamLbl.textContent = 'Quadro';
    var tamGroup = mkEl('div');
    tamGroup.style.cssText = 'display:flex;align-items:center;gap:6px;';
    tamGroup.appendChild(tamLbl);
    tamGroup.appendChild(tamSel);

    // ---- Botoes de layout ----
    var ctrl = mkEl('div');
    ctrl.id = 'mk-labels';
    ctrl.title = 'Alternar visibilidade das etiquetas';
    ctrl.style.cssText =
      'width:30px;height:30px;border-radius:4px;cursor:pointer;' +
      'display:flex;align-items:center;justify-content:center;' +
      'font-size:14px;user-select:none;color:' + cores.destaque + ';' +
      'background:#313244;border:1px solid ' + cores.destaque + ';';
    ctrl.innerHTML = 'T';

    var menuBtn = mkEl('div');
    menuBtn.id = 'mk-menu-btn';
    menuBtn.title = 'Mostrar/ocultar menus';
    menuBtn.style.cssText =
      'width:30px;height:30px;border-radius:4px;cursor:pointer;' +
      'display:flex;align-items:center;justify-content:center;' +
      'font-size:14px;user-select:none;color:' + cores.destaque + ';' +
      'background:#313244;border:1px solid ' + cores.destaque + ';';
    menuBtn.innerHTML = '\\u2630';

    var layoutGroup = mkEl('div');
    layoutGroup.style.cssText =
      'display:flex;gap:6px;border:1px solid ' + cores.destaque + ';' +
      'border-radius:6px;padding:3px;background:#313244;';
    layoutGroup.appendChild(ctrl);
    layoutGroup.appendChild(menuBtn);

    // ---- Grupo 3D: toggle + slider de intensidade ----
    var btn3D = mkEl('div');
    btn3D.id = 'mk-btn-3d';
    btn3D.title = 'Alternar modo 3D (onda viajante de profundidade)';
    btn3D.style.cssText =
      'width:30px;height:30px;border-radius:4px;cursor:pointer;' +
      'display:flex;align-items:center;justify-content:center;' +
      'font-size:14px;user-select:none;transition:all .3s ease;' +
      'background:#313244;border:1px solid ' + cores.destaque + ';';
    btn3D.innerHTML = '\\u1F34D'; // onda de serpente (3D ativo)
    var modo3DAtivo = (typeof localStorage !== 'undefined' && localStorage.getItem('modo3D') === 'true');
    btn3D._ativo = modo3DAtivo;
    btn3D.style.boxShadow = btn3D._ativo ? '0 0 12px ' + cores.destaque : 'none';
    btn3D.addEventListener('click', function() {
      btn3D._ativo = !btn3D._ativo;
      btn3D.innerHTML = btn3D._ativo ? '\\u1F34D' : '\\u2605'; // serpente vs estrela
      btn3D.style.background = btn3D._ativo ? cores.fundo : '#313244';
      btn3D.style.boxShadow = btn3D._ativo ? '0 0 14px ' + cores.destaque : 'none';
      if (typeof _toggle3D === 'function') _toggle3D(btn3D._ativo);
    });

    // Botao flash
    var btnFlash = mkEl('div');
    btnFlash.id = 'mk-btn-flash';
    btnFlash.title = 'Alternar flash nos cliques nos nos';
    btnFlash.style.cssText = btn3D.style.cssText;
    btnFlash.innerHTML = '\\u26A1';
    btnFlash._ativo = (typeof localStorage !== 'undefined' && localStorage.getItem('flashEnabled') !== 'false');
    btnFlash.style.boxShadow = btnFlash._ativo ? '0 0 12px ' + cores.destaque : 'none';
    btnFlash.addEventListener('click', function() {
      btnFlash._ativo = !btnFlash._ativo;
      btnFlash.style.opacity = btnFlash._ativo ? '1' : '0.4';
      btnFlash.style.boxShadow = btnFlash._ativo ? '0 0 14px ' + cores.destaque : 'none';
      if (typeof _toggleFlash === 'function') _toggleFlash(btnFlash._ativo);
    });

    var label3D = mkEl('span');
    label3D.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';min-width:40px;';
    label3D.textContent = '3D';
    var slider3D = mkEl('input');
    slider3D.type = 'range';
    slider3D.min = '0';
    slider3D.max = '3';
    slider3D.step = '0.1';
    slider3D.value = String(parseFloat((typeof localStorage !== 'undefined' && localStorage.getItem('waveIntensidade')) || '1') || 1);
    slider3D.style.cssText = 'width:100px;accent-color:' + cores.destaque + ';';
    slider3D.addEventListener('input', function() {
      var v = parseFloat(slider3D.value);
      if (typeof _aplicarWaveIntensidade === 'function') _aplicarWaveIntensidade(v);
    });
    var grupo3D = mkEl('div');
    grupo3D.style.cssText = 'display:flex;align-items:center;gap:6px;';
    grupo3D.appendChild(label3D);
    grupo3D.appendChild(slider3D);
    grupo3D.appendChild(btn3D);
    grupo3D.appendChild(btnFlash);

    // ---- Botao reset (🔄) alinhado ao lado do painel ----
    var btnReset = mkEl('div');
    btnReset.id = 'mk-btn-reset';
    btnReset.title = 'Resetar preferencias do grafo (tema, velocidade, orbita) e recarregar';
    btnReset.style.cssText =
      'width:28px;height:28px;border-radius:4px;cursor:pointer;' +
      'display:flex;align-items:center;justify-content:center;' +
      'font-size:14px;user-select:none;color:' + cores.destaque + ';' +
      'background:#313244;border:1px solid ' + cores.destaque + ';';
    btnReset.innerHTML = '\\u21BB'; // seta ciclo (reset)
    btnReset.addEventListener('click', function() {
      if (confirm('\\u1EAFResetar todas as preferencias do cerebro para o padrao?')) {
        var chaves = ['temaGrafo','modo3D','flashEnabled','waveIntensidade','labelsAnimated','orbAmplGlobal'];
        chaves.forEach(function(k) { try { localStorage.removeItem(k); } catch(e){} });
        location.reload();
      }
    });

    // ---- BANNER DE VERSAO - aparece por 4 segundos ----
    (function() {
      var banner = mkEl('div');
      banner.style.cssText = 'position:fixed;top:20px;left:50%;transform:translateX(-50%);z-index:99999;' +
        'background:#cba6f7;color:#000;padding:8px 20px;border-radius:8px;font-size:13px;font-weight:bold;' +
        'box-shadow:0 4px 20px rgba(0,0,0,0.6);pointer-events:none;';
      banner.textContent = 'Cerebro Vivo v2 — Temas + Filtros — ' + new Date().toLocaleString('pt-BR');
      document.body.appendChild(banner);
      setTimeout(function() { banner.style.opacity = '0'; banner.style.transition = 'opacity 1s'; }, 3000);
      setTimeout(function() { if (banner.parentNode) banner.parentNode.removeChild(banner); }, 4000);
    })();

    // ---- Seletor de tema estetico (Neon / Glow / Calmo / Padrao) ----
    var temaSel = mkEl('select');
    temaSel.style.cssText =
      'background:' + cores.fundo + ';color:' + cores.texto + ';border:1px solid ' +
      cores.borda + ';border-radius:4px;font-size:11px;padding:2px 4px;cursor:pointer;';
    [
      { nome: 'Neon',    valor: 'neon',  icone: '\\u26A1' },
      { nome: 'Glow',    valor: 'glow',  icone: '\\u2600' },
      { nome: 'Calmo',   valor: 'calm',  icone: '\\uD83C\\uDF3F' },
      { nome: 'Padrao',  valor: 'padrao',icone: '\\u25C9' }
    ].forEach(function(t){
      var op = mkEl('option');
      op.value = t.valor;
      op.textContent = t.icone + ' ' + t.nome;
      temaSel.appendChild(op);
    });
    var temaSalvo = localStorage.getItem('temaGrafo') || 'glow';
    temaSel.value = temaSalvo;
    temaSel.addEventListener('change', function(){
      try { if (typeof aplicarTema === 'function') aplicarTema(temaSel.value); }
      catch(e){}
    });
    var temaLbl = mkEl('span');
    temaLbl.style.cssText = 'font-size:10px;color:' + cores.texto2 + ';';
    temaLbl.textContent = 'Tema';
    var temaGroup = mkEl('div');
    temaGroup.style.cssText = 'display:flex;align-items:center;gap:6px;';
    temaGroup.appendChild(temaLbl);
    temaGroup.appendChild(temaSel);

    var painel = mkEl('div');
    painel.id = 'mk-controles';
    painel.title = 'Controles do cerebro';
    painel.style.cssText =
      'position:fixed;right:10px;z-index:9999;display:flex;' +
      'flex-direction:column;gap:8px;padding:8px 10px;border-radius:8px;' +
      'background:rgba(30,30,46,0.88);border:1px solid ' + cores.borda + ';' +
      'box-shadow:0 2px 10px rgba(0,0,0,0.5);';
    painel.appendChild(temaGroup);
    painel.appendChild(velGroup);
    painel.appendChild(orbGroup);
    painel.appendChild(grupo3D);
    painel.appendChild(flashGroup);
    painel.appendChild(buscaGroup);
    painel.appendChild(tamGroup);
    layoutGroup.appendChild(btnReset);
    painel.appendChild(layoutGroup);
    
    if(window.pywebview && window.pywebview.api && window.pywebview.api.debug_log){
      window.pywebview.api.debug_log("WIDGET_JS_EXTRA: appending painel");
    }
document.body.appendChild(painel);

    // ---- Botao hide panel (olho) ----
    var painelToggle = mkEl('div');
    painelToggle.id = 'mk-painel-toggle';
    painelToggle.title = 'Ocultar/mostrar painel de controles';
    painelToggle.style.cssText =
      'position:fixed;top:22px;left:10px;z-index:99998;width:28px;height:28px;' +
      'border-radius:4px;cursor:pointer;display:flex;align-items:center;' +
      'justify-content:center;font-size:14px;user-select:none;' +
      'background:rgba(30,30,46,0.7);border:1px solid ' + cores.borda + ';';
    painelToggle.innerHTML = '\\u1F441'; // olho
    painelToggle._visivel = true;
    painelToggle.onclick = function() {
      painelToggle._visivel = !painelToggle._visivel;
      painel.style.display = painelToggle._visivel ? 'flex' : 'none';
      painelToggle.innerHTML = painelToggle._visivel ? '\\u1F441' : '\\u1F442';
    };
    document.body.appendChild(painelToggle);

    function reposicionarPainel() {
      var hdr = document.getElementById('header');
      var topo = 22;
      try {
        if (hdr && hdr.offsetParent !== null) {
          var r = hdr.getBoundingClientRect();
          if (r && r.bottom > 0) topo = Math.round(r.bottom) + 10;
        }
      } catch(e){}
      painel.style.top = topo + 'px';
    }
    window.addEventListener('resize', reposicionarPainel);
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      setTimeout(reposicionarPainel, 400);
    } else {
      document.addEventListener('DOMContentLoaded', function(){ setTimeout(reposicionarPainel, 400); });
    }
    window.addEventListener('pywebviewready', function(){ setTimeout(reposicionarPainel, 400); });
    document.addEventListener('contextmenu', function(){ setTimeout(reposicionarPainel, 80); });

    function aplicarLabels() {
      if (typeof nodes === 'undefined') return;
      var oculto = localStorage.getItem('labelsOcultos') !== 'false';
      var tam = oculto ? 0 : 11;
      var upd = nodes.get().map(function(n){ return { id: n.id, font: Object.assign({}, n.font, { size: tam }) }; });
      nodes.update(upd);
    }

    ctrl.onmousedown = function(e) {
      e.preventDefault(); e.stopPropagation();
      // Toggle etiquetas: 'false' explicito = mostrar; qualquer outro = oculto
      var oculto = localStorage.getItem('labelsOcultos') !== 'false';
      localStorage.setItem('labelsOcultos', oculto ? 'false' : 'true');
      aplicarLabels();
      ctrl.style.opacity = oculto ? '1' : '0.55';
    };

    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      aplicarLabels();
    } else {
      document.addEventListener('DOMContentLoaded', aplicarLabels);
    }
    window.addEventListener('pywebviewready', aplicarLabels);

    var lastCmdTs = 0;
    function buscarComandoVoz() {
      if (!window.pywebview || !window.pywebview.api || !window.pywebview.api.comando_grafo) return;
      window.pywebview.api.comando_grafo(lastCmdTs).then(function(cmd) {
        if (cmd && cmd.filtro) {
          lastCmdTs = parseInt(cmd.ts || 0, 10);
          if (typeof destacar === 'function') {
            destacar(cmd.filtro, cmd.valor, cmd.cor);
          }
        }
      }).catch(function(){});
    }
    setInterval(buscarComandoVoz, 2500);
    if (document.readyState !== 'loading') { buscarComandoVoz(); }
    else { document.addEventListener('DOMContentLoaded', buscarComandoVoz); }

    function aplicarMenus() {
      var oculto = localStorage.getItem('menuOculto') === 'true';
      var hdr = document.getElementById('header');
      var painelLateral = document.getElementById('painel');
      var net = document.getElementById('net');
      if (hdr) hdr.style.display = oculto ? 'none' : '';
      if (painelLateral && oculto) painelLateral.classList.remove('visivel');
      if (net) net.style.height = oculto ? '100vh' : '';
      menuBtn.innerHTML = oculto ? '\\u2630' : '\\u2026';
      menuBtn.style.opacity = oculto ? '0.55' : '1';
      if (typeof network !== 'undefined' && network.redraw) { network.redraw(); }
      if (typeof reposicionarPainel === 'function') {
        setTimeout(reposicionarPainel, 60);
      }
    }
    menuBtn.onmousedown = function(e) {
      e.preventDefault(); e.stopPropagation();
      var nao = localStorage.getItem('menuOculto') !== 'true';
      localStorage.setItem('menuOculto', nao ? 'true' : 'false');
      aplicarMenus();
    };
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      aplicarMenus();
    } else {
      document.addEventListener('DOMContentLoaded', aplicarMenus);
    }
    window.addEventListener('pywebviewready', aplicarMenus);

    function aplicarPersistidos() {
      try {
        if (typeof _aplicarVelocidade === 'function') {
          var v = parseFloat(localStorage.getItem('velGrafo') || '1');
          _aplicarVelocidade(v);
        }
        if (typeof _aplicarOrbita === 'function') {
          var o = parseFloat(localStorage.getItem('orbGrafo') || '1');
          _aplicarOrbita(o);
        }
        if (typeof _atualizarStats === 'function') _atualizarStats();
      } catch(e){}
    }
    if (document.readyState === 'complete' || document.readyState === 'interactive') {
      setTimeout(aplicarPersistidos, 1500);
    } else {
      document.addEventListener('DOMContentLoaded', function(){ setTimeout(aplicarPersistidos, 1500); });
    }
    window.addEventListener('pywebviewready', aplicarPersistidos);
  })();
  }
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
