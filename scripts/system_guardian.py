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

# PIDs dos serviços Eco protegidos - atualizado a cada ciclo
PROTECTED_ECO_PIDS = set()

# Fonte única de verdade dos serviços Eco: a própria tabela de processos.
# Correspondência por token terminando em "<script>.py" (imune a falsos
# positivos de wrappers powershell/python -c que só CONTÊM a string).
SERVICOS_ECO_SCRIPTS = ("tts_service.py", "widget_edge.py", "dialogo.py", "widget_grafo.py")

def _token_e_script(token, script):
    return ((token or "").lower().strip('"').endswith(script))

def _pids_servicos_eco():
    """Retorna {script_py: pid} do primeiro processo vivo de cada serviço Eco."""
    achados = {}
    for p in psutil.process_iter(["pid", "cmdline"]):
        try:
            for t in (p.info["cmdline"] or []):
                for script in SERVICOS_ECO_SCRIPTS:
                    if script not in achados and _token_e_script(t, script):
                        achados[script] = p.info["pid"]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return achados

def update_protected_eco_pids():
    """Atualiza conjunto de PIDs dos serviços Eco que nunca devem ser mortos.

    Varredura direta da tabela de processos: não lê nem apaga arquivos de
    PID (a trava runtime/widget.pid pertence exclusivamente ao widget).
    """
    global PROTECTED_ECO_PIDS
    PROTECTED_ECO_PIDS = set(_pids_servicos_eco().values())

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
    """Narrador vivo? Agora integrado ao widget — checa state file."""
    try:
        estado_file = BASE / "runtime" / "narracao_estado.json"
        if estado_file.exists():
            import json
            estado = json.loads(estado_file.read_text(encoding="utf-8"))
            return bool(estado.get("ativo", True))
    except Exception:
        pass
    return False

def is_tts_service_up():
    """TTS Service vivo? Fonte única: varredura de cmdline por token."""
    return "tts_service.py" in _pids_servicos_eco()

def is_widget_up():
    """Widget Edge vivo? Fonte única: varredura de cmdline por token."""
    return "widget_edge.py" in _pids_servicos_eco()

def _pid_roda_script(pid, script_py):
    """Verdadeiro se a cmdline do PID termina com SCRIPT_PY.
    Existe desde o primeiro instante do processo (independe de pid file)."""
    try:
        return any(
            (t or "").lower().strip('"').endswith(script_py)
            for t in psutil.Process(pid).cmdline()
        )
    except Exception:
        return False

def start_widget():
    """Inicia o widget_edge.py."""
    try:
        # Edge tem trava própria (O_EXCL em runtime/widget.pid):
        # se já há instância viva, ela continua; nunca matar antes de gerar.
        py = "C:/Users/David Jr/AppData/Local/Programs/Python/Python312/pythonw.exe"
        script = str(BASE / "scripts" / "widget_edge.py")
        proc = subprocess.Popen([py, script], cwd=str(BASE), creationflags=subprocess.CREATE_NO_WINDOW)
        # NÃO escreve runtime/widget.pid: essa trava pertence ao widget (O_EXCL).
        # Guardian é apenas observador via tabela de processos.
        # Aguarda e verifica se widget realmente subiu
        for _ in range(10):
            time.sleep(0.5)
            if not (psutil.pid_exists(proc.pid) and psutil.Process(proc.pid).is_running()):
                log.error(f"Widget morreu logo após iniciar (PID {proc.pid})")
                return False
        log.warning("Widget iniciado e confirmado rodando")
        return True
    except Exception as e:
        log.error(f"Falha ao iniciar widget: {e}")
    return False

def kill_widget():
    """Mata todas as instâncias do widget_edge.py."""
    killed = False
    for p in psutil.process_iter(["pid", "name"]):
        try:
            cmd = " ".join(p.cmdline() or []).lower()
            if "widget_edge" in cmd:
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
    """Narrador agora é thread interna do widget_edge.py — não precisa de processo separado."""
    log.info("Narrador integrado ao widget — start_narrador é no-op")
    return True


def start_tts_service():
    try:
        py = "C:/Users/David Jr/AppData/Local/Programs/Python/Python312/pythonw.exe"
        script = str(BASE / "scripts" / "tts_service.py")
        proc = subprocess.Popen([py, script], cwd=str(BASE), creationflags=subprocess.CREATE_NO_WINDOW)
        # PID file imediato para proteção contra RAM cleanup
        pid_file = BASE / "runtime" / "tts_service.pid"
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(proc.pid))
        # Aguarda e verifica se tts_service realmente subiu
        for _ in range(10):
            time.sleep(0.5)
            if psutil.pid_exists(proc.pid) and psutil.Process(proc.pid).is_running():
                log.warning("TTS Service reiniciado e confirmado rodando")
                return True
        log.error(f"TTS Service morreu logo após iniciar (PID {proc.pid})")
        return False
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
    # Protege serviços Eco (narrador, tts_service, widget) - nunca matar
    for pid_file in [BASE / "runtime" / "narrador.pid", 
                     BASE / "runtime" / "tts_service.pid", 
                     BASE / "runtime" / "widget.pid"]:
        try:
            if pid_file.exists():
                pids.add(int(pid_file.read_text().strip()))
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
        ctrl = BASE / "runtime" / "narracao_estado.json"
        if ctrl.exists():
            d = json.loads(ctrl.read_text(encoding="utf-8"))
            return bool(d.get("ativo", False)) and not bool(d.get("pausado", False))
    except Exception:
        pass
    return False


def is_widget_pid(pid: int) -> bool:
    """Verifica se PID é do widget_edge.py via PID file."""
    try:
        pid_file = BASE / "runtime" / "widget.pid"
        if pid_file.exists():
            return int(pid_file.read_text().strip()) == pid
    except Exception:
        pass
    return False


def is_narrador_pid(pid: int) -> bool:
    """Narrador agora é thread do widget — não há PID separado para proteger."""
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
            # Proteção incondicional dos serviços Eco
            if pid in PROTECTED_ECO_PIDS:
                continue
            if is_bridge(pid) or is_serve(pid) or is_tailscale(pid):
                continue
            # Protege widget/narrador/tts_service se Eco ativo (fallback)
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
    # CLÁUSULA PÉTREA: nunca matar serviços Eco (narrador, tts_service, widget)
    # Proteção dupla: pid file E cmdline (imune a corrida de gravação)
    if (_pid_roda_script(pid, "narrador_desktop.py")
            or _pid_roda_script(pid, "tts_service.py")
            or _pid_roda_script(pid, "widget_edge.py")
            or _pid_roda_script(pid, "widget_grafo.py")
            or is_narrador_pid(pid) or is_tts_service_pid(pid) or is_widget_pid(pid)):
        log.warning(f"Kill bloqueado para serviço Eco PID {pid} ({name}): {reason}")
        return False
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
    # Monitora serviços Eco (narrador, tts_service, widget) - INICIA PRIMEIRO
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
    # Atualiza PIDs protegidos dos serviços Eco APÓS iniciar serviços
    update_protected_eco_pids()
    # Atualiza ESSENTIAL_PIDS com novos PIDs
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
            # Proteção incondicional dos serviços Eco
            if pid in PROTECTED_ECO_PIDS:
                log.warning(f"CPU runaway em serviço Eco PID {pid} - protegido, não matar")
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
    """Lê resultado da auditoria do arquivo atômico (escrito por audit_runner.py)."""
    try:
        result_file = BASE / "runtime" / "audit_result.json"
        if not result_file.exists():
            log.warning("AUDIT: arquivo de resultado não encontrado")
            return
        
        content = result_file.read_text(encoding="utf-8")
        if not content or not content.strip():
            log.warning("AUDIT: arquivo de resultado vazio")
            return
        
        try:
            data = json.loads(content)
        except (json.JSONDecodeError, TypeError) as e:
            log.error(f"AUDIT: JSON inválido - {e}")
            return
        
        # Verifica se resultado não é muito antigo (max 45 min = 2700s)
        age = time.time() - data.get("timestamp", 0)
        if age > 2700:
            log.warning(f"AUDIT: resultado antigo ({age:.0f}s), aguardando novo")
            return
        
        if "error" in data:
            log.error(f"AUDIT erro na execução: {data['error']}")
            return
        
        score = data.get("score", 0)
        findings = data.get("findings", [])
        errors = sum(1 for f in findings if f.get("severity") == "error")
        warns = sum(1 for f in findings if f.get("severity") == "warn")
        
        if errors > 0 or warns > 0:
            log.warning(f"AUDIT: score={score}/100, {errors} erros, {warns} warnings")
        else:
            log.info(f"AUDIT: score={score}/100, tudo OK")
            
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
            capture_output=True, text=True, timeout=30, cwd=str(BASE),
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        )
        if r.returncode == 1:
            log.warning(f"OpenCode resilience: limpeza recomendada - {r.stdout.strip()}")
            r_clean = subprocess.run(
                [sys.executable, str(resilience_script), "--clean"],
                capture_output=True, text=True, timeout=60, cwd=str(BASE),
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            if r_clean.returncode == 0:
                log.info(f"OpenCode cache limpo: {r_clean.stdout.strip()}")
            else:
                detalhe = (r_clean.stderr.strip() or r_clean.stdout.strip() or "sem mensagem")
                log.error(f"OpenCode resilience falhou (exit {r_clean.returncode}): {detalhe[:200]}")
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
                # Executa audit_runner.py em processo separado (protegido do RAM cleanup)
                try:
                    subprocess.run(
                        [sys.executable, str(BASE / "scripts" / "audit_runner.py")],
                        cwd=str(BASE), timeout=60,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                    )
                except subprocess.TimeoutExpired:
                    log.warning("AUDIT: timeout executando audit_runner")
                except Exception as e:
                    log.error(f"AUDIT erro ao executar runner: {e}")
                # Depois lê o resultado (run_audit_periodico agora lê do arquivo)
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
