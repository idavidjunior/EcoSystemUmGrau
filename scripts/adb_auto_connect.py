#!/usr/bin/env python3
"""Auto-conecta ADB ao celular usando o ADB Connection Manager.

Refatorado para delegar toda a lógica de conexão ao
`adb_connection_manager.py` (fonte única de conexão).

Fluxo:
1. Consulta o ConnectionManager (multi-transporte: USB → WiFi → mDNS → Tailscale)
2. Preserva conexão saudável existente
3. Retorna JSON com status final (formato compatível com consumidores antigos)

Formato de saída preservado (consumidores aguardam):
  {ok, connected, method, devices, serial, tailscale_output?, error?}

Uso:
  python scripts/adb_auto_connect.py
"""

import json
import os
import sys

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)

from adb_connection_manager import ConnectionManager, find_adb, parse_devices


def main():
    adb = find_adb()
    if not os.path.exists(adb):
        result = {'ok': False, 'error': f'ADB não encontrado: {adb}', 'devices': []}
        print(json.dumps(result, ensure_ascii=False))
        return 1

    cm = ConnectionManager(adb=adb)
    cm.load_state()
    res = cm.connect()

    devices = cm._devices()
    best_serial = res.get('device')
    if not best_serial:
        # fallback: primeira device 'device'
        for d in devices:
            if d['state'] == 'device':
                best_serial = d['id']
                break

    # Formato compatível com consumidores antigos
    method = res.get('transport') or ('failed' if not res['success'] else 'existing')
    result = {
        'ok': res['success'],
        'connected': res['connected'],
        'method': method,
        'devices': devices,
        'serial': best_serial,
        'state': res.get('state'),
        'attempts': res.get('attempts'),
        'latency_ms': res.get('latency_ms'),
    }
    if res.get('error'):
        result['error'] = res['error']

    cm.save_state()
    print(json.dumps(result, ensure_ascii=False))
    return 0 if res['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
