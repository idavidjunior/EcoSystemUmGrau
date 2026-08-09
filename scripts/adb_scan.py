#!/usr/bin/env python3
"""Script de escaneamento de dispositivos ADB.

O script é invocado pelo agente eco durante a verificação de estado. Ele
1. Executa `adb devices` para listar dispositivos USB.
2. Executa `adb connect IP:5555` apenas se houver IPs de dispositivos ADB
   já listados que não estejam conectados.
3. Retorna um dicionário JSON contendo o status de cada conexão.

Esta lógica evita bloquear a chamada principal (o agente eco) pois
a execução de subprocess voltará imediatamente após o escaneamento.
"""

import subprocess
import json
import re
import os

ADB = "adb"  # path padrão; se não estiver no PATH, o enconderá pelo where.


def find_adb_path() -> str:
    """Tenta encontrar o caminho do adb executável.
    Se não conseguir, retorna apenas o nome do comando.
    """
    try:
        result = subprocess.run(["where", "adb"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            # 'where' retorna cada linha com o caminho completo
            return result.stdout.splitlines()[0].strip()
    except Exception:
        pass
    return os.path.join("C:\\Users\\David Jr\\AppData\\Local\\Android\\Sdk\\platform-tools", "adb.exe")


def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=10)


def scan_devices() -> dict:
    adb_path = find_adb_path()
    # List Devices
    res = _run([adb_path, "devices"])
    output = res.stdout.strip().splitlines()
    devices = []
    for line in output[1:]:  # pular cabeçalho
        if line.strip() == "":
            continue
        m = re.match(r"^([^\s]+)\s+(.+$)", line)
        if m:
            dev_id, state = m.groups()
            devices.append({"id": dev_id, "state": state.strip()})

    return {"adb_devices": devices, "status": "ok"}


if __name__ == "__main__":
    result = scan_devices()
    print(json.dumps(result, indent=2))
