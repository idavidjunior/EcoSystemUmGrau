#!/usr/bin/env python3
"""Mecanismo simples para escanear conexões atuais do EcoSystemUmGrau.

Funcionalidades:
  * Executa `adb devices` e obtém lista de dispositivos Android.
  * Executa `tailscale status` e captura o estado da rede Tailscale.
  * Salva os resultados em `scripts/scan_log.txt` para auditoria.
  * Também imprime no console para mostrar que o scan está rodando.

É executado automaticamente quando o EcoSystemUmGrau é iniciado
(see scripts/runtime_boot.py).
"""

import subprocess
import datetime
import os

SCAN_LOG = os.path.join(os.path.dirname(__file__), "scan_log.txt")

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip() or result.stderr.strip()
    except Exception as e:
        return f"Erro ao executar {cmd!r}: {e}"

def scan_adb():
    return run_cmd("adb devices")


def scan_tailscale():
    return run_cmd("tailscale status")


def main():
    timestamp = datetime.datetime.utcnow().isoformat()
    adb_output = scan_adb()
    tailscale_output = scan_tailscale()
    log_entries = [f"--- Scan de conexões {timestamp} UTC ---", "ADB:", adb_output, "", "Tailscale:", tailscale_output, "\n"]
    os.makedirs(os.path.dirname(SCAN_LOG), exist_ok=True)
    with open(SCAN_LOG, "a", encoding="utf-8") as f:
        f.write("\n".join(log_entries))
    # também imprime no console
    print("\n".join(log_entries))

if __name__ == "__main__":
    main()
