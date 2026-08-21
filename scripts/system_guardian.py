import psutil, time, logging, json, os, sys, signal, subprocess
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
LOG = BASE / "scripts" / "guardian_log.txt"
PID_FILE = BASE / "scripts" / "guardian.pid"
STATE_FILE = BASE / "scripts" / "guardian_state.json"
NARRACAO_FILE = BASE / "runtime" / "narracao_estado.json"
BRIDGE_FLAG = BASE / "runtime" / "bridge_enabled.flag"

RAM_CRITICAL_MB = 200
RAM_WARN_MB = 500
CPU_RUNAWAY_PCT = 80.0
CPU_RUNAWAY_SECONDS = 300
CHECK_INTERVAL = 20

CPU_HISTORY = {}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG, encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger("guardian")

def track_cpu(pid, name, cpu_pct):
    now = time.time()
    if pid not in CPU_HISTORY:
        CPU_HISTORY[pid] = {"name": name, "start": now, "samples": []}
    CPU_HISTORY[pid]["samples"].append((now, cpu_pct))
    CPU_HISTORY[pid]["samples"] = [(t, c) for t, c in CPU_HISTORY[pid]["samples"] if now - t < CPU_RUNAWAY_SECONDS + 60]

def is_cpu_runaway(pid):
    if pid not in CPU_HISTORY:
        return False
    samples = CPU_HISTORY[pid]["samples"]
    if len(samples) < CPU_RUNAWAY_SECONDS / CHECK_INTERVAL:
        return False
    avg = sum(c for _, c in samples) / len(samples)
    return avg >= CPU_RUNAWAY_PCT

def is_bridge_up():
    try:
        for conn in psutil.net_connections(kind="tcp"):
            if conn.laddr.port == 8765 and conn.status == "LISTEN":
                return True
    except Exception:
        pass
    return False

def is_serve_up():
    try:
        for conn in psutil.net_connections(kind="tcp"):
            if conn.laddr.port == 8767 and conn.status == "LISTEN":
                return True
    except Exception:
        pass
    return False

def start_bridge():
    try:
        py = "C:/Users/David Jr/AppData/Local/Programs/Python/Python312/python.exe"
        bridge = str(BASE / "scripts" / "jarvis_bridge.py")
        subprocess.Popen([py, bridge], cwd=str(BASE), creationflags=subprocess.CREATE_NO_WINDOW)
        log.warning("Bridge 8765 reiniciado")
        return True
    except Exception as e:
        log.error(f"Falha ao iniciar bridge: {e}")
        return False

def start_serve():
    try:
        opencode = os.path.join(os.environ.get("APPDATA", ""), "npm", "node_modules", "opencode-ai", "bin", "opencode.exe")
        if os.path.exists(opencode):
            subprocess.Popen([opencode, "serve", "--port", "8767"], creationflags=subprocess.CREATE_NO_WINDOW)
            log.warning("Serve 8767 reiniciado")
            return True
    except Exception as e:
        log.error(f"Falha ao iniciar serve: {e}")
    return False

def is_narrador_up():
    """Verifica se narrador_desktop.py está rodando."""
    for p in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            cmd = " ".join(p.info["cmdline"] or []).lower()
            if "narrador_desktop" in cmd:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False
def is_tts_service_up():
    """Verifica se tts_service.py está rodando."""
    for p in psutil.process_iter(["pid", "name"]):
        try:
            cmd = " ".join(p.cmdline() or []).lower()
            if "tts_service" in cmd:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False


def is_widget_up():
    """Verifica se widget_controle_jarvis.py está rodando."""
    for p in psutil.process_iter(["pid", "name"]):
        try:
            cmd = " ".join(p.cmdline() or []).lower()
            if "widget_controle_jarvis" in cmd:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def start_widget():
    """Inicia o widget_controle_jarvis.py."""
    try:
        py = "C:/Users/David Jr/AppData/Local/Programs/Python/Python312/pythonw.exe"
        script = str(BASE / "scripts" / "widget_controle_jarvis.py")
        proc = subprocess.Popen([py, script], cwd=str(BASE), creationflags=subprocess.CREATE_NO_WINDOW)
        # Escreve PID file para proteção contra RAM cleanup
        pid_file = BASE / "runtime" / "widget.pid"
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(proc.pid))
        log.warning("Widget reiniciado")
        return True
    except Exception as e:
        log.error(f"Falha ao iniciar widget: {e}")
    return False

def kill_widget():
    """Mata todas as instâncias do widget_controle_jarvis.py."""
    killed = False
    for p in psutil.process_iter(["pid", "name"]):
        try:
            cmd = " ".join(p.cmdline() or []).lower()
            if "widget_controle_jarvis" in cmd:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except psutil.TimeoutExpired:
                    p.kill()
                log.warning(f"Widget morto PID {p.pid}")
                killed = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return killed

def restart_widget():
    """Reinicia o widget (mata + inicia)."""
    kill_widget()
    time.sleep(1)
    return start_widget()
def start_narrador():
    try:
        py = "C:/Users/David Jr/AppData/Local/Programs/Python/Python312/pythonw.exe"
        script = str(BASE / "scripts" / "narrador_desktop.py")
        proc = subprocess.Popen([py, script], cwd=str(BASE), creationflags=subprocess.CREATE_NO_WINDOW)
        # PID file imediato para proteção contra RAM cleanup
        pid_file = BASE / "runtime" / "narrador.pid"
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(proc.pid))
        log.warning("Narrador reiniciado")
        return True
    except Exception as e:
        log.error(f"Falha ao iniciar narrador: {e}")
    return False


def start_tts_service():
    try:
        py = "C:/Users/David Jr/AppData/Local/Programs/Python/Python312/pythonw.exe"
        script = str(BASE / "scripts" / "tts_service.py")
        proc = subprocess.Popen([py, script], cwd=str(BASE), creationflags=subprocess.CREATE_NO_WINDOW)
        # PID file imediato para proteção contra RAM cleanup
        pid_file = BASE / "runtime" / "tts_service.pid"
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(proc.pid))
        log.warning("TTS Service reiniciado")
        return True
    except Exception as e:
        log.error(f"Falha ao iniciar tts_service: {e}")
    return False

def pause_narrador(reason):
    try:
        state = {"ativo": False, "pausado": True, "motivo": reason}
        NARRACAO_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = NARRACAO_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
        tmp.replace(NARRACAO_FILE)
        log.warning(f"Narrador pausado: {reason}")
    except Exception as e:
        log.error(f"Erro ao pausar narrador: {e}")

def ensure_bridge_flag():
    try:
        BRIDGE_FLAG.parent.mkdir(parents=True, exist_ok=True)
        BRIDGE_FLAG.touch(exist_ok=True)
    except Exception:
        pass

ESSENTIAL_EXES = {
    "winlogon", "services", "lsass", "csrss", "smss",
    "svchost", "System", "Idle", "Registry", "MsMpEng",
    "explorer", "conhost", "dwm", "fontdrvhost",
    "spoolsv", "TeamViewer", "TeamViewer_Service",
    "SecurityHealthService", "SecurityHealthSystray",
    "RuntimeBroker", "sihost", "taskhostw", "ctfmon",
    "SearchIndexer", "ShellExperienceHost",
    "StartMenuExperienceHost", "TextInputHost",
    "Widgets", "LockApp", "SystemSettings",
    "ApplicationFrameHost", "windowsinternal",
    "comhost", "rundll32", "audiodg", "sppsvc",
    "WmiPrvSE", "wlanext", "NisSrv", "MpCmdRun",
}

ESSENTIAL_PIDS = set()

def get_essential_pids():
    pids = set()
    try:
        for p in psutil.process_iter(["pid", "name"]):
            try:
                if p.info["name"] and any(
                    e in p.info["name"].lower() for e in ESSENTIAL_EXES
                ):
                    pids.add(p.info["pid"])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass
    return pids

def is_bridge(pid):
    try:
        p = psutil.Process(pid)
        for conn in p.connections():
            if conn.laddr.port == 8765:
                return True
        cmd = " ".join(p.cmdline()).lower()
        return "jarvis_bridge" in cmd
    except Exception:
        return False

def is_serve(pid):
    try:
        p = psutil.Process(pid)
        for conn in p.connections():
            if conn.laddr.port == 8767:
                return True
        cmd = " ".join(p.cmdline()).lower()
        return "opencode serve" in cmd or "opencode-serve" in cmd
    except Exception:
        return False

def is_tailscale(pid):
    try:
        p = psutil.Process(pid)
        cmd = " ".join(p.cmdline()).lower()
        return "tailscale" in cmd
    except Exception:
        return False

def is_eco_active() -> bool:
    """Verifica se Eco está ativo via narracao_estado.json."""
    try:
        ctrl = ROOT / "runtime" / "narracao_estado.json"
        if ctrl.exists():
            d = json.loads(ctrl.read_text(encoding="utf-8"))
            return bool(d.get("ativo", False)) and not bool(d.get("pausado", False))
    except Exception:
        pass
    return False


def is_widget_pid(pid: int) -> bool:
    """Verifica se PID é do widget_controle_jarvis.py via PID file."""
    try:
        pid_file = BASE / "runtime" / "widget.pid"
        if pid_file.exists():
            return int(pid_file.read_text().strip()) == pid
    except Exception:
        pass
    return False


def is_narrador_pid(pid: int) -> bool:
    """Verifica se PID é do narrador_desktop.py (serviço Eco protegido) via PID file."""
    try:
        pid_file = BASE / "runtime" / "narrador.pid"
        if pid_file.exists():
            return int(pid_file.read_text().strip()) == pid
    except Exception:
        pass
    return False


def is_tts_service_pid(pid: int) -> bool:
    """Verifica se PID é do tts_service.py (serviço Eco protegido) via PID file."""
    try:
        pid_file = BASE / "runtime" / "tts_service.pid"
        if pid_file.exists():
            return int(pid_file.read_text().strip()) == pid
    except Exception:
        pass
    return False


def is_desktop_opencode(pid: int) -> bool:
    """Verifica se PID é o desktop OpenCode (intocável por automação).

    CLÁUSULA PÉTREA — SOBERANIA DO OPCODE DESKTOP: o desktop roda como
    OpenCode.exe em @opencode-aidesktop e NUNCA pode ser fechado por scripts,
    watchdog, bridges ou agentes. Só o usuário pode fechá-lo manualmente.
    """
    try:
        p = psutil.Process(pid)
        path = (p.exe() or "").lower()
        if "@opencode-aidesktop" in path and path.endswith("opencode.exe"):
            return True
    except psutil.AccessDenied:
        # Sem permissão para ler o caminho: usa o nome com capitalização do
        # desktop (OpenCode.exe) como último recurso para nunca matá-lo.
        try:
            if (p.name() or "") == "OpenCode.exe":
                return True
        except Exception:
            pass
    except psutil.NoSuchProcess:
        pass
    return False


def get_kill_candidates():
    candidates = []
    eco_on = is_eco_active()
    for p in psutil.process_iter(["pid", "name", "memory_info", "create_time"]):
        try:
            pid = p.info["pid"]
            if pid < 1000:
                continue
            if pid in ESSENTIAL_PIDS:
                continue
            if is_bridge(pid) or is_serve(pid) or is_tailscale(pid):
                continue
            # Protege widget/narrador/tts_service se Eco ativo
            if eco_on and (is_widget_pid(pid) or is_narrador_pid(pid) or is_tts_service_pid(pid)):
                continue
            # CLÁUSULA PÉTREA: desktop OpenCode (@opencode-aidesktop) é intocável
            if is_desktop_opencode(pid):
                continue

            name = (p.info["name"] or "").lower()
            mem = p.info["memory_info"].rss if p.info["memory_info"] else 0

            if "opencode" in name or "python" in name:
                candidates.append((pid, mem, 0, name))
            elif name == "powershell.exe":
                candidates.append((pid, mem, 1, name))
            elif name == "chrome.exe":
                candidates.append((pid, mem, 2, name))
            elif name == "java.exe" and mem > 100 * 1024 * 1024:
                candidates.append((pid, mem, 3, name))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    candidates.sort(key=lambda x: (x[2], -x[1]))
    return candidates

def kill_process(pid, name, reason):
    try:
        p = psutil.Process(pid)
        mem_mb = p.memory_info().rss / 1024 / 1024
        p.terminate()
        try:
            p.wait(timeout=3)
        except psutil.TimeoutExpired:
            p.kill()
            p.wait(timeout=2)
        log.warning(f"Morto PID {pid} ({name}) - {reason} - liberou ~{mem_mb:.0f} MB")
        return True
    except Exception as e:
        log.error(f"Erro ao matar PID {pid} ({name}): {e}")
        return False

def get_ram_mb():
    return psutil.virtual_memory().available / 1024 / 1024

def get_disk_free_gb():
    return psutil.disk_usage("C:").free / 1024 / 1024 / 1024

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def check_and_act():
    global ESSENTIAL_PIDS
    ESSENTIAL_PIDS = get_essential_pids()

    ram_mb = get_ram_mb()
    disk_gb = get_disk_free_gb()
    ram_pct = psutil.virtual_memory().percent

    state = {
        "timestamp": datetime.now().isoformat(),
        "ram_mb": round(ram_mb, 1),
        "ram_pct": round(ram_pct, 1),
        "disk_gb": round(disk_gb, 1),
        "actions": [],
    }

    ensure_bridge_flag()

    if not is_bridge_up():
        log.warning("Bridge 8765 fora do ar - reiniciando")
        if start_bridge():
            state["actions"].append({"action": "restart_bridge", "port": 8765})
    if not is_serve_up():
        log.warning("Serve 8767 fora do ar - reiniciando")
        if start_serve():
            state["actions"].append({"action": "restart_serve", "port": 8767})
    # Monitora serviços Eco (narrador, tts_service, widget)
    if not is_narrador_up():
        log.warning("Narrador fora do ar - reiniciando")
        if start_narrador():
            state["actions"].append({"action": "restart_narrador"})
    if not is_tts_service_up():
        log.warning("TTS Service fora do ar - reiniciando")
        if start_tts_service():
            state["actions"].append({"action": "restart_tts_service"})
    if not is_widget_up():
        log.warning("Widget fora do ar - reiniciando")
        if start_widget():
            state["actions"].append({"action": "restart_widget"})

    for pid, name in list(CPU_HISTORY.items()):
        try:
            p = psutil.Process(pid)
            cpu = p.cpu_percent(interval=None)
            track_cpu(pid, name, cpu)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            CPU_HISTORY.pop(pid, None)

    for pid, info in list(CPU_HISTORY.items()):
        if is_cpu_runaway(pid):
            if is_desktop_opencode(pid):
                log.warning(f"CPU runaway no desktop OpenCode (PID {pid}) - protegido, nao matar")
                CPU_HISTORY.pop(pid, None)
                continue
            try:
                p = psutil.Process(pid)
                name = info["name"]
                cpu_avg = sum(c for _, c in info["samples"]) / len(info["samples"])
                log.warning(f"CPU runaway detectado: PID {pid} ({name}) média {cpu_avg:.1f}% por {CPU_RUNAWAY_SECONDS}s")
                if kill_process(pid, name, f"CPU runaway {cpu_avg:.1f}% por {CPU_RUNAWAY_SECONDS}s"):
                    state["actions"].append({"action": "kill_cpu_runaway", "pid": pid, "name": name, "cpu_avg": round(cpu_avg, 1)})
                    if name.lower() == "python" and ram_mb < RAM_WARN_MB:
                        pause_narrador(f"CPU runaway python {cpu_avg:.1f}%")
            except Exception as e:
                log.error(f"Erro ao processar runaway PID {pid}: {e}")

    if ram_mb > RAM_WARN_MB:
        state["status"] = "ok"
        save_state(state)
        return

    log.warning(f"RAM critica: {ram_mb:.0f} MB livre - agindo...")
    state["status"] = "critical"

    killed_any = False
    if ram_mb < RAM_CRITICAL_MB:
        state["level"] = "CRITICAL"
        targets = get_kill_candidates()[:6]
    else:
        state["level"] = "WARNING"
        targets = get_kill_candidates()[:3]

    for pid, mem, priority, name in targets:
        if get_ram_mb() > RAM_WARN_MB:
            log.info(f"RAM ja suficiente ({get_ram_mb():.0f} MB), parando de matar")
            break
        mem_mb = mem / 1024 / 1024
        reason = f"RAM {ram_mb:.0f}MB, alvo maior {mem_mb:.0f}MB"
        if kill_process(pid, name, reason):
            killed_any = True
            state["actions"].append({
                "pid": pid,
                "name": name,
                "mem_mb": round(mem_mb, 1),
                "reason": reason,
            })

    if not killed_any and ram_mb < RAM_CRITICAL_MB:
        log.warning("Nada mais para matar - RAM ainda critica")
        state["actions"].append({"note": "Nada para matar, RAM ainda critica"})

    save_state(state)

def run_audit_periodico():
    """Roda audit_eco.py e registra resultado."""
    try:
        audit_script = BASE / "scripts" / "audit_eco.py"
        if not audit_script.exists():
            return
        r = subprocess.run(
            [sys.executable, str(audit_script), "--json"],
            capture_output=True, text=True, timeout=30, cwd=str(BASE)
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            score = data.get("score", 0)
            errors = sum(1 for f in data.get("findings", []) if f.get("severity") == "error")
            warns = sum(1 for f in data.get("findings", []) if f.get("severity") == "warn")
            if errors > 0 or warns > 0:
                log.warning(f"AUDIT: score={score}/100, {errors} erros, {warns} warnings")
            else:
                log.info(f"AUDIT: score={score}/100, tudo OK")
        else:
            log.error(f"AUDIT falhou: {r.stderr[:200]}")
    except Exception as e:
        log.error(f"AUDIT erro: {e}")

AUDIT_INTERVALO = 90  # rodar audit a cada 90 ciclos (90 * 20s = 30 min)
OPENCODE_RESILIENCE_INTERVALO = 45  # rodar resiliência a cada 45 ciclos (45 * 20s = 15 min)

def run_opencode_resilience():
    """Verifica e limpa cache do OpenCode se necessário."""
    try:
        resilience_script = BASE / "scripts" / "opencode_resilience.py"
        if not resilience_script.exists():
            return
        r = subprocess.run(
            [sys.executable, str(resilience_script), "--check"],
            capture_output=True, text=True, timeout=30, cwd=str(BASE)
        )
        if r.returncode == 1:
            log.warning(f"OpenCode resilience: limpeza recomendada - {r.stdout.strip()}")
            r_clean = subprocess.run(
                [sys.executable, str(resilience_script), "--clean"],
                capture_output=True, text=True, timeout=60, cwd=str(BASE)
            )
            if r_clean.returncode == 0:
                log.info(f"OpenCode cache limpo: {r_clean.stdout.strip()}")
            else:
                log.error(f"OpenCode resilience falhou: {r_clean.stderr[:200]}")
        else:
            log.info(f"OpenCode resilience: {r.stdout.strip()}")
    except Exception as e:
        log.error(f"OpenCode resilience erro: {e}")

def run_forever():
    log.info("System Guardian iniciado")
    log.info(f"RAM critica: <{RAM_CRITICAL_MB} MB, alerta: <{RAM_WARN_MB} MB, intervalo: {CHECK_INTERVAL}s")
    log.info(f"Audit periodico: a cada {AUDIT_INTERVALO * CHECK_INTERVAL // 60} minutos")
    log.info(f"OpenCode resilience: a cada {OPENCODE_RESILIENCE_INTERVALO * CHECK_INTERVAL // 60} minutos")

    with open(PID_FILE, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))

    ciclos = 0
    while True:
        try:
            check_and_act()
            ciclos += 1
            if ciclos >= AUDIT_INTERVALO:
                ciclos = 0
                run_audit_periodico()
            if ciclos % OPENCODE_RESILIENCE_INTERVALO == 0:
                run_opencode_resilience()
        except Exception as e:
            log.error(f"Erro no ciclo: {e}")
        time.sleep(CHECK_INTERVAL)

def handle_stop(sig, frame):
    log.info("System Guardian parado")
    if PID_FILE.exists():
        PID_FILE.unlink()
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)
    run_forever()
