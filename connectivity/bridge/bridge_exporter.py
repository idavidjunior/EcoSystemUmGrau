#!/usr/bin/env python3
"""
EcoSystemUmGrau Bridge Resilience - Export/Import Tool
Usado para migrar configuracoes entre maquinas
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

BRIDGE_DIR = Path(__file__).parent
CONFIG_DIR = BRIDGE_DIR / "configs"
LEARNING_DIR = BRIDGE_DIR / "learning"
HEALTH_DIR = BRIDGE_DIR / "health"
DEPLOY_DIR = BRIDGE_DIR / "deployment"

for d in [CONFIG_DIR, LEARNING_DIR, HEALTH_DIR, DEPLOY_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def _calc_uptime(events):
    """Calcula resumo de uptime"""
    if not events:
        return {"status": "no_data"}

    by_endpoint = {}
    for event in events:
        ep_id = event.get("endpoint_id", "unknown")
        level = event.get("level", "UNKNOWN")

        if ep_id not in by_endpoint:
            by_endpoint[ep_id] = {"ok": 0, "warnings": 0, "critical": 0}

        if level == "OK":
            by_endpoint[ep_id]["ok"] += 1
        elif level in ["WARNING"]:
            by_endpoint[ep_id]["warnings"] += 1
        elif level in ["CRITICAL", "ERROR"]:
            by_endpoint[ep_id]["critical"] += 1

    return by_endpoint


def export_config(output_file=None):
    """Exporta toda a configuracao e estado"""
    if output_file is None:
        output_file = str(DEPLOY_DIR / "bridge_export.json")

    export_data = {
        "version": "2.0",
        "exported_at": datetime.now().isoformat(),
        "endpoints": [],
        "learning_history": [],
        "health_reports": [],
        "current_status": {}
    }

    # Exporta configuracao de endpoints
    config_file = CONFIG_DIR / "bridge_config.json"
    if config_file.exists():
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                export_data["endpoints"] = data.get("endpoints", [])
            else:
                export_data["endpoints"] = data

    # Exporta aprendizado
    learning_file = LEARNING_DIR / "failures.json"
    if learning_file.exists():
        with open(learning_file, encoding="utf-8") as f:
            export_data["learning_history"] = json.load(f)

    # Exporta status atual
    status_file = BRIDGE_DIR / "events.jsonl"
    if status_file.exists():
        events = []
        with open(status_file, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))
        export_data["current_status"] = {
            "last_events": events[-10:],
            "uptime_summary": _calc_uptime(events)
        }

    # Salva export
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"[OK] Configuracao exportada para: {output_file}")
    print(f"   - {len(export_data['endpoints'])} endpoints")
    print(f"   - {len(export_data['learning_history'])} eventos de aprendizado")
    print(f"   - {len(export_data['current_status'].get('last_events', []))} eventos recentes")

    return output_file


def import_config(import_file=None):
    """Importa configuracao de arquivo"""
    if import_file is None:
        import_file = str(DEPLOY_DIR / "bridge_export.json")

    if not Path(import_file).exists():
        print(f"[ERRO] Arquivo nao encontrado: {import_file}")
        return False

    with open(import_file, encoding="utf-8") as f:
        import_data = json.load(f)

    # Restaura endpoints
    config_file = CONFIG_DIR / "bridge_config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(import_data.get("endpoints", []), f, indent=2, ensure_ascii=False)

    # Restaura aprendizado
    if import_data.get("learning_history"):
        learning_file = LEARNING_DIR / "failures.json"
        with open(learning_file, "w", encoding="utf-8") as f:
            json.dump(import_data["learning_history"], f, indent=2, ensure_ascii=False)

    print(f"[OK] Configuracao importada de: {import_file}")
    print(f"   - {len(import_data.get('endpoints', []))} endpoints restaurados")
    print(f"   - {len(import_data.get('learning_history', []))} eventos de aprendizado restaurados")

    return True


def generate_deployment_package():
    """Gera pacote de deploy completo"""
    deploy_script = DEPLOY_DIR / "deploy_bridge.sh"

    script_content = '''#!/bin/bash
# EcoSystemUmGrau Bridge Resilience - Auto Deploy Script
set -e
echo "[Instalando Bridge Resilience v2.0..."
pip install psutil requests 2>/dev/null || true
if ! command -v adb &> /dev/null; then
    echo "Instalando ADB..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update && sudo apt-get install -y android-tools-adb
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        brew install android-platform-tools
    fi
fi
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    sudo cp deployment/bridge-resilience.service /etc/systemd/system/
    sudo systemctl enable bridge-resilience
    sudo systemctl start bridge-resilience
elif [[ "$OSTYPE" == "darwin"* ]]; then
    cp deployment/com.bridgeservice.plist ~/Library/LaunchAgents/
    launchctl load ~/Library/LaunchAgents/com.bridgeservice.plist
fi
echo "[OK] Instalacao completa!"
echo "Verificar status: python bridge/universal_bridge.py --health"
'''

    with open(deploy_script, "w", encoding="utf-8") as f:
        f.write(script_content)

    os.chmod(deploy_script, 0o755)

    # Gera systemd service para Linux
    systemd_service = DEPLOY_DIR / "bridge-resilience.service"
    with open(systemd_service, "w", encoding="utf-8") as f:
        f.write("""[Unit]
Description=EcoSystemUmGrau Bridge Resilience Daemon
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/EcoSystemUmGrau/connectivity/bridge/universal_bridge.py --daemon
Restart=always
RestartSec=10
User=root

[Install]
WantedBy=multi-user.target
""")

    print("[OK] Pacote de deploy gerado em: connectivity/deployment/")
    print("   - deploy_bridge.sh (auto-install)")
    print("   - bridge-resilience.service (systemd)")


def main():
    if len(sys.argv) < 2:
        print("Uso: python bridge_exporter.py [export|import|deploy]")
        print("\nComandos:")
        print("  export  - Exporta configuracao atual")
        print("  import  - Importa configuracao previamente exportada")
        print("  deploy  - Gera pacote de deploy")
        return

    cmd = sys.argv[1]
    if cmd == "export":
        export_config(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "import":
        import_config(sys.argv[2] if len(sys.argv) > 2 else None)
    elif cmd == "deploy":
        generate_deployment_package()
    else:
        print(f"Comando desconhecido: {cmd}")


if __name__ == "__main__":
    main()
