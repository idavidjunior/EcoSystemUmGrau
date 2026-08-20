#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""unified_bridge.py — Ponte única: monitora SQLite (narrador) + serve TTS (service).

Único processo com SpeechPipeline singleton. Elimina IPC entre narrador e service.
GARANTIA DE INSTÂNCIA ÚNICA: lock de arquivo + limpeza automática de duplicatas.
"""
import json
import os
import re
import sqlite3
import sys
import threading
import time
import uuid
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ==================== SINGLETON / LOCK DE PROCESSO ====================
PID_FILE = ROOT / "runtime" / "unified_bridge.pid"
LOCK_FILE = ROOT / "runtime" / "unified_bridge.lock"

def _cleanup_duplicate_processes():
    """Mata quaisquer processos unified_bridge.py anteriores (exceto o atual)."""
    current_pid = os.getpid()
    killed = 0
    try:
        # Usa WMI para listar processos python com unified_bridge na command line
        result = subprocess.run(
            ["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if "unified_bridge.py" in line:
                parts = line.strip().split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[-1])
                        if pid != current_pid:
                            # Verifica se este PID NÃO é o dono do lock atual
                            lock_holder = None
                            if PID_FILE.exists():
                                try:
                                    lock_holder = int(PID_FILE.read_text(encoding="utf-8").strip())
                                except Exception:
                                    pass
                            if pid != lock_holder:
                                subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                                             capture_output=True, timeout=5)
                                killed += 1
                    except (ValueError, IndexError):
                        pass
    except Exception as e:
        print(f"[bridge] cleanup aviso: {e}", flush=True)

    # Também limpa PID file órfão se não bate com lock holder vivo
    try:
        if PID_FILE.exists():
            old_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            if old_pid != current_pid:
                # Verifica se o processo do PID file ainda vive
                result = subprocess.run(["tasklist", "/FI", f"PID eq {old_pid}"],
                                      capture_output=True, text=True, timeout=5)
                if str(old_pid) not in result.stdout:
                    PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass

    if killed:
        print(f"[bridge] Limpeza: {killed} processo(s) duplicado(s) removido(s)", flush=True)

def _acquire_lock() -> bool:
    """Adquire lock exclusivo (arquivo). Retorna True se conseguiu, False se já existe outro."""
    try:
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Cria arquivo exclusivamente (falha se já existe)
        fd = os.open(LOCK_FILE, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        # Registra PID
        PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
        return True
    except FileExistsError:
        # Verifica se o processo dono do lock ainda vive
        try:
            if PID_FILE.exists():
                pid = int(PID_FILE.read_text(encoding="utf-8").strip())
                # Checa se processo existe
                result = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"],
                                      capture_output=True, text=True, timeout=5)
                if str(pid) not in result.stdout:
                    # Processo morto - remove lock órfão e tenta novamente
                    LOCK_FILE.unlink(missing_ok=True)
                    PID_FILE.unlink(missing_ok=True)
                    return _acquire_lock()
        except Exception:
            pass
        return False
    except Exception:
        return False

def _release_lock():
    """Libera lock na saída."""
    try:
        LOCK_FILE.unlink(missing_ok=True)
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass

# Limpeza e lock ANTES de inicializar SpeechPipeline
_cleanup_duplicate_processes()
if not _acquire_lock():
    print("[bridge] ERRO: Outra instância já está rodando. Saindo.", flush=True)
    sys.exit(1)

# Registra liberação no atexit
import atexit
atexit.register(_release_lock)

# ==================== FIM SINGLETON ====================

# SpeechPipeline singleton
try:
    from tts import SpeechPipeline
    _speech = SpeechPipeline()
    SPEECH_AVAILABLE = True
except Exception as e:
    print(f"[bridge] SpeechPipeline indisponível: {e}", flush=True)
    SPEECH_AVAILABLE = False
    _speech = None

# Fallback vox_audio
VOX = ROOT / "scripts" / "vox_audio.py"

# Paths
DB = Path(os.environ.get("OPENCODE_DB", r"C:\Users\David Jr\.local\share\opencode\opencode.db"))
POSICAO = ROOT / "runtime" / "narrador_posicao.json"
CONTROLE = ROOT / "runtime" / "narracao_estado.json"
PARAR_FALA = ROOT / "runtime" / "parar_fala.flag"
TTS_CMD = ROOT / "runtime" / "tts_cmd.json"
LOG = ROOT / "scripts" / "bridge_log.txt"
EXCLUIR_PADRAO = ["watchdog-health"]
DEBOUNCE_S = 0.5
FALAR_TIMEOUT = 90

# Perfil do usuário
try:
    from scripts.profile_hook import format_response_for_profile, get_response_config
    _profile_config = get_response_config()
    PROFILE_HOOK_AVAILABLE = True
except ImportError as e:
    print(f"[bridge] profile_hook indisponível: {e}", flush=True)
    _profile_config = {}
    PROFILE_HOOK_AVAILABLE = False
    def format_response_for_profile(texto, config):
        return texto
    def get_response_config():
        return {}

# Detecção inglês
try:
    from detect_english_words import pipeline_completo_tts
    ENGLISH_DETECT_AVAILABLE = True
except ImportError as e:
    print(f"[bridge] detect_english_words indisponível: {e}", flush=True)
    ENGLISH_DETECT_AVAILABLE = False
    def pipeline_completo_tts(texto):
        return texto


def _log(msg):
    linha = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(linha, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except Exception:
        pass


def _atomic_write(path: Path, data: dict):
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    try:
        tmp.replace(path)
    except OSError:
        import os as _os
        _os.replace(tmp, path)


# ==================== NARRADOR (monitora SQLite) ====================

def conectar_db():
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=10)
    c.execute("PRAGMA query_only=ON")
    return c


def ler_posicao():
    try:
        if POSICAO.exists():
            return json.loads(POSICAO.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"ultimo_ts": 0}


def salvar_posicao(pos):
    try:
        POSICAO.parent.mkdir(parents=True, exist_ok=True)
        tmp = POSICAO.with_suffix(".tmp")
        tmp.write_text(json.dumps(pos, ensure_ascii=False), encoding="utf-8")
        tmp.replace(POSICAO)
    except Exception as e:
        _log(f"posição não salva: {e}")


def estado_ativo():
    try:
        if CONTROLE.exists():
            estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
            ativo = estado.get("ativo", True)
            pausado = estado.get("pausado", False)
            return ativo and not pausado
    except Exception:
        pass
    return True


def limpar_texto(texto):
    if not texto:
        return ""
    texto = re.sub(r"```.*?```", " ", texto, flags=re.DOTALL)
    texto = re.sub(r"`([^`]+)`", r"\1", texto)
    texto = re.sub(r"^#{1,6}\s*", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"(\*\*|__|~~)", "", texto)
    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)
    texto = re.sub(r"^\s*[-*+]\s+", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"^\s*\d+[.)]\s+", "", texto, flags=re.MULTILINE)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto)
    return texto.strip()


def partes_novas(conn, ultimo_ts, excluir):
    if not DB.exists():
        return []
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT p.id, p.time_created, p.data, m.data, s.title, s.id
               FROM part p
               JOIN message m ON m.id = p.message_id
               JOIN session s ON s.id = p.session_id
               WHERE p.time_created > ? AND p.data LIKE '%"type":"text"%'
               ORDER BY p.time_created ASC LIMIT 800""",
            (ultimo_ts,),
        )
        saida = []
        for pid, ts, pdata, mdata, titulo, sid in cur.fetchall():
            try:
                p = json.loads(pdata)
                m = json.loads(mdata)
            except Exception:
                continue
            if p.get("type") != "text":
                continue
            if m.get("role") != "assistant":
                continue
            if titulo and any(x.lower() in titulo.lower() for x in excluir):
                continue
            texto = (p.get("text") or "").strip()
            if not texto:
                continue
            saida.append((ts or 0, sid, titulo or "", texto))
        return saida
    except Exception as e:
        _log(f"erro lendo banco: {e}")
        return []


# ==================== TTS SERVICE (processa comandos) ====================

_paused = False
_current_req_id = None
_processing = False
_lock = threading.Lock()


def _read_tts_cmd():
    try:
        if TTS_CMD.exists():
            return json.loads(TTS_CMD.read_text(encoding="utf-8-sig"))
    except Exception:
        pass
    return None


def _clear_tts_cmd():
    try:
        TTS_CMD.unlink(missing_ok=True)
    except Exception:
        pass


def _write_resp(req_id, status, msg=""):
    resp_file = ROOT / "runtime" / f"tts_resp_{req_id}.json"
    _atomic_write(resp_file, {"status": status, "request_id": req_id, "msg": msg})


def _speak_text(texto: str, stop_flag: Path, req_id: str) -> bool:
    global _current_req_id, _processing
    with _lock:
        _current_req_id = req_id
        _processing = True
    try:
        if SPEECH_AVAILABLE and _speech:
            _speech.speak(texto, block=True, stop_flag=stop_flag)
            return True
        import subprocess
        subprocess.run(
            [sys.executable, str(VOX), "falar", texto],
            cwd=str(ROOT),
            timeout=90,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except Exception as e:
        _log(f"erro fala: {e}")
        return False
    finally:
        with _lock:
            _current_req_id = None
            _processing = False


def processar_tts_cmd():
    global _paused
    if not TTS_CMD.exists():
        return
    try:
        mtime = TTS_CMD.stat().st_mtime
    except OSError:
        return
    if not hasattr(processar_tts_cmd, "_last_mtime"):
        processar_tts_cmd._last_mtime = 0
    if mtime == processar_tts_cmd._last_mtime:
        return
    processar_tts_cmd._last_mtime = mtime

    cmd = _read_tts_cmd()
    if not cmd:
        return
    _clear_tts_cmd()

    c = cmd.get("cmd")
    req_id = cmd.get("request_id", str(uuid.uuid4())[:8])

    if c == "speak":
        texto = cmd.get("texto", "").strip()
        if texto and not _paused:
            _log(f"TTS req={req_id}: {texto[:60]}...")
            ok = _speak_text(texto, PARAR_FALA, req_id)
            _write_resp(req_id, "ok" if ok else "error")
        elif _paused:
            _write_resp(req_id, "ignored", "pausado")
        else:
            _write_resp(req_id, "ignored", "texto vazio")

    elif c == "stop":
        _log(f"STOP req={req_id}")
        try:
            PARAR_FALA.write_text(str(int(time.time())), encoding="utf-8")
        except Exception:
            pass
        # Pausa narração: atualiza CONTROLE para não ler mais do banco
        try:
            if CONTROLE.exists():
                estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
                estado["pausado"] = True
                _atomic_write(CONTROLE, estado)
                _log("Narração PAUSADA via STOP (PS ECO)")
        except Exception:
            pass
        _write_resp(req_id, "ok")

    elif c == "pause":
        _paused = True
        _log("TTS PAUSADO")
        _write_resp(req_id, "ok")

    elif c == "resume":
        _paused = False
        _log("TTS RESUMIDO")
        _write_resp(req_id, "ok")


# ==================== WIDGET (pywebview) ====================

WIDGET_HTML = """<!DOCTYPE html>
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
</body></html>"""

VIEW_FILE = ROOT / "docs" / "widget_unified.html"
DEFAULT_W, DEFAULT_H = 220, 284
TITLE = "Jarvis Controle"
BG = "#1e1e2e"
GEO_FILE = ROOT / "runtime" / "widget_geo.json"

def _build_widget_view() -> Path:
    VIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    VIEW_FILE.write_text(WIDGET_HTML, encoding="utf-8")
    return VIEW_FILE


# ==================== WIDGET DISPATCH ====================

def _widget_dispatch(click: str, win):
    if click == "voz":
        at, pa = ler_estado_voz()
        # Toggle via CONTROLE
        try:
            if CONTROLE.exists():
                estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
            else:
                estado = {"ativo": True, "pausado": False}
            estado["ativo"] = not (estado.get("ativo", True) and not estado.get("pausado", False))
            if not estado["ativo"]:
                estado["pausado"] = True
            _atomic_write(CONTROLE, estado)
            _log(f"Widget: voz {'ON' if estado['ativo'] and not estado['pausado'] else 'OFF'}")
        except Exception as e:
            _log(f"widget voz error: {e}")
    elif click == "fala":
        # Stop = pausa narração + interrompe TTS
        try:
            PARAR_FALA.write_text(str(int(time.time())), encoding="utf-8")
            if CONTROLE.exists():
                estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
                estado["pausado"] = True
                _atomic_write(CONTROLE, estado)
            _log("Widget: STOP (parar fala + pausar narração)")
        except Exception as e:
            _log(f"widget stop error: {e}")
    elif click == "mic":
        _log("Widget: mic click (não implementado no unified)")
    elif click == "close":
        # Para TTS e fecha janela
        try:
            PARAR_FALA.write_text(str(int(time.time())), encoding="utf-8")
        except Exception:
            pass
        import os
        os._exit(0)
    elif click == "minimize":
        try:
            win.minimize()
        except Exception:
            try:
                win.hide()
            except Exception:
                pass
    elif click == "topo":
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "Jarvis Controle")
            if hwnd:
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
        except Exception:
            pass
    elif click == "fix":
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "Jarvis Controle")
            if hwnd:
                ctypes.windll.user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
                ctypes.windll.user32.SetWindowPos(hwnd, 1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
        except Exception:
            pass


# ==================== WIDGET POLLER (roda em thread) ====================

def _widget_poller(win, stop_event):
    last_click = ""
    tick = 0
    cur_x = 0
    cur_y = 0
    pos_inited = False
    while not stop_event.wait(0.25):
        # init pos
        if not pos_inited:
            try:
                win.evaluate_js("window.__winPosX=0;window.__winPosY=0;")
                pos_inited = True
            except Exception:
                pass
        # clicks
        try:
            click = win.evaluate_js("localStorage.getItem('jarvis_click')||''") or ""
        except Exception:
            click = ""
        if click and click != last_click:
            last_click = click
            _widget_dispatch(click, win)
            try:
                win.evaluate_js("localStorage.removeItem('jarvis_click')")
            except Exception:
                pass
        # drag
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
                _log(f"[widget drag] error: {e}")
        # push state to UI
        tick += 1
        if tick >= 4:
            tick = 0
            try:
                at, pa = ler_estado_voz()
                voz_on = at and not pa
                mic_on = False  # mic não implementado no unified
                tts_ativo_flag = False
                try:
                    narr = json.loads(CONTROLE.read_text(encoding="utf-8"))
                    tts_ativo_flag = bool(narr.get("ativo", False)) and not bool(narr.get("pausado", False))
                except Exception:
                    pass
                st = {
                    "voz": voz_on,
                    "mic": mic_on,
                    "ativo": at,
                    "pausado": pa,
                    "tts_ativo": tts_ativo_flag,
                    "texto": ""
                }
                win.evaluate_js(
                    "if(window.applyState)window.applyState(" + json.dumps(st) + ")"
                )
            except Exception:
                pass


# ==================== WIDGET MAIN (roda na thread principal) ====================

def _run_widget():
    import webview
    _build_widget_view()
    geo = {}
    if GEO_FILE.exists():
        try:
            geo = json.loads(GEO_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    w = int(geo.get("width", 220))
    h = int(geo.get("height", 284))
    x = geo.get("x")
    y = geo.get("y")
    sempre_topo = geo.get("sempre_topo", True)

    win = webview.create_window(
        "Jarvis Controle",
        url=str(VIEW_FILE.resolve()),
        width=w, height=h,
        x=x, y=y,
        resizable=True,
        frameless=True,
        easy_drag=True,
        focus=False,
        on_top=sempre_topo,
        background_color="#1e1e2e",
    )

    stop_event = threading.Event()
    poller_thread = threading.Thread(target=_widget_poller, args=(win, stop_event), daemon=True)
    poller_thread.start()

    try:
        _log("Iniciando webview.start()")
        # Tenta com http_port=0 (porta aleatória) para evitar conflito
        webview.start(debug=True, http_port=0)
        _log("webview.start() retornou")
    except OSError as e:
        if "Address already in use" in str(e) or "Port" in str(e):
            _log(f"Porta em uso, tentando sem http_server...")
            try:
                webview.start(debug=False, http_server=False)
                _log("webview.start() retornou (sem http_server)")
            except Exception as e2:
                _log(f"webview.start() erro (sem http_server): {e2}")
                import traceback
                traceback.print_exc()
    except Exception as e:
        _log(f"webview.start() erro: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Save geometry
        try:
            win.evaluate_js("""
                (function(){
                    var x=window.screenX||0,y=window.screenY||0,w=window.innerWidth||0,h=window.innerHeight||0;
                    var st=window.__sempre_topo||true;
                    localStorage.setItem('jarvis_geo', JSON.stringify({x:x,y:y,width:w,height:h,sempre_topo:st}));
                })();
            """)
        except Exception:
            pass
        # Save from localStorage
        try:
            geo_js = win.evaluate_js("localStorage.getItem('jarvis_geo')")
            if geo_js:
                d = json.loads(geo_js)
                _atomic_write(GEO_FILE, d)
        except Exception:
            pass


# ==================== NARRADOR/TTS LOOP (background thread) ====================

def _bridge_loop():
    try:
        _log("=" * 50)
        _log("  Unified Bridge — Narrador + TTS Service + Widget")
        _log(f"  SpeechPipeline: {'OK' if SPEECH_AVAILABLE else 'fallback vox_audio'}")
        _log(f"  Banco: {DB.name}")
        _log(f"  TTS cmd: {TTS_CMD}")
        _log(f"  Stop flag: {PARAR_FALA}")
        _log("=" * 50)

        excluir = EXCLUIR_PADRAO
        pos = ler_posicao()
        ultimo_ts = pos.get("ultimo_ts", 0)
        conn = conectar_db()
        buffer = []
        timer = None
        buffer_lock = threading.Lock()
        falando_lock = threading.Lock()
        estado_logado = None

        def flush_buffer():
            with buffer_lock:
                textos = buffer
                buffer.clear()
            nonlocal timer
            timer = None
            texto = " ".join(textos).strip()
            texto = limpar_texto(texto)
            texto = pipeline_completo_tts(texto)
            if PROFILE_HOOK_AVAILABLE:
                texto = format_response_for_profile(texto, _profile_config)
            if len(texto) < 15:
                return
            with falando_lock:
                _log(f"narrador falando ({len(texto)} chars): {texto[:70]}...")
                try:
                    req_id = f"narr_{uuid.uuid4().hex[:8]}"
                    _speak_text(texto, PARAR_FALA, req_id)
                except Exception as e:
                    _log(f"falha narrador: {e}")

        while True:
            try:
                # 1. Processa comandos TTS (widget, stop, pause)
                processar_tts_cmd()

                # 2. Verifica estado narração ativo/pausado
                ativo = estado_ativo()
                if ativo != estado_logado:
                    estado_logado = ativo
                    if ativo:
                        _log("narração ATIVADA (AT ECO)")
                    else:
                        try:
                            if CONTROLE.exists():
                                estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
                                if estado.get("ativo", True) and estado.get("pausado", False):
                                    _log("narração PAUSADA (PS ECO)")
                                else:
                                    _log("narração DESATIVADA (DT ECO)")
                            else:
                                _log("narração DESATIVADA (DT ECO)")
                        except Exception:
                            _log("narração PAUSADA (PS ECO)")

                # 3. Lê novas partes do banco se narração ativa
                if ativo:
                    novas = partes_novas(conn, ultimo_ts, excluir)
                    if novas:
                        textos = [t for _, _, _, t in novas]
                        with buffer_lock:
                            buffer.extend(textos)
                        if timer is None:
                            timer = threading.Timer(DEBOUNCE_S, flush_buffer)
                            timer.daemon = True
                            timer.start()
                        ultimo_ts = max(x[0] for x in novas)
                        salvar_posicao({"ultimo_ts": ultimo_ts})

                # 4. Limpa flag PARAR_FALA antiga
                if PARAR_FALA.exists():
                    try:
                        ts = float(PARAR_FALA.read_text(encoding="utf-8").strip())
                        if time.time() - ts > 2:
                            PARAR_FALA.unlink(missing_ok=True)
                    except Exception:
                        pass

                time.sleep(0.05)

            except KeyboardInterrupt:
                _log("Bridge encerrado")
                break
            except Exception as e:
                _log(f"loop error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.5)

        try:
            conn.close()
        except Exception:
            pass
    except Exception as e:
        _log(f"_bridge_loop erro fatal: {e}")
        import traceback
        traceback.print_exc()


# ==================== MAIN ====================

def main():
    # Inicia loop de narrador/TTS em background thread
    bridge_thread = threading.Thread(target=_bridge_loop, daemon=True)
    bridge_thread.start()

    # Roda widget na thread principal (webview.start bloqueia)
    try:
        _run_widget()
    except Exception as e:
        _log(f"main erro: {e}")
        import traceback
        traceback.print_exc()
    return 0


if __name__ == "__main__":
    sys.exit(main())