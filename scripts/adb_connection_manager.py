#!/usr/bin/env python3
"""ADB Connection Manager — centraliza conexão ADB multi-transporte.

Ponto único de lógica de conexão para o ecossistema. Transportes abstratos
(USB/WiFi/mDNS/Tailscale) com máquina de estados, health check, backoff
progressivo com jitter e JSON padronizado de saída.

Uso (CLI):
  python adb_connection_manager.py connect                # conecta (auto)
  python adb_connection_manager.py connect --transport usb
  python adb_connection_manager.py status                 # status JSON
  python adb_connection_manager.py health                 # health check
  python adb_connection_manager.py disconnect --serial x
  python adb_connection_manager.py devices                # lista devices
  python adb_connection_manager.py diagnose               # diagnóstico completo

Uso (API):
  from adb_connection_manager import ConnectionManager
  cm = ConnectionManager()
  result = cm.connect()
  state = cm.status()
  ok = cm.health()
"""

from __future__ import annotations

import json
import os
import re
import socket
import subprocess
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Windows: evita console janela em subprocessos
CREATE_NO_WINDOW = 0x08000000

SCRIPTS_DIR = Path(__file__).parent
ADB_REDMI = SCRIPTS_DIR / 'adb-redmi.ps1'
CONFIG_FILE = SCRIPTS_DIR / '.adb_tailscale.json'
STATE_FILE = SCRIPTS_DIR / '.adb_connection_state.json'

# --- Estados da máquina de estados ---
OFFLINE = 'OFFLINE'
DETECTING = 'DETECTING'
CONNECTING = 'CONNECTING'
CONNECTED = 'CONNECTED'
DEGRADED = 'DEGRADED'
UNAUTHORIZED = 'UNAUTHORIZED'
DISCONNECTED = 'DISCONNECTED'
FAILED = 'FAILED'
BACKOFF = 'BACKOFF'
RETRYING = 'RETRYING'

ALL_STATES = [OFFLINE, DETECTING, CONNECTING, CONNECTED, DEGRADED, UNAUTHORIZED,
              DISCONNECTED, FAILED, BACKOFF, RETRYING]

# Health check classificação
HEALTH_OK = 'CONNECTED'
HEALTH_UNRESPONSIVE = 'CONNECTED_BUT_UNRESPONSIVE'
HEALTH_UNAUTHORIZED = 'UNAUTHORIZED'
HEALTH_OFFLINE = 'OFFLINE'
HEALTH_DISCONNECTED = 'DISCONNECTED'

# Backoff progressivo com jitter (s)
BACKOFF_SCHEDULE = [5, 10, 20, 30, 60, 120, 300]
BACKOFF_MAX = 300

# Eventos de log mínimos
EVENTS = ('CONNECTION_ATTEMPT', 'CONNECTION_SUCCESS', 'CONNECTION_FAILURE',
          'DEVICE_CONNECTED', 'DEVICE_DISCONNECTED', 'HEALTH_CHECK',
          'TRANSPORT_CHANGED', 'BACKOFF_STARTED', 'BACKOFF_ENDED',
          'DAEMON_STARTED', 'DAEMON_STOPPED')

# Prioridade de transporte padrão
TRANSPORT_PRIORITY = ('usb', 'wifi', 'mdns', 'tailscale')


def _now_iso():
    return datetime.now().isoformat(timespec='seconds')


def _run(cmd, timeout=10, **kwargs):
    """Wrapper para subprocess.run com CREATE_NO_WINDOW no Windows."""
    if os.name == 'nt':
        kwargs.setdefault('creationflags', CREATE_NO_WINDOW)
    kwargs.setdefault('capture_output', True)
    kwargs.setdefault('text', True)
    return subprocess.run(cmd, timeout=timeout, **kwargs)


def find_adb() -> str:
    """Encontra o caminho do adb nos caminhos conhecidos."""
    try:
        res = _run(['where', 'adb'], timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.splitlines()[0].strip()
    except Exception:
        pass
    candidates = [
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'platform-tools', 'platform-tools', 'adb.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', 'adb.exe'),
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Android', 'platform-tools', 'adb.exe'),
        'adb',
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


def parse_devices(output: str) -> List[Dict[str, str]]:
    """Converte saída de `adb devices` em lista de dicts."""
    devices = []
    for line in output.strip().splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            devices.append({'id': parts[0], 'state': parts[1]})
    return devices


# ---------------------------------------------------------------------------
# Transportes (interface abstrata)
# ---------------------------------------------------------------------------
class BaseTransport(ABC):
    name = 'base'
    priority = 99

    def __init__(self, manager: 'ConnectionManager'):
        self.m = manager

    @abstractmethod
    def detect(self) -> List[Dict[str, str]]:
        """Detecta dispositivos candidatos deste transporte."""

    @abstractmethod
    def connect(self, device: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Tenta conectar. Retorna dict com success/serial/error."""

    def disconnect(self, serial: str) -> bool:
        """Desconecta dispositivo (opcional)."""
        return True

    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se o transporte está disponível."""


class USBTransport(BaseTransport):
    name = 'usb'
    priority = 1

    def detect(self) -> List[Dict[str, str]]:
        devices = self.m._devices()
        # USB = sem IP:porta no id
        return [d for d in devices
                if d['state'] == 'device'
                and not ('_' in d['id'])
                and not (':' in d['id'] and d['id'].split(':')[-1].isdigit())]

    def connect(self, device=None) -> Dict[str, Any]:
        # USB já conectado pelo sistema; apenas valida
        for d in self.detect():
            return {'success': True, 'serial': d['id'], 'transport': self.name}
        return {'success': False, 'error': 'Nenhum dispositivo USB detectado', 'transport': self.name}

    def is_available(self) -> bool:
        res = _run([self.m.adb, 'devices'], timeout=10)
        return any('.' not in line.split()[0] for line in res.stdout.splitlines()[1:]
                   if line.strip() and ':' not in line.split()[0] and len(line.split()) >= 2)


class WifiTransport(BaseTransport):
    name = 'wifi'
    priority = 2

    def _local_ips(self) -> List[str]:
        ips = []
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                if ip.startswith(('192.168.', '10.', '172.')) and ip not in ips:
                    ips.append(ip)
        except Exception:
            pass
        return ips

    def detect(self) -> List[Dict[str, str]]:
        return [d for d in self.m._devices()
                if d['state'] == 'device'
                and ':' in d['id'] and d['id'].split(':')[-1].isdigit()
                and '_' not in d['id']]

    def connect(self, device=None) -> Dict[str, Any]:
        for ip in self._local_ips():
            target = f"{ip}:5555"
            try:
                res = _run([self.m.adb, 'connect', target], timeout=10)
                if 'connected to' in res.stdout.lower() or 'already connected' in res.stdout.lower():
                    return {'success': True, 'serial': target, 'transport': self.name}
            except Exception:
                continue
        return {'success': False, 'error': 'WiFi local falhou', 'transport': self.name}

    def disconnect(self, serial: str) -> bool:
        try:
            _run([self.m.adb, 'disconnect', serial], timeout=10)
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        return bool(self._local_ips())


class MDNSTransport(BaseTransport):
    name = 'mdns'
    priority = 3

    def _mdns_port(self) -> Optional[str]:
        try:
            res = _run([self.m.adb, 'mdns', 'services'], timeout=10)
            m = re.search(r'_adb[_-]tls[_-]connect\._tcp.*:(\d+)', res.stdout)
            if not m:
                m = re.search(r'_adb\._tcp.*:(\d+)', res.stdout)
            return m.group(1) if m else None
        except Exception:
            return None

    def detect(self) -> List[Dict[str, str]]:
        return [d for d in self.m._devices()
                if d['state'] == 'device' and '_' in d['id']]

    def connect(self, device=None) -> Dict[str, Any]:
        port = self._mdns_port()
        if not port:
            return {'success': False, 'error': 'mDNS não encontrou serviço', 'transport': self.name}
        ips = self.m._local_ips()
        for ip in ips:
            target = f"{ip}:{port}"
            try:
                res = _run([self.m.adb, 'connect', target], timeout=10)
                if 'connected to' in res.stdout.lower() or 'already connected' in res.stdout.lower():
                    return {'success': True, 'serial': target, 'transport': self.name}
            except Exception:
                continue
        return {'success': False, 'error': 'mDNS connect falhou', 'transport': self.name}

    def disconnect(self, serial: str) -> bool:
        try:
            _run([self.m.adb, 'disconnect', serial], timeout=10)
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        return self._mdns_port() is not None


class TailscaleTransport(BaseTransport):
    name = 'tailscale'
    priority = 4

    def _config(self) -> Dict[str, Any]:
        if CONFIG_FILE.exists():
            try:
                return json.loads(CONFIG_FILE.read_text(encoding='utf-8'))
            except Exception:
                pass
        return {}

    def detect(self) -> List[Dict[str, str]]:
        # Tailscale device aparece como IP:porta; não distinguimos por prefixo,
        # mas prioridade resolve. Reusamos devices conectados.
        return [d for d in self.m._devices() if d['state'] == 'device']

    def connect(self, device=None) -> Dict[str, Any]:
        try:
            if not ADB_REDMI.exists():
                return {'success': False, 'error': f'adb-redmi.ps1 não existe: {ADB_REDMI}', 'transport': self.name}
            res = _run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', str(ADB_REDMI)],
                       timeout=60)
            # Verifica se conectou
            devices = self.m._devices()
            connected = [d for d in devices if d['state'] == 'device']
            if connected:
                return {'success': True, 'serial': connected[0]['id'], 'transport': self.name}
            return {'success': False, 'error': res.stderr.strip() or 'Tailscale não conectou',
                    'transport': self.name}
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Tailscale timeout (60s)', 'transport': self.name}
        except Exception as e:
            return {'success': False, 'error': str(e), 'transport': self.name}

    def disconnect(self, serial: str) -> bool:
        try:
            _run([self.m.adb, 'disconnect', serial], timeout=10)
            return True
        except Exception:
            return False

    def is_available(self) -> bool:
        return ADB_REDMI.exists()


TRANSPORT_CLASSES = {
    'usb': USBTransport,
    'wifi': WifiTransport,
    'mdns': MDNSTransport,
    'tailscale': TailscaleTransport,
}


# ---------------------------------------------------------------------------
# Connection Manager
# ---------------------------------------------------------------------------
class ConnectionManager:
    """Gerencia conexão ADB multi-transporte com estados e backoff."""

    def __init__(self, adb: Optional[str] = None, priority: tuple = TRANSPORT_PRIORITY):
        self.adb = adb or find_adb()
        self.priority = priority
        self.transports = [
            TRANSPORT_CLASSES[name](self) for name in priority
            if name in TRANSPORT_CLASSES
        ]
        self.state = OFFLINE
        self.device: Optional[str] = None
        self.transport: Optional[str] = None
        self.attempts = 0
        self.last_error: Optional[str] = None
        self.last_connected_at: Optional[str] = None
        self.last_disconnected_at: Optional[str] = None
        self.backoff_idx = 0
        self._log_events: List[Dict[str, Any]] = []

    # --- infra ---
    def _devices(self) -> List[Dict[str, str]]:
        try:
            res = _run([self.adb, 'devices'], timeout=10)
            return parse_devices(res.stdout)
        except Exception:
            return []

    def _local_ips(self) -> List[str]:
        ips = []
        try:
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                if ip.startswith(('192.168.', '10.', '172.')) and ip not in ips:
                    ips.append(ip)
        except Exception:
            pass
        return ips

    def _log(self, event: str, **data):
        entry = {'event': event, **data, 'ts': _now_iso()}
        self._log_events.append(entry)
        return entry

    # --- health check ---
    def health(self) -> Dict[str, Any]:
        """Verifica saúde da conexão. Não confia só em adb devices."""
        start = time.time()
        devices = self._devices()
        latency = round((time.time() - start) * 1000, 1)

        state_devices = [d for d in devices if d['state'] == 'device']
        if not state_devices:
            res = {'status': HEALTH_DISCONNECTED, 'devices': devices, 'latency_ms': latency,
                   'state': DISCONNECTED}
            self._log('HEALTH_CHECK', status=res['status'], latency_ms=latency)
            return res

        serial = state_devices[0]['id']
        # Teste shell para confirmar responsividade
        try:
            shell = _run([self.adb, '-s', serial, 'shell', 'echo', 'ok'], timeout=10)
            responsive = shell.returncode == 0 and 'ok' in shell.stdout
        except Exception:
            responsive = False

        if responsive:
            status = HEALTH_OK
            state = CONNECTED
        else:
            status = HEALTH_UNRESPONSIVE
            state = DEGRADED

        self._log('HEALTH_CHECK', status=status, latency_ms=latency, serial=serial)
        return {'status': status, 'state': state, 'serial': serial,
                'devices': devices, 'latency_ms': latency}

    # --- backoff ---
    def _backoff_delay(self) -> float:
        idx = min(self.backoff_idx, len(BACKOFF_SCHEDULE) - 1)
        base = BACKOFF_SCHEDULE[idx]
        jitter = 0.25 * base  # ±25%
        import random
        return max(1, base + (random.uniform(-jitter, jitter)))

    def _backoff(self):
        delay = self._backoff_delay()
        self.state = BACKOFF
        self._log('BACKOFF_STARTED', attempt=self.attempts, delay_s=round(delay, 1))
        time.sleep(delay)
        self.backoff_idx = min(self.backoff_idx + 1, len(BACKOFF_SCHEDULE) - 1)
        self._log('BACKOFF_ENDED', attempt=self.attempts)

    def _reset_backoff(self):
        if self.backoff_idx != 0:
            self._log('BACKOFF_ENDED', reset=True)
        self.backoff_idx = 0
        self.attempts = 0

    # --- track-devices ---
    def track_devices(self, on_change=None, timeout=30):
        """Mecanismo principal de eventos (adb track-devices)."""
        try:
            proc = subprocess.Popen(
                [self.adb, 'track-devices'],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                text=True, creationflags=CREATE_NO_WINDOW if os.name == 'nt' else 0)
        except Exception:
            return False

        last_states = {}
        try:
            deadline = time.time() + timeout
            while time.time() < deadline:
                line = proc.stdout.readline()
                if not line:
                    break
                parts = line.split()
                if len(parts) == 2:
                    serial, state = parts[0], parts[1]
                    prev = last_states.get(serial)
                    last_states[serial] = state
                    if prev != state:
                        if on_change:
                            on_change(serial, prev, state)
            proc.kill()
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
            return False
        return True

    # --- conexão ---
    def connect(self, transport: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
        """Conecta ao melhor dispositivo. Preserva conexão saudável salvo force."""
        start = time.time()

        # 1. Se já conectado e saudável, preserva (salvo force)
        if not force:
            h = self.health()
            if h['status'] == HEALTH_OK:
                self.state = CONNECTED
                self.device = h.get('serial')
                elapsed = round((time.time() - start) * 1000, 1)
                return {'success': True, 'connected': True, 'state': CONNECTED,
                        'device': self.device, 'transport': self.transport or 'existing',
                        'attempts': self.attempts, 'latency_ms': elapsed,
                        'error': None, 'timestamp': _now_iso()}

        # 2. Seleciona transporte-alvo
        targets = [transport] if transport else None

        self.state = DETECTING
        self._log('CONNECTION_ATTEMPT', transport=transport or 'auto')

        # 3. Tenta cada transporte em ordem de prioridade
        for tr in self.transports:
            if targets and tr.name not in targets:
                continue
            self.state = CONNECTING
            self.attempts += 1
            try:
                result = tr.connect()
            except Exception as e:
                self._log('CONNECTION_FAILURE', transport=tr.name, error=str(e))
                continue

            if result.get('success'):
                self.state = CONNECTED
                self.device = result.get('serial')
                self.transport = tr.name
                self.last_connected_at = _now_iso()
                self._reset_backoff()
                self._log('CONNECTION_SUCCESS', transport=tr.name, serial=self.device)
                elapsed = round((time.time() - start) * 1000, 1)
                return {'success': True, 'connected': True, 'state': CONNECTED,
                        'device': self.device, 'transport': tr.name,
                        'attempts': self.attempts, 'latency_ms': elapsed,
                        'error': None, 'timestamp': _now_iso()}
            else:
                self._log('CONNECTION_FAILURE', transport=tr.name,
                          error=result.get('error'))
                self.last_error = result.get('error')

        # 4. Falhou tudo
        self.state = FAILED
        self.attempts += 1
        self._log('CONNECTION_FAILURE', transport='all',
                  error=self.last_error)
        elapsed = round((time.time() - start) * 1000, 1)
        return {'success': False, 'connected': False, 'state': FAILED,
                'device': None, 'transport': None,
                'attempts': self.attempts, 'latency_ms': elapsed,
                'error': self.last_error or 'Todos os transportes falharam',
                'timestamp': _now_iso()}

    def disconnect(self, serial: Optional[str] = None) -> Dict[str, Any]:
        """Desconecta dispositivo (este ou o atual)."""
        serial = serial or self.device
        if not serial:
            return {'success': False, 'error': 'Nenhum device ativo', 'state': self.state,
                    'timestamp': _now_iso()}
        for tr in self.transports:
            tr.disconnect(serial)
        self.state = DISCONNECTED
        self.last_disconnected_at = _now_iso()
        self._log('DEVICE_DISCONNECTED', serial=serial)
        return {'success': True, 'disconnected': serial, 'state': DISCONNECTED,
                'timestamp': _now_iso()}

    # --- status ---
    def status(self) -> Dict[str, Any]:
        h = self.health()
        return {
            'success': True,
            'state': h['state'],
            'health': h['status'],
            'device': h.get('serial'),
            'transport': self.transport,
            'attempts': self.attempts,
            'latency_ms': h['latency_ms'],
            'error': self.last_error,
            'devices': h['devices'],
            'last_connected_at': self.last_connected_at,
            'last_disconnected_at': self.last_disconnected_at,
            'timestamp': _now_iso(),
        }

    def get_device(self) -> Optional[str]:
        """Retorna serial do device atual (ou None)."""
        h = self.health()
        return h.get('serial') if h['status'] == HEALTH_OK else self.device

    def wait_until_connected(self, timeout=60) -> Dict[str, Any]:
        deadline = time.time() + timeout
        while time.time() < deadline:
            h = self.health()
            if h['status'] == HEALTH_OK:
                return {'success': True, 'device': h['serial'], 'state': CONNECTED}
            time.sleep(2)
        return {'success': False, 'error': 'Timeout aguardando conexão',
                'state': self.state}

    def execute(self, command: str, args: Optional[List[str]] = None,
                timeout: int = 10) -> Dict[str, Any]:
        """Executa comando adb com validação. Não roda comandos arbitrários."""
        allowed = {'shell', 'devices', 'get-state', 'mdns', 'connect', 'disconnect',
                   'version', 'help', 'wait-for-device'}
        if command not in allowed:
            return {'success': False, 'error': f'Comando não permitido: {command}'}
        cmd = [self.adb]
        if self.device and command in {'shell', 'get-state'}:
            cmd += ['-s', self.device]
        cmd += [command] + (list(args) if args else [])
        try:
            res = _run(cmd, timeout=timeout)
            return {'success': res.returncode == 0, 'returncode': res.returncode,
                    'stdout': res.stdout, 'stderr': res.stderr,
                    'command': command}
        except Exception as e:
            return {'success': False, 'error': str(e), 'command': command}

    # --- diagnóstico ---
    def diagnose(self) -> Dict[str, Any]:
        adb_exists = os.path.exists(self.adb)
        adb_output = {}
        if adb_exists:
            try:
                v = _run([self.adb, 'version'], timeout=5)
                adb_output['version'] = v.stdout.strip()
            except Exception:
                pass

        devices = self._devices()
        h = self.health()

        # Tailscale
        tailscale_output = ''
        try:
            t = _run(['tailscale', 'status'], timeout=5)
            tailscale_output = t.stdout[:500]
        except Exception:
            tailscale_output = 'tailscale não encontrado'

        # mDNS
        mdns_services = []
        try:
            m = _run([self.adb, 'mdns', 'services'], timeout=5)
            mdns_services = m.stdout.strip().splitlines()
        except Exception:
            pass

        return {
            'adbd': {
                'found': adb_exists,
                'path': self.adb,
                **adb_output,
            },
            'server': {
                'devices': devices,
            },
            'authorization': {
                # states unauthorized/offline indicam necessidade de autorização
                'unauthorized': any(d['state'] in ('unauthorized', 'offline') for d in devices),
            },
            'transport': self.transport,
            'state': h['state'],
            'health': h['status'],
            'current_device': h.get('serial'),
            'mdns_services': mdns_services,
            'tailscale': tailscale_output,
            'last_connected_at': self.last_connected_at,
            'last_disconnected_at': self.last_disconnected_at,
            'last_error': self.last_error,
            'retry_count': self.attempts,
            'backoff_idx': self.backoff_idx,
            'timestamp': _now_iso(),
        }

    def save_state(self):
        data = {
            'state': self.state,
            'device': self.device,
            'transport': self.transport,
            'attempts': self.attempts,
            'last_error': self.last_error,
            'last_connected_at': self.last_connected_at,
            'last_disconnected_at': self.last_disconnected_at,
            'backoff_idx': self.backoff_idx,
            'timestamp': _now_iso(),
        }
        try:
            STATE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2),
                                  encoding='utf-8')
        except Exception:
            pass

    def load_state(self):
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding='utf-8'))
                self.state = data.get('state', OFFLINE)
                self.device = data.get('device')
                self.transport = data.get('transport')
                self.attempts = data.get('attempts', 0)
                self.last_error = data.get('last_error')
                self.last_connected_at = data.get('last_connected_at')
                self.last_disconnected_at = data.get('last_disconnected_at')
                self.backoff_idx = data.get('backoff_idx', 0)
                return True
            except Exception:
                pass
        return False


# ---------------------------------------------------------------------------
# Concorrência (lock)
# ---------------------------------------------------------------------------
_LOCK_FILE = Path(os.environ.get('TEMP', '/tmp')) / 'adb_connection.lock'


class ConnectionLock:
    """Lock de concorrência: impede múltiplos processos de conectar."""
    acquired = False

    def __enter__(self):
        if _LOCK_FILE.exists():
            try:
                pid = int(_LOCK_FILE.read_text().strip())
                if _pid_alive(pid):
                    raise ConnectionError(
                        f'Outro processo de conexão ativo (PID {pid}). '
                        'Aguardando finalizar ou remova o lock em '
                        f'{_LOCK_FILE}.')
            except ValueError:
                pass
        _LOCK_FILE.write_text(str(os.getpid()), encoding='utf-8')
        self.acquired = True
        return self

    def __exit__(self, *exc):
        if self.acquired:
            try:
                _LOCK_FILE.unlink(missing_ok=True)
            except Exception:
                pass


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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _json_out(obj: Any, exit_code: int = 0):
    print(json.dumps(obj, ensure_ascii=False))
    return exit_code


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='ADB Connection Manager')
    sub = parser.add_subparsers(dest='cmd')

    p_connect = sub.add_parser('connect')
    p_connect.add_argument('--transport', choices=['usb', 'wifi', 'mdns', 'tailscale'])
    p_connect.add_argument('--force', action='store_true')

    sub.add_parser('disconnect')
    p_disc = sub.add_parser('disconnect-serial')

    sub.add_parser('status')
    sub.add_parser('health')
    sub.add_parser('devices')
    sub.add_parser('diagnose')
    sub.add_parser('wait')
    p_wait = sub.add_parser('wait-connected')

    args = parser.parse_args(argv)
    cmd = args.cmd

    cm = ConnectionManager()
    cm.load_state()

    if not os.path.exists(cm.adb):
        return _json_out({'success': False, 'error': f'ADB não encontrado: {cm.adb}',
                          'state': FAILED, 'timestamp': _now_iso()}, 1)

    if cmd == 'connect':
        try:
            with ConnectionLock():
                result = cm.connect(transport=getattr(args, 'transport', None),
                                    force=getattr(args, 'force', False))
            cm.save_state()
            return _json_out(result, 0 if result['success'] else 1)
        except ConnectionError as e:
            return _json_out({'success': False, 'connected': False, 'error': str(e),
                              'state': FAILED, 'timestamp': _now_iso()}, 1)

    if cmd in ('disconnect', 'disconnect-serial'):
        result = cm.disconnect()
        cm.save_state()
        return _json_out(result, 0 if result['success'] else 1)

    if cmd == 'status':
        return _json_out(cm.status(), 0)

    if cmd == 'health':
        return _json_out(cm.health(), 0)

    if cmd == 'devices':
        return _json_out({'devices': cm._devices(), 'timestamp': _now_iso()}, 0)

    if cmd == 'diagnose':
        return _json_out(cm.diagnose(), 0)

    if cmd == 'wait-connected':
        result = cm.wait_until_connected()
        return _json_out(result, 0 if result['success'] else 1)

    parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
