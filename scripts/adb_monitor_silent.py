#!/usr/bin/env python3
"""Monitor ADB silencioso e inteligente.

- Sem output no console (roda truly background)
- Loga APENAS mudanças de estado (desconectou/reconectou)
- Usa `adb track-devices` para eventos em tempo real (mecanismo principal)
- Fallback: polling adaptativo (5s desconectado / 60s estável)
- Backoff progressivo com jitter na reconexão automática
- Single instance (PID file lock)
- Toda lógica de conexão delegada ao adb_connection_manager.py
"""

import json
import subprocess
import sys
import os
import time
import signal
from pathlib import Path
from datetime import datetime

# Windows: evita criar console janela em subprocessos
CREATE_NO_WINDOW = 0x08000000

SCRIPTS_DIR = Path(__file__).parent
sys.path.insert(0, str(SCRIPTS_DIR))

from adb_connection_manager import ConnectionManager, RETRYING, find_adb

PID_FILE = Path(os.environ.get('TEMP', '/tmp')) / 'adb_monitor_silent.pid'
LOG_FILE = Path(os.environ.get('TEMP', '/tmp')) / 'adb_monitor_silent.log'

# Intervalos (s)
POLL_CONNECTED = 60
POLL_DISCONNECTED = 5

# Estado
_running = True
_last_devices = None


def _write_log(entry: dict):
    """Escreve log estruturado (JSONL) - apenas mudanças."""
    entry['ts'] = datetime.now().isoformat(timespec='seconds')
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass


def _current_connected_ids(cm: ConnectionManager):
    """IDs de devices 'device' atuais."""
    devices = cm._devices()
    return tuple(sorted(d['id'] for d in devices if d['state'] == 'device'))


def _reconnect(cm: ConnectionManager):
    """Tenta reconectar com backoff progressivo central."""
    cm.state = RETRYING
    _write_log({'event': 'auto_reconnect_attempt', 'attempt': cm.attempts})
    result = cm.connect()
    if result['success']:
        cm._reset_backoff()
        _write_log({'event': 'auto_reconnect', 'method': result.get('transport'),
                    'device': result.get('device')})
        return True
    else:
        _write_log({'event': 'reconnect_failed', 'error': result.get('error'),
                    'backoff_idx': cm.backoff_idx})
        return False


def _monitor_loop(cm: ConnectionManager):
    global _running, _last_devices

    _write_log({'event': 'monitor_start', 'pid': os.getpid()})

    # Tenta track-devices como mecanismo principal (30s de candidatura)
    # Se suportado, rola em thread; senão cai para polling.
    track_supported = [False]

    def _on_track_change(serial, prev, state):
        _write_log({'event': 'device_state_change', 'serial': serial,
                    'prev': prev, 'state': state})
        if state == 'device':
            _write_log({'event': 'reconnected', 'devices': [serial]})
        elif prev == 'device':
            _write_log({'event': 'disconnected', 'lost': [serial]})
            # Tenta reconectar
            _reconnect(cm)

    try:
        track_supported[0] = cm.track_devices(on_change=_on_track_change, timeout=8)
    except Exception:
        track_supported[0] = False

    # Estado inicial
    _last_devices = _current_connected_ids(cm)
    _write_log({'event': 'initial_state',
                'connected': bool(_last_devices),
                'devices': list(_last_devices),
                'track_devices': track_supported[0]})

    # Loop principal (polling é sempre um fallback/verificação periódica)
    while _running:
        try:
            current = _current_connected_ids(cm)

            if current != _last_devices:
                prev_connected = bool(_last_devices)
                connected = bool(current)
                if connected and not prev_connected:
                    _write_log({'event': 'reconnected', 'devices': list(current)})
                elif not connected and prev_connected:
                    _write_log({'event': 'disconnected', 'lost': list(_last_devices)})
                    _reconnect(cm)
                else:
                    _write_log({'event': 'changed', 'devices': list(current)})
                _last_devices = current

            # Intervalo adaptativo
            sleep = POLL_CONNECTED if current else POLL_DISCONNECTED
            for _ in range(sleep):
                if not _running:
                    break
                time.sleep(1)

        except Exception as e:
            _write_log({'event': 'error', 'error': str(e)})
            time.sleep(10)

    _write_log({'event': 'monitor_stop'})


def _signal_handler(signum, frame):
    global _running
    _running = False


def _acquire_lock() -> bool:
    """Single instance via PID file."""
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            if _pid_alive(old_pid):
                return False
        except (ValueError, OSError):
            pass
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    return True


def _pid_alive(pid: int) -> bool:
    try:
        if os.name == 'nt':
            import ctypes
            h = ctypes.windll.kernel32.OpenProcess(1, False, pid)
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return True
            return False
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def _release_lock():
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def _stop():
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if _pid_alive(pid):
                if os.name == 'nt':
                    import ctypes
                    h = ctypes.windll.kernel32.OpenProcess(1, False, pid)
                    if h:
                        ctypes.windll.kernel32.TerminateProcess(h, 0)
                        ctypes.windll.kernel32.CloseHandle(h)
                else:
                    os.kill(pid, signal.SIGTERM)
                _release_lock()
                print("Monitor parado")
                return
            _release_lock()
            print("Monitor já parado (lock removido)")
            return
        except Exception:
            _release_lock()
            print("Monitor já parado (lock removido)")
            return
    print("Monitor não está rodando")


def _status():
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            if _pid_alive(pid):
                print(f"Rodando (PID: {pid})")
                return
            print("Parado (PID órfão)")
            return
        except Exception:
            print("Parado (lock órfão)")
            return
    print("Parado")


def _logs():
    if LOG_FILE.exists():
        lines = LOG_FILE.read_text(encoding='utf-8', errors='replace').strip().splitlines()
        for line in lines[-20:]:
            try:
                print(json.loads(line))
            except Exception:
                print(line)
    else:
        print("Sem logs")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Monitor ADB silencioso')
    parser.add_argument('action', nargs='?', default='start',
                        choices=['start', 'stop', 'status', 'logs'])
    args = parser.parse_args()

    if args.action == 'stop':
        _stop()
        return
    if args.action == 'status':
        _status()
        return
    if args.action == 'logs':
        _logs()
        return

    # START
    if not _acquire_lock():
        print("Monitor já rodando")
        return

    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)

    adb = find_adb()
    if not os.path.exists(adb):
        _write_log({'event': 'error', 'error': f'ADB não encontrado: {adb}'})
        _release_lock()
        return

    cm = ConnectionManager(adb=adb)
    cm.load_state()

    # NÃO daemoniza - o wrapper (adb_monitor_daemon.py) cuida disso
    _monitor_loop(cm)
    _release_lock()


if __name__ == '__main__':
    main()
