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
import os
import random
import re
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

_NO_CONSOLE = getattr(subprocess, "CREATE_NO_WINDOW", 0)

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

# --- Arquivos de estado do ecossistema (fonte unica) ---
CONTROLE = ROOT / "runtime" / "narracao_estado.json"     # voz: {ativo, pausado}
NARRADOR_PID = ROOT / "runtime" / "narrador.pid"
NARRADOR_POS = ROOT / "runtime" / "narrador_posicao.json"
NARRADOR = SCRIPTS / "narrador_desktop.py"
JARVIS_AUDIO = SCRIPTS / "jarvis_audio.py"               # CLI de controle existente
VOX = SCRIPTS / "vox_audio.py"                            # fallback de fala direta

# --- Estado de microfone (conveno runtime/*.json) ---
MIC_ESTADO = ROOT / "runtime" / "mic_estado.json"
MIC_PID = ROOT / "runtime" / "mic.pid"
DIALOGO = SCRIPTS / "dialogo.py"

LOG_NARRADOR = SCRIPTS / "narrador_desktop_log.txt"      # para texto corrente da fala
PARAR_FALA = ROOT / "runtime" / "parar_fala.flag"        # interrupção de fala (polling no TTS)

# --- Geometria da janela ---
GEO_FILE = ROOT / "runtime" / "widget_controle_geometria.json"

# --- Atalho de inicialização automática ---
ATALHO_WINDOWS = ROOT / "runtime" / "jarvis_atalho.lnk"
VIEW_COPY = ROOT / "docs" / "widget_controle.html"
ICON_PATH = ROOT / "assets" / "jarvis.ico"
DEFAULT_W, DEFAULT_H = 280, 540
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
# Frases — usa módulo unificado frases_manager
# ============================================================

from frases_manager import (
    frases_ativacao,
    frases_desativacao,
    frases_mic_on,
    frases_mic_off,
    frases_interromper,
    frases_minimizar,
    frases_topo,
    frases_tras,
    frases_sleep,
    registrar_saudacao,
    classificar_conexao,
    obter_saudacoes_hoje,
    marcar_atividade,
)

# Aliases para compatibilidade com código existente
def _escolher_frase_ativacao() -> str:
    return frases_ativacao.escolher()


def _aprender_frase_ativacao(nova: str):
    frases_ativacao.aprender(nova)


def _escolher_frase_desativacao() -> str:
    return frases_desativacao.escolher()


def _aprender_frase_desativacao(nova: str):
    frases_desativacao.aprender(nova)


def _escolher_frase_acao(acao: str) -> str:
    manager = {
        "mic_on": frases_mic_on,
        "mic_off": frases_mic_off,
        "interromper": frases_interromper,
        "minimizar": frases_minimizar,
        "topo": frases_topo,
        "tras": frases_tras,
        "sleep": frases_sleep,
    }.get(acao)
    return manager.escolher() if manager else ""


def _aprender_frase_acao(acao: str, nova: str):
    manager = {
        "mic_on": frases_mic_on,
        "mic_off": frases_mic_off,
        "interromper": frases_interromper,
        "minimizar": frases_minimizar,
        "topo": frases_topo,
        "tras": frases_tras,
        "sleep": frases_sleep,
    }.get(acao)
    if manager:
        manager.aprender(nova)


# ============================================================
# Throttling de narração — evita falar em sequência rápido
# ============================================================
_ultima_narracao_ts = 0.0
_NARRACAO_MIN_GAP = 3.0  # segundos mínimo entre frases
_NARRACAO_ACOES_TRIVIAIS = {"minimizar", "tras", "topo"}  # não narra


def _falar_acao(acao: str):
    """Fala frase variada para a ação, com throttling."""
    global _ultima_narracao_ts
    if acao in _NARRACAO_ACOES_TRIVIAIS:
        return  # ações triviais não narra
    agora = time.time()
    if agora - _ultima_narracao_ts < _NARRACAO_MIN_GAP:
        return  # throttle: não fala tão rápido
    try:
        at, pa = ler_estado_voz()
        if at and not pa:
            frase = _escolher_frase_acao(acao)
            if frase:
                _ultima_narracao_ts = agora
                falar_direto(frase)
    except Exception as e:
        print(f"[widget] erro falar_acao({acao}): {e}", flush=True)


def _falar_direto_throttle(texto: str):
    """falar_direto com throttle — usado para transições de voz."""
    global _ultima_narracao_ts
    agora = time.time()
    if agora - _ultima_narracao_ts < _NARRACAO_MIN_GAP:
        return
    _ultima_narracao_ts = agora
    falar_direto(texto)


def _resetar_posicao_narrador():
    """Atualiza narrador_posicao.json para timestamp atual — evita narrar backlog."""
    try:
        agora = int(time.time() * 1000)  # timestamp em ms como o narrador usa
        _atomic_write(NARRADOR_POS, {"ultimo_ts": agora})
    except Exception as e:
        print(f"[widget] erro reset posicao narrador: {e}", flush=True)


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


def _linhas_log():
    try:
        if LOG_NARRADOR.exists():
            return LOG_NARRADOR.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        pass
    return []


def _ts_log(linha):
    m = re.match(r"\[([\dT:.+-]+)\]\s*(.*)", linha)
    if not m:
        return None, linha
    try:
        return datetime.fromisoformat(m.group(1)), m.group(2)
    except ValueError:
        return None, linha


def tts_ativo():
    """True se o narrador estiver falando agora (ultima 'falando' sem falha apos, janela ~120s)."""
    agora = datetime.now()
    ultimo_falando = None
    falha_depois = False
    for linha in _linhas_log():
        ts, resto = _ts_log(linha)
        if ts is None:
            continue
        rk = resto.lower()
        if "falando (" in rk:
            ultimo_falando = ts
            falha_depois = False
        elif "speechpipeline falhou" in rk or "falha de voz" in rk:
            if ultimo_falando is not None and ts > ultimo_falando:
                falha_depois = True
    if ultimo_falando is None or falha_depois:
        return False
    return (agora - ultimo_falando).total_seconds() <= 120


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


# ============================================================
# Novas funções auxiliares — widget features
# ============================================================

WIDGET_STATE = ROOT / "runtime" / "widget_state.json"
MODEL_MONITOR = ROOT / "runtime" / "model_monitor.json"
STATE_FILE = ROOT / "runtime" / "state.json"


def _ler_tema() -> str:
    """ Lê tema do widget_state.json. """
    try:
        if WIDGET_STATE.exists():
            d = json.loads(WIDGET_STATE.read_text(encoding="utf-8"))
            return d.get("theme", "dark")
    except Exception:
        pass
    return "dark"


def _ler_volume() -> int:
    """ Lê volume (0-100) do widget_state.json. """
    try:
        if WIDGET_STATE.exists():
            d = json.loads(WIDGET_STATE.read_text(encoding="utf-8"))
            return int(d.get("volume", 80))
    except Exception:
        pass
    return 80


def _ler_tasks_pendentes() -> list:
    """ Lê pending tasks abertas de state.json. """
    try:
        if STATE_FILE.exists():
            d = json.loads(STATE_FILE.read_text(encoding="utf-8"))
            pending = d.get("pending", [])
            return [{"id": p.get("id"), "text": p.get("text", "")[:80]}
                    for p in pending if not p.get("done", False)][:5]
    except Exception:
        pass
    return []


def _ler_model_stats() -> dict:
    """ Lê stats de llm_feedback.json (dados reais de latência/taxa). """
    try:
        feedback_file = ROOT / "docs" / "llm_feedback.json"
        if feedback_file.exists():
            d = json.loads(feedback_file.read_text(encoding="utf-8"))
            # Pega o modelo com melhor score
            best_model = "N/A"
            best_score = -1
            total_ok = 0
            total_fail = 0
            best_lat = 0
            for modelo, stats in d.items():
                ok = stats.get("sucessos", 0)
                fail = stats.get("falhas", 0)
                total = ok + fail
                if total == 0:
                    continue
                taxa = ok / total
                lat = stats.get("latencia_ms_total", 0) / max(1, ok) if ok else 99999
                s = taxa * 0.8 + max(0.1, 1.0 - (lat - 500) / 14500) * 0.2
                if s > best_score:
                    best_score = s
                    best_model = modelo
                    best_lat = int(lat)
                total_ok += ok
                total_fail += fail
            custo = 0.0  # llm_feedback.json não rastreia custo
            return {"model": best_model, "cost": custo, "limit": 5.0,
                    "latency_ms": best_lat, "latency_max_ms": 20000,
                    "requests": total_ok + total_fail, "success_rate": round(total_ok / max(1, total_ok + total_fail) * 100)}
    except Exception:
        pass
    return {"model": "N/A", "cost": 0.0, "limit": 5.0, "latency_ms": 0, "latency_max_ms": 20000, "requests": 0, "success_rate": 0}


def _ler_recent_errors() -> list:
    """ Lê erros reais dos logs (ignora linhas 'falando' do narrador e warm-up antigo). """
    errors = []
    now = time.time()
    try:
        logs_dir = SCRIPTS
        log_files = sorted(logs_dir.glob("*log*.txt"), key=lambda f: f.stat().st_mtime, reverse=True)[:3]
        for lf in log_files:
            try:
                lines = lf.read_text(encoding="utf-8", errors="replace").splitlines()
                for line in reversed(lines[-300:]):
                    ll = line.lower()
                    # Ignora linhas de narração (frases faladas pelo Jarvis)
                    if "falando (" in ll:
                        continue
                    # Ignora warm-up do bridge (não é erro real)
                    if "warm-up" in ll:
                        continue
                    # Ignora erros muito antigos (>30 min)
                    # Aceita formato ISO (T) e formato com vírgula (2026-08-20 08:33:44,436)
                    ts_match = re.match(r'[\[(\s]*(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})', line)
                    if ts_match:
                        try:
                            from datetime import datetime
                            ts_str = ts_match.group(1).replace("T", " ")
                            log_time = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                            age_min = (now - log_time.timestamp()) / 60
                            if age_min > 30:
                                continue
                        except Exception:
                            pass
                    # Padrões de erro reais (match com formato dos logs)
                    is_real_error = (
                        "[error]" in ll or
                        "error:" in ll or
                        "[erro]" in ll or
                        ("[warning]" in ll and "falhou" in ll) or
                        ("warning:" in ll and ("erro" in ll or "falhou" in ll)) or
                        "traceback" in ll or
                        "exception:" in ll or
                        "falha de voz" in ll or
                        "speechpipeline falhou" in ll or
                        # "erro" como palavra isolada, não como substring de "interrompido"
                        (ll.startswith("[") and re.search(r'\berro\b', ll) and "falando" not in ll)
                    )
                    if is_real_error:
                        ts, msg = _ts_log(line)
                        if msg:
                            errors.append(msg[:100])
                        if len(errors) >= 3:
                            break
            except Exception:
                pass
            if errors:
                break
    except Exception:
        pass
    return errors


def _ler_notificacoes() -> list:
    """ Lê últimas mensagens faladas pelo narrador (últimas 3). """
    notifs = []
    try:
        if LOG_NARRADOR.exists():
            for line in reversed(LOG_NARRADOR.read_text(encoding="utf-8", errors="replace").splitlines()):
                if "falando (" in line.lower():
                    ts, msg = _ts_log(line)
                    if msg:
                        notifs.append(msg[:100])
                    if len(notifs) >= 3:
                        break
    except Exception:
        pass
    return notifs


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
        "conn": {
            "narrador": narrador_rodando(),
            "tts": tts_ativo() or narrador_rodando(),
            "bridge": tts_ativo(),
        },
        "volume": _ler_volume(),
        "sleep": {"active": False, "remaining": 0, "minutes": 0},
        "tasks": _ler_tasks_pendentes(),
        "errors": _ler_recent_errors(),
        "model": _ler_model_stats(),
        "theme": _ler_tema(),
        "notifs": _ler_notificacoes(),
    }


# ============================================================
# Acoes de controle (rodam em background via threads)
# ============================================================

def _detached():
    return getattr(subprocess, "DETACHED_PROCESS", 0) | subprocess.CREATE_NEW_PROCESS_GROUP | _NO_CONSOLE


def _thread(target, *args):
    threading.Thread(target=target, args=args, daemon=True).start()


# TTS via serviço único (tts_service.py) — elimina duplicidade de SpeechPipeline
import uuid

TTS_CMD = ROOT / "runtime" / "tts_cmd.json"
PARAR_FALA = ROOT / "runtime" / "parar_fala.flag"


def _enviar_tts_cmd(cmd: dict):
    """Envia comando de voz ao tts_service com escrita atômica resiliente a lock (WinError 5)."""
    TTS_CMD.parent.mkdir(parents=True, exist_ok=True)
    tmp = TTS_CMD.with_suffix(".tmp")
    tmp.write_text(json.dumps(cmd, ensure_ascii=False), encoding="utf-8")
    for _ in range(6):
        try:
            tmp.replace(TTS_CMD)
            return
        except OSError:
            time.sleep(0.15)
    try:
        tmp.replace(TTS_CMD)
    except OSError as e:
        print(f"[widget] falha de voz: {e}", flush=True)

# Perfil do usuário para formatação
try:
    from user_profile import get_profile
    _widget_profile_config = get_profile().get_response_config()
    WIDGET_PROFILE_AVAILABLE = True
except ImportError as e:
    print(f"[widget] user_profile não disponível: {e}", flush=True)
    _widget_profile_config = {}
    WIDGET_PROFILE_AVAILABLE = False
    def format_response_for_profile(texto, config):
        return texto
    def get_response_config():
        return {}


def _falar_direto_worker(texto: str):
    # Se o narrador_desktop.py já está rodando e fala ativa, ele vai ler do SQLite.
    # O widget só fala direto para feedbacks rápidos de botões, então:
    # 1) Não falar se o narrador já está falando agora (evita sobreposição)
    # 2) Envia para tts_service.py (processo único de TTS)
    try:
        if narrador_rodando() and tts_ativo():
            return  # Narrador já fala — deixe-o terminar
        if WIDGET_PROFILE_AVAILABLE:
            texto = format_response_for_profile(texto, _widget_profile_config)
        req_id = str(uuid.uuid4())[:8]
        cmd = {"cmd": "speak", "texto": texto, "request_id": req_id, "priority": 1}
        _enviar_tts_cmd(cmd)
        # Não aguarda resposta (fire-and-forget para feedbacks rápidos)
    except Exception as e:
        print(f"[widget] falha de voz direta: {e}", flush=True)


def falar_direto(texto: str):
    _thread(_falar_direto_worker, texto)


def cmd_voz(ativar: bool):
    try:
        if ativar:
            _resetar_posicao_narrador()
            # Widget JÁ é o narrador — só seta estado ativo
            _atomic_write(CONTROLE, {"ativo": True, "pausado": False})
            frase = _escolher_frase_ativacao()
            falar_direto(frase)
        else:
            frase = _escolher_frase_desativacao()
            falar_direto(frase)
            _atomic_write(CONTROLE, {"ativo": False, "pausado": True})
    except Exception as e:
        print(f"[widget] erro voz({'on' if ativar else 'off'}): {e}", flush=True)


def cmd_interromper_fala():
    _falar_acao("interromper")
    try:
        PARAR_FALA.write_text(str(int(time.time())), encoding="utf-8")
    except Exception as e:
        print(f"[widget] erro parar_fala.flag: {e}", flush=True)
    try:
        subprocess.run([sys.executable, str(JARVIS_AUDIO), "stop"],
                       cwd=str(ROOT), capture_output=True, creationflags=_NO_CONSOLE, timeout=20)
    except Exception as e:
        print(f"[widget] erro stop: {e}", flush=True)
    # Mantém a flag por 1.5s: o narrador checa a flag a cada 0.05s durante a
    # fala (SpeechPipeline.speak block=True, stop_flag=PARAR_FALA) e a consome
    # via unlink ao detectar. Apagar imediatamente causava corrida — a flag
    # sumia antes do polling e a fala continuava.
    time.sleep(1.5)
    try:
        PARAR_FALA.unlink(missing_ok=True)
    except Exception as e:
        print(f"[widget] erro limpar flag: {e}", flush=True)
    print("[widget] voz interrompida", flush=True)


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
            _atomic_write(MIC_ESTADO, {
                "ativo": True,
                "status": "listening",
                "modo": "vad",
                "timestamp": int(time.time()),
            })
            _falar_acao("mic_on")
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
        _atomic_write(MIC_ESTADO, {"ativo": False, "status": "off", "timestamp": int(time.time())})
        _falar_acao("mic_off")


def _reconciliar_mic():
    """Limpa estado órfão de microfone (ativo sem processo vivo)."""
    if MIC_ESTADO.exists():
        try:
            d = json.loads(MIC_ESTADO.read_text(encoding="utf-8"))
            if d.get("ativo", False) and not mic_ativo():
                _atomic_write(MIC_ESTADO, {"ativo": False, "status": "off", "timestamp": int(time.time())})
                MIC_PID.unlink(missing_ok=True)
        except Exception:
            pass


# ============================================================
# Geometria da janela
# ============================================================

def _enviar_para_tras(win):
    """Envia a janela para trás de todas as outras janelas (Z-order bottom)."""
    _set_window_zorder(win, topmost=False)
    _falar_acao("tras")


def _fixar_no_topo(win):
    """Fixar janela no topo de todas as outras (HWND_TOPMOST)."""
    _set_window_zorder(win, topmost=True)
    _falar_acao("topo")


def _set_window_zorder(win, topmost: bool):
    """Define Z-order da janela via Windows API."""
    try:
        import ctypes
        user32 = ctypes.windll.user32
        
        # Constantes Windows
        HWND_TOPMOST = -1
        HWND_NOTOPMOST = -2
        HWND_BOTTOM = 1
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_NOACTIVATE = 0x0010
        
        # Tenta obter HWND
        hwnd = None
        try:
            if hasattr(win, 'gui') and win.gui:
                hwnd = getattr(win.gui, 'hwnd', None) or getattr(win.gui, '_hwnd', None)
        except Exception:
            pass
        
        if not hwnd:
            hwnd = user32.FindWindowW(None, TITLE)
        
        if hwnd:
            if topmost:
                # Fixar no topo (acima de todas)
                user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                  SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
                print(f"[widget] Janela fixada no topo (HWND: {hwnd})", flush=True)
            else:
                # Remover fixação no topo OU enviar para trás
                user32.SetWindowPos(hwnd, HWND_NOTOPMOST, 0, 0, 0, 0,
                                  SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
                # Se for "Trás", envia para bottom
                if not topmost:
                    user32.SetWindowPos(hwnd, HWND_BOTTOM, 0, 0, 0, 0,
                                      SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)
                print(f"[widget] Janela {'fixada no topo' if topmost else 'enviada para trás'} (HWND: {hwnd})", flush=True)
        else:
            print("[widget] HWND não encontrado", flush=True)
    except Exception as e:
        print(f"[widget] erro z-order: {e}", flush=True)


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
        # Padrão: canto inferior esquerdo
        area = _screen_area()
        if area:
            sw, sh = area
            return {"x": 0, "y": max(0, sh - DEFAULT_H), "width": DEFAULT_W, "height": DEFAULT_H}
        return {"x": 0, "y": None, "width": DEFAULT_W, "height": DEFAULT_H}
    try:
        raw = GEO_FILE.read_text(encoding="utf-8")
        d = json.loads(raw) if raw.strip() else {}
    except Exception:
        d = {}
    return _clamp_geo({"x": d.get("x"), "y": d.get("y"),
                       "width": int(d.get("width", DEFAULT_W)),
                       "height": int(d.get("height", DEFAULT_H))})


def _minimizar(win):
    """Minimiza a janela. Tenta win.minimize() nativo, depois JS; fallback hide com estado."""
    _falar_acao("minimizar")
    try:
        win.minimize()
        return
    except Exception:
        pass
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
            var st=window.__sempre_topo||True;
            localStorage.setItem('jarvis_geo', JSON.stringify({x:x,y:y,width:w,height:h,sempre_topo:st}));
          })();
        """)
    except Exception:
        pass


# ============================================================
# HTML / CSS / JS (self-contained; Python-Driven via evaluate_js)
# ============================================================

HTML = r"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link rel="icon" href="jarvis.ico" type="image/x-icon">
<style>
:root{--bg:#1e1e2e;--sb:#313244;--in:#181825;--tx:#cdd6f4;--tx2:#a6adc8;--tx3:#6c7086;
--on:#a6e3a1;--off:#f38ba8;--acc:#89b4fa;--warn:#f9e2af;--stop:#f28465;--bdr:#45475a;}
*{margin:0;padding:0;box-sizing:border-box;}
html,body{overflow:hidden;font-family:'Segoe UI',system-ui,sans-serif;
background:var(--bg);color:var(--tx);width:100%;height:100%;}
.topbar{background:var(--sb);height:22px;cursor:move;
display:flex;align-items:center;justify-content:space-between;
padding:0 8px;font-size:11px;color:var(--tx2);user-select:none;}
.drag{flex:1;cursor:move;min-height:22px;}
.close{background:var(--off);width:14px;height:14px;border-radius:3px;
display:flex;align-items:center;justify-content:center;
font-size:10px;line-height:1;cursor:pointer;color:var(--bg);font-weight:bold;}
.controls{padding:10px;display:flex;flex-direction:column;gap:8px;overflow-y:auto;}
.btn{display:flex;align-items:center;justify-content:space-between;
padding:7px 9px;border:none;border-radius:6px;cursor:pointer;
font-size:12px;background:var(--sb);color:var(--tx);transition:.15s;}
.btn:hover{filter:brightness(1.15);}
.btn.on{background:var(--on);color:var(--bg);}
.btn.off{background:var(--off);color:var(--bg);}
.btn.stop{background:var(--stop);color:var(--bg);}
.btn.sm{padding:5px 7px;font-size:11px;text-align:center;justify-content:center;}
.sw{width:8px;height:8px;border-radius:50%;display:inline-block;margin-right:5px;}
.sw.on{background:var(--on);box-shadow:0 0 6px var(--on);}
.sw.off{background:var(--off);}
.row{display:flex;gap:6px;}
.row .btn{flex:1;}
.section-title{font-size:9px;color:var(--tx3);text-transform:uppercase;
letter-spacing:0.5px;margin-top:6px;margin-bottom:3px;}
.info{font-size:9px;color:var(--tx3);word-break:break-word;padding:6px 8px;
background:var(--in);border-radius:5px;min-height:18px;}
.info.falando{color:var(--on);font-weight:500;}

.conn-row{display:flex;gap:8px;font-size:9px;color:var(--tx3);align-items:center;}
.conn-dot{width:6px;height:6px;border-radius:50%;display:inline-block;}
.conn-dot.on{background:var(--on);box-shadow:0 0 4px var(--on);}
.conn-dot.off{background:var(--off);}

.vol-row{display:flex;align-items:center;gap:6px;}
.vol-row label{font-size:10px;color:var(--tx2);}
.vol-slider{-webkit-appearance:none;appearance:none;width:100%;height:3px;
border-radius:2px;background:var(--bdr);outline:none;}
.vol-slider::-webkit-slider-thumb{-webkit-appearance:none;appearance:none;
width:10px;height:10px;border-radius:50%;background:var(--acc);cursor:pointer;}
.vol-val{font-size:10px;color:var(--tx2);min-width:24px;text-align:right;}

.tasks-list{font-size:9px;color:var(--tx2);max-height:50px;overflow-y:auto;}
.task-item{padding:2px 0;border-bottom:1px solid var(--sb);white-space:nowrap;
overflow:hidden;text-overflow:ellipsis;}
.task-item:last-child{border:none;}

.error-toast{position:fixed;top:30px;left:50%;transform:translateX(-50%);
background:var(--sb);color:var(--off);font-size:10px;padding:5px 24px 5px 10px;
border-radius:4px;border:1px solid var(--off);z-index:999;max-width:90%;
text-align:center;animation:fadeIn .3s;display:none;cursor:pointer;}
.error-toast .dismiss{position:absolute;right:4px;top:2px;font-size:12px;
color:var(--off);cursor:pointer;font-weight:bold;}
@keyframes fadeIn{from{opacity:0;transform:translateX(-50%) translateY(-5px);}
to{opacity:1;transform:translateX(-50%) translateY(0);}}

.model-chip{display:inline-flex;align-items:center;gap:4px;font-size:9px;
color:var(--tx2);background:var(--in);padding:2px 6px;border-radius:3px;}

.sleep-row{display:flex;align-items:center;gap:6px;}
.sleep-row select{background:var(--in);color:var(--tx);border:1px solid var(--bdr);
border-radius:4px;font-size:10px;padding:2px 4px;}
.sleep-info{font-size:9px;color:var(--warn);}
.sleep-active{color:var(--warn);font-weight:500;}

.themes-row{display:flex;gap:4px;}
.theme-btn{width:16px;height:16px;border-radius:50%;border:2px solid transparent;
cursor:pointer;transition:.15s;}
.theme-btn.active{border-color:var(--tx);}
.theme-btn:hover{transform:scale(1.15);}
.theme-btn.dark{background:#1e1e2e;}
.theme-btn.neon{background:#0a0a1a;}
.theme-btn.calm{background:#1a2332;}

.notif-log{font-size:9px;color:var(--tx2);max-height:48px;overflow-y:auto;}
.notif-item{padding:2px 0;border-bottom:1px solid var(--sb);white-space:nowrap;
overflow:hidden;text-overflow:ellipsis;}
.notif-item:last-child{border:none;}

::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-track{background:var(--in);}
::-webkit-scrollbar-thumb{background:var(--bdr);border-radius:2px;}

.pulse{animation:pulse 1s infinite;}
@keyframes pulse{0%,100%{opacity:1;}50%{opacity:.3;}}
</style>
</head><body>
<div class="error-toast" id="errorToast"><span id="errorMsg"></span><span class="dismiss" id="errorDismiss">x</span></div>
<div class="topbar">
  <div style="display:flex;align-items:center;gap:4px;">
    <div class="drag" id="drag"></div><span>Jarvis</span>
  </div>
  <div class="close" id="closeBtn" title="Fechar">x</div>
</div>
<div class="controls">
  <div class="conn-row">
    <span><span class="conn-dot off" id="dotNarr"></span>Narr</span>
    <span><span class="conn-dot off" id="dotTTS"></span>TTS</span>
    <span><span class="conn-dot off" id="dotBridge"></span>Bridge</span>
    <span style="flex:1"></span>
    <span class="model-chip" id="modelChip">-</span>
  </div>
  <div class="row">
    <button class="btn off" id="btnVoz"><span><span class="sw off" id="swVoz"></span>Voz</span><span id="lblVoz">OFF</span></button>
    <button class="btn stop" id="btnFala"><span>Stop</span></button>
  </div>
  <div class="row">
    <button class="btn off" id="btnMic"><span><span class="sw off" id="swMic"></span>Mic</span><span id="lblMic">OFF</span></button>
    <button class="btn" id="btnRepetir">Repetir</button>
  </div>
  <div class="info" id="info">conectando...</div>
  <div class="vol-row">
    <label>Voz</label>
    <input type="range" class="vol-slider" id="volSlider" min="0" max="100" value="80">
    <span class="vol-val" id="volVal">80</span>
  </div>
  <div class="sleep-row">
    <select id="sleepSelect">
      <option value="0">Timer</option>
      <option value="5">5 min</option>
      <option value="15">15 min</option>
      <option value="30">30 min</option>
      <option value="60">1h</option>
      <option value="120">2h</option>
    </select>
    <span class="sleep-info" id="sleepInfo"></span>
  </div>
  <div class="section-title">Tarefas</div>
  <div class="tasks-list" id="tasksList">-</div>
  <div class="section-title">Notificacoes</div>
  <div class="notif-log" id="notifLog">-</div>
  <div class="themes-row">
    <div class="theme-btn dark active" id="themeDark" title="Dark"></div>
    <div class="theme-btn neon" id="themeNeon" title="Neon"></div>
    <div class="theme-btn calm" id="themeCalm" title="Calm"></div>
  </div>
  <div class="row">
    <button class="btn sm" id="minimizeBtn">_</button>
    <button class="btn sm" id="topoBtn">Top</button>
    <button class="btn sm" id="fixBtn">Tras</button>
  </div>
</div>
<script>
(function(){
  var _volTimer=null;
  function cls(el,c){ if(el) el.className=c; }

  var themes={
    dark:{bg:'#1e1e2e',sb:'#313244',in:'#181825',tx:'#cdd6f4',tx2:'#a6adc8',tx3:'#6c7086',bdr:'#45475a'},
    neon:{bg:'#0a0a1a',sb:'#151528',in:'#080818',tx:'#e0e0ff',tx2:'#9090c0',tx3:'#505080',bdr:'#252550'},
    calm:{bg:'#1a2332',sb:'#243447',in:'#152030',tx:'#d0dce8',tx2:'#8898a8',tx3:'#586878',bdr:'#344458'}
  };
  function applyTheme(t){
    var th=themes[t]||themes.dark;
    var r=document.documentElement;
    r.style.setProperty('--bg',th.bg);r.style.setProperty('--sb',th.sb);
    r.style.setProperty('--in',th.in);r.style.setProperty('--tx',th.tx);
    r.style.setProperty('--tx2',th.tx2);r.style.setProperty('--tx3',th.tx3);
    r.style.setProperty('--bdr',th.bdr);
    document.body.style.background=th.bg;document.body.style.color=th.tx;
    document.querySelector('.topbar').style.background=th.sb;
    document.querySelector('.topbar').style.color=th.tx2;
    document.querySelector('.close').style.background=var_off;
    document.querySelectorAll('.btn:not(.on):not(.off):not(.stop)').forEach(function(b){
      b.style.background=th.sb;b.style.color=th.tx;
    });
    document.querySelectorAll('.info:not(.falando)').forEach(function(i){
      i.style.background=th.in;i.style.color=th.tx3;
    });
    document.querySelectorAll('.theme-btn').forEach(function(b){
      cls(b,'theme-btn '+b.id.replace('theme','').toLowerCase()+(t===b.id.replace('theme','').toLowerCase()?' active':''));
    });
    document.querySelector('.tasks-list').style.color=th.tx2;
    document.querySelector('.notif-log').style.color=th.tx2;
    document.querySelectorAll('.task-item,.notif-item').forEach(function(el){
      el.style.borderBottomColor=th.sb;
    });
    localStorage.setItem('jarvis_theme',t);
  }
  var var_off='#f38ba8';

  window.applyState = function(s){
    var v=s.voz, m=s.mic;
    cls(document.getElementById('swVoz'),'sw '+(v?'on':'off'));
    cls(document.getElementById('btnVoz'),'btn '+(v?'on':'off'));
    document.getElementById('lblVoz').textContent = v?'ON':'OFF';
    cls(document.getElementById('swMic'),'sw '+(m?'on':'off'));
    cls(document.getElementById('btnMic'),'btn '+(m?'on':'off'));
    document.getElementById('lblMic').textContent = m?'ON':'OFF';
    if(m) document.getElementById('btnMic').classList.add('pulse');
    else document.getElementById('btnMic').classList.remove('pulse');
    var info=document.getElementById('info');
    if(s.tts_ativo){ info.textContent=(s.texto||'FALANDO').substring(0,80); info.className='info falando'; }
    else if(s.ativo){ info.textContent='JARVIS ativo | online'; info.className='info'; }
    else { info.textContent='online (voz off)'; info.className='info'; }
    if(s.conn){
      var cn=s.conn.narrador,ct=s.conn.tts,cb=s.conn.bridge;
      cls(document.getElementById('dotNarr'),'conn-dot '+(cn?'on':'off'));
      cls(document.getElementById('dotTTS'),'conn-dot '+(ct?'on':'off'));
      cls(document.getElementById('dotBridge'),'conn-dot '+(cb?'on':'off'));
    }
    if(s.model){
      var mc=document.getElementById('modelChip');
      var name=s.model.model.split('/').pop();
      var lat=s.model.latency_ms||0;
      var latStr=lat>0?lat+'ms':'-';
      var reqs=s.model.requests||0;
      var sr=s.model.success_rate||0;
      mc.textContent=name+' | '+latStr+' | '+reqs+'r '+sr+'%';
    }
    if(s.volume!==undefined){
      var sl=document.getElementById('volSlider');
      if(document.activeElement!==sl){sl.value=s.volume;}
      document.getElementById('volVal').textContent=s.volume;
    }
    if(s.sleep){
      var si=document.getElementById('sleepInfo');
      if(s.sleep.active&&s.sleep.remaining>0){
        var mm=Math.floor(s.sleep.remaining/60),sec=s.sleep.remaining%60;
        si.textContent=mm+':'+(sec<10?'0':'')+sec;
        si.className='sleep-info sleep-active';
      }else{si.textContent='';si.className='sleep-info';}
    }
    if(s.tasks&&s.tasks.length>0){
      var h='';
      s.tasks.forEach(function(t){h+='<div class="task-item">#'+t.id+' '+t.text+'</div>';});
      document.getElementById('tasksList').innerHTML=h;
    }else{document.getElementById('tasksList').textContent='-';}
    if(s.notifs&&s.notifs.length>0){
      var nh='';
      s.notifs.forEach(function(n){nh+='<div class="notif-item">'+n+'</div>';});
      document.getElementById('notifLog').innerHTML=nh;
    }else{document.getElementById('notifLog').textContent='-';}
    if(s.errors&&s.errors.length>0){
      var toast=document.getElementById('errorToast');
      document.getElementById('errorMsg').textContent=s.errors[0];
      toast.style.display='block';
    }
    if(s.theme) applyTheme(s.theme);
  };

  function clickSet(k){ localStorage.setItem('jarvis_click', k); }
  document.getElementById('btnVoz').addEventListener('click', function(){
    var isOn=this.classList.contains('on');
    cls(this,isOn?'btn off':'btn on'); document.getElementById('lblVoz').textContent=isOn?'OFF':'ON'; clickSet('voz');
  });
  document.getElementById('btnFala').addEventListener('click', function(){ clickSet('fala'); });
  document.getElementById('btnRepetir').addEventListener('click', function(){ clickSet('repetir'); });
  document.getElementById('btnMic').addEventListener('click', function(){
    var isOn=this.classList.contains('on');
    cls(this,isOn?'btn off':'btn on'); document.getElementById('lblMic').textContent=isOn?'OFF':'ON'; clickSet('mic');
  });

  document.getElementById('volSlider').addEventListener('input', function(){
    document.getElementById('volVal').textContent=this.value;
  });
  document.getElementById('volSlider').addEventListener('change', function(){
    var v=this.value;
    if(_volTimer) clearTimeout(_volTimer);
    _volTimer=setTimeout(function(){clickSet('volume:'+v);},200);
  });

  document.getElementById('sleepSelect').addEventListener('change', function(){
    var v=parseInt(this.value);
    clickSet('sleep:'+v);
  });

  document.getElementById('themeDark').addEventListener('click',function(){clickSet('theme:dark');});
  document.getElementById('themeNeon').addEventListener('click',function(){clickSet('theme:neon');});
  document.getElementById('themeCalm').addEventListener('click',function(){clickSet('theme:calm');});

  document.getElementById('errorDismiss').addEventListener('click',function(){
    document.getElementById('errorToast').style.display='none';
  });
  document.getElementById('errorToast').addEventListener('click',function(){
    this.style.display='none';
  });

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
_sleep_timer = None
_sleep_end_time = 0


def _dispatch(click: str, win):
    global _sleep_end_time
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
        _thread(_fixar_no_topo, win)
    elif click == "fix":
        _thread(_enviar_para_tras, win)
    elif click.startswith("volume:"):
        try:
            vol = max(0, min(100, int(click.split(":", 1)[1])))
            ws = {}
            if WIDGET_STATE.exists():
                try:
                    ws = json.loads(WIDGET_STATE.read_text(encoding="utf-8"))
                except Exception:
                    ws = {}
            ws["volume"] = vol
            _atomic_write(WIDGET_STATE, ws)
        except Exception as e:
            print(f"[widget] erro volume: {e}", flush=True)
    elif click.startswith("theme:"):
        theme = click.split(":", 1)[1]
        ws = {}
        if WIDGET_STATE.exists():
            try:
                ws = json.loads(WIDGET_STATE.read_text(encoding="utf-8"))
            except Exception:
                ws = {}
        ws["theme"] = theme
        _atomic_write(WIDGET_STATE, ws)
    elif click.startswith("sleep:"):
        try:
            mins = int(click.split(":", 1)[1])
            if mins <= 0:
                _sleep_end_time = 0
                _falar_acao("sleep")
            else:
                _sleep_end_time = time.time() + mins * 60
        except Exception as e:
            print(f"[widget] erro sleep: {e}", flush=True)
    elif click == "stop_sleep":
        _sleep_end_time = 0
    elif click == "close":
        try:
            win.evaluate_js("localStorage.removeItem('jarvis_click')")
        except Exception:
            pass
        # Para TTS do widget e narrador antes de fechar
        try:
            if WIDGET_SPEECH_AVAILABLE and _WIDGET_SPEECH:
                _WIDGET_SPEECH.stop()
        except Exception:
            pass
        # Sinaliza narrador para parar
        try:
            PARAR_FALA.write_text(str(int(time.time())), encoding="utf-8")
        except Exception:
            pass
        # Para vox_audio se estiver rodando
        try:
            subprocess.run([sys.executable, str(JARVIS_AUDIO), "stop"],
                           cwd=str(ROOT), capture_output=True, creationflags=_NO_CONSOLE, timeout=5)
        except Exception:
            pass
        _thread(win.destroy)


def _toggle_always_on_top(win, on_top: bool):
    """Alterna preferência de janela sempre no topo e aplica imediatamente."""
    try:
        geo = _carregar_geo()
        geo["sempre_topo"] = on_top
        _atomic_write(GEO_FILE, geo)
        # Aplica imediatamente via Windows API
        _set_window_zorder(win, topmost=on_top)
        # Feedback visual no JS
        win.evaluate_js(f"localStorage.setItem('jarvis_mode', '{'always' if on_top else 'behind'}')")
        win.evaluate_js(f"console.log('[widget] sempre_topo: {on_top} (aplicado imediatamente)')")
    except Exception as e:
        print(f"[widget] erro toggle on_top: {e}", flush=True)


def _poller(win, stop, init_x=None, init_y=None):
    """loop principal: detecta cliques + drag via localStorage, empurra estado via evaluate_js."""
    last_click = ""
    tick = 0
    cur_x = init_x if init_x is not None else 0
    cur_y = init_y if init_y is not None else 0
    _pos_inited = False
    _last_voz_ativo = None  # rastreia transição de voz para narrar ativação/desativação

    while not stop.wait(0.25):
        if not _pos_inited:
            try:
                win.evaluate_js(
                    "window.__winPosX=%d;window.__winPosY=%d;" % (int(cur_x), int(cur_y)))
                _pos_inited = True
            except Exception:
                pass
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
        elif click:
            # Mesmo botão clicado novamente — processa e limpa
            last_click = ""
            _dispatch(click, win)
            try:
                win.evaluate_js("localStorage.removeItem('jarvis_click')")
            except Exception:
                pass
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
        tick += 1
        if tick >= 4:
            tick = 0
            try:
                st = estado_unificado()
                # Sleep timer check
                global _sleep_end_time
                if _sleep_end_time > 0:
                    remaining = _sleep_end_time - time.time()
                    if remaining <= 0:
                        _sleep_end_time = 0
                        _atomic_write(CONTROLE, {"ativo": False, "pausado": True})
                    else:
                        st["sleep"] = {
                            "active": True,
                            "remaining": int(remaining),
                            "minutes": max(1, int(remaining / 60)),
                        }
                # Detecta transição de voz para narrar ativação/desativação
                voz_ativo = st.get("voz", False)
                if _last_voz_ativo is not None and voz_ativo != _last_voz_ativo:
                    if voz_ativo:
                        _falar_direto_throttle("Eco ativado")
                    else:
                        _falar_direto_throttle("Eco desativado")
                _last_voz_ativo = voz_ativo

                win.evaluate_js(
                    "if(window.applyState)window.applyState(" + json.dumps(st) + ")",
                )
            except Exception:
                pass


def _processos_com(cmd_fragmento: str) -> list[int]:
    """Retorna PIDs de processos python/pythonw cuja linha de comando contém o fragmento."""
    pids = []
    try:
        saida = subprocess.run(
            ["wmic", "process", "where", "name='python.exe' or name='pythonw.exe'",
             "get", "ProcessId,CommandLine"],
            capture_output=True, text=True, timeout=10
        )
        for linha in saida.stdout.splitlines():
            if cmd_fragmento in linha:
                partes = linha.strip().split()
                if partes:
                    try:
                        pid = int(partes[-1])
                        if pid != os.getpid():
                            pids.append(pid)
                    except ValueError:
                        pass
    except Exception:
        pass
    return pids


def _garantir_instancia_unica() -> None:
    """Trava contra duplicação de widgets Jarvis.

    O unified_bridge.py é a ponte única canônica (narrador + TTS + widget).
    O widget_controle_jarvis.py é o widget antigo que NÃO deve rodar separado.
    Regras:
      1. Se o unified_bridge.py já está rodando, o widget antigo sai.
      2. Se já existe outro widget_controle_jarvis.py, o mais novo sai.
    """
    # 1) unified_bridge.py rodando? Widget antigo não abre por cima.
    bridges = _processos_com("unified_bridge.py")
    if bridges:
        print(f"[widget] unified_bridge.py já ativo (PIDs {bridges}) - widget antigo não abre.", flush=True)
        sys.exit(0)
    # 2) Duplicata do próprio widget? Mantém o mais antigo.
    duplicatas = _processos_com("widget_controle_jarvis.py")
    if duplicatas:
        print(f"[widget] Outra instância do widget já ativa (PIDs {duplicatas}) - saindo.", flush=True)
        sys.exit(0)


def _self_test_error_filter():
    """Auto-teste: valida se o filtro de erros casa com os formatos reais dos logs.

    Roda na inicialização do widget. Se detectar mismatch, loga aviso.
    Motivo: erros de formato no filtro causam erros stale no toast do widget.
    """
    ts_pattern = r'[\[(\s]*(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2})'
    test_samples = [
        "2026-08-20 08:33:44,436 ERROR:vox:HTTP 500",
        "[2026-08-20 10:19:53] FALHA ao restaurar desktop",
    ]
    for sample in test_samples:
        if not re.match(ts_pattern, sample):
            print(f"[widget SELF-TEST] FALHA: regex timestamp não casa com: {sample[:50]}", flush=True)
            return False

    # Verifica se padrões de erro casam com formato ERROR:vox: do bridge
    log_files = sorted(SCRIPTS.glob("*log*.txt"), key=lambda f: f.stat().st_mtime, reverse=True)[:2]
    sample_lines = []
    for lf in log_files:
        try:
            lines = lf.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in lines[-100:]:
                if "error" in line.lower() or "warning" in line.lower():
                    sample_lines.append(line)
                    if len(sample_lines) >= 5:
                        break
        except Exception:
            pass
        if len(sample_lines) >= 5:
            break

    if sample_lines:
        error_patterns = ["error:", "[error]", "traceback", "exception:", "falha de voz"]
        matched = sum(1 for l in sample_lines if any(p in l.lower() for p in error_patterns))
        if matched == 0 and sample_lines:
            print(f"[widget SELF-TEST] AVISO: nenhum erro real casou com padrões ({len(sample_lines)} linhas testadas)", flush=True)
            return False

    print("[widget SELF-TEST] Filtro de erros OK", flush=True)
    return True


def main() -> int:
    global _janela_global
    _garantir_instancia_unica()
    import webview

    _self_test_error_filter()
    _reconciliar_mic()
    _resetar_posicao_narrador()  # evita narrar backlog antigo ao iniciar
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