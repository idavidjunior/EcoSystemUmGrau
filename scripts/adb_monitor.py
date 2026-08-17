#!/usr/bin/env python3
"""Monitor vivo de ADB — roda em background e mantém conexão ativa.

Funcionamento:
- Loop infinito com intervalo configurável (padrão 30s)
- A cada ciclo: scan → se desconectou → tenta reconectar (ordem: USB → WiFi → mDNS → Tailscale)
- Loga mudanças de estado
- Pode rodar como daemon/serviço
- Sinais: SIGTERM/SIGINT para parada limpa
"""

import json
import subprocess
import sys
import os
import time
import signal
import threading
from datetime import datetime

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
AUTO_CONNECT = os.path.join(SCRIPTS_DIR, 'adb_auto_connect.py')

# Estado global
running = True
last_state = None
lock = threading.Lock()


def log(msg, level="INFO"):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {msg}", flush=True)


def run_auto_connect():
    """Executa o script de auto-connect e retorna resultado parseado."""
    try:
        res = subprocess.run(
            [sys.executable, AUTO_CONNECT],
            capture_output=True, text=True, timeout=90
        )
        if res.stdout.strip():
            return json.loads(res.stdout.strip())
    except json.JSONDecodeError:
        log(f"Erro parse JSON: {res.stdout[:200]}", "ERROR")
    except subprocess.TimeoutExpired:
        log("Timeout no auto-connect", "ERROR")
    except Exception as e:
        log(f"Erro exec auto-connect: {e}", "ERROR")
    return None


def monitor_loop(interval=30):
    """Loop principal de monitoramento."""
    global last_state, running
    
    log(f"Monitor ADB iniciado (intervalo: {interval}s)")
    log("Ordem de prioridade: USB → WiFi local → mDNS → Tailscale")
    
    while running:
        try:
            result = run_auto_connect()
            
            if result:
                connected = result.get('connected', False)
                method = result.get('method', 'unknown')
                devices = result.get('devices', [])
                device_ids = [d['id'] for d in devices if d['state'] == 'device']
                
                current_state = {
                    'connected': connected,
                    'method': method,
                    'devices': device_ids
                }
                
                # Detectar mudança de estado
                with lock:
                    if last_state != current_state:
                        if last_state is None:
                            log(f"Estado inicial: connected={connected}, method={method}, devices={device_ids}")
                        else:
                            if connected and not last_state.get('connected'):
                                log(f"RECONECTADO: method={method}, devices={device_ids}", "SUCCESS")
                            elif not connected and last_state.get('connected'):
                                log(f"DESCONECTADO: devices perdidos={last_state.get('devices')}", "WARNING")
                            elif connected and method != last_state.get('method'):
                                log(f"MUDANÇA DE MÉTODO: {last_state.get('method')} → {method}", "INFO")
                        
                        last_state = current_state
            
        except Exception as e:
            log(f"Erro no loop: {e}", "ERROR")
        
        # Sleep com verificação de parada a cada 1s
        for _ in range(interval):
            if not running:
                break
            time.sleep(1)
    
    log("Monitor ADB finalizado")


def signal_handler(signum, frame):
    global running
    log(f"Sinal {signum} recebido, parando...")
    running = False


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Monitor vivo ADB')
    parser.add_argument('--interval', type=int, default=30, help='Intervalo em segundos (padrão: 30)')
    parser.add_argument('--once', action='store_true', help='Executa apenas uma vez e sai')
    args = parser.parse_args()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    if args.once:
        result = run_auto_connect()
        if result:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result and result.get('connected') else 1
    
    monitor_loop(args.interval)
    return 0


if __name__ == '__main__':
    sys.exit(main())