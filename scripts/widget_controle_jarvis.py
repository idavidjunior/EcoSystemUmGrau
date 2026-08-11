"""widget_controle_jarvis.py — Janela flutuante de controle visual da narração Jarvis no PC.

Controles visuais (sempre no topo, sem bordas, arrastável pela barra superior):
  - Voz ON/OFF      -> liga/desliga narração  (AT ECO / DT ECO)
  - Parar Fala      -> interrompe TTS ativo   (STOP ECO)
  - Mic ON/OFF      -> liga/desliga escuta STT (dialogo.py --modo vad)

Estado em tempo real: a cada 1s o JS consulta bridge.ler_estado() que le os mesmos
arquivos que os demais scripts usam (runtime/narracao_estado.json e
runtime/mic_estado.json). Nada eh pelejado: o widget eh 100% leitor de estados e
100% compativel com jarvis_audio.py / narrador_desktop.py / dialogo.py.

Posicao/tamanho persistidos em runtime/widget_controle_geometria.json
(mesma convencao do widget_grafo.py).

Uso:
  python scripts/widget_controle_jarvis.py

Integre globalmente: registre o comando `controle` no opencode.jsonc:
  $ controle   -> abre esta janela flutuante
"""
import json
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

# --- Arquivos de estado do ecossistema (fonte unica) ---
CONTROLE = ROOT / "runtime" / "narracao_estado.json"          # voz: {ativo, pausado}
NARRADOR_PID = ROOT / "runtime" / "narrador.pid"               # PID do narrador_desktop
NARRADOR = SCRIPTS / "narrador_desktop.py"
VOX = SCRIPTS / "vox_audio.py"
JARVIS_AUDIO = SCRIPTS / "jarvis_audio.py"                    # CLI de controle existente

# --- Novo estado de microfone (convencao runtime/*.json) ---
MIC_ESTADO = ROOT / "runtime" / "mic_estado.json"             # {ativo, timestamp}
MIC_PID = ROOT / "runtime" / "mic.pid"                        # PID do dialogo.py
DIALOGO = SCRIPTS / "dialogo.py"                               # loop STT VAD

# --- Geometria da janela ---
GEO_FILE = ROOT / "runtime" / "widget_controle_geometria.json"
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
# Leituras de estado (visao unificada)
# ============================================================

def ler_estado_voz():
    """Retorna (ativo, pausado) de runtime/narracao_estado.json."""
    try:
        if CONTROLE.exists():
            d = json.loads(CONTROLE.read_text(encoding="utf-8"))
            return bool(d.get("ativo", True)), bool(d.get("pausado", False))
    except Exception:
        pass
    return True, False


def processo_vivo(pid_path: Path):
    """True se o PID em pid_path corresponde a um processo python vivo."""
    try:
        if pid_path.exists():
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            if pid > 0:
                out = subprocess.run(
                    ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
                    capture_output=True, text=True, timeout=10).stdout
                return str(pid) in out
    except Exception:
        pass
    return False


def narrador_rodando():
    return processo_vivo(NARRADOR_PID)


def tts_ativo():
    """Detecta processo TTS (vox_audio.py falar) em execucao."""
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq python.exe", "/NH"],
            capture_output=True, text=True, timeout=15).stdout
        for linha in out.splitlines():
            if "vox_audio.py" in linha and "falar" in linha:
                return True
    except Exception:
        pass
    return False


def mic_ativo():
    """True se o microfone esta logicamente ativo e o processo esta vivo."""
    try:
        if MIC_ESTADO.exists():
            d = json.loads(MIC_ESTADO.read_text(encoding="utf-8"))
            if not d.get("ativo", False):
                return False
    except Exception:
        return False
    return processo_vivo(MIC_PID)


# ============================================================
# Acoes de controle (rodam em background via threads)
# ============================================================

def _detached():
    return getattr(subprocess, "DETACHED_PROCESS", 0) | subprocess.CREATE_NEW_PROCESS_GROUP


def cmd_voz(ativar: bool):
    """Liga/desliga narracao via jarvis_audio.py (fonte unica de verdade)."""
    try:
        if ativar:
            subprocess.run([sys.executable, str(JARVIS_AUDIO), "on"],
                           cwd=str(ROOT), capture_output=True, timeout=35)
        else:
            subprocess.run([sys.executable, str(JARVIS_AUDIO), "stop"],
                           cwd=str(ROOT), capture_output=True, timeout=20)
            subprocess.run([sys.executable, str(JARVIS_AUDIO), "off"],
                           cwd=str(ROOT), capture_output=True, timeout=20)
    except Exception as e:
        print(f"[widget] erro voz({'on' if ativar else 'off'}): {e}", flush=True)


def cmd_interromper_fala():
    """Mata TTS ativo imediatamente (STOP ECO)."""
    try:
        subprocess.run([sys.executable, str(JARVIS_AUDIO), "stop"],
                       cwd=str(ROOT), capture_output=True, timeout=20)
    except Exception as e:
        print(f"[widget] erro stop: {e}", flush=True)


def cmd_mic(ativar: bool):
    """Liga/desliga microfone via dialogo.py --modo vad."""
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
                                   capture_output=True, timeout=8)
        except Exception as e:
            print(f"[widget] erro mic off (kill): {e}", flush=True)
        try:
            MIC_PID.unlink(missing_ok=True)
        except Exception:
            pass
        _atomic_write(MIC_ESTADO, {"ativo": False, "timestamp": int(time.time())})


# ============================================================
# Bridge Python <-> JavaScript (pywebview js_api)
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
        if not raw.strip():
            return {"x": None, "y": None, "width": DEFAULT_W, "height": DEFAULT_H}
        d = json.loads(raw)
    except Exception:
        d = {}
    return _clamp_geo({"x": d.get("x"), "y": d.get("y"),
                       "width": int(d.get("width", DEFAULT_W)),
                       "height": int(d.get("height", DEFAULT_H))})


class Bridge:
    def __init__(self):
        self._win = None

    def ping(self):
        return "pong"

    def ler_estado(self):
        """Visao unificada em tempo real (polling de 1s pelo JS)."""
        ativo, pausado = ler_estado_voz()
        return {
            "voz": ativo and not pausado,
            "ativo": ativo,
            "pausado": pausado,
            "mic": mic_ativo(),
            "narrador": narrador_rodando(),
            "tts_ativo": tts_ativo(),
            "ts": int(time.time()),
        }

    def toggle_voz(self):
        ativo, pausado = ler_estado_voz()
        novo_estado_ativo = ativo and not pausado
        threading.Thread(target=cmd_voz, args=(not novo_estado_ativo,), daemon=True).start()
        return {"acao": "voz", "destino": not novo_estado_ativo}

    def interromper_fala(self):
        threading.Thread(target=cmd_interromper_fala, daemon=True).start()
        return {"acao": "stop"}

    def toggle_mic(self):
        ativo = mic_ativo()
        threading.Thread(target=cmd_mic, args=(not ativo,), daemon=True).start()
        return {"acao": "mic", "destino": not ativo}

    def fechar(self):
        _persistir_geo()

    # --- movimento / geometria da janela ---
    def mover(self, x, y):
        if self._win is not None and hasattr(self._win, "move"):
            try:
                self._win.move(int(x), int(y))
            except Exception:
                pass
        return {"x": int(x), "y": int(y)}

    def guardar_geo(self, x=None, y=None, width=None, height=None):
        data = _carregar_geo()
        if width is not None:
            data["width"] = int(width)
        if height is not None:
            data["height"] = int(height)
        if x is not None and not (x == 0 and y == 0):
            data["x"] = int(x)
        if y is not None and not (x == 0 and y == 0):
            data["y"] = int(y)
        data = _clamp_geo(data)
        _atomic_write(GEO_FILE, data)
        return data


def _persistir_geo():
    try:
        if _janela_global is not None and hasattr(_janela_global, "evaluate_js"):
            _janela_global.evaluate_js("""
              if(window.pywebview && window.pywebview.api){
                window.pywebview.api.guardar_geo(
                  Math.round(window.screenX||0), Math.round(window.screenY||0),
                  Math.round(window.innerWidth||0), Math.round(window.innerHeight||0));
              }
            """)
    except Exception:
        pass


_janela_global = None


# ============================================================
# HTML / CSS / JS (self-contained, dark theme do ecossistema)
# ============================================================

HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{overflow:hidden;font-family:'Segoe UI',system-ui,sans-serif;
background:#1e1e2e;color:#cdd6f4;width:100%;height:100%;}
.topbar{background:#313244;height:22px;cursor:move;
display:flex;align-items:center;justify-content:space-between;
padding:0 8px;font-size:11px;color:#a6adc8;user-select:none;}
.drag{flex:1;cursor:move;}
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
.info{font-size:10px;color:#6c7086;margin-top:2px;}
</style>
</head><body>
<div class="topbar">
  <div style="display:flex;align-items:center;gap:4px;">
    <div class="drag" id="drag"></div>
    <span>🎙️ Jarvis</span>
  </div>
  <div class="close" id="closeBtn">✕</div>
</div>
<div class="controls">
  <button class="btn off" id="btnVoz">
    <span><span class="sw off" id="swVoz"></span>Voz</span>
    <span id="lblVoz">OFF</span>
  </button>
  <button class="btn stop" id="btnFala">
    <span>⏹ Parar Fala</span>
  </button>
  <button class="btn off" id="btnMic">
    <span><span class="sw off" id="swMic"></span>Mic</span>
    <span id="lblMic">OFF</span>
  </button>
  <div class="info" id="info">conectando...</div>
</div>
<script>
(function(){
  const api = window.pywebview && window.pywebview.api;
  let estado = null;

  function esc(e,c){e.className=c;}

  async function refresh(){
    if(!api){document.getElementById('info').textContent='sem bridge';return;}
    try{
      estado = await api.ler_estado();
      const v = estado.voz;
      esc(document.getElementById('swVoz'),'sw '+(v?'on':'off'));
      esc(document.getElementById('btnVoz'),'btn '+(v?'on':'off'));
      document.getElementById('lblVoz').textContent=v?'ON':'OFF';
      esc(document.getElementById('swMic'),'sw '+(estado.mic?'on':'off'));
      esc(document.getElementById('btnMic'),'btn '+(estado.mic?'on':'off'));
      document.getElementById('lblMic').textContent=estado.mic?'ON':'OFF';
      let inf='online';
      if(estado.narrador) inf='narrador● ';
      if(estado.tts_ativo) inf+='tts● ';
      document.getElementById('info').textContent=inf+'| '+new Date().toLocaleTimeString();
    }catch(e){
      document.getElementById('info').textContent='erro: '+e;
    }
  }

  // Aplica estado visual imediato a partir do estado retornado pelo bridge.
  function applyDestino(destino, chave){
    // chave: 'voz' | 'mic'
    if(chave==='voz'){
      const on=Boolean(destino); esc(document.getElementById('swVoz'),'sw '+(on?'on':'off'));
      esc(document.getElementById('btnVoz'),'btn '+(on?'on':'off'));
      document.getElementById('lblVoz').textContent=on?'ON':'OFF';
    }else if(chave==='mic'){
      const on=Boolean(destino); esc(document.getElementById('swMic'),'sw '+(on?'on':'off'));
      esc(document.getElementById('btnMic'),'btn '+(on?'on':'off'));
      document.getElementById('lblMic').textContent=on?'ON':'OFF';
    }
  }

  document.getElementById('btnVoz').addEventListener('click',async()=>{
    try{ const r=await api.toggle_voz(); if(r&&r.destino!==undefined) applyDestino(r.destino,'voz'); }catch(e){}
    setTimeout(refresh,800);
  });
  document.getElementById('btnFala').addEventListener('click',async()=>{
    try{ await api.interromper_fala(); }catch(e){}
    // feedback visual imediato: desativa o indicador tts
    document.getElementById('info').textContent='fala interrompida';
    setTimeout(refresh,500);
  });
  document.getElementById('btnMic').addEventListener('click',async()=>{
    try{ const r=await api.toggle_mic(); if(r&&r.destino!==undefined) applyDestino(r.destino,'mic'); }catch(e){}
    setTimeout(refresh,800);
  });
  document.getElementById('closeBtn').addEventListener('click',()=>{
    api.fechar();
  });

  // drag da barra superior
  const drag=document.getElementById('drag');
  let px=0,py=0,fx=0,fy=0,dragging=false;
  drag.addEventListener('mousedown',e=>{
    px=e.clientX;py=e.clientY;
    fx=window.screenX||0;fy=window.screenY||0;
    dragging=true;
    e.preventDefault();
  });
  document.addEventListener('mousemove',e=>{
    if(!dragging)return;
    const dx=e.clientX-px,dy=e.clientY-py;
    api.mover(fx+dx,fy+dy);
    fx+=dx;fy+=dy;
  });
  document.addEventListener('mouseup',()=>{dragging=false;});

  // salva geometria no beforeunload
  window.addEventListener('beforeunload',()=>{
    api.guardar_geo(
      Math.round(window.screenX||0),Math.round(window.screenY||0),
      Math.round(window.innerWidth||0),Math.round(window.innerHeight||0));
  });

  setInterval(refresh,1000);
  refresh();
})();
</script>
</body></html>
"""


# ============================================================
# Main
# ============================================================

VIEW_COPY = ROOT / "docs" / "widget_controle.html"


def _build_view() -> Path:
    """Escreve o HTML inline num arquivo local e retorna o caminho.

    CRUCIAL: servir via url=file:// (e NAO html=) faz o pywebview injetar
    window.pywebview.api no contexto da pagina. Com html= inline a ponte NAO
    aparece na pagina (window.pywebview fica undefined -> 'sem bridge').
    O widget_grafo.py ja usava url=file:// e funcionava por isso.
    """
    VIEW_COPY.parent.mkdir(parents=True, exist_ok=True)
    VIEW_COPY.write_text(HTML, encoding="utf-8")
    return VIEW_COPY


def main() -> int:
    global _janela_global
    import webview

    geo = _carregar_geo()
    w = int(geo.get("width", DEFAULT_W))
    h = int(geo.get("height", DEFAULT_H))
    x = geo.get("x")
    y = geo.get("y")

    view = _build_view()
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
        on_top=True,
        js_api=bridge,
        background_color=BG,
    )
    bridge._win = win
    _janela_global = win

    try:
        webview.start(debug=False)
    finally:
        _persistir_geo()
    return 0


if __name__ == "__main__":
    sys.exit(main())
