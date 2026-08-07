#!/usr/bin/env python3
"""
EcoSystemUmGrau - Bridge Resiliência
Sistema avançado de redundância e failover para conexões ADB/Tailscale

Estratégias implementadas:
1. Múltiplas fontes de conexão (ADB TCP/IP, USB, Tailscale)
2. Failover automático entre métodos
3. Detecção preditiva de falhas
4. Backup de configurações
5. Health checks contínuos
6. Auto-aprendizado de padrões de falha
"""

import subprocess
import time
import json
import os
import sys
import shutil
import socket
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).parent.parent
BRIDGE_DIR = BASE_DIR / "connectivity" / "bridge"
BACKUP_DIR = BRIDGE_DIR / "backups"
LEARNING_DIR = BRIDGE_DIR / "learning"
HEALTH_DIR = BRIDGE_DIR / "health"

for d in [BRIDGE_DIR, BACKUP_DIR, LEARNING_DIR, HEALTH_DIR]:
    d.mkdir(parents=True, exist_ok=True)

class BridgeResiliencia:
    def __init__(self):
        self.config = {
            "adb_paths": [
                "C:\\Users\\David Jr\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe",
            ],
            "device_ips": ["192.168.15.4", "192.168.15.5", "192.168.15.6"],
            "tailscale_exit_nodes": ["100.91.141.101", "100.64.71.9"],
            "backup_methods": ["tailscale", "adb_tcp", "usb_fallback"],
            "health_check_interval": 15,
            "failover_timeout": 60,
            "max_retries": 5
        }
        self.load_config()
        self.failure_history = self.load_learning()
        self.current_method = "tailscale"
        self.backup_available = False

    def load_config(self):
        """Carrega configuração do arquivo"""
        config_file = BRIDGE_DIR / "bridge_config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    saved = json.load(f)
                    self.config.update(saved)
            except:
                pass

    def save_config(self):
        """Salva configuração"""
        with open(BRIDGE_DIR / "bridge_config.json", "w") as f:
            json.dump(self.config, f, indent=2)

    def load_learning(self):
        """Carrega histórico de falhas para aprendizado"""
        learning_file = LEARNING_DIR / "failure_patterns.json"
        if learning_file.exists():
            try:
                with open(learning_file) as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_learning(self):
        """Salva histórico de falhas"""
        learning_file = LEARNING_DIR / "failure_patterns.json"
        with open(learning_file, "w") as f:
            json.dump(self.failure_history, f, indent=2)

    def log_event(self, message, level="INFO", method=None):
        """Registra eventos de conexão"""
        timestamp = datetime.now().isoformat()
        entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "method": method or self.current_method,
            "uptime_pct": self.calculate_uptime(),
            "active_connections": self.get_active_connections()
        }

        log_file = BRIDGE_DIR / "bridge_events.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def calculate_uptime(self):
        """Calcula uptime das conexões baseado no histórico"""
        if not self.failure_history:
            return 100.0

        total_time = 0
        failure_time = 0
        now = datetime.now()

        for event in self.failure_history[-100:]:  # Últimos 100 eventos
            if "timestamp" in event and "downtime" in event:
                timestamp = datetime.fromisoformat(event["timestamp"])
                downtime = event.get("downtime", 60)
                gap = (now - timestamp).total_seconds()
                if gap < 86400:  # Últimas 24 horas
                    failure_time += downtime

        total_time = 86400  # 24 horas
        uptime = max(0, 100 - (failure_time / total_time * 100))
        return round(uptime, 2)

    def get_active_connections(self):
        """Conta conexões ativas de todos os métodos"""
        connections = {
            "adb": len(self.get_adb_devices()),
            "tailscale": len(self.get_tailscale_devices())
        }
        return connections

    def get_adb_devices(self):
        """Lista dispositivos ADB conectados"""
        for adb_path in self.config["adb_paths"]:
            try:
                result = subprocess.run(
                    [adb_path, "devices"],
                    capture_output=True, text=True, timeout=10
                )

                devices = []
                for line in result.stdout.strip().split('\n')[1:]:
                    if 'device' in line and not line.startswith('*'):
                        parts = line.split()
                        if len(parts) >= 2 and parts[1] == "device":
                            devices.append(parts[0])
                return devices
            except:
                continue
        return []

    def get_tailscale_devices(self):
        """Lista dispositivos Tailscale conectados"""
        try:
            result = subprocess.run(
                ["tailscale", "status", "--json"],
               capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                peers = data.get("Peer", {})
                return list(peers.keys())
            return []
        except:
            return []

    def check_adb_tcp(self, device_ip: str) -> bool:
        """Verifica conexão ADB TCP/IP"""
        for adb_path in self.config["adb_paths"]:
            try:
                result = subprocess.run(
                    [adb_path, "connect", f"{device_ip}:5555"],
                    capture_output=True, text=True, timeout=15
                )
                if "connected" in result.stdout.lower() or "already" in result.stdout.lower():
                    self.log_event(f"ADB TCP conectado: {device_ip}", "SUCCESS", "adb_tcp")
                    return True
            except:
                continue
        return False

    def check_tailscale_connection(self) -> bool:
        """Verifica conexão Tailscale"""
        try:
            result = subprocess.run(
                ["tailscale", "status"],
                capture_output=True, text=True, timeout=10
            )
            return "active" in result.stdout.lower()
        except:
            return False

    def check_exit_node_health(self, node_ip: str) -> bool:
        """Verifica saúde de um exit node via ping"""
        try:
            result = subprocess.run(
                ["ping", "-n", "3", "-w", "5", node_ip],
                capture_output=True, text=True, timeout=20
            )
            return result.returncode == 0 and "TTL" in result.stdout
        except:
            return False

    def backup_method_activation(self) -> bool:
        """Tenta métodos de backup em ordem de prioridade"""
        methods = self.config["backup_methods"]

        for method in methods:
            if method == self.current_method:
                continue

            if method == "adb_tcp":
                for ip in self.config["device_ips"]:
                    if self.check_adb_tcp(ip):
                        self.current_method = "adb_tcp"
                        return True

            elif method == "tailscale":
                if self.check_tailscale_connection():
                    self.current_method = "tailscale"
                    return True

            elif method == "usb_fallback":
                devices = self.get_adb_devices()
                if devices:
                    self.current_method = "usb_fallback"
                    return True

        return False

    def failover(self):
        """Executa failover para método de backup"""
        self.log_event("Iniciando failover automático", "WARNING")

        if self.backup_method_activation():
            self.log_event("Failover bem-sucedido", "SUCCESS", self.current_method)
            return True
        else:
            self.log_event("Todos os métodos de backup falharam", "CRITICAL")
            self.record_failure("all_methods_failed", "Failover total falhou")
            return False

    def record_failure(self, failure_type: str, details: str):
        """Registra falha para aprendizado futuro"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "failure_type": failure_type,
            "details": details,
            "method": self.current_method,
            "downtime": 0,
            "resolved": False
        }
        self.failure_history.append(event)
        self.save_learning()

    def analyze_failure_patterns(self):
        """Analisa padrões de falha para prevenção preditiva"""
        if len(self.failure_history) < 3:
            return None

        # Conta tipos de falha por método
        failures_by_method = {}
        for event in self.failure_history[-20:]:
            method = event.get("method", "unknown")
            failures_by_method[method] = failures_by_method.get(method, 0) + 1

        # Identifica método mais instável
        if failures_by_method:
            unstable = max(failures_by_method, key=failures_by_method.get)
            count = failures_by_method[unstable]

            if count >= 3:
                self.log_event(
                    f"Método {unstable} apresenta {count} falhas - prioridade de failover ajustada",
                    "ANALYSIS"
                )
                # Reordena métodos de backup para priorizar este
                if unstable in self.config["backup_methods"]:
                    self.config["backup_methods"].remove(unstable)
                    self.config["backup_methods"].insert(0, unstable)

        # Identifica padrões horários de falha
        hour_failures = {}
        for event in self.failure_history:
            try:
                hour = datetime.fromisoformat(event["timestamp"]).hour
                hour_failures[hour] = hour_failures.get(hour, 0) + 1
            except:
                continue

        peak_hour = max(hour_failures, key=hour_failures.get) if hour_failures else None
        if peak_hour and hour_failures[peak_hour] >= 3:
            self.log_event(
                f"Falhas concentradas às {peak_hour}:00 - ajustando intervalo de check",
                "ANALYSIS"
            )
            self.config["health_check_interval"] = 5  # Mais agressivo nesse horário

        return {
            "failures_by_method": failures_by_method,
            "peak_hour": peak_hour,
            "total_analyzed": len(self.failure_history[-20:])
        }

    def health_check(self) -> Tuple[bool, Dict]:
        """Executa health check completo"""
        health_status = {
            "timestamp": datetime.now().isoformat(),
            "methods": {},
            "overall": "healthy",
            "recommendations": []
        }

        # Check ADB
        adb_devices = self.get_adb_devices()
        health_status["methods"]["adb"] = {
            "connected": len(adb_devices) > 0,
            "devices": adb_devices
        }

        # Check Tailscale
        ts_ok = self.check_tailscale_connection()
        ts_devices = self.get_tailscale_devices()
        health_status["methods"]["tailscale"] = {
            "connected": ts_ok,
            "devices": ts_devices
        }

        # Check exit nodes
        for node in self.config["tailscale_exit_nodes"]:
            healthy = self.check_exit_node_health(node)
            health_status["methods"][f"exit_node_{node}"] = {
                "healthy": healthy,
                "ip": node
            }

        # Determine overall health
        if not ts_ok and not adb_devices:
            health_status["overall"] = "unhealthy"
            health_status["recommendations"].append("Ativar método de backup imediatamente")
        elif not ts_ok:
            health_status["overall"] = "degraded"
            health_status["recommendations"].append("Tailscale offline - usar ADB como backup")

        return health_status["overall"] == "healthy", health_status

    def save_health_report(self, health_status: dict):
        """Salva relatório de saúde"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = HEALTH_DIR / f"health_{timestamp}.json"
        with open(report_file, "w") as f:
            json.dump(health_status, f, indent=2)

        # Mantém apenas os últimos 50 relatórios
        reports = sorted(HEALTH_DIR.glob("health_*.json"), reverse=True)
        for old in reports[50:]:
            try:
                old.unlink()
            except:
                pass

    def run_bridge_cycle(self):
        """Executa ciclo completo de ponte e resiliência"""
        # Health check
        healthy, health_status = self.health_check()
        self.save_health_report(health_status)

        if not healthy:
            self.log_event(f"Status: {health_status['overall']}", "WARNING")

            # Análise preditiva
            patterns = self.analyze_failure_patterns()

            # Failover se necessário
            if health_status["overall"] == "unhealthy":
                recovered = self.failover()
                if recovered:
                    self.log_event("Recuperado via failover", "SUCCESS")
                else:
                    self.log_event("Falha crítica - todos os métodos inativos", "CRITICAL")
        else:
            # Atualiza uptime
            for event in self.failure_history:
                if not event.get("resolved"):
                    event["resolved"] = True
                    event["downtime"] = int((datetime.now() - datetime.fromisoformat(event["timestamp"])).total_seconds())
            self.save_learning()

        return healthy

def main():
    bridge = BridgeResiliencia()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--health":
            healthy, status = bridge.health_check()
            print(json.dumps(status, indent=2))
        elif sys.argv[1] == "--failover":
            bridge.failover()
        elif sys.argv[1] == "--analyze":
            patterns = bridge.analyze_failure_patterns()
            print(json.dumps(patterns, indent=2))
        elif sys.argv[1] == "--daemon":
            print("Iniciando ponte de resiliência (Ctrl+C para parar)")
            while True:
                try:
                    bridge.run_bridge_cycle()
                    time.sleep(bridge.config["health_check_interval"])
                except KeyboardInterrupt:
                    print("\nDesligando ponte de resiliência")
                    break
                except Exception as e:
                    bridge.log_event(f"Erro no ciclo: {e}", "ERROR")
                    time.sleep(5)
    else:
        healthy = bridge.run_bridge_cycle()
        sys.exit(0 if healthy else 1)

if __name__ == "__main__":
    main()
