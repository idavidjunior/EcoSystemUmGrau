#!/usr/bin/env python3
"""
EcoSystemUmGrau - Guardião de Conexões
Monitoramento autônomo e resiliência para ADB e Tailscale
"""

import subprocess
import time
import json
import os
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
STATUS_FILE = BASE_DIR / "connectivity" / "status" / "connection_status.json"
LOG_FILE = BASE_DIR / "connectivity" / "logs" / "guardian.log"
RECOVERY_LOG = BASE_DIR / "connectivity" / "logs" / "recovery_actions.log"

STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

class ConnectionGuardian:
    def __init__(self):
        self.adb_path = self._find_adb()
        self.tailscale_path = self._find_tailscale()
        self.state = {"last_check": None, "adb": {}, "tailscale": {}}
        self.load_state()

    def _find_adb(self):
        result = subprocess.run(["where", "adb"], capture_output=True, text=True)
        return result.stdout.strip().split('\n')[0] if result.stdout.strip() else None

    def _find_tailscale(self):
        result = subprocess.run(["where", "tailscale"], capture_output=True, text=True)
        return result.stdout.strip().split('\n')[0] if result.stdout.strip() else None

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"[{timestamp}] [{level}] {message}\n"
        with open(LOG_FILE, "a") as f:
            f.write(entry)
        print(entry.strip())

    def log_recovery(self, action, success):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status = "SUCCESS" if success else "FAILED"
        entry = f"[{timestamp}] [{status}] {action}\n"
        with open(RECOVERY_LOG, "a") as f:
            f.write(entry)

    def check_adb(self):
        if not self.adb_path:
            self.log("ADB não encontrado", "CRITICAL")
            return {"status": "missing", "devices": [], "auto_installed": False}

        try:
            result = subprocess.run(
                [self.adb_path, "devices"],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout.strip()
            devices = []
            for line in output.split('\n')[1:]:
                if line.strip() and not line.startswith('*'):
                    parts = line.split()
                    if len(parts) >= 2:
                        devices.append({"id": parts[0], "status": parts[1]})

            active = [d for d in devices if d["status"] == "device"]
            status = "connected" if active else "disconnected"

            if status == "disconnected" and devices:
                self.log(f"Tentando reconexão ADB para {devices}", "WARNING")
                self._recover_adb(devices)

            return {
                "status": status,
                "devices": devices,
                "active_count": len(active),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.log(f"Erro ao checar ADB: {e}", "ERROR")
            return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

    def _recover_adb(self, devices):
        for device in devices:
            try:
                subprocess.run([self.adb_path, "connect", device["id"]],
                             capture_output=True, text=True, timeout=15)
                self.log_recovery(f"Reconexão ADB para {device['id']}", True)
            except Exception as e:
                self.log_recovery(f"Reconexão ADB para {device['id']}: {e}", False)

    def check_tailscale(self):
        if not self.tailscale_path:
            self.log("Tailscale não encontrado", "CRITICAL")
            return {"status": "missing", "devices": [], "online": False}

        try:
            result = subprocess.run(
                [self.tailscale_path, "status"],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout.strip()
            lines = output.split('\n')

            devices = []
            online = False
            for line in lines:
                if 'active' in line:
                    online = True
                if any(kw in line for kw in ['100.', '192.168.', 'desktop-', 'android']):
                    parts = line.split()
                    if len(parts) >= 2:
                        devices.append({
                            "ip": parts[0],
                            "name": parts[1],
                            "status": parts[-1] if parts[-1] in ['active', 'offline'] else 'unknown'
                        })

            if not online:
                self.log("Tailscale offline - tentando reiniciar", "WARNING")
                self._recover_tailscale()

            return {
                "status": "online" if online else "offline",
                "devices": devices,
                "online": online,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            self.log(f"Erro ao checar Tailscale: {e}", "ERROR")
            return {"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()}

    def _recover_tailscale(self):
        actions = [
            ["netsh", "interface", "set", "interface", "Tailscale", "enabled"],
            ["sc", "start", " tailscale"],
            [self.tailscale_path, "up"],
            [self.tailscale_path, "serve", "restart"]
        ]

        for cmd in actions:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                success = result.returncode == 0
                action_str = " ".join(cmd)
                self.log_recovery(f"Tailscale recovery: {action_str}", success)
                if success:
                    break
            except Exception as e:
                self.log_recovery(f"Tailscale recovery: {' '.join(cmd)} - {e}", False)

    def auto_heal(self):
        """Detecta problemas comuns e aplica correções"""
        problems = []

        # Check 1: ADB not in PATH
        if not self.adb_path:
            problems.append(("adb_missing", "Adicionando ADB ao PATH"))
            self._install_adb()

        # Check 2: Tailscale offline
        ts_status = self.check_tailscale()
        if ts_status["status"] == "offline":
            problems.append(("tailscale_offline", "Reconectando Tailscale"))

        # Check 3: ADB devices missing
        adb_status = self.check_adb()
        if adb_status["status"] == "disconnected":
            problems.append(("adb_disconnected", "Reconectando dispositivos ADB"))

        # Check 4: Network adapter issues
        if self._check_network_adapter():
            problems.append(("network_adapter", "Reiniciando adaptador de rede"))
            self._fix_network_adapter()

        if problems:
            self.log(f"Auto-curando {len(problems)} problemas: {problems}", "HEAL")

        return problems

    def _install_adb(self):
        """Tenta localizar e adicionar ADB ao PATH via Android SDK"""
        sdk_paths = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk" / "platform-tools",
            Path(os.environ.get("ANDROID_HOME", "")) / "platform-tools",
            Path(os.environ.get("ANDROID_SDK_ROOT", "")) / "platform-tools"
        ]

        for path in sdk_paths:
            adb_exe = path / "adb.exe"
            if adb_exe.exists():
                current_path = os.environ.get("PATH", "")
                if str(path) not in current_path:
                    os.environ["PATH"] = str(path) + os.pathsep + current_path
                    self.adb_path = str(adb_exe)
                    self.log(f"ADB encontrado e adicionado ao PATH: {adb_exe}", "HEAL")
                    return True
        return False

    def _check_network_adapter(self):
        """Verifica se há problemas com adaptadores de rede"""
        try:
            result = subprocess.run(
                ["ipconfig", "/all"],
                capture_output=True, text=True, timeout=5
            )
            output = result.stdout.lower()

            # Detecta adaptadores problemáticos
            if "sem configuração ip" in output and "tailscale" in output:
                return True
            return False
        except:
            return False

    def _fix_network_adapter(self):
        """Reinicia adaptadores de rede com problemas"""
        adapters = ["Tailscale", "vEthernet (WSL)", "Bluetooth", "Wi-Fi"]
        for adapter in adapters:
            try:
                subprocess.run(["netsh", "interface", "set", "interface", adapter, "enabled"],
                             capture_output=True, timeout=10)
            except:
                pass

    def save_state(self):
        self.state["last_check"] = datetime.now().isoformat()
        self.state["adb"] = self.check_adb()
        self.state["tailscale"] = self.check_tailscale()

        with open(STATUS_FILE, "w") as f:
            json.dump(self.state, f, indent=2)

        self.log(f"Status salvo: {STATUS_FILE}", "STATUS")

    def load_state(self):
        if STATUS_FILE.exists():
            try:
                with open(STATUS_FILE, "r") as f:
                    self.state = json.load(f)
                    self.adb_path = self.state.get("adb_path", self.adb_path)
            except:
                self.state = {"last_check": None, "adb": {}, "tailscale": {}}

    def run_cycle(self):
        """Executa um ciclo completo de verificação e cura"""
        self.log("Iniciando ciclo de monitoramento", "CYCLE")

        # Auto-detecta e cura problemas
        healed = self.auto_heal()

        # Re-verifica após cura
        self.save_state()

        # Resumo
        adb_ok = self.state["adb"].get("status") in ["connected", "device"]
        ts_ok = self.state["tailscale"].get("status") == "online"

        self.log(f"Ciclo concluído: ADB={'OK' if adb_ok else 'ISSUE'}, "
                f"Tailscale={'OK' if ts_ok else 'ISSUE'}, Curados={len(healed)}")

        return adb_ok and ts_ok

def main():
    guardian = ConnectionGuardian()

    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        guardian.log("Modo daemon ativado - vigilância contínua", "DAEMON")
        interval = 30  # segundos entre ciclos
        while True:
            try:
                guardian.run_cycle()
                time.sleep(interval)
            except KeyboardInterrupt:
                guardian.log("Guardião desligado pelo usuário", "DAEMON")
                break
            except Exception as e:
                guardian.log(f"Erro no ciclo: {e}", "ERROR")
                time.sleep(5)
    else:
        success = guardian.run_cycle()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
