#!/usr/bin/env python3
"""Wrapper scrcpy com reconexão automática e fallbacks.

- Reconecta se ADB cair (usa adb_monitor_daemon)
- Tenta múltiplas estratégias de encoding
- Fallback: screenrecord + ffplay se scrcpy falhar
- Loga apenas mudanças de estado
"""

import subprocess
import sys
import os
import time
import signal
import threading
from pathlib import Path

SCRCPY_DIR = Path(__file__).parent
SCRIPTS_DIR = SCRCPY_DIR.parent
SCRCPY_EXE = SCRCPY_DIR / 'scrcpy.exe'
ADB_EXE = SCRCPY_DIR / 'adb.exe'
LOG_FILE = Path(os.environ.get('TEMP', '/tmp')) / 'scrcpy_daemon.log'

# Estratégias de conexão (ordem de preferência - testadas e funcionando no Xiaomi/Redmi Android 13+)
STRATEGIES = [
    {
        'name': 'scrcpy_lowres',
        'args': ['--max-size', '1024', '--video-bit-rate', '4M', '--max-fps', '20'],
        'desc': 'Baixa resolução (FUNCIONA no Xiaomi/Redmi Android 13+)'
    },
    {
        'name': 'scrcpy_medium',
        'args': ['--max-size', '1280', '--video-bit-rate', '6M', '--max-fps', '30'],
        'desc': 'Resolução média'
    },
    {
        'name': 'scrcpy_h264',
        'args': ['--video-codec', 'h264', '--video-bit-rate', '8M', '--max-fps', '30'],
        'desc': 'H.264 hardware'
    },
    {
        'name': 'scrcpy_h265',
        'args': ['--video-codec', 'h265', '--video-bit-rate', '8M', '--max-fps', '30'],
        'desc': 'H.265 hardware'
    },
    {
        'name': 'scrcpy_default',
        'args': ['--max-fps', '30', '--video-bit-rate', '8M'],
        'desc': 'Default (auto codec)'
    },
    {
        'name': 'scrcpy_screen_source',
        'args': ['--video-source', 'screen', '--max-fps', '30', '--video-bit-rate', '8M'],
        'desc': 'Screen source (sem display)'
    },
]

_running = True
_current_proc = None
_lock = threading.Lock()


def log(msg, level="INFO"):
    ts = time.strftime("%H:%M:%S")
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def find_device_serial():
    """Retorna serial do melhor device 'device' via ADB (preferência: mDNS/Wireless Debugging)."""
    try:
        # Usa adb_auto_connect.py para obter o melhor serial
        import subprocess, json
        res = subprocess.run([
            sys.executable, 
            os.path.join(SCRIPTS_DIR, 'adb_auto_connect.py')
        ], capture_output=True, text=True, timeout=30)
        if res.returncode == 0:
            result = json.loads(res.stdout)
            if result.get('connected') and result.get('serial'):
                return result['serial']
    except Exception:
        pass
    
    # Fallback: método original
    try:
        res = subprocess.run([str(ADB_EXE), 'devices'], capture_output=True, text=True, timeout=5)
        for line in res.stdout.strip().splitlines()[1:]:
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) >= 2 and parts[1] == 'device':
                return parts[0]
    except Exception:
        pass
    return None


def run_scrcpy(serial, strategy, startup_timeout=5, max_runtime=0):
    """Executa scrcpy com estratégia dada. Retorna (processo, erro) ou (None, erro).
    
    startup_timeout: segundos para aguardar startup e detectar erros de encoding
    max_runtime: 0 = roda indefinido (até sair ou erro), >0 = mata após N segundos
    """
    args = [str(SCRCPY_EXE), '-s', serial] + strategy['args']
    log(f"Tentando: {strategy['name']} ({strategy['desc']})")
    try:
        kwargs = {}
        if os.name == 'nt':
            kwargs['creationflags'] = 0x08000000  # CREATE_NO_WINDOW
        proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kwargs)
        
        # Aguarda startup_timeout para detectar erros de encoding
        start = time.time()
        while time.time() - start < startup_timeout:
            if proc.poll() is not None:
                # Processo terminou antes do tempo
                try:
                    output = proc.stdout.read()
                    if 'Capture/encoding error' in output or ('MediaCodec' in output and 'Error' in output):
                        return None, "Encoding error (MediaCodec)"
                except:
                    pass
                return None, f"Exit code {proc.returncode}"
            time.sleep(0.1)
        
        # Startup OK - se max_runtime > 0, aguarda mais; se 0, retorna processo rodando
        if max_runtime > 0:
            # Aguarda mais tempo limitado
            remaining = max_runtime - startup_timeout
            try:
                return_code = proc.wait(timeout=remaining)
                if return_code == 0:
                    return proc, None
                else:
                    try:
                        output = proc.stdout.read()
                        if 'Capture/encoding error' in output or ('MediaCodec' in output and 'Error' in output):
                            return None, "Encoding error (MediaCodec)"
                    except:
                        pass
                    return None, f"Exit code {return_code}"
            except subprocess.TimeoutExpired:
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except:
                    pass
                return None, f"Timeout ({max_runtime}s)"
        else:
            # Sucesso no startup - retorna processo para rodar indefinido
            return proc, None
        
    except Exception as e:
        return None, str(e)


def fallback_screenrecord(serial):
    """Fallback: adb screenrecord + ffplay (se ffplay disponível)."""
    log("Tentando fallback: screenrecord + ffplay")
    try:
        # Verifica ffplay
        ffplay = subprocess.run(['where', 'ffplay'], capture_output=True, text=True, timeout=3)
        if ffplay.returncode != 0:
            log("ffplay não encontrado no PATH", "WARN")
            return None
        
        # Inicia screenrecord no device (pipe stdout)
        adb_args = [str(ADB_EXE), '-s', serial, 'exec-out', 'screenrecord', '--output-format=h264', '-']
        ffplay_args = ['ffplay', '-f', 'h264', '-i', '-', '-fflags', 'nobuffer', '-flags', 'low_delay', '-framedrop', '-']
        
        adb_proc = subprocess.Popen(adb_args, stdout=subprocess.PIPE)
        ffplay_proc = subprocess.Popen(ffplay_args, stdin=adb_proc.stdout)
        
        log("Fallback screenrecord iniciado")
        return (adb_proc, ffplay_proc)
    except Exception as e:
        log(f"Falha no fallback: {e}", "ERROR")
        return None


def signal_handler(signum, frame):
    global _running, _current_proc
    log(f"Sinal {signum} recebido, parando...")
    _running = False
    with _lock:
        if _current_proc:
            try:
                _current_proc.terminate()
            except Exception:
                pass


def monitor_loop(serial, interval=5):
    """Loop principal: tenta estratégias, reconecta se cair."""
    global _running, _current_proc
    
    log(f"scrcpy_daemon iniciado para {serial}")
    strategy_idx = 0
    
    while _running:
        # Verifica se device ainda está conectado
        if not find_device_serial():
            log("Device desconectado, aguardando reconexão ADB...", "WARN")
            time.sleep(interval)
            continue
        
        strategy = STRATEGIES[strategy_idx % len(STRATEGIES)]
        log(f"Estratégia: {strategy['name']} ({strategy['desc']})")
        
        proc, error = run_scrcpy(serial, strategy)
        if error:
            log(f"Falha: {error}", "WARN")
            strategy_idx += 1
            time.sleep(2)
            continue
        
        with _lock:
            _current_proc = proc
        
        # Aguarda processo terminar
        return_code = proc.wait()
        
        with _lock:
            _current_proc = None
        
        if not _running:
            break
        
        log(f"scrcpy saiu (code={return_code}), tentando próxima estratégia...", "WARN")
        strategy_idx += 1
        time.sleep(2)
        
        # Se esgotou estratégias, tenta fallback
        if strategy_idx >= len(STRATEGIES):
            log("Todas estratégias falharam, tentando fallback screenrecord...", "WARN")
            fallback = fallback_screenrecord(serial)
            if fallback:
                adb_proc, ffplay_proc = fallback
                ffplay_proc.wait()
                adb_proc.wait()
            strategy_idx = 0  # Reinicia ciclo
            time.sleep(5)
    
    log("scrcpy_daemon finalizado")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='scrcpy daemon com reconexão')
    parser.add_argument('--serial', help='Serial do device (auto-detecta se omitido)')
    parser.add_argument('--interval', type=int, default=5, help='Intervalo de reconexão (s)')
    parser.add_argument('--once', action='store_true', help='Executa uma vez e sai')
    args = parser.parse_args()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Auto-detecta serial
    serial = args.serial or find_device_serial()
    if not serial:
        log("Nenhum device ADB encontrado. Conecte o celular.", "ERROR")
        return 1
    
    log(f"Device alvo: {serial}")
    
    if args.once:
        # Tenta estratégias até uma funcionar
        for strategy in STRATEGIES:
            proc, error = run_scrcpy(serial, strategy, startup_timeout=5, max_runtime=0)
            if not error and proc:
                proc.wait()
                return 0
            log(f"Falha: {error}", "WARN")
        # Fallback
        fallback = fallback_screenrecord(serial)
        if fallback:
            adb_proc, ffplay_proc = fallback
            ffplay_proc.wait()
            adb_proc.wait()
            return 0
        return 1
    
    monitor_loop(serial, args.interval)
    return 0


if __name__ == '__main__':
    sys.exit(main())