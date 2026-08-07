#!/usr/bin/env python3
"""
EcoSystemUmGrau - Watcher de Conexões
Verifica e mantém conexões ADB e Tailscale ativas
Criado para rodar via Tarefa Agendada do Windows
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
LOG_FILE = BASE_DIR / "connectivity" / "logs" / "watcher.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log(message, level="INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{level}] {message}"
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")

def find_adb():
    paths = [
        os.environ.get("ANDROID_HOME", "") + "\\platform-tools",
        os.environ.get("LOCALAPPDATA", "") + "\\Android\\Sdk\\platform-tools",
        "C:\\adb",
    ]
    for path in paths:
        adb_path = Path(path) / "adb.exe"
        if adb_path.exists():
            return str(adb_path)
    return None

def check_adb():
    adb_path = find_adb()
    if not adb_path:
        log("ADB não encontrado no sistema", "CRITICAL")
        return False

    try:
        result = subprocess.run([adb_path, "devices"], capture_output=True, text=True, timeout=10)
        if "device" in result.stdout:
            devices = [line.split()[0] for line in result.stdout.split('\n')[1:] if line.strip().startswith("0") or line.strip().startswith("1")]
            log(f"ADB dispositivos ativos: {devices}")
            return True
        else:
            log("Tentando reconectar ADB...", "WARNING")
            try:
                subprocess.run([adb_path, "start-server"], capture_output=True, timeout=10)
                log("ADB server reiniciado", "RECOVERY")
                return True
            except Exception as e:
                log(f"Falha na reconexão ADB: {e}", "ERROR")
                return False
    except Exception as e:
        log(f"Erro no check ADB: {e}", "ERROR")
        return False

def check_tailscale():
    try:
        result = subprocess.run(["tailscale", "status"], capture_output=True, text=True, timeout=15)
        if "active" in result.stdout:
            log("Tailscale conexão ativa", "OK")
            return True
        else:
            log("Tailscale offline - tentando restaurar", "WARNING")
            # Tentativa 1: reiniciar serviço
            try:
                subprocess.run(["net", "start", "tailscale"], capture_output=True, timeout=15)
                result = subprocess.run(["tailscale", "up"], capture_output=True, text=True, timeout=15)
                log(f"Tailscale restaurado: {result.stdout[:100]}", "RECOVERY")
                return True
            except Exception as e:
                log(f"Falha na restauração Tailscale: {e}", "ERROR")
                return False
    except Exception as e:
        log(f"Erro no check Tailscale: {e}", "ERROR")
        return False

def main():
    log("=== Ciclo de monitoramento iniciado ===")
    adb_ok = check_adb()
    ts_ok = check_tailscale()

    status = {
        "timestamp": datetime.now().isoformat(),
        "adb": "active" if adb_ok else "inactive",
        "tailscale": "active" if ts_ok else "inactive"
    }

    log(f"Status final: ADB={status['adb']}, Tailscale={status['tailscale']}")

if __name__ == "__main__":
    main()
