#!/usr/bin/env python3
"""Wrapper para rodar monitor ADB como daemon persistente no Windows.

Uso:
  python scripts/adb_monitor_daemon.py start   # inicia em background
  python scripts/adb_monitor_daemon.py stop    # para
  python scripts/adb_monitor_daemon.py status  # status
  python scripts/adb_monitor_daemon.py logs    # mostra logs
"""

import os
import sys
import json
import time
import signal
import subprocess
import threading
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent
MONITOR_SCRIPT = SCRIPTS_DIR / 'adb_monitor_silent.py'
PID_FILE = Path(os.environ.get('TEMP', '/tmp')) / 'adb_monitor.pid'
LOG_FILE = Path(os.environ.get('TEMP', '/tmp')) / 'adb_monitor.log'
PYTHON_EXE = sys.executable


def is_running():
    if not PID_FILE.exists():
        return False
    try:
        pid = int(PID_FILE.read_text().strip())
        # Verifica se processo existe
        if os.name == 'nt':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            handle = kernel32.OpenProcess(1, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
            if handle:
                kernel32.CloseHandle(handle)
                return True
            return False
        else:
            os.kill(pid, 0)
            return True
    except (ValueError, OSError, ProcessLookupError):
        return False


def get_pid():
    if PID_FILE.exists():
        try:
            return int(PID_FILE.read_text().strip())
        except ValueError:
            return None
    return None


def start_daemon(interval=30):
    if is_running():
        print(f"[INFO] Monitor já rodando (PID: {get_pid()})")
        return False
    
    # Inicia processo detached
    if os.name == 'nt':
        # Windows: usa CREATE_NEW_PROCESS_GROUP + DETACHED_PROCESS
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        DETACHED_PROCESS = 0x00000008
        proc = subprocess.Popen(
            [PYTHON_EXE, str(MONITOR_SCRIPT), '--interval', str(interval)],
            stdout=open(LOG_FILE, 'a', encoding='utf-8'),
            stderr=subprocess.STDOUT,
            creationflags=CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS,
            start_new_session=True
        )
    else:
        # Linux/Mac: fork duplo
        proc = subprocess.Popen(
            [PYTHON_EXE, str(MONITOR_SCRIPT), '--interval', str(interval)],
            stdout=open(LOG_FILE, 'a', encoding='utf-8'),
            stderr=subprocess.STDOUT,
            start_new_session=True
        )
    
    PID_FILE.write_text(str(proc.pid), encoding="utf-8")
    print(f"[OK] Monitor iniciado (PID: {proc.pid}, interval: {interval}s)")
    print(f"Logs: {LOG_FILE}")
    return True


def stop_daemon():
    pid = get_pid()
    if not pid or not is_running():
        print("[INFO] Monitor não está rodando")
        return False
    
    try:
        if os.name == 'nt':
            import ctypes
            kernel32 = ctypes.windll.kernel32
            # CTRL_BREAK_EVENT para process group
            handle = kernel32.OpenProcess(1, False, pid)  # PROCESS_TERMINATE
            if handle:
                kernel32.TerminateProcess(handle, 0)
                kernel32.CloseHandle(handle)
        else:
            os.kill(pid, signal.SIGTERM)
        
        # Aguarda terminar
        for _ in range(10):
            if not is_running():
                break
            time.sleep(0.5)
        
        PID_FILE.unlink(missing_ok=True)
        print(f"[OK] Monitor parado (PID: {pid})")
        return True
    except Exception as e:
        print(f"[ERRO] Falha ao parar: {e}")
        return False


def show_status():
    if is_running():
        pid = get_pid()
        print(f"Status: RODANDO (PID: {pid})")
        print(f"PID file: {PID_FILE}")
        print(f"Log file: {LOG_FILE}")
        if LOG_FILE.exists():
            size = LOG_FILE.stat().st_size
            print(f"Log size: {size} bytes")
    else:
        print("Status: PARADO")


def show_logs(tail=50, follow=False):
    if not LOG_FILE.exists():
        print("[INFO] Log não existe ainda")
        return
    
    if follow:
        # tail -f estilo
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            f.seek(0, 2)  # fim do arquivo
            while True:
                line = f.readline()
                if line:
                    print(line.rstrip())
                else:
                    time.sleep(0.5)
    else:
        lines = LOG_FILE.read_text(encoding='utf-8').splitlines()
        for line in lines[-tail:]:
            print(line)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Daemon do monitor ADB')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'logs'])
    parser.add_argument('--interval', type=int, default=30, help='Intervalo em segundos')
    parser.add_argument('--tail', type=int, default=50, help='Linhas para mostrar (logs)')
    parser.add_argument('--follow', '-f', action='store_true', help='Follow logs (tail -f)')
    args = parser.parse_args()
    
    if args.action == 'start':
        start_daemon(args.interval)
    elif args.action == 'stop':
        stop_daemon()
    elif args.action == 'restart':
        stop_daemon()
        time.sleep(1)
        start_daemon(args.interval)
    elif args.action == 'status':
        show_status()
    elif args.action == 'logs':
        show_logs(args.tail, args.follow)


if __name__ == '__main__':
    main()