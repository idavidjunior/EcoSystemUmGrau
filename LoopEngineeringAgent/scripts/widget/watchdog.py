#!/usr/bin/env python
"""
watchdog.py — Self-healing daemon: detecta MCP down, recupera, escala.

Arquitetura: loop 10s, escreve watchdog_recovery.json.
widget_updater.py mergeia no widget_status.json para o widget exibir.
"""

import subprocess, json, time, os, sys, socket
from datetime import datetime

RECOVERY_FILE = os.path.join(os.path.expanduser("~"), "Desktop", "watchdog_recovery.json")

class State:
    def __init__(self):
        self.consecutive_failures = 0
        self.total_recoveries = 0
        self.critical = False
        self.last_healthy = datetime.now().isoformat()
        self.recovery_history = []
        self.last_status = "ok"

state = State()
MAX_FAILURES = 3

def _safe_run(args, timeout=8):
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        return subprocess.run(args, capture_output=True, text=True, timeout=timeout, startupinfo=si)
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sys.stderr.write(f"[WATCHDOG {ts}] {msg}\n")
    sys.stderr.flush()

def check_mcp_count():
    r = _safe_run(["cmd", "/c", "wmic", "process", "where", "name='python.exe'", "get", "CommandLine"], timeout=5)
    if r is None:
        return 0
    return r.stdout.count("provider_mcp_server")

def kill_all_mcp():
    r = _safe_run(["cmd", "/c", "wmic", "process", "where", "name='python.exe' and CommandLine like '%provider_mcp_server%'", "get", "ProcessId"], timeout=5)
    if r is None:
        return 0
    pids = [int(l.strip()) for l in r.stdout.strip().split("\n") if l.strip().isdigit()]
    for pid in pids:
        _safe_run(["taskkill", "/F", "/PID", str(pid)], timeout=3)
    if pids:
        log(f"Limpou {len(pids)} MCP zumbis")
    return len(pids)

def recover():
    killed = kill_all_mcp()
    log(f"Aguardando OpenCode reiniciar MCP (30s)...")
    for i in range(10):
        time.sleep(3)
        proc = check_mcp_count()
        if proc >= 1:
            log(f"OpenCode reiniciou MCP ({killed} zumbis limpos)")
            return True
    log("OpenCode NAO reiniciou MCP. Escalando...")
    return False

def run_cycle():
    global state
    proc = check_mcp_count()
    healthy = proc >= 1
    now = datetime.now().isoformat()

    if healthy:
        if state.consecutive_failures > 0:
            log(f"Recuperado apos {state.consecutive_failures} falhas")
            state.recovery_history.append({"time": now, "type": "auto_recovery", "action": f"recuperou apos {state.consecutive_failures} falhas"})
        state.consecutive_failures = 0
        state.last_healthy = now
        state.critical = False
        state.last_status = "ok"
        return {"status": "ok", "message": "MCP saudavel"}

    state.consecutive_failures += 1
    log(f"Falha #{state.consecutive_failures}: {proc} proc(s) MCP")

    if state.consecutive_failures >= MAX_FAILURES:
        state.critical = True
        state.last_status = "critical"
        msg = f"CRITICO: {state.consecutive_failures} falhas - MCP precisa de intervencao (reiniciar OpenCode)"
        log(msg)
        state.recovery_history.append({"time": now, "type": "critical", "action": msg})
        return {"status": "critical", "message": msg}

    success = recover()
    state.total_recoveries += 1
    action = f"Recuperacao #{state.total_recoveries}: {'OK' if success else 'FALHA'}"
    log(action)
    state.recovery_history.append({"time": now, "type": "restart_ok" if success else "restart_failed", "action": action})
    if len(state.recovery_history) > 50:
        state.recovery_history = state.recovery_history[-50:]

    if success:
        state.consecutive_failures = 0
        state.last_healthy = now
        state.critical = False
        state.last_status = "recovered"
        return {"status": "recovered", "message": f"MCP recuperado (tentativa #{state.total_recoveries})"}
    else:
        state.last_status = "failed"
        return {"status": "failed", "message": f"Falha #{state.consecutive_failures}/{MAX_FAILURES}"}

def save_status(s):
    data = {
        "status": s["status"],
        "message": s["message"],
        "consecutive_failures": state.consecutive_failures,
        "total_recoveries": state.total_recoveries,
        "last_healthy": state.last_healthy,
        "critical": state.critical,
        "recovery_history": state.recovery_history[-5:],
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        with open(RECOVERY_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

if __name__ == "__main__":
    log("Watchdog iniciado")
    save_status({"status": "ok", "message": "Watchdog iniciado"})
    while True:
        try:
            s = run_cycle()
            save_status(s)
        except Exception as e:
            log(f"Erro no ciclo: {e}")
            import traceback
            log(traceback.format_exc())
            save_status({"status": "error", "message": f"Erro: {e}"})
        time.sleep(10)
