"""widget_controle_jarvis.py — Janela flutuante que materializa a voz do Jarvis no PC.

Essa janela e a voice UI do opencode-desktop: reflete e controla a narração que o
narrador_desktop.py extrai do SQLite e fala via vox_audio (pt-BR, AntonioNeural),
alem de ligar o microfone (dialogo.py --modo vad). Quando o Jarvis esta falando,
o widget mostra "LUNO FALANDO" + o texto corrente.

Arquitetura Python-Driven (robusta, backend-independente):
  - O Python polleia o estado (arquivos de estado + PIDs) e empurra UI via
    win.evaluate_js("applyState(JSON)") — funciona sem window.pywebview global.
  - Os cliques do JS vao pro localStorage; o Python detecta via evaluate_js
    polling (nao depende de window.pywebview.api, que eh unreliable neste backend).
  - Drag da barra superior: JS escreve posicao no localStorage; Python chama win.move.

Motivo da arquitetura (bug aprendido): em pywebview 6.2.1 + WebView2, passar
shadow=False ou depender da global window.pywebview.api deixa de funcionar.
O evaluate_js (Python->JS) e localStorage (JS->Python) sao confiaveis ao passo.

Uso:
  python scripts/widget_controle_jarvis.py        (console visivel)
  pythonw scripts/widget_controle_jarvis.py       (sem console)
  $ controle  (via opencode.jsonc -> scripts/controle.bat -> pythonw)
"""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

_NO_CONSOLE = getattr(subprocess, "CREATE_NO_WINDOW", 0)

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

# --- Arquivos de estado do ecossistema (fonte unica) ---
CONTROLE = ROOT / "runtime" / "narracao_estado.json"     # voz: {ativo, pausado}
NARRADOR_PID = ROOT / "runtime" / "narrador.pid"
NARRADOR = SCRIPTS / "narrador_desktop.py"
JARVIS_AUDIO = SCRIPTS / "jarvis_audio.py"               # CLI de controle existente

# --- Estado de microfone (conveno runtime/*.json) ---
MIC_ESTADO = ROOT / "runtime" / "mic_estado.json"
MIC_PID = ROOT / "runtime" / "mic.pid"
DIALOGO = SCRIPTS / "dialogo.py"

LOG_NARRADOR = SCRIPTS / "narrador_desktop_log.txt"      # para texto corrente da fala

# --- Geometria da janela ---
GEO_FILE = ROOT / "runtime" / "widget_controle_geometria.json"

# --- Atalho de inicialização automática ---
ATALHO_WINDOWS = ROOT / "runtime" / "jarvis_atalho.lnk"

# --- Atalho de inicialização automática ---
ATALHO_WINDOWS = ROOT / "runtime" / "jarvis_atalho.lnk"
VIEW_COPY = ROOT / "docs" / "widget_controle.html"
ICON_PATH = ROOT / "assets" / "jarvis.ico"
DEFAULT_W, DEFAULT_H = 220, 284
TITLE = "Jarvis Controle"
BG = "#1e1e2e"


# ============================================================
# Estado de arquivo (atomic write: tmp + replace)
# ============================================================

def _atomic_write(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    try:
        tmp.replace(path)
    except OSError:
        import os
        os.replace(tmp, path)


# ============================================================
# Leituras de estado (visao unificada — fonte unica de verdade)
# ============================================================

def ler_estado_voz():
    try:
        if CONTROLE.exists():
            d = json.loads(CONTROLE.read_text(encoding="utf-8"))
            return bool(d.get("ativo", True)), bool(d.get("pausado", False))
    except Exception:
        pass
    return True, False


def processo_vivo(pid_path: Path):
    try:
        if pid_path.exists():
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            if pid > 0:
                out = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True, creationflags=_NO_CONSOLE, text=True, timeout=10).stdout
                return str(pid) in out
    except Exception:
        pass
    return False


def narrador_rodando():
    return processo_vivo(NARRADOR_PID)


def tts_ativo():
    """True se houver processo vox_audio.py falar em execucao."""
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/NH"],
            capture_output=True, creationflags=_NO_CONSOLE, text=True, timeout=15).stdout
        for linha in out.splitlines():
            if "vox_audio.py" in linha and "falar" in linha:
                return True
    except Exception:
        pass
    return False


def mic_ativo():
    try:
        if MIC_ESTADO.exists():
            d = json.loads(MIC_ESTADO.read_text(encoding="utf-8"))
            if not d.get("ativo", False):
                return False
    except Exception:
        return False
    return processo_vivo(MIC_PID)


def ultima_fala():
    """Texto corrente que o Jarvis esta falando (ultima linha 'falando' do log)."""
    try:
        if LOG_NARRADOR.exists():
            for l in reversed(LOG_NARRADOR.read_text(encoding="utf-8", errors="replace").splitlines()):
                lk = l.lower()
                if "falando (" in lk:
                    idx = l.find(":")
                    if idx > 0:
                        return l[idx + 1:].strip()[:140]
    except Exception:
        pass
    return ""


def estado_unificado():
    at, pa = ler_estado_voz()
    return {
        "voz": at and not pa,
        "ativo": at,
        "pausado": pa,
        "mic": mic_ativo(),
        "narrador": narrador_rodando(),
        "tts_ativo": tts_ativo(),
        "texto": ultima_fala() if tts_ativo() else "",
        "ts": int(time.time()),
    }


# ============================================================
# Acoes de controle (rodam em background via threads)
# ============================================================

def _detached():
    return getattr(subprocess, "DETACHED_PROCESS", 0) | subprocess.CREATE_NEW_PROCESS_GROUP | _NO_CONSOLE


def _thread(target, *args):
    threading.Thread(target=target, args=args, daemon=True).start()


def cmd_voz(ativar: bool):
    try:
        if ativar:
            subprocess.run([sys.executable, str(JARVIS_AUDIO), "on"],
                           cwd=str(ROOT), capture_output=True, creationflags=_NO_CONSOLE, timeout=35)
        else:
            subprocess.run([sys.executable, str(JARVIS_AUDIO), "stop"],
                           cwd=str(ROOT), capture_output=True, creationflags=_NO_CONSOLE, timeout=20)
            subprocess.run([sys.executable, str(JARVIS_AUDIO), "off"],
                           cwd=str(ROOT), capture_output=True, creationflags=_NO_CONSOLE, timeout=20)
    except Exception as e:
        print(f"[widget] erro voz({'on' if ativar else 'off'}): {e}", flush=True)


def cmd_interromper_fala():
    try:
        subprocess.run([sys.executable, str(JARVIS_AUDIO), "stop"],
                       cwd=str(ROOT), capture_output=True, creationflags=_NO_CONSOLE, timeout=20)
    except Exception as e:
        print(f"[widget] erro stop: {e}", flush=True)


def cmd_mic(ativar: bool):
    if ativar:
        if mic_ativo():
            return
        try:
            proc = subprocess.Popen(
                [sys.executable, str(DIALOGO), "--modo", "vad"],
                cwd=str(ROOT), creationflags=_detached(),
                close_fds=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            MIC_PID.write_text(str(proc.pid), encoding="utf-8")
            _atomic_write(MIC_ESTADO, {"ativo": True, "timestamp": int(time.time())})
        except Exception as e:
            print(f"[widget] erro mic on: {e}", flush=True)
    else:
        try:
            if MIC_PID.exists():
                pid = int(MIC_PID.read_text(encoding="utf-8").strip())
                if pid > 0:
                    subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"],
                                   capture_output=True, creationflags=_NO_CONSOLE, timeout=8)
        except Exception as e:
            print(f"[widget] erro mic off (kill): {e}", flush=True)
        try:
            MIC_PID.unlink(missing_ok=True)
        except Exception:
            pass
        _atomic_write(MIC_ESTADO, {"ativo": False, "timestamp": int(time.time())})


# ============================================================
# Geometria da janela
# ============================================================

def _screen_area():
    try:
        import ctypes
        u = ctypes.windll.user32
        return int(u.GetSystemMetrics(0)), int(u.GetSystemMetrics(1))
    except Exception:
        return None


def _clamp_geo(data: dict) -> dict:
    w = int(data.get("width", DEFAULT_W))
    h = int(data.get("height", DEFAULT_H))
    x, y = data.get("x"), data.get("y")
    area = _screen_area()
    if area:
        sw, sh = area
        if sw > 160 and sh > 120:
            w = max(120, min(int(w), sw))
            h = max(120, min(int(h), sh))
            if x is not None:
                x = max(0, min(int(x), sw - 40))
            if y is not None:
                y = max(0, min(int(y), sh - 40))
    return {"x": x, "y": y, "width": w, "height": h}


def _carregar_geo() -> dict:
    if not GEO_FILE.exists():
        return {"x": None, "y": None, "width": DEFAULT_W, "height": DEFAULT_H}
    try:
        raw = GEO_FILE.read_text(encoding="utf-8")
        d = json.loads(raw) if raw.strip() else {}
    except Exception:
        d = {}
    return _clamp_geo({"x": d.get("x"), "y": d.get("y"),
                       "width": int(d.get("width", DEFAULT_W)),
                       "height": int(d.get("height", DEFAULT_H))})


def _minimizar(win):
    """Minimiza a janela. Tenta via pywebview, fallback para hide/show com estado persistido."""
    try:
        # Tenta minimizar via JavaScript (pywebview API)
        win.evaluate_js("window.pywebview.minimize()")
        return
    except Exception:
        pass
    # Fallback: esconde a janela e marca estado para restauração posterior
    try:
        win.hide()
        _atomic_write(ROOT / "runtime" / "widget_minimizado.json", {"minimizado": True, "timestamp": int(time.time())})
        print("[widget] Janela minimizada (hide). Use o atalho ou reabra via 'controle' para restaurar.", flush=True)
    except Exception as e:
        print(f"[widget] erro minimizar: {e}", flush=True)


def _restaurar_se_minimizado():
    """Verifica se janela estava minimizada e restaura (chamado no main)."""
    flag = ROOT / "runtime" / "widget_minimizado.json"
    if flag.exists():
        try:
            d = json.loads(flag.read_text(encoding="utf-8"))
            if d.get("minimizado"):
                flag.unlink(missing_ok=True)
                return True
        except Exception:
            pass
    return False

def _guardar_geo(win):
    try:
        win.evaluate_js("""
          (function(){
            var x=window.screenX||0,y=window.screenY||0,w=window.innerWidth||0,h=window.innerHeight||0;
            window.pywebview=null;  /* noop de compat */
            var st=window.__sempre_topo||True;
            localStorage.setItem('jarvis_geo', JSON.stringify({x:x,y:y,width:w,height:h,sempre_topo:st}));
          })();
        """)
    except Exception:
        pass


# ============================================================
# HTML / CSS / JS (self-contained; Python-Driven via evaluate_js)
# ============================================================

HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="icon" href="jarvis.ico" type="image/x-icon">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{overflow:hidden;font-family:'Segoe UI',system-ui,sans-serif;
background:#1e1e2e;color:#cdd6f4;width:100%;height:100%;}
.topbar{background:#313244;height:22px;cursor:move;
display:flex;align-items:center;justify-content:space-between;
padding:0 8px;font-size:11px;color:#a6adc8;user-select:none;}
  .drag{flex:1;cursor:move;min-height:22px;}
.title{display:flex;align-items:center;gap:5px;font-weight:600;}
.close{background:#f38ba8;width:14px;height:14px;border-radius:3px;
display:flex;align-items:center;justify-content:center;
font-size:10px;line-height:1;cursor:pointer;color:#1e1e2e;font-weight:bold;}
.controls{padding:12px;display:flex;flex-direction:column;gap:10px;}
.btn{display:flex;align-items:center;justify-content:space-between;
padding:8px 10px;border:none;border-radius:6px;cursor:pointer;
font-size:13px;background:#313244;color:#cdd6f4;transition:.15s;}
.btn:hover{background:#45475a;}
.btn.on{background:#a6e3a1;color:#1e1e2e;}
.btn.off{background:#f38ba8;color:#1e1e2e;}
.btn.stop{background:#f28465;color:#1e1e2e;}
.sw{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px;}
.sw.on{background:#a6e3a1;box-shadow:0 0 6px #a6e3a1;}
.sw.off{background:#f38ba8;}
.info{font-size:10px;color:#6c7086;margin-top:2px;word-break:break-word;}
.info.falando{color:#a6e3a1;}
.row{display:flex;gap:8px;}
.row .btn{flex:1;}
</style>
</head><body>
<div class="topbar">
  <div style="display:flex;align-items:center;gap:4px;">
    <div class="drag" id="drag"></div><span>🎙️ Jarvis</span>
  </div>
</div>
<div class="controls">
  <button class="btn off" id="btnVoz"><span><span class="sw off" id="swVoz"></span>Voz</span><span id="lblVoz">OFF</span></button>
  <button class="btn stop" id="btnFala"><span>⏹ Parar Fala</span></button>
  <button class="btn off" id="btnMic"><span><span class="sw off" id="swMic"></span>Mic</span><span id="lblMic">OFF</span></button>
  <div class="row">
    <button class="btn" id="minimizeBtn" title="Minimizar">_</button>
    <button class="btn" id="topoBtn" title="Sempre no topo">Top</button>
    <button class="btn" id="fixBtn" title="Fixar atrás">Trás</button>
    <button class="btn" id="closeBtn" title="Fechar">✕</button>
  </div>
  <div class="info" id="info">conectando...</div>
</div>
<script>
(function(){
  // ---- UI driven pelo Python via win.evaluate_js("applyState({...})") ----
  function cls(el,c){ if(el) el.className=c; }
  window.applyState = function(s){
    var v=s.voz, m=s.mic;
    cls(document.getElementById('swVoz'),'sw '+(v?'on':'off'));
    cls(document.getElementById('btnVoz'),'btn '+(v?'on':'off'));
    document.getElementById('lblVoz').textContent = v?'ON':'OFF';
    cls(document.getElementById('swMic'),'sw '+(m?'on':'off'));
    cls(document.getElementById('btnMic'),'btn '+(m?'on':'off'));
    document.getElementById('lblMic').textContent = m?'ON':'OFF';
    var info=document.getElementById('info');
    if(s.tts_ativo){ info.textContent='🔊 FALANDO'; info.className='info falando';
      info.title='FALANDO: ' + (s.texto||''); }
    else if(s.ativo){ info.textContent='JARVIS ativo | online'; info.className='info';
      info.title='Ativo'; }
    else { info.textContent='online (voz off)'; info.className='info';
      info.title='Desativado'; }
  };

  // ---- feedback otimistico no clique (o Python confirma/corrige em ~1s) ----
  function clickSet(k){ localStorage.setItem('jarvis_click', k); }
  document.getElementById('btnVoz').addEventListener('click', function(){
    var isOn=this.classList.contains('on');
    cls(this,isOn?'btn off':'btn on'); document.getElementById('lblVoz').textContent=isOn?'OFF':'ON'; clickSet('voz');
  });
  document.getElementById('btnMic').addEventListener('click', function(){
    var isOn=this.classList.contains('on');
    cls(this,isOn?'btn off':'btn on'); document.getElementById('lblMic').textContent=isOn?'OFF':'ON'; clickSet('mic');
  });
  document.getElementById('btnFala').addEventListener('click', function(){ clickSet('fala'); });
  document.getElementById('closeBtn').addEventListener('click', function(){ clickSet('close'); });
  document.getElementById('minimizeBtn').addEventListener('click', function(){ clickSet('minimize'); });
  document.getElementById('topoBtn').addEventListener('click', function(){ clickSet('topo'); });
  document.getElementById('fixBtn').addEventListener('click', function(){ clickSet('fix'); });

  // ---- drag da barra superior: JS escreve posicao -> Python faz win.move ----
  // Usa screenX/screenY absolutos com offset calculado no mousedown.
  // Eventos em window para capturar quando mouse sai da janela.
  var dragging=false, offX=0, offY=0, winX=0, winY=0;
  document.getElementById('drag').addEventListener('mousedown', function(e){
    dragging=true;
    winX=window.__winPosX||0; winY=window.__winPosY||0;
    offX=e.clientX; offY=e.clientY;
    e.preventDefault();
  });
  window.addEventListener('mousemove', function(e){
    if(!dragging) return;
    var nx=winX+(e.clientX-offX), ny=winY+(e.clientY-offY);
    window.__winPosX=Math.round(nx); window.__winPosY=Math.round(ny);
    localStorage.setItem('jarvis_move', JSON.stringify({x:Math.round(nx),y:Math.round(ny)}));
  });
  window.addEventListener('mouseup', function(){ dragging=false; });
})();
</script>
</body></html>
"""


def _build_view() -> Path:
    """Escreve HTML inline num arquivo local (carregado via url=file://)."""
    VIEW_COPY.parent.mkdir(parents=True, exist_ok=True)
    VIEW_COPY.write_text(HTML, encoding="utf-8")
    return VIEW_COPY


# ============================================================
# Poller Python-Driven (Python->JS via evaluate_js; JS->Python via localStorage)
# ============================================================

_janela_global = None


def _dispatch(click: str, win):
    if click == "voz":
        at, pa = ler_estado_voz()
        _thread(cmd_voz, not (at and not pa))
    elif click == "fala":
        _thread(cmd_interromper_fala)
    elif click == "mic":
        _thread(cmd_mic, not mic_ativo())
    elif click == "minimize":
        _thread(_minimizar, win)
    elif click == "topo":
        _thread(_toggle_always_on_top, win, True)
    elif click == "fix":
        _thread(_toggle_always_on_top, win, False)
    elif click == "close":
        try:
            win.evaluate_js("localStorage.removeItem('jarvis_click')")
        except Exception:
            pass
        _thread(win.destroy)


def _toggle_always_on_top(win, on_top: bool):
    """Alterna preferência de janela sempre no topo. Requer reinício do widget para aplicar."""
    try:
        geo = _carregar_geo()
        geo["sempre_topo"] = on_top
        _atomic_write(GEO_FILE, geo)
        # Feedback visual no JS
        win.evaluate_js(f"localStorage.setItem('jarvis_mode', '{'always' if on_top else 'behind'}')")
        win.evaluate_js(f"console.log('[widget] sempre_topo salvo: {on_top}. Reinicie o widget para aplicar.')")
    except Exception as e:
        print(f"[widget] erro toggle on_top: {e}", flush=True)


def _poller(win, stop, init_x=None, init_y=None):
    """loop principal: detecta cliques + drag via localStorage, empurra estado via evaluate_js."""
    last_click = ""
    tick = 0
    # Posicao atual da janela (Python e JS mantem em sync)
    cur_x = init_x if init_x is not None else 0
    cur_y = init_y if init_y is not None else 0
    _pos_inited = False
    while not stop.wait(0.25):
        # --- inicializa posicao JS uma vez (evaluate_js pode falhar antes do webview.start) ---
        if not _pos_inited:
            try:
                win.evaluate_js(
                    "window.__winPosX=%d;window.__winPosY=%d;" % (int(cur_x), int(cur_y)))
                _pos_inited = True
            except Exception:
                pass
        # --- cliques (JS->Python via localStorage) ---
        try:
            click = win.evaluate_js("localStorage.getItem('jarvis_click')||''") or ""
        except Exception:
            click = ""
        if click and click != last_click:
            last_click = click
            _dispatch(click, win)
            try:
                win.evaluate_js("localStorage.removeItem('jarvis_click')")
            except Exception:
                pass
        # --- drag (JS escreve, Python move a janela) ---
        try:
            mv = win.evaluate_js("localStorage.getItem('jarvis_move')") or ""
        except Exception:
            mv = ""
        if mv and mv.strip():
            try:
                d = json.loads(mv)
                nx, ny = int(d["x"]), int(d["y"])
                if nx != cur_x or ny != cur_y:
                    win.move(nx, ny)
                    cur_x, cur_y = nx, ny
                    win.evaluate_js("window.__winPosX=%d;window.__winPosY=%d;" % (nx, ny))
                win.evaluate_js("localStorage.removeItem('jarvis_move')")
            except Exception as e:
                print(f"[drag] error: {e}", flush=True)
        # --- estado UI (Python->JS) a cada ~1s ---
        tick += 1
        if tick >= 4:
            tick = 0
            try:
                st = estado_unificado()
                win.evaluate_js(
                    "if(window.applyState)window.applyState(" + json.dumps(st) + ")",
                )
            except Exception:
                pass


def main() -> int:
    global _janela_global
    import webview

    view = _build_view()
    geo = _carregar_geo()
    w = int(geo.get("width", DEFAULT_W))
    h = int(geo.get("height", DEFAULT_H))
    x = geo.get("x")
    y = geo.get("y")
    # Carregar preferência de 'sempre em primeiro plano'
    sempre_topo = geo.get("sempre_topo", True)  # Padrão: True

    win = webview.create_window(
        TITLE,
        url=str(view.resolve()),
        width=w, height=h,
        x=x, y=y,
        resizable=True,
        frameless=True,
        easy_drag=True,
        focus=False,
        on_top=sempre_topo,
        background_color=BG,
    )
    _janela_global = win

    # Restaurar se estava minimizado
    if _restaurar_se_minimizado():
        try:
            win.show()
            print("[widget] Janela restaurada após minimizar.", flush=True)
        except Exception as e:
            print(f"[widget] erro restaurar: {e}", flush=True)

    stop = threading.Event()
    threading.Thread(target=_poller, args=(win, stop, x, y), daemon=True).start()

    try:
        webview.start(debug=False)
    finally:
        stop.set()
        _guardar_geo(win)
    return 0


if __name__ == "__main__":
    sys.exit(main())