#!/usr/bin/env python3
"""Widget de Supervisao — Dashboard em tempo real via pywebview.

Padroes replicados do widget_edge.py:
- pywebview com js_api (SupervisaoApi)
- Poller daemon que empurra dados ao JS via evaluate_js()
- Singleton por PID (O_CREAT | O_EXCL)
- Estado persistente em JSON com escrita atomica
- Integracao com maestro_estado.json, guardian_state.json, guardian_log.txt, maestro.log
"""
import json
import os
import re
import socket
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    psutil = None

# ---------------------------------------------------------------------------
# Caminhos
# ---------------------------------------------------------------------------
BASE = Path(__file__).resolve().parent.parent
RUNTIME = BASE / "runtime"
SCRIPTS = BASE / "scripts"
WWW = BASE / "www"
UI = WWW / "supervisao.html"

PID_FILE = RUNTIME / "supervisao.pid"
STATE_FILE = RUNTIME / "supervisao_state.json"

MAESTRO_STATE = RUNTIME / "maestro_estado.json"
GUARDIAN_STATE = SCRIPTS / "guardian_state.json"
GUARDIAN_LOG = SCRIPTS / "guardian_log.txt"
MAESTRO_LOG = RUNTIME / "maestro.log"
VOZ_STATE = RUNTIME / "voz_estado.json"

LARGURA = 1100
ALTURA = 900

# ---------------------------------------------------------------------------
# Metadados dos servicos
# ---------------------------------------------------------------------------
SVC_META = {
    "runtime_maestro.py": {"display": "Maestro", "owner": "maestro"},
    "widget_edge.py":     {"display": "Widget",  "owner": "guardian"},
    "tts_service.py":     {"display": "TTS",     "owner": "guardian"},
    "jarvis_bridge.py":   {"display": "Bridge",  "owner": "guardian"},
    "dialogo.py":         {"display": "Dialogo", "owner": "manual"},
    "system_guardian.py": {"display": "Guardian", "owner": "system"},
    "vigilante.ps1":      {"display": "Vigilante", "owner": "system"},
    "watchdog.ps1":       {"display": "Keeper",  "owner": "system"},
}

# ---------------------------------------------------------------------------
# Persistencia atomica (padrao Edge)
# ---------------------------------------------------------------------------
_estado_lock = threading.Lock()


def _ler_estado():
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _salvar_estado(update):
    with _estado_lock:
        estado = _ler_estado()
        estado.update(update)
        tmp = STATE_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(estado, ensure_ascii=False), encoding="utf-8")
        for _ in range(3):
            try:
                os.replace(tmp, STATE_FILE)
                return
            except OSError:
                time.sleep(0.05)


# ---------------------------------------------------------------------------
# Leitura de dados reais
# ---------------------------------------------------------------------------
def _ler_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _ler_log(path, n=20):
    lines = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if line and line.startswith("["):
                    lines.append(line)
        return lines[-n:]
    except Exception:
        return []


def _processos_vivos():
    if not psutil:
        return {}
    achados = {}
    for p in psutil.process_iter(["pid", "cmdline", "memory_info"]):
        try:
            cmd = " ".join(p.info["cmdline"] or []).lower()
            for script in SVC_META:
                if script.replace(".ps1", "") in cmd or script in cmd:
                    if script not in achados:
                        mem = 0
                        try:
                            mem = p.info["memory_info"].rss / (1024 * 1024)
                        except Exception:
                            pass
                        achados[script] = {
                            "pid": p.info["pid"],
                            "vivo": True,
                            "mem_mb": round(mem, 1),
                        }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return achados


def _log_guardian_filtrado(n=10):
    entradas = []
    try:
        with open(GUARDIAN_LOG, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if any(k in line for k in [
                    "reiniciando", "Morto", "RAM critica", "fora do ar",
                    "Bridge", "TTS", "Widget", "Narrador", "iniciado",
                    "MAESTRO_OFFLINE", "registrar:", "parar:",
                ]):
                    entradas.append(line)
        return entradas[-n:]
    except Exception:
        return []


def _parse_log(line):
    try:
        ts = line[:19]
        rest = line[22:] if len(line) > 22 else line
        return {"ts": ts, "raw": rest}
    except Exception:
        return {"ts": "", "raw": line}


def montar_estado():
    maestro = _ler_json(MAESTRO_STATE)
    guardian = _ler_json(GUARDIAN_STATE)
    vivos = _processos_vivos()

    # Estado da voz compartilhado com Edge
    voz_estado = _ler_json(VOZ_STATE)
    voz_ligada = voz_estado.get("ligada", False)

    servicos = {}
    for nome, info in maestro.get("servicos", {}).items():
        meta = SVC_META.get(nome, {"display": nome, "owner": info.get("owner", "?")})
        vivo_real = nome in vivos
        servicos[nome] = {
            "display": meta["display"],
            "pid": vivos[nome]["pid"] if vivo_real else info.get("pid", 0),
            "owner": info.get("owner", "?"),
            "vivo": vivo_real,
            "mem_mb": vivos[nome].get("mem_mb", 0) if vivo_real else 0,
            "motivo": info.get("motivo_inatividade", ""),
            "heartbeat": info.get("last_heartbeat", 0),
        }

    for nome, info in vivos.items():
        if nome not in servicos:
            meta = SVC_META.get(nome, {"display": nome, "owner": "?"})
            servicos[nome] = {
                "display": meta["display"],
                "pid": info["pid"],
                "owner": "?",
                "vivo": True,
                "mem_mb": info.get("mem_mb", 0),
                "motivo": "",
                "heartbeat": 0,
            }

    gc_status = guardian.get("status", "ok")
    gc_ram = guardian.get("ram_mb", 0)
    gc_disk = guardian.get("disk_gb", 0)
    gc_actions = guardian.get("actions", [])

    log_lines = _log_guardian_filtrado(10)
    log_parsed = [_parse_log(l) for l in log_lines]

    maestro_lines = _ler_log(MAESTRO_LOG, 15)
    maestro_log_parsed = [_parse_log(l) for l in maestro_lines]

    return {
        "servicos": servicos,
        "voz_ligada": voz_ligada,
        "guardian": {
            "status": gc_status,
            "ram_mb": gc_ram,
            "disk_gb": gc_disk,
            "actions": gc_actions,
        },
        "log_guardian": log_parsed,
        "log_maestro": maestro_log_parsed,
        "timestamp": datetime.now().isoformat(),
    }


# ---------------------------------------------------------------------------
# API exposta ao JS via pywebview
# ---------------------------------------------------------------------------
class SupervisaoApi:
    """API exposta ao JavaScript via pywebview (window.pywebview.api)."""

    def __init__(self):
        self._window = None
        self._frente = _ler_estado().get("topo", True)
        self._rodando = True

    def status(self):
        est = montar_estado()
        est["frente"] = self._frente
        est["glossario_aberto"] = bool(_ler_estado().get("glossario_aberto", False))
        return est

    def toggle_topo(self):
        """Alterna sempre-no-topo <-> fundo do desktop (replica Edge)."""
        try:
            import ctypes
            self._frente = not self._frente
            hwnd = self._hwnd()
            if not hwnd:
                return self._frente
            u32 = ctypes.windll.user32
            flags = 0x0001 | 0x0002 | 0x0010  # NOSIZE|NOMOVE|NOACTIVATE
            if not self._frente:
                u32.SetWindowPos(hwnd, -2, 0, 0, 0, 0, flags)
                u32.SetWindowPos(hwnd, 1, 0, 0, 0, 0, flags)
            else:
                for tentativa in range(4):
                    if tentativa == 1:
                        u32.SetWindowPos(hwnd, -1, 0, 0, 0, 0,
                                         flags | 0x0040)
                    elif tentativa in (2, 3):
                        try:
                            import webview
                            webview.windows[0].native.TopMost = True
                        except Exception:
                            pass
                    else:
                        u32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, flags)
                    atual = bool(u32.GetWindowLongW(hwnd, -20) & 0x8)
                    if atual == self._frente:
                        break
                    time.sleep(0.25)
            _salvar_estado({"topo": self._frente})
            print("janela: " + ("frente" if self._frente else "fundo"),
                  flush=True)
            return self._frente
        except Exception as e:
            print(f"topo: {type(e).__name__}: {e}", flush=True)
            return self._frente

    def _hwnd(self):
        """Retorna o handle da janela da supervisao."""
        import ctypes
        u32 = ctypes.windll.user32
        # Tentar por titulo
        h = u32.FindWindowW(None, "Cadeia de Supervisao")
        if h:
            return h
        # Tentar pelo processo
        if self._window:
            try:
                import webview
                if webview.windows:
                    return int(webview.windows[0].native._addresses.get(
                        'hwnd', 0))
            except Exception:
                pass
        return u32.GetForegroundWindow()

    def abrir_codigo(self, caminho):
        """Abre o arquivo de codigo-fonte no editor padrao."""
        import subprocess
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        caminho_abs = os.path.normpath(os.path.join(base, caminho))
        if os.path.isfile(caminho_abs):
            subprocess.Popen(["cmd", "/c", "start", "", caminho_abs], shell=False)
            return True
        return False

    def minimizar(self):
        """Minimiza a janela."""
        if self._window:
            self._window.minimize()
        return True

    def maximizar(self):
        """Alterna maximizar/restaurar."""
        if self._window:
            if self._window.maximized:
                self._window.restore()
            else:
                self._window.maximize()
        return True

    def fechar(self):
        """Fecha a janela."""
        self._rodando = False
        if self._window:
            self._window.destroy()
        return True

    def glossario_toggle(self):
        """Alterna estado do glossário (expandido/recolhido)."""
        aberto = not bool(_ler_estado().get("glossario_aberto", False))
        _salvar_estado({"glossario_aberto": aberto})
        return {"glossario_aberto": aberto}


# ---------------------------------------------------------------------------
# Poller — empurra dados ao JS a cada 3s (padrao Edge)
# ---------------------------------------------------------------------------
def _poller(api):
    time.sleep(5)
    while api._rodando:
        try:
            if api._window:
                estado = montar_estado()
                estado["frente"] = api._frente
                js = json.dumps(estado, ensure_ascii=False)
                api._window.evaluate_js(f"window.atualizar({js})")
        except Exception as e:
            print(f"[poller] {e}", flush=True)
        time.sleep(3)


# ---------------------------------------------------------------------------
# Singleton por PID (padrao Edge)
# ---------------------------------------------------------------------------
def _instancia_unica():
    me = str(os.getpid())
    for _ in range(2):
        try:
            fd = os.open(str(PID_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            if psutil:
                try:
                    for p in psutil.process_iter(["pid", "cmdline"]):
                        if p.info["pid"] == os.getpid():
                            continue
                        if any(
                            t.lower().strip('"').endswith("widget_supervisao.py")
                            for t in (p.info["cmdline"] or [])
                        ):
                            os.close(fd)
                            PID_FILE.unlink()
                            return False
                except Exception:
                    pass
            os.write(fd, me.encode())
            os.close(fd)
            return True
        except FileExistsError:
            dono_vivo = False
            try:
                dono = int(PID_FILE.read_text().strip())
                p = psutil.Process(dono)
                if any(t.lower().endswith("widget_supervisao.py") for t in p.cmdline()):
                    dono_vivo = True
            except Exception:
                pass
            if dono_vivo:
                return False
            try:
                PID_FILE.unlink()
            except FileNotFoundError:
                pass
    return False


# ---------------------------------------------------------------------------
# Area util e posicao (padrao Edge)
# ---------------------------------------------------------------------------
def _area_util():
    """(left, top, right, bottom) da area util via SPI_GETWORKAREA."""
    import ctypes

    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

    try:
        rc = RECT()
        ok = ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rc), 0)
        if ok:
            return int(rc.left), int(rc.top), int(rc.right), int(rc.bottom)
    except Exception:
        pass
    u = ctypes.windll.user32
    return 0, 0, u.GetSystemMetrics(0), u.GetSystemMetrics(1)


def _posicao_valida(largura, altura):
    """Posicao salva se ainda couber na area util."""
    try:
        x = int(_ler_estado().get("win_x", 200))
        y = int(_ler_estado().get("win_y", 200))
    except (TypeError, ValueError):
        return None
    l, t, r, b = _area_util()
    if not (l <= x < r and t <= y < b and x + largura <= r + 8 and y + altura <= b + 8):
        return None
    return x, y


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if sys.stdout is None or sys.stderr is None:
        f = open(RUNTIME / "supervisao.log", "a", buffering=1, encoding="utf-8")
        sys.stdout = f
        sys.stderr = f

    import faulthandler
    faulthandler.enable(file=sys.stderr)
    print(time.strftime("[%Y-%m-%d %H:%M:%S] boot"), flush=True)

    if not _instancia_unica():
        print("Supervisao ja esta rodando.", flush=True)
        return
    print("trava ok", flush=True)

    import webview

    api = SupervisaoApi()

    pos = _posicao_valida(LARGURA, ALTURA)
    if pos:
        px, py = pos
    else:
        l, t, r, b = _area_util()
        px = int(l) + 8
        py = max(int(t), int(b) - ALTURA - 8)

    window = webview.create_window(
        "Cadeia de Supervisao",
        str(UI),
        js_api=api,
        x=px,
        y=py,
        width=LARGURA,
        height=ALTURA,
        frameless=True,
        easy_drag=True,
        on_top=True,
        focus=False,
        background_color="#080b12",
    )
    api._window = window
    print("janela criada", flush=True)

    try:
        def _on_moved():
            try:
                x = max(window.x or 0, 0)
                y = max(window.y or 0, 0)
                _salvar_estado({"win_x": x, "win_y": y})
            except Exception:
                pass
        window.events.moved += _on_moved
    except Exception:
        pass

    threading.Thread(target=_poller, args=(api,), daemon=True).start()

    try:
        webview.start()
    finally:
        try:
            if PID_FILE.read_text().strip() == str(os.getpid()):
                PID_FILE.unlink()
        except Exception:
            pass
    print("encerrado", flush=True)


if __name__ == "__main__":
    main()
