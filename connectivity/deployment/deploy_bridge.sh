#!/bin/bash
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
