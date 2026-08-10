"""
Watchdog do OpenCode Serve — monitora e reinicia automaticamente o serve
quando ele trava ou retorna erros 500.

Uso:
  python scripts/serve_watchdog.py          # inicia o watchdog
  python scripts/serve_watchdog.py --check  # verifica uma vez e sai
  python scripts/serve_watchdog.py --stop   # para o watchdog rodando

O watchdog roda como processo independente e monitora o serve a cada
WATCHDOG_INTERVAL segundos. Se o serve não responder ou retornar 500,
ele mata o processo e inicia um novo.
"""

import argparse
import json
import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

WORKDIR = Path(r"C:\Users\David Jr\Documents\Default Project")
BIN = str(Path(os.environ["APPDATA"]) / r"npm\node_modules\opencode-ai\bin\opencode.exe")
PORT = int(os.environ.get("OPENCODE_SERVE_PORT", "8767"))
PORT_RESERVA = int(os.environ.get("OPENCODE_SERVE_PORT_RESERVA", "8768"))
SERVER_USER = "opencode"
SERVER_PASS = ""
try:
    _env = SCRIPTS_DIR / ".env"
    if _env.exists():
        for _ln in _env.read_text(encoding="utf-8").splitlines():
            if _ln.startswith("OPENCODE_SERVER_PASSWORD="):
                SERVER_PASS = _ln.split("=", 1)[1].strip().strip('"').strip("'")
                break
except Exception:
    pass
if not SERVER_PASS:
    SERVER_PASS = os.environ.get("OPENCODE_SERVER_PASSWORD", "")

BIN_DIR = str(Path(os.environ["APPDATA"]) / r"npm\node_modules\opencode-ai\bin\opencode.exe")

WATCHDOG_INTERVAL = 30
WATCHDOG_LOG = SCRIPTS_DIR / "watchdog.log"
PID_FILE = SCRIPTS_DIR / "watchdog.pid"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("watchdog")
try:
    fh = logging.FileHandler(WATCHDOG_LOG, mode="a", encoding="utf-8")
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s:%(name)s:%(message)s"))
    logger.addHandler(fh)
except PermissionError:
    pass


def _port_responding(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        r = s.connect_ex(("127.0.0.1", port))
        s.close()
        return r == 0
    except Exception:
        return False


def _serve_healthy(port):
    if not SERVER_PASS:
        return _port_responding(port)
    try:
        import base64
        import urllib.request
        creds = base64.b64encode(f"{SERVER_USER}:{SERVER_PASS}".encode()).decode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/session",
            data=json.dumps({"title": "watchdog-health"}).encode(),
            method="POST",
            headers={"Content-Type": "application/json", "Authorization": f"Basic {creds}"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            if "id" in data:
                sid = data["id"]
                body = json.dumps({"parts": [{"type": "text", "text": "ok"}]}).encode()
                req2 = urllib.request.Request(
                    f"http://127.0.0.1:{port}/session/{sid}/message",
                    data=body,
                    method="POST",
                    headers={"Content-Type": "application/json", "Authorization": f"Basic {creds}"},
                )
                with urllib.request.urlopen(req2, timeout=60) as resp2:
                    d2 = json.loads(resp2.read().decode())
                    texts = [p.get("text", "") for p in d2.get("parts", []) if p.get("type") == "text"]
                    return len(texts) > 0
        return False
    except Exception as e:
        logger.warning(f"health check falhou: {e}")
        return False


def _find_serve_pid(port):
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for line in result.stdout.splitlines():
            if f":{port}" in line and "LISTENING" in line:
                pid = line.split()[-1].strip()
                if pid.isdigit():
                    return int(pid)
    except Exception:
        pass
    return None


def _kill_pid(pid):
    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return True
    except Exception:
        return False


def _start_serve(port):
    try:
        proc = subprocess.Popen(
            [BIN_DIR, "serve", "--port", str(port)],
            cwd=str(WORKDIR),
            env={**os.environ, "OPENCODE_SERVER_PASSWORD": SERVER_PASS},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for _ in range(15):
            time.sleep(1)
            if _port_responding(port):
                logger.info(f"serve iniciado na porta {port} (pid={proc.pid})")
                return True
        logger.error(f"serve não subiu na porta {port} após 15s")
        return False
    except Exception as e:
        logger.error(f"erro ao iniciar serve: {e}")
        return False


def _restart_serve(port):
    logger.warning(f"reiniciando serve na porta {port}...")
    pid = _find_serve_pid(port)
    if pid:
        logger.info(f"matando processo {pid}")
        _kill_pid(pid)
        time.sleep(2)
    return _start_serve(port)


def check_once():
    for port in (PORT, PORT_RESERVA):
        if _port_responding(port):
            if _serve_healthy(port):
                print(f"[OK] serve saudável na porta {port}")
                return True
            else:
                print(f"[WARN] serve na porta {port} não responde bem, reiniciando...")
                if _restart_serve(port):
                    print(f"[OK] serve reiniciado na porta {port}")
                    return True
    print(f"[ERROR] serve não encontrado nas portas {PORT}/{PORT_RESERVA}")
    return False


def run_watchdog():
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            os.kill(old_pid, 0)
            print(f"watchdog já está rodando (pid={old_pid})")
            return
        except (OSError, ValueError):
            pass
    PID_FILE.write_text(str(os.getpid()))
    logger.info("=" * 50)
    logger.info("  Serve Watchdog iniciado")
    logger.info(f"  portas: {PORT}, {PORT_RESERVA}")
    logger.info(f"  intervalo: {WATCHDOG_INTERVAL}s")
    logger.info("=" * 50)
    consecutive_failures = 0
    max_failures = 3
    try:
        while True:
            time.sleep(WATCHDOG_INTERVAL)
            healthy = False
            for port in (PORT, PORT_RESERVA):
                if _port_responding(port) and _serve_healthy(port):
                    healthy = True
                    consecutive_failures = 0
                    break
            if not healthy:
                consecutive_failures += 1
                logger.warning(f"serve não saudável ({consecutive_failures}/{max_failures})")
                if consecutive_failures >= max_failures:
                    logger.warning(f"limite atingido ({max_failures}) — reiniciando serve")
                    for port in (PORT, PORT_RESERVA):
                        if _port_responding(port):
                            if _restart_serve(port):
                                consecutive_failures = 0
                                break
                    else:
                        if _start_serve(PORT):
                            consecutive_failures = 0
    except KeyboardInterrupt:
        logger.info("watchdog interrompido")
    finally:
        try:
            PID_FILE.unlink()
        except Exception:
            pass


def stop_watchdog():
    if not PID_FILE.exists():
        print("watchdog não está rodando")
        return
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 9)
        PID_FILE.unlink()
        print(f"watchdog (pid={pid}) parado")
    except Exception as e:
        print(f"erro ao parar watchdog: {e}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Watchdog do OpenCode Serve")
    ap.add_argument("--check", action="store_true", help="verifica uma vez e sai")
    ap.add_argument("--stop", action="store_true", help="para o watchdog rodando")
    args = ap.parse_args()
    if args.stop:
        stop_watchdog()
    elif args.check:
        check_once()
    else:
        run_watchdog()
