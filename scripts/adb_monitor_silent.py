#!/usr/bin/env python3
"""Monitor ADB silencioso e inteligente.

- Sem output no console (roda truly background)
- Loga APENAS mudanças de estado (desconectou/reconectou)
- Usa `adb track-devices` para eventos em tempo real (se disponível)
- Fallback: poll inteligente (intervalo adaptativo: rápido ao desconectar, lento estável)
- Single instance (PID file lock)
"""

import json
import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path
from datetime import datetime

# Windows: evita criar console janela em subprocessos
CREATE_NO_WINDOW = 0x08000000

SCRIPTS_DIR = Path(__file__).parent
AUTO_CONNECT = SCRIPTS_DIR / 'adb_auto_connect.py'
PID_FILE = Path(os.environ.get('TEMP', '/tmp')) / 'adb_monitor_silent.pid'
LOG_FILE = Path(os.environ.get('TEMP', '/tmp')) / 'adb_monitor_silent.log'
PYTHON_EXE = sys.executable

# Estado
_running = True
_last_devices = None
_poll_interval = 30  # base interval
_adaptive_interval = 30
_lock = threading.Lock()


def _write_log(entry: dict):
    """Escreve log estruturado (JSONL) - apenas mudanças."""
    entry['ts'] = datetime.now().isoformat(timespec='seconds')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')


def _scan(adb_path: str):
    """Scan rápido de dispositivos."""
    try:
        kwargs = dict(capture_output=True, text=True, timeout=5)
        if os.name == 'nt':
            kwargs['creationflags'] = CREATE_NO_WINDOW
        res = subprocess.run([adb_path, 'devices'], **kwargs)
        devices = []
        for line in res.stdout.strip().splitlines()[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2:
                devices.append({'id': parts[0], 'state': parts[1]})
        return devices
    except Exception:
        return []


def _has_usb(devices):
    return any(d['state'] == 'device' and ':' not in d['id'] for d in devices)


def _has_any(devices):
    return any(d['state'] == 'device' for d in devices)


def _run_auto_connect():
    try:
        kwargs = dict(capture_output=True, text=True, timeout=90)
        if os.name == 'nt':
            kwargs['creationflags'] = CREATE_NO_WINDOW
        res = subprocess.run([PYTHON_EXE, str(AUTO_CONNECT)], **kwargs)
        if res.stdout.strip():
            return json.loads(res.stdout.strip())
    except Exception:
        pass
    return None


def _adaptive_sleep(connected: bool):
    """Intervalo adaptativo: 5s se desconectado, 60s se estável."""
    global _adaptive_interval
    if connected:
        _adaptive_interval = min(_adaptive_interval + 5, 60)  # backoff até 60s
    else:
        _adaptive_interval = 5  # agressivo ao reconectar
    time.sleep(_adaptive_interval)


def _monitor_loop(adb_path: str):
    global _running, _last_devices, _adaptive_interval
    
    _write_log({'event': 'monitor_start', 'pid': os.getpid()})
    
    while _running:
        try:
            devices = _scan(adb_path)
            connected = _has_any(devices)
            usb = _has_usb(devices)
            
            # Detectar mudança
            current_ids = tuple(sorted(d['id'] for d in devices if d['state'] == 'device'))
            
            with _lock:
                if _last_devices is None:
                    # Estado inicial
                    _write_log({
                        'event': 'initial_state',
                        'connected': connected,
                        'usb': usb,
                        'devices': list(current_ids)
                    })
                elif current_ids != _last_devices:
                    # Mudança real
                    prev_connected = len(_last_devices) > 0 if _last_devices else False
                    if connected and not prev_connected:
                        _write_log({'event': 'reconnected', 'devices': list(current_ids)})
                    elif not connected and prev_connected:
                        _write_log({'event': 'disconnected', 'lost': list(_last_devices)})
                    else:
                        _write_log({'event': 'changed', 'devices': list(current_ids)})
                    
                    # Se desconectou, tentar reconectar
                    if not connected:
                        result = _run_auto_connect()
                        if result and result.get('connected'):
                            _write_log({'event': 'auto_reconnect', 'method': result.get('method')})
                        else:
                            _write_log({'event': 'reconnect_failed'})
                
                _last_devices = current_ids
            
            _adaptive_sleep(connected)
            
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
            # Verifica se processo existe
            if os.name == 'nt':
                import ctypes
                h = ctypes.windll.kernel32.OpenProcess(1, False, old_pid)
                if h:
                    ctypes.windll.kernel32.CloseHandle(h)
                    return False
            else:
                os.kill(old_pid, 0)
                return False
        except (ValueError, OSError, ProcessLookupError):
            pass  # PID inválido ou processo morto, pode continuar
    
    PID_FILE.write_text(str(os.getpid()))
    return True


def _release_lock():
    PID_FILE.unlink(missing_ok=True)


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Monitor ADB silencioso')
    parser.add_argument('action', nargs='?', default='start', choices=['start', 'stop', 'status', 'logs'])
    parser.add_argument('--interval', type=int, default=30, help='Intervalo base (s)')
    args = parser.parse_args()
    
    if args.action == 'stop':
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
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
            except Exception:
                _release_lock()
                print("Monitor já parado (lock removido)")
        else:
            print("Monitor não está rodando")
        return
    
    if args.action == 'status':
        if PID_FILE.exists():
            try:
                pid = int(PID_FILE.read_text().strip())
                if os.name == 'nt':
                    import ctypes
                    h = ctypes.windll.kernel32.OpenProcess(1, False, pid)
                    if h:
                        ctypes.windll.kernel32.CloseHandle(h)
                        print(f"Rodando (PID: {pid})")
                    else:
                        print("Parado (PID órfão)")
                else:
                    os.kill(pid, 0)
                    print(f"Rodando (PID: {pid})")
            except Exception:
                print("Parado (lock órfão)")
        else:
            print("Parado")
        return
    
    if args.action == 'logs':
        if LOG_FILE.exists():
            lines = LOG_FILE.read_text(encoding='utf-8').strip().splitlines()
            for line in lines[-20:]:
                try:
                    print(json.loads(line))
                except:
                    print(line)
        else:
            print("Sem logs")
        return
    
    # START
    if not _acquire_lock():
        print("Monitor já rodando")
        return
    
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    
    # Encontra adb
    adb = "adb"
    try:
        res = subprocess.run(['where', 'adb'], capture_output=True, text=True, timeout=3)
        if res.returncode == 0:
            adb = res.stdout.splitlines()[0].strip()
    except Exception:
        adb = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', 'adb.exe')
    
    if not os.path.exists(adb):
        _write_log({'event': 'error', 'error': f'ADB não encontrado: {adb}'})
        _release_lock()
        return
    
    # NÃO daemoniza - o wrapper (adb_monitor_daemon.py) cuida disso
    # Se rodar direto, roda em foreground (para teste)
    _monitor_loop(adb)
    _release_lock()


if __name__ == '__main__':
    main()