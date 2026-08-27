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
    """Mata processos duplicados do unified_bridge.py apenas.

    O unified_bridge.py é a ponte única canônica (TTS service).
    NÃO mata widget_edge.py (é o widget/narrador oficial).
    """
    current_pid = os.getpid()
    killed = 0
    try:
        result = subprocess.run(
            ["wmic", "process", "where", "name='python.exe' or name='pythonw.exe'",
             "get", "ProcessId,CommandLine"],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.splitlines():
            if "unified_bridge.py" in line:
                parts = line.strip().split()
                if len(parts) >= 2:
                    try:
                        pid = int(parts[-1])
                        if pid != current_pid:
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
        _log(f"[bridge] cleanup aviso: {e}", flush=True)

    try:
        if PID_FILE.exists():
            old_pid = int(PID_FILE.read_text(encoding="utf-8").strip())
            if old_pid != current_pid:
                result = subprocess.run(["tasklist", "/FI", f"PID eq {old_pid}"],
                                      capture_output=True, text=True, timeout=5)
                if str(old_pid) not in result.stdout:
                    PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass

    if killed:
        _log(f"[bridge] Limpeza: {killed} processo(s) unified_bridge duplicado(s) removido(s)", flush=True)

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

# Notificações e histórico do widget
NOTIF_FILE = ROOT / "runtime" / "widget_notifs.json"
HIST_FILE = ROOT / "runtime" / "widget_history.json"
ULTIMO_RESUMO_FILE = ROOT / "runtime" / "ultimo_resumo.json"

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
    for _ in range(6):
        try:
            tmp.replace(path)
            return
        except OSError:
            time.sleep(0.1)
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


def ler_estado_voz():
    """Lê estado atual da voz (ativo, pausado) de CONTROLE."""
    try:
        if CONTROLE.exists():
            d = json.loads(CONTROLE.read_text(encoding="utf-8"))
            return bool(d.get("ativo", True)), bool(d.get("pausado", False))
    except Exception:
        pass
    return True, False


def estado_ativo():
    try:
        ativo, pausado = ler_estado_voz()
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


def _add_notif(msg):
    try:
        notifs = []
        if NOTIF_FILE.exists():
            notifs = json.loads(NOTIF_FILE.read_text(encoding="utf-8"))
        notifs.append(f"[{datetime.now().strftime('%H:%M')}] {msg}")
        if len(notifs) > 20:
            notifs = notifs[-20:]
        _atomic_write(NOTIF_FILE, notifs)
    except Exception:
        pass


def _add_hist(cmd):
    try:
        hist = []
        if HIST_FILE.exists():
            hist = json.loads(HIST_FILE.read_text(encoding="utf-8"))
        hist.append(cmd)
        if len(hist) > 20:
            hist = hist[-20:]
        _atomic_write(HIST_FILE, hist)
    except Exception:
        pass


def _salvar_ultimo_resumo(texto):
    try:
        _atomic_write(ULTIMO_RESUMO_FILE, {"texto": texto, "ts": time.time()})
    except Exception:
        pass


def _ler_ultimo_resumo():
    try:
        if ULTIMO_RESUMO_FILE.exists():
            d = json.loads(ULTIMO_RESUMO_FILE.read_text(encoding="utf-8"))
            if time.time() - d.get("ts", 0) < 3600:
                return d.get("texto", "")
    except Exception:
        pass
    return ""


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
        from atividade_emit import emitir
        emitir("fala", 0.95)
    except Exception:
        pass
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
        try:
            from atividade_emit import emitir as _emitir_fim
            _emitir_fim("fala", 0.0)
        except Exception:
            pass
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
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<link rel="icon" href="jarvis.ico" type="image/x-icon">
<style>
*{margin:0;padding:0;box-sizing:border-box;}
html,body{overflow:hidden;font-family:'Segoe UI',system-ui,sans-serif;
background:#1e1e2e;color:#cdd6f4;width:100%;height:100%;font-size:13px;}
::-webkit-scrollbar{width:6px;}
::-webkit-scrollbar-track{background:#181825;}
::-webkit-scrollbar-thumb{background:#45475a;border-radius:3px;}
.topbar{background:#313244;height:28px;cursor:move;
display:flex;align-items:center;justify-content:space-between;
padding:0 10px;font-size:12px;color:#a6adc8;user-select:none;
flex-shrink:0;}
.drag{flex:1;cursor:move;min-height:28px;display:flex;align-items:center;gap:6px;}
.title{display:flex;align-items:center;gap:6px;font-weight:600;}
.close{background:#f38ba8;width:18px;height:18px;border-radius:4px;
display:flex;align-items:center;justify-content:center;
font-size:11px;line-height:1;cursor:pointer;color:#1e1e2e;font-weight:bold;
flex-shrink:0;}
.main{padding:10px;display:flex;flex-direction:column;height:calc(100% - 28px);overflow-y:auto;
min-height:0;}
.row{display:flex;gap:8px;flex-wrap:wrap;}
.row .btn{flex:1 1 45%; min-width:0;}
.btn{display:flex;align-items:center;justify-content:space-between;
padding:8px 10px;border:none;border-radius:6px;cursor:pointer;
font-size:13px;background:#313244;color:#cdd6f4;transition:.15s;
white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.btn:hover{background:#45475a;}
.btn.on{background:#a6e3a1;color:#1e1e2e;}
.btn.off{background:#f38ba8;color:#1e1e2e;}
.btn.stop{background:#f28465;color:#1e1e2e;}
.sw{width:10px;height:10px;border-radius:50%;display:inline-block;margin-right:6px;flex-shrink:0;}
.sw.on{background:#a6e3a1;box-shadow:0 0 6px #a6e3a1;}
.sw.off{background:#f38ba8;}
.section{margin-top:10px;}
.section-title{font-size:10px;color:#6c7086;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:5px;}
.info{font-size:12px;color:#6c7086;word-break:break-word;padding:8px 10px;
background:#181825;border-radius:6px;min-height:22px;}
.info.falando{color:#a6e3a1;font-weight:500;}
.modes{display:flex;gap:6px;margin-bottom:8px;}
.mode-btn{flex:1;padding:6px;border:none;border-radius:5px;cursor:pointer;
font-size:11px;background:#181825;color:#a6adc8;transition:.15s;white-space:nowrap;}
.mode-btn.active{background:#89b4fa;color:#1e1e2e;font-weight:600;}
.mode-btn:hover{background:#313244;}
.sys-row{display:flex;gap:10px;font-size:10px;color:#a6adc8;margin-top:4px;flex-wrap:wrap;}
.sys-val{color:#a6e3a1;font-weight:500;}
.sys-val.warn{color:#f9e2af;}
.sys-val.crit{color:#f38ba8;}
.txt-input{display:flex;gap:6px;margin-top:8px;}
.txt-input input{flex:1;padding:8px 10px;border:1px solid #45475a;border-radius:5px;
background:#181825;color:#cdd6f4;font-size:12px;outline:none;min-width:0;}
.txt-input input:focus{border-color:#89b4fa;}
.txt-input button{padding:8px 14px;border:none;border-radius:5px;
background:#89b4fa;color:#1e1e2e;font-size:12px;cursor:pointer;font-weight:600;
flex-shrink:0;white-space:nowrap;}
.txt-input button:hover{background:#74c7ec;}
.notif{font-size:10px;color:#a6adc8;padding:4px 0;border-bottom:1px solid #313244;line-height:1.4;}
.notif:last-child{border:none;}
.hist{font-size:10px;color:#6c7086;padding:4px 0;border-bottom:1px solid #181825;line-height:1.4;}
.hist:last-child{border:none;}
.hist .cmd{color:#89b4fa;}
.mic-active{animation:pulse 1s infinite;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.4;}}

/* Responsive: small widths */
@media (max-width: 260px) {
  html,body {font-size:11px;}
  .topbar {height:24px;padding:0 8px;font-size:11px;}
  .drag {min-height:24px;gap:4px;}
  .close {width:16px;height:16px;font-size:10px;}
  .main {padding:8px;height:calc(100% - 24px);}
  .row {gap:6px;}
  .row .btn {flex:1 1 100%;}
  .btn {padding:7px 8px;font-size:12px;}
  .sw {width:8px;height:8px;margin-right:5px;}
  .txt-input input {padding:6px 8px;font-size:11px;}
  .txt-input button {padding:6px 10px;font-size:11px;}
  .modes {gap:4px;}
  .mode-btn {padding:5px;font-size:10px;}
  .section-title {font-size:9px;}
  .info {font-size:11px;padding:6px 8px;}
  .txt-input {gap:4px;}
  .txt-input button {padding:6px 8px;font-size:11px;}
}

/* Very small widths */
@media (max-width: 200px) {
  html,body {font-size:10px;}
  .topbar {height:22px;padding:0 6px;}
  .drag {gap:3px;}
  .close {width:14px;height:14px;}
  .main {padding:6px;}
  .btn {padding:5px 6px;font-size:10px;}
  .section-title {font-size:8px;}
  .info {font-size:10px;padding:4px 6px;min-height:18px;}
  .modes {gap:3px;}
  .mode-btn {padding:4px;font-size:9px;}
}

</style>
</head><body>
<div class="topbar">
  <div style="display:flex;align-items:center;gap:4px;">
    <div class="drag" id="drag"></div><span>🎙️ Jarvis</span>
  </div>
  <div class="close" id="closeBtn" title="Fechar">✕</div>
</div>
<div class="main">
  <div class="modes" id="modes">
    <button class="mode-btn active" data-m="narrador">Narrador</button>
    <button class="mode-btn" data-m="dialogo">Diálogo</button>
    <button class="mode-btn" data-m="silencioso">Silencioso</button>
  </div>
  <div class="row">
    <button class="btn off" id="btnVoz"><span><span class="sw off" id="swVoz"></span>Voz</span><span id="lblVoz">OFF</span></button>
    <button class="btn stop" id="btnFala"><span>⏹ Parar</span></button>
  </div>
  <div class="row">
    <button class="btn off" id="btnMic"><span><span class="sw off" id="swMic"></span>Mic</span><span id="lblMic">OFF</span></button>
    <button class="btn" id="btnRepetir" title="Repetir último resumo">🔁 Repetir</button>
  </div>
  <div class="txt-input">
    <input type="text" id="txtCmd" placeholder="Digite um comando..." />
    <button id="btnSend">▶</button>
  </div>
  <div class="section">
    <div class="section-title">Status</div>
    <div class="info" id="info">conectando...</div>
  </div>
  <div class="section" id="sysSection" style="display:none;">
    <div class="section-title">Sistema</div>
    <div class="sys-row">
      <span>CPU: <span class="sys-val" id="sysCpu">-</span></span>
      <span>RAM: <span class="sys-val" id="sysRam">-</span></span>
      <span>Disco: <span class="sys-val" id="sysDisk">-</span></span>
    </div>
  </div>
  <div class="section" id="notifSection" style="display:none;">
    <div class="section-title">Notificações</div>
    <div id="notifList"></div>
  </div>
  <div class="section" id="histSection" style="display:none;">
    <div class="section-title">Histórico</div>
    <div id="histList"></div>
  </div>
  <div class="row" style="margin-top:auto;padding-top:8px;">
    <button class="btn" id="minimizeBtn" title="Minimizar">_</button>
    <button class="btn" id="topoBtn" title="Sempre no topo">Top</button>
    <button class="btn" id="fixBtn" title="Fixar atrás">Trás</button>
  </div>
</div>
(function(){
  var recon=null;
  function cls(el,c){ if(el) el.className=c; }

  function setMode(m){
    localStorage.setItem('jarvis_modo',m);
    document.querySelectorAll('.mode-btn').forEach(function(b){
      cls(b,b.dataset.m===m?'mode-btn active':'mode-btn');
    });
  }

  window.applyState = function(s){
    var v=s.voz, m=s.mic;
    cls(document.getElementById('swVoz'),'sw '+(v?'on':'off'));
    cls(document.getElementById('btnVoz'),'btn '+(v?'on':'off'));
    document.getElementById('lblVoz').textContent = v?'ON':'OFF';
    cls(document.getElementById('swMic'),'sw '+(m?'on':'off'));
    cls(document.getElementById('btnMic'),'btn '+(m?'on':'off'));
    document.getElementById('lblMic').textContent = m?'ON':'OFF';
    if(m) document.getElementById('btnMic').classList.add('mic-active');
    else document.getElementById('btnMic').classList.remove('mic-active');
    var info=document.getElementById('info');
    if(s.tts_ativo){
      info.textContent='🔊 '+(s.texto||'FALANDO').substring(0,80);
      info.className='info falando';
    }
    else if(s.ativo){ info.textContent='JARVIS ativo | online'; info.className='info'; }
    else { info.textContent='online (voz off)'; info.className='info'; }
    if(s.modo) setMode(s.modo);
    if(s.sys){
      document.getElementById('sysSection').style.display='';
      var sc=s.sys.cpu,sr=s.sys.ram,sd=s.sys.disk;
      var ec=sc>80?'crit':sc>60?'warn':'', er=sr>80?'crit':sr>60?'warn':'', ed=sd>90?'crit':sd>70?'warn':'';
      document.getElementById('sysCpu').textContent=sc+'%';
      document.getElementById('sysCpu').className='sys-val '+ec;
      document.getElementById('sysRam').textContent=sr+'%';
      document.getElementById('sysRam').className='sys-val '+er;
      document.getElementById('sysDisk').textContent=sd+'%';
      document.getElementById('sysDisk').className='sys-val '+ed;
    }
    if(s.notifs && s.notifs.length>0){
      document.getElementById('notifSection').style.display='';
      var nh='';
      s.notifs.slice(-5).reverse().forEach(function(n){
        nh+='<div class="notif">'+n+'</div>';
      });
      document.getElementById('notifList').innerHTML=nh;
    }
    if(s.hist && s.hist.length>0){
      document.getElementById('histSection').style.display='';
      var hh='';
      s.hist.slice(-5).reverse().forEach(function(h){
        hh+='<div class="hist"><span class="cmd">'+h+'</span></div>';
      });
      document.getElementById('histList').innerHTML=hh;
    }
  };

  function clickSet(k){ localStorage.setItem('jarvis_click', k); }

  document.getElementById('btnVoz').addEventListener('click', function(){
    var isOn=this.classList.contains('on');
    cls(this,isOn?'btn off':'btn on'); document.getElementById('lblVoz').textContent=isOn?'OFF':'ON';
    clickSet('voz');
  });

  document.getElementById('btnFala').addEventListener('click', function(){ clickSet('fala'); });
  document.getElementById('btnRepetir').addEventListener('click', function(){ clickSet('repetir'); });

  document.getElementById('btnMic').addEventListener('click', function(){
    var isOn=this.classList.contains('on');
    if(isOn){
      stopMic();
      cls(this,'btn off'); document.getElementById('lblMic').textContent='OFF';
      cls(document.getElementById('swMic'),'sw off');
      this.classList.remove('mic-active');
      localStorage.setItem('jarvis_mic','false');
    } else {
      startMic();
      cls(this,'btn on mic-active'); document.getElementById('lblMic').textContent='ON';
      cls(document.getElementById('swMic'),'sw on');
      localStorage.setItem('jarvis_mic','true');
    }
  });

  function startMic(){
    var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!SR){ alert('Speech Recognition não suportado neste navegador.'); return; }
    recon=new SR();
    recon.lang='pt-BR';
    recon.continuous=true;
    recon.interimResults=false;
    recon.onresult=function(e){
      var last=e.results[e.results.length-1];
      if(last.isFinal){
        var txt=last[0].transcript.trim();
        if(txt) localStorage.setItem('jarvis_mic_text',txt);
      }
    };
    recon.onerror=function(){};
    recon.onend=function(){
      if(document.getElementById('btnMic').classList.contains('on')){
        try{recon.start();}catch(e){}
      }
    };
    try{recon.start();}catch(e){}
  }

  function stopMic(){
    if(recon){try{recon.stop();}catch(e){} recon=null;}
  }

  function sendText(){
    var inp=document.getElementById('txtCmd');
    var v=inp.value.trim();
    if(!v) return;
    localStorage.setItem('jarvis_text_cmd',v);
    inp.value='';
  }
  document.getElementById('btnSend').addEventListener('click',sendText);
  document.getElementById('txtCmd').addEventListener('keydown',function(e){
    if(e.key==='Enter') sendText();
  });

  document.querySelectorAll('.mode-btn').forEach(function(b){
    b.addEventListener('click',function(){setMode(this.dataset.m);});
  });

  document.getElementById('closeBtn').addEventListener('click', function(){ clickSet('close'); });
  document.getElementById('minimizeBtn').addEventListener('click', function(){ clickSet('minimize'); });
  document.getElementById('topoBtn').addEventListener('click', function(){
    var cur=localStorage.getItem('jarvis_sempre_topo');
    var novo=cur!=='true';
    localStorage.setItem('jarvis_sempre_topo',novo?'true':'false');
    clickSet('topo');
  });
  document.getElementById('fixBtn').addEventListener('click', function(){
    localStorage.setItem('jarvis_sempre_topo','false');
    clickSet('fix');
  });

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

  localStorage.setItem('jarvis_sempre_topo','true');
})();
</script>
</body></html>"""

VIEW_FILE = ROOT / "docs" / "widget_unified.html"
DEFAULT_W, DEFAULT_H = 280, 420
TITLE = "Jarvis Controle"
BG = "#1e1e2e"
GEO_FILE = ROOT / "runtime" / "widget_geo.json"

def _build_widget_view() -> Path:
    VIEW_FILE.parent.mkdir(parents=True, exist_ok=True)
    VIEW_FILE.write_text(WIDGET_HTML, encoding="utf-8")
    return VIEW_FILE


# ==================== ECO WIDGET CONTROL ====================
# Importa funções do eco_widget (orquestra widget + narrador)
try:
    import sys as _sys
    _sys.path.insert(0, str(ROOT / "scripts"))
    from eco_widget import activate as eco_activate, deactivate as eco_deactivate
    ECO_WIDGET_AVAILABLE = True
except Exception as _e:
    _log(f"[bridge] eco_widget indisponível: {_e}")
    ECO_WIDGET_AVAILABLE = False
    def eco_activate(): return {"ok": False, "erro": "eco_widget indisponível"}
    def eco_deactivate(): return {"ok": False, "erro": "eco_widget indisponível"}

# ==================== ECO COMMAND HANDLER ====================
def _handle_eco_command(texto: str) -> bool:
    """Processa comandos @eco, /eco, Eco, Desativar Eco.
    Retorna True se foi comando eco processado."""
    txt = texto.strip()
    low = txt.lower()
    # @eco ou /eco (com ou sem @ ou /)
    if low in ("@eco", "/eco", "eco"):
        if ECO_WIDGET_AVAILABLE:
            try:
                res = eco_activate()
                _log(f"Eco ativado via comando: {res.get('mensagem', 'OK')}")
            except Exception as e:
                _log(f"Erro ao ativar eco: {e}")
        else:
            _log("eco_widget indisponível para ativar")
        return True
    # Desativar Eco (com variações)
    if low in ("desativar eco", "desative eco", "desliga eco", "para eco", "pare eco", "eco off", "eco desligar"):
        if ECO_WIDGET_AVAILABLE:
            try:
                res = eco_deactivate()
                _log(f"Eco desativado via comando: {res.get('mensagem', 'OK')}")
            except Exception as e:
                _log(f"Erro ao desativar eco: {e}")
        else:
            _log("eco_widget indisponível para desativar")
        return True
    return False

# ==================== WIDGET DISPATCH ====================

def _widget_dispatch(click: str, win):
    if click == "voz":
        at, pa = ler_estado_voz()
        novo_ativo = not (at and not pa)
        try:
            if CONTROLE.exists():
                estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
            else:
                estado = {"ativo": True, "pausado": False}
            estado["ativo"] = novo_ativo
            estado["pausado"] = False if novo_ativo else True
            if novo_ativo:
                estado["buffer_descartado"] = True
            _atomic_write(CONTROLE, estado)
            _log(f"Widget: voz {'ON' if novo_ativo else 'OFF'}")
        except Exception as e:
            _log(f"widget voz error: {e}")
    elif click == "fala":
        at, pa = ler_estado_voz()
        novo_pausado = not pa
        try:
            if CONTROLE.exists():
                estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
            else:
                estado = {"ativo": True, "pausado": False}
            estado["pausado"] = novo_pausado
            if novo_pausado:
                estado["buffer_descartado"] = True
            _atomic_write(CONTROLE, estado)
            if novo_pausado:
                PARAR_FALA.write_text(str(int(time.time())), encoding="utf-8")
                _log("Widget: fala PAUSADA → buffer descartado")
            else:
                _log("Widget: fala RETOMADA (buffer antigo descartado)")
        except Exception as e:
            _log(f"widget stop error: {e}")
    elif click == "mic":
        _log("Widget: mic toggle (Web Speech API no HTML)")
    elif click == "repetir":
        ultimo = _ler_ultimo_resumo()
        if ultimo:
            _log(f"Widget: repetindo último resumo: {ultimo[:50]}...")
            try:
                tts_cmd_obj = {"cmd": "speak", "texto": ultimo, "request_id": str(uuid.uuid4())[:8]}
                _atomic_write(TTS_CMD, tts_cmd_obj)
            except Exception as e:
                _log(f"widget repetir error: {e}")
        else:
            _log("Widget: nenhum resumo para repetir")
    elif click == "close":
        try:
            PARAR_FALA.write_text(str(int(time.time())), encoding="utf-8")
        except Exception:
            pass
        _release_lock()
        import sys as _sys
        _sys.exit(0)
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
            hwnd = ctypes.windll.user32.FindWindowW(None, TITLE)
            if hwnd:
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
            try:
                if GEO_FILE.exists():
                    geo = json.loads(GEO_FILE.read_text(encoding="utf-8"))
                else:
                    geo = {}
                geo["sempre_topo"] = True
                _atomic_write(GEO_FILE, geo)
            except Exception:
                pass
        except Exception:
            pass
    elif click == "fix":
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, TITLE)
            if hwnd:
                ctypes.windll.user32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
                ctypes.windll.user32.SetWindowPos(hwnd, 1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
            try:
                if GEO_FILE.exists():
                    geo = json.loads(GEO_FILE.read_text(encoding="utf-8"))
                else:
                    geo = {}
                geo["sempre_topo"] = False
                _atomic_write(GEO_FILE, geo)
            except Exception:
                pass
        except Exception:
            pass


# ==================== WIDGET POLLER (roda em thread) ====================

def _widget_poller(win, stop_event, init_x=0, init_y=0):
    last_click = ""
    tick = 0
    cur_x = init_x
    cur_y = init_y
    cur_w = DEFAULT_W
    cur_h = DEFAULT_H
    cur_sempre_topo = True
    pos_inited = False
    falas_descartadas = 0
    while not stop_event.wait(0.25):
        # init pos
        if not pos_inited:
            try:
                win.evaluate_js("window.__winPosX=%d;window.__winPosY=%d;" % (init_x, init_y))
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
                    _atomic_write(GEO_FILE, {"x": nx, "y": ny, "width": cur_w, "height": cur_h, "sempre_topo": cur_sempre_topo})
                win.evaluate_js("localStorage.removeItem('jarvis_move')")
            except Exception as e:
                _log(f"[widget drag] error: {e}")
        # push state to UI + read new inputs
        tick += 1
        if tick >= 2:
            tick = 0
            try:
                # Read real window size
                try:
                    size_js = win.evaluate_js("JSON.stringify({w:window.outerWidth||220,h:window.outerHeight||284})")
                    if size_js:
                        sz = json.loads(size_js)
                        cur_w = int(sz.get("w", cur_w))
                        cur_h = int(sz.get("h", cur_h))
                except Exception:
                    pass

                # Read sempre_topo state
                try:
                    st_js = win.evaluate_js("localStorage.getItem('jarvis_sempre_topo')")
                    if st_js is not None:
                        cur_sempre_topo = st_js != "false"
                except Exception:
                    pass

                at, pa = ler_estado_voz()
                voz_on = at and not pa
                tts_ativo_flag = False
                tts_texto = ""
                try:
                    narr = json.loads(CONTROLE.read_text(encoding="utf-8"))
                    tts_ativo_flag = bool(narr.get("ativo", False)) and not bool(narr.get("pausado", False))
                    tts_texto = narr.get("ultimo_texto", "")
                except Exception:
                    pass

                # Read mic state from widget
                mic_on = False
                try:
                    mic_js = win.evaluate_js("localStorage.getItem('jarvis_mic')||'false'")
                    mic_on = mic_js == "true"
                except Exception:
                    pass

                # Read mode from widget
                modo = "narrador"
                try:
                    modo_js = win.evaluate_js("localStorage.getItem('jarvis_modo')||'narrador'")
                    modo = modo_js if modo_js in ("narrador", "dialogo", "silencioso") else "narrador"
                except Exception:
                    pass

                # Read text input from widget
                txt_cmd = ""
                try:
                    txt_js = win.evaluate_js("localStorage.getItem('jarvis_text_cmd')||''")
                    if txt_js:
                        txt_cmd = txt_js
                        win.evaluate_js("localStorage.removeItem('jarvis_text_cmd')")
                except Exception:
                    pass

                # Process text command
                if txt_cmd:
                    _log(f"Widget texto: {txt_cmd[:60]}")
                    # 1. Tenta comandos Eco primeiro
                    if _handle_eco_command(txt_cmd):
                        # Comando Eco processado — já falou via eco_widget
                        pass
                    else:
                        # 2. Fallback: ecoa o comando (comportamento original)
                        try:
                            tts_cmd_obj = {"cmd": "speak", "texto": f"Entendido. Processando: {txt_cmd}", "request_id": str(uuid.uuid4())[:8]}
                            _atomic_write(TTS_CMD, tts_cmd_obj)
                        except Exception as e:
                            _log(f"widget text cmd error: {e}")

                # Handle mic speech result from widget
                try:
                    mic_txt_js = win.evaluate_js("localStorage.getItem('jarvis_mic_text')||''")
                    if mic_txt_js:
                        _log(f"Widget mic texto: {mic_txt_js[:60]}")
                        win.evaluate_js("localStorage.removeItem('jarvis_mic_text')")
                        try:
                            tts_cmd_obj = {"cmd": "speak", "texto": f"Você disse: {mic_txt_js}. Processando seu pedido.", "request_id": str(uuid.uuid4())[:8]}
                            _atomic_write(TTS_CMD, tts_cmd_obj)
                        except Exception as e:
                            _log(f"widget mic text error: {e}")
                except Exception:
                    pass

                # Read and apply mode changes
                if modo == "silencioso" and voz_on:
                    try:
                        if CONTROLE.exists():
                            estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
                            estado["ativo"] = False
                            estado["pausado"] = True
                            _atomic_write(CONTROLE, estado)
                            _log("Widget: modo silencioso → voz OFF")
                            at, pa = False, True
                            voz_on = False
                    except Exception:
                        pass

                # System status (every 10 ticks = ~2.5s)
                sys_status = None
                if tick == 0:
                    try:
                        import psutil
                        cpu = psutil.cpu_percent(interval=0.1)
                        mem = psutil.virtual_memory()
                        disk = psutil.disk_usage("/")
                        sys_status = {"cpu": round(cpu, 1), "ram": round(mem.percent, 1), "disk": round(disk.percent, 1)}
                    except ImportError:
                        try:
                            import shutil
                            disk = shutil.disk_usage("/")
                            sys_status = {"cpu": 0, "ram": 0, "disk": round((disk.used / disk.total) * 100, 1)}
                        except Exception:
                            pass

                # Notifications
                notifs = []
                try:
                    nf = ROOT / "runtime" / "widget_notifs.json"
                    if nf.exists():
                        notifs = json.loads(nf.read_text(encoding="utf-8"))
                        if len(notifs) > 10:
                            notifs = notifs[-10:]
                except Exception:
                    pass

                # Command history
                hist = []
                try:
                    hf = ROOT / "runtime" / "widget_history.json"
                    if hf.exists():
                        hist = json.loads(hf.read_text(encoding="utf-8"))
                        if len(hist) > 10:
                            hist = hist[-10:]
                except Exception:
                    pass

                st = {
                    "voz": voz_on,
                    "mic": mic_on,
                    "ativo": at,
                    "pausado": pa,
                    "tts_ativo": tts_ativo_flag,
                    "texto": tts_texto,
                    "modo": modo,
                }
                if sys_status:
                    st["sys"] = sys_status
                if notifs:
                    st["notifs"] = notifs
                if hist:
                    st["hist"] = hist
                win.evaluate_js(
                    "if(window.applyState)window.applyState(" + json.dumps(st, ensure_ascii=False) + ")"
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
    poller_thread = threading.Thread(target=_widget_poller, args=(win, stop_event, x or 0, y or 0), daemon=True)
    poller_thread.start()

    # Register close handler to save geometry BEFORE window destruction
    def _on_close():
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "Jarvis Controle")
            if hwnd:
                rect = (ctypes.c_int * 4)()
                ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                sx, sy = rect[0], rect[1]
                sw, sh = rect[2] - rect[0], rect[3] - rect[1]
                _atomic_write(GEO_FILE, {"x": sx, "y": sy, "width": sw, "height": sh, "sempre_topo": True})
        except Exception:
            pass
        try:
            PARAR_FALA.write_text(str(int(time.time())), encoding="utf-8")
        except Exception:
            pass
        _release_lock()
        stop_event.set()

    try:
        win.events.closing += _on_close
    except Exception:
        pass

    try:
        _log("Iniciando webview.start()")
        # Tenta com http_port=0 (porta aleatória) para evitar conflito
        webview.start(debug=False, http_port=0)
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
        _log("Widget encerrado")
        try:
            stop_event.set()
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

        def _resumir_para_fala(texto: str) -> str:
            """Aplica regra Fala Resumida: narra apenas 1-3 frases curtas do essencial."""
            if not texto:
                return ""
            # Remove marcas SSML/XML
            import re as _re
            texto = _re.sub(r"<[^>]+>", "", texto)
            # Divide em sentenças
            sentencas = _re.split(r"(?<=[.!?])\s+", texto.strip())
            # Filtra sentenças muito longas (>100 chars) ou técnicas
            curtas = []
            for s in sentencas:
                s = s.strip()
                if not s:
                    continue
                if len(s) > 120:
                    # Tenta encurtar pegando só o início até vírgula ou conjunção
                    partes = _re.split(r",\s*| e\s+| mas\s+| por[ée]m\s+", s)
                    if partes:
                        s = partes[0].strip()
                if len(s) <= 120:
                    curtas.append(s)
                if len(curtas) >= 3:
                    break
            if not curtas:
                # Fallback: primeira frase ou primeiros 120 chars
                primeira = sentencas[0] if sentencas else texto[:120]
                curtas = [primeira.strip()]
            return " ".join(curtas[:3])


        def flush_buffer():
            with buffer_lock:
                textos = list(buffer)
                buffer.clear()
            nonlocal timer
            timer = None

            if not textos:
                return

            texto = " ".join(textos).strip()
            texto = limpar_texto(texto)
            texto = pipeline_completo_tts(texto)
            if PROFILE_HOOK_AVAILABLE:
                texto = format_response_for_profile(texto, _profile_config)
            if len(texto) < 15:
                return

            # REGRA FALA RESUMIDA: narra só 1-3 frases curtas do essencial
            texto = _resumir_para_fala(texto)
            if len(texto) < 10:
                return

            # Verifica se buffer foi descartado (parar fala + reativar)
            try:
                if CONTROLE.exists():
                    estado = json.loads(CONTROLE.read_text(encoding="utf-8"))
                    if estado.get("buffer_descartado", False):
                        estado["buffer_descartado"] = False
                        _atomic_write(CONTROLE, estado)
                        _log(f"buffer descartado (parar fala + reativar): {texto[:40]}...")
                        _add_notif("Buffer descartado (fala interrompida)")
                        return
            except Exception:
                pass

            with falando_lock:
                _log(f"narrador falando ({len(texto)} chars): {texto[:70]}...")
                try:
                    req_id = f"narr_{uuid.uuid4().hex[:8]}"
                    _speak_text(texto, PARAR_FALA, req_id)
                    _salvar_ultimo_resumo(texto)
                    _add_hist(texto[:60])
                except Exception as e:
                    _log(f"falha narrador: {e}")

        saudacao_enviada = False
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
                        if not saudacao_enviada:
                            try:
                                from frases_manager import saudacao_dinamica
                                texto_saudacao = saudacao_dinamica()
                                _log(f"saudação: {texto_saudacao}")
                                req_id = f"saud_{uuid.uuid4().hex[:8]}"
                                _speak_text(texto_saudacao, PARAR_FALA, req_id)
                                saudacao_enviada = True
                            except Exception as e:
                                _log(f"falha saudação: {e}")
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
                    # Re-lê posição do disco periodicamente (widget pode ter resetado)
                    try:
                        pos_now = ler_posicao()
                        ts_now = pos_now.get("ultimo_ts", 0)
                        if ts_now > ultimo_ts:
                            ultimo_ts = ts_now
                            # Descarta buffer obsoleto
                            with buffer_lock:
                                buffer.clear()
                    except Exception:
                        pass
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

    # Widget removido: Edge (widget_edge.py) é o único widget oficial.
    # Mantém o processo vivo para sustentar a thread de narrador/TTS.
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())