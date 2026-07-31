import psutil, time, logging, json, os, sys, signal
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).parent.parent
LOG = BASE / "scripts" / "guardian_log.txt"
PID_FILE = BASE / "scripts" / "guardian.pid"
STATE_FILE = BASE / "scripts" / "guardian_state.json"

RAM_CRITICAL_MB = 200
RAM_WARN_MB = 500
CHECK_INTERVAL = 20

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG, encoding="utf-8"), logging.StreamHandler()],
)
log = logging.getLogger("guardian")

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
            if conn.laddr.port == 8766:
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

def get_kill_candidates():
    candidates = []
    for p in psutil.process_iter(["pid", "name", "memory_info", "create_time"]):
        try:
            pid = p.info["pid"]
            if pid < 1000:
                continue
            if pid in ESSENTIAL_PIDS:
                continue
            if is_bridge(pid) or is_serve(pid) or is_tailscale(pid):
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
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

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

def run_forever():
    log.info("System Guardian iniciado")
    log.info(f"RAM critica: <{RAM_CRITICAL_MB} MB, alerta: <{RAM_WARN_MB} MB, intervalo: {CHECK_INTERVAL}s")

    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    while True:
        try:
            check_and_act()
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
