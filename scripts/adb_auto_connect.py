#!/usr/bin/env python3
"""Auto-conecta ADB ao celular (WiFi local → Tailscale).

Fluxo:
1. Executa `adb devices` → lista dispositivos
2. Se já houver dispositivo "device" → OK
3. Tenta WiFi local: `adb connect <ip>:5555` (IPs da rede local)
4. Tenta mDNS: `adb mdns services` → descobre porta Wireless Debugging
5. Se não → roda `adb-redmi.ps1` (Tailscale connect)
6. Re-valida com `adb devices`
7. Retorna JSON com status final
"""

import json
import subprocess
import sys
import os
import re
import socket

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
ADB_REDMI = os.path.join(SCRIPTS_DIR, 'adb-redmi.ps1')

# Windows: evita criar console janela em subprocessos
CREATE_NO_WINDOW = 0x08000000


def _run(cmd, **kwargs):
    """Wrapper para subprocess.run com CREATE_NO_WINDOW no Windows."""
    if os.name == 'nt':
        kwargs.setdefault('creationflags', CREATE_NO_WINDOW)
    return subprocess.run(cmd, **kwargs)


def find_adb():
    try:
        res = _run(['where', 'adb'], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return res.stdout.splitlines()[0].strip()
    except Exception:
        pass
    # Tenta múltiplos caminhos conhecidos no Windows
    candidates = [
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'platform-tools', 'platform-tools', 'adb.exe'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Android', 'Sdk', 'platform-tools', 'adb.exe'),
        os.path.join(os.environ.get('PROGRAMFILES', ''), 'Android', 'platform-tools', 'adb.exe'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return candidates[0]


def scan_devices(adb_path):
    res = _run([adb_path, 'devices'], capture_output=True, text=True, timeout=10)
    lines = res.stdout.strip().splitlines()
    devices = []
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 2:
            devices.append({'id': parts[0], 'state': parts[1]})
    return devices


def get_best_serial(devices):
    """Retorna o melhor serial para scrcpy.
    Prioridade: mDNS (Wireless Debugging) > USB > outros.
    """
    for d in devices:
        if d['state'] == 'device' and '._adb-tls-connect._tcp' in d['id']:
            return d['id']  # mDNS name para Wireless Debugging
    for d in devices:
        if d['state'] == 'device' and not (':' in d['id'] and d['id'].split(':')[-1].isdigit()):
            return d['id']  # USB serial
    for d in devices:
        if d['state'] == 'device':
            return d['id']  # fallback: qualquer device
    return None


def has_connected_device(devices):
    return any(d['state'] == 'device' for d in devices)


def has_usb_device(devices):
    """Verifica se há dispositivo USB conectado (não TCP/IP)."""
    for d in devices:
        if d['state'] == 'device' and not (':' in d['id'] and d['id'].split(':')[-1].isdigit()):
            # USB devices geralmente não têm IP:porta no ID
            # mas adb pode mostrar serial number direto
            return True
    return False


def get_local_ips():
    """Retorna IPs locais da máquina (para tentar adb connect)."""
    ips = []
    try:
        # Método 1: hostname -I (Linux) / Get-NetIPAddress (Windows)
        # Em Windows, usar socket
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None):
            ip = info[4][0]
            if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.'):
                if ip not in ips:
                    ips.append(ip)
    except Exception:
        pass
    return ips


def try_wifi_connect(adb_path, ips):
    """Tenta adb connect <ip>:5555 para cada IP local."""
    for ip in ips:
        target = f"{ip}:5555"
        try:
            res = _run([adb_path, 'connect', target], capture_output=True, text=True, timeout=10)
            if 'connected to' in res.stdout.lower():
                return True, target, res.stdout
        except Exception:
            pass
    return False, None, ''


def try_mdns_connect(adb_path):
    """Tenta descobrir porta via mDNS e conectar."""
    try:
        res = _run([adb_path, 'mdns', 'services'], capture_output=True, text=True, timeout=10)
        # Procura _adb-tls-connect._tcp ou _adb._tcp
        m = re.search(r'_adb[_-]tls[_-]connect\._tcp.*:(\d+)', res.stdout)
        if not m:
            m = re.search(r'_adb\._tcp.*:(\d+)', res.stdout)
        if m:
            port = m.group(1)
            # Tenta conectar nos IPs locais com essa porta
            ips = get_local_ips()
            for ip in ips:
                target = f"{ip}:{port}"
                try:
                    res2 = _run([adb_path, 'connect', target], capture_output=True, text=True, timeout=10)
                    if 'connected to' in res2.stdout.lower():
                        return True, target, res2.stdout
                except Exception:
                    pass
    except Exception:
        pass
    return False, None, ''


def run_adb_redmi():
    """Roda o script PowerShell de conexão Tailscale."""
    try:
        res = _run(
            ['powershell', '-ExecutionPolicy', 'Bypass', '-File', ADB_REDMI],
            capture_output=True, text=True, timeout=60
        )
        return res.returncode == 0, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return False, '', 'Timeout (60s)'
    except Exception as e:
        return False, '', str(e)


def main():
    adb = find_adb()
    if not os.path.exists(adb):
        result = {'ok': False, 'error': f'ADB não encontrado: {adb}', 'devices': []}
        print(json.dumps(result, ensure_ascii=False))
        return 1

    # 1. Scan inicial
    devices = scan_devices(adb)
    best_serial = get_best_serial(devices)
    if has_connected_device(devices):
        # Prioridade: USB > WiFi/Tailscale
        if has_usb_device(devices):
            result = {'ok': True, 'connected': True, 'method': 'usb_priority', 'devices': devices, 'serial': best_serial}
            print(json.dumps(result, ensure_ascii=False))
            return 0
        # Se já conectado mas não USB (ex: WiFi/Tailscale anterior), mantém
        result = {'ok': True, 'connected': True, 'method': 'already_connected', 'devices': devices, 'serial': best_serial}
        print(json.dumps(result, ensure_ascii=False))
        return 0

    # 2. Tentar WiFi local (adb connect IP:5555)
    local_ips = get_local_ips()
    if local_ips:
        ok, target, out = try_wifi_connect(adb, local_ips)
        if ok:
            devices = scan_devices(adb)
            if has_connected_device(devices):
                best_serial = get_best_serial(devices)
                result = {'ok': True, 'connected': True, 'method': f'wifi_local:{target}', 'devices': devices, 'serial': best_serial}
                print(json.dumps(result, ensure_ascii=False))
                return 0

    # 3. Tentar mDNS (Wireless Debugging)
    ok, target, out = try_mdns_connect(adb)
    if ok:
        devices = scan_devices(adb)
        if has_connected_device(devices):
            best_serial = get_best_serial(devices)
            result = {'ok': True, 'connected': True, 'method': f'mdns:{target}', 'devices': devices, 'serial': best_serial}
            print(json.dumps(result, ensure_ascii=False))
            return 0

    # 4. Tentar Tailscale
    ok, stdout, stderr = run_adb_redmi()

    # 5. Re-scan final
    devices = scan_devices(adb)
    connected = has_connected_device(devices)
    best_serial = get_best_serial(devices)

    method = 'tailscale' if connected else 'failed'
    if ok and not connected:
        method = 'tailscale_attempted'

    result = {
        'ok': connected,
        'connected': connected,
        'method': method,
        'devices': devices,
        'serial': best_serial,
        'tailscale_output': stdout if ok else stderr
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if connected else 1


if __name__ == '__main__':
    sys.exit(main())