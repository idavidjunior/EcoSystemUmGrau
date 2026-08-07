#!/usr/bin/env python3
"""
EcoSystemUmGrau - Universal Bridge Resilience System
Monitorea y mantiene conexiones múltiples con auto-reconexión y aprendizaje
"""

import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from dataclasses import asdict

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from EcoSystemUmGrau.connectivity.bridge.core import (
    ConnectionEndpoint,
    HEALTH_CHECKERS,
    check_adb_tcp, check_adb_usb, check_tailscale,
    check_ssh, check_http, check_dns, check_mqtt,
    check_websocket, check_vpn, check_serial
)

BASE_DIR = Path(__file__).parent.parent.parent
BRIDGE_DIR = BASE_DIR / "connectivity" / "bridge"
CONFIG_DIR = BRIDGE_DIR / "configs"
HEALTH_DIR = BRIDGE_DIR / "health"
LEARNING_DIR = BRIDGE_DIR / "learning"

for d in [CONFIG_DIR, HEALTH_DIR, LEARNING_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class UniversalBridge:
    """Puente universal de resiliência multi-protocolo"""

    def __init__(self):
        self.endpoints: dict[str, ConnectionEndpoint] = {}
        self.status: dict = {}
        self.failure_history: list = []
        self.uptime_tracker: dict = {}
        self.alerts: list = []
        self.current_method = "primary"

        self._load_default_endpoints()
        self._load_config()

    def _load_default_endpoints(self):
        """Configura endpoints padrão com fallback chain"""
        adb_path = "C:\\Users\\David Jr\\AppData\\Local\\Android\\Sdk\\platform-tools\\adb.exe"

        self.endpoints["adb_usb"] = ConnectionEndpoint(
            id="adb_usb", type="adb_usb", name="ADB USB", primary=True,
            config={"adb_path": adb_path},
            fallback_chain=["adb_tcp", "tailscale_forward"]
        )

        self.endpoints["adb_tcp"] = ConnectionEndpoint(
            id="adb_tcp", type="adb_tcp", name="ADB TCP/IP", primary=False,
            config={
                "adb_path": adb_path,
                "device_ips": ["192.168.15.4:5555", "192.168.15.5:5555"]
            },
            fallback_chain=["adb_usb", "tailscale_forward"]
        )

        self.endpoints["tailscale_exit"] = ConnectionEndpoint(
            id="tailscale_exit", type="tailscale_exit", name="Tailscale Exit", primary=True,
            config={"exit_nodes": ["100.91.141.101", "100.64.71.9"]},
            fallback_chain=["adb_tcp", "vpn_alternative"]
        )

        self.endpoints["ssh_primary"] = ConnectionEndpoint(
            id="ssh_primary", type="ssh", name="SSH Primary", primary=True,
            config={"host": "192.168.15.4", "port": 22},
            fallback_chain=["ssh_backup", "tailscale_exit"]
        )

        self.endpoints["ssh_backup"] = ConnectionEndpoint(
            id="ssh_backup", type="ssh", name="SSH Backup", primary=False,
            config={"host": "100.64.71.9", "port": 22},
            fallback_chain=["ssh_primary"]
        )

        self.endpoints["api_local"] = ConnectionEndpoint(
            id="api_local", type="http", name="API Local", primary=True,
            config={"url": "http://127.0.0.1:8765/health", "expected_status": 200},
            fallback_chain=["api_remote", "http_polling"]
        )

        self.endpoints["api_remote"] = ConnectionEndpoint(
            id="api_remote", type="http", name="API Remote", primary=False,
            config={"url": "https://api.davidjunior.dev/health", "expected_status": 200, "timeout": 15},
            fallback_chain=["api_local"]
        )

        self.endpoints["mqtt_broker"] = ConnectionEndpoint(
            id="mqtt_broker", type="mqtt", name="MQTT Broker", primary=True,
            config={"host": "192.168.15.4", "port": 1883},
            fallback_chain=["mqtt_cloud", "websocket_bridge"]
        )

        self.endpoints["mqtt_cloud"] = ConnectionEndpoint(
            id="mqtt_cloud", type="mqtt", name="MQTT Cloud", primary=False,
            config={"host": "mqtt.davidjunior.dev", "port": 8883},
            fallback_chain=["mqtt_broker"]
        )

        self.endpoints["dns_primary"] = ConnectionEndpoint(
            id="dns_primary", type="dns", name="DNS Resolution", primary=True,
            config={"resolvers": ["8.8.8.8", "1.1.1.1", "192.168.15.1"], "test_domain": "google.com"},
            fallback_chain=["dns_tailscale"]
        )

        self.endpoints["ws_service"] = ConnectionEndpoint(
            id="ws_service", type="websocket", name="WebSocket Service", primary=True,
            config={"url": "ws://192.168.15.4:8765/ws"},
            fallback_chain=["ws_backup", "http_polling"]
        )

        self.endpoints["vpn_alternative"] = ConnectionEndpoint(
            id="vpn_alternative", type="vpn", name="Alternative VPN", primary=False,
            config={"type": "openvpn", "config_path": "~/.vpn/alternative.ovpn"},
            fallback_chain=["tailscale_exit"]
        )

    def _load_config(self):
        config_file = CONFIG_DIR / "bridge_config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    saved = json.load(f)
                    for ep_data in saved.get("endpoints", []):
                        ep = ConnectionEndpoint(**ep_data)
                        self.endpoints[ep.id] = ep
            except Exception as e:
                print(f"Aviso: não foi possível carregar config: {e}")

    def _save_config(self):
        config_file = CONFIG_DIR / "bridge_config.json"
        endpoints_data = [asdict(ep) for ep in self.endpoints.values()]
        with open(config_file, "w") as f:
            json.dump({"endpoints": endpoints_data}, f, indent=2)

    def log_event(self, endpoint_id, level, message, data=None):
        timestamp = datetime.now()
        entry = {
            "timestamp": timestamp.isoformat(),
            "epoch": timestamp.timestamp(),
            "endpoint_id": endpoint_id,
            "level": level,
            "message": message,
            "data": data or {},
            "uptime_pct": self.uptime_tracker.get(endpoint_id, {}).get("uptime_pct", 100.0)
        }

        log_file = BRIDGE_DIR / "events.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")

        print(f"[{timestamp.strftime('%H:%M:%S')}] [{level}] {endpoint_id}: {message}")
        return entry

    def check_endpoint(self, endpoint):
        """Verifica um endpoint usando seu checker apropriado"""
        checker = HEALTH_CHECKERS.get(endpoint.type)
        if checker:
            try:
                return checker(endpoint)
            except Exception as e:
                return False, {"error": str(e)}
        return False, {"error": f"No checker for type {endpoint.type}"}

    def run_health_check(self):
        """Verifica todos os endpoints e gera relatório"""
        results = {}
        all_healthy = True

        for ep_id, endpoint in self.endpoints.items():
            is_healthy, data = self.check_endpoint(endpoint)
            results[ep_id] = {
                "healthy": is_healthy,
                "type": endpoint.type,
                "name": endpoint.name,
                "primary": endpoint.primary,
                "details": data,
                "timestamp": datetime.now().isoformat()
            }

            if not is_healthy:
                all_healthy = False
                self.log_event(ep_id, "WARNING", f"Endpoint indisponível: {data.get('error', 'unknown')}")

                # Tenta failover se for endpoint primário
                if endpoint.primary:
                    self.try_failover(endpoint)
            else:
                self.log_event(ep_id, "OK", "Endpoint saudável")

        # Salva relatório de saúde
        self._save_health_report(results)

        return all_healthy, results

    def try_failover(self, failed_endpoint):
        """Tenta endpoints de fallback para o endpoint falho"""
        self.log_event(failed_endpoint.id, "FAILOVER", "Iniciando failover automático")

        for fallback_id in failed_endpoint.fallback_chain:
            if fallback_id in self.endpoints:
                fallback_ep = self.endpoints[fallback_id]
                is_healthy, data = self.check_endpoint(fallback_ep)

                if is_healthy:
                    self.log_event(fallback_id, "FAILOVER", "Fallback ativado com sucesso", data)
                    self.current_method = fallback_id
                    self._record_learning(f"failover_{failed_endpoint.id}", f"Recuperado via {fallback_id}")
                    return True
                else:
                    self.log_event(fallback_id, "FAILOVER", f"Fallback também falhou: {data.get('error', 'unknown')}")

        self.log_event(failed_endpoint.id, "CRITICAL", "Todos os métodos de fallback falharam")
        self._record_learning(f"total_failure_{failed_endpoint.id}", "Todos os métodos falharam")
        return False

    def _record_learning(self, failure_type, details):
        """Registra falha para aprendizado"""
        event = {
            "timestamp": datetime.now().isoformat(),
            "failure_type": failure_type,
            "details": details,
            "resolved": True
        }
        self.failure_history.append(event)

        learning_file = LEARNING_DIR / "failures.json"
        with open(learning_file, "w") as f:
            json.dump(self.failure_history[-100:], f, indent=2)

    def _save_health_report(self, results):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = HEALTH_DIR / f"health_{timestamp}.json"
        with open(report_file, "w") as f:
            json.dump({
                "timestamp": timestamp,
                "all_healthy": all(r["healthy"] for r in results.values()),
                "results": results
            }, f, indent=2)

        # Mantém apenas últimos 50 relatórios
        reports = sorted(HEALTH_DIR.glob("health_*.json"), reverse=True)
        for old in reports[50:]:
            try:
                old.unlink()
            except:
                pass

    def run_daemon(self, interval=15):
        """Executa como daemon de vigilância contínua"""
        self.log_event("bridge", "DAEMON", f"Iniciando daemon de resiliência (interval={interval}s)")

        while True:
            try:
                healthy, results = self.run_health_check()
                time.sleep(interval)
            except KeyboardInterrupt:
                self.log_event("bridge", "DAEMON", "Recebido Ctrl+C - parando")
                break
            except Exception as e:
                self.log_event("bridge", "ERROR", f"Erro no ciclo: {e}")
                time.sleep(5)

    def get_uptime_summary(self):
        """Gera resumo de uptime"""
        if not self.failure_history:
            return {"status": "no_data"}

        total = len(self.failure_history)
        by_type = {}
        for event in self.failure_history:
            ft = event.get("failure_type", "unknown")
            by_type[ft] = by_type.get(ft, 0) + 1

        return {
            "total_events": total,
            "failure_types": by_type,
            "last_check": datetime.now().isoformat()
        }


def main():
    bridge = UniversalBridge()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--daemon":
            bridge.run_daemon()
        elif sys.argv[1] == "--health":
            healthy, results = bridge.run_health_check()
            print(json.dumps({"all_healthy": healthy, "results": results}, indent=2))
        elif sys.argv[1] == "--summary":
            print(json.dumps(bridge.get_uptime_summary(), indent=2))
        elif sys.argv[1] == "--endpoints":
            for ep_id, ep in bridge.endpoints.items():
                print(f"{ep_id}: {ep.type} ({'primary' if ep.primary else 'backup'}) -> fallbacks: {ep.fallback_chain}")
    else:
        healthy, results = bridge.run_health_check()
        sys.exit(0 if healthy else 1)


if __name__ == "__main__":
    main()
