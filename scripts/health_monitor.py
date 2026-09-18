#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""health_monitor.py — Health Checks Contínuos do Ecossistema.

Monitoramento contínuo da saúde de todos os serviços (Jarvis, TTS, Vigilante, MCPs),
verificação de integridade de dados e monitoramento de recursos (CPU, memória, disco).

Uso:
  python scripts/health_monitor.py check           # Health check completo
  python scripts/health_monitor.py check-service jarvis  # Check de serviço específico
  python scripts/health_monitor.py monitor         # Modo monitoramento contínuo
  python scripts/health_monitor.py status          # Status geral de saúde

Saída JSON: {servicos, integridade, recursos, alertas, timestamp}
"""
import json
import os
import psutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"

# Serviços a monitorar
SERVICES = {
    "jarvis_bridge": {"process": "python", "pattern": "jarvis_bridge.py"},
    "tts_service": {"process": "python", "pattern": "tts_service.py"},
    "vigilante": {"process": "powershell", "pattern": "vigilante.ps1"},
    "widget_supervisao": {"process": "python", "pattern": "widget_supervisao.py"},
}

# Arquivos críticos para integridade
CRITICAL_FILES = [
    ROOT / "config" / "agents" / "00-system-rules.md",
    ROOT / "ler-runtime" / "knowledge" / "knowledge_graph.json",
    ROOT / "conhecimento" / "memoria" / "memories.json",
    ROOT / "conversa_unica.json",
]


class HealthMonitor:
    """Monitor de saúde contínuo do ecossistema."""
    
    def __init__(self):
        self.alerts = []
        self._last_check = None
        
    def _check_process_running(self, service_name: str) -> dict:
        """Verifica se um processo de serviço está rodando."""
        service_config = SERVICES.get(service_name, {})
        process_type = service_config.get("process", "")
        pattern = service_config.get("pattern", "")
        
        if not pattern:
            return {
                "status": "unknown",
                "message": f"Serviço {service_name} não configurado"
            }
        
        try:
            # Listar processos do tipo especificado
            if process_type == "python":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq python.exe", "/FO", "CSV"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                processes = result.stdout
                running = pattern in processes
            elif process_type == "powershell":
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq powershell.exe", "/FO", "CSV"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                processes = result.stdout
                running = pattern in processes
            else:
                running = False
            
            if running:
                return {
                    "status": "healthy",
                    "message": f"Serviço {service_name} está rodando"
                }
            else:
                return {
                    "status": "unhealthy",
                    "message": f"Serviço {service_name} não está rodando"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Erro ao verificar {service_name}: {e}"
            }
    
    def check_service(self, service: str) -> dict:
        """Health check de um serviço específico."""
        result = self._check_process_running(service)
        
        # Adiciona timestamp
        result["timestamp"] = datetime.now().isoformat()
        result["service"] = service
        
        # Gera alerta se unhealthy
        if result["status"] == "unhealthy":
            self.alerts.append({
                "severity": "high",
                "service": service,
                "message": result["message"],
                "timestamp": result["timestamp"]
            })
        
        return result
    
    def check_integrity(self) -> dict:
        """Verificação de integridade de dados críticos."""
        integrity = {
            "files_checked": len(CRITICAL_FILES),
            "files_ok": 0,
            "files_corrupted": 0,
            "files_missing": 0,
            "details": []
        }
        
        for file_path in CRITICAL_FILES:
            if not file_path.exists():
                integrity["files_missing"] += 1
                integrity["details"].append({
                    "file": str(file_path.relative_to(ROOT)),
                    "status": "missing"
                })
                self.alerts.append({
                    "severity": "critical",
                    "type": "integrity",
                    "message": f"Arquivo crítico ausente: {file_path.name}",
                    "timestamp": datetime.now().isoformat()
                })
                continue
            
            try:
                # Verifica se o arquivo pode ser lido
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                # Verifica integridade básica (JSON)
                if file_path.suffix == ".json":
                    try:
                        json.loads(content)
                        integrity["files_ok"] += 1
                        integrity["details"].append({
                            "file": str(file_path.relative_to(ROOT)),
                            "status": "ok"
                        })
                    except json.JSONDecodeError as e:
                        integrity["files_corrupted"] += 1
                        integrity["details"].append({
                            "file": str(file_path.relative_to(ROOT)),
                            "status": "corrupted",
                            "error": str(e)
                        })
                        self.alerts.append({
                            "severity": "high",
                            "type": "integrity",
                            "message": f"Arquivo JSON corrompido: {file_path.name}",
                            "timestamp": datetime.now().isoformat()
                        })
                else:
                    integrity["files_ok"] += 1
                    integrity["details"].append({
                        "file": str(file_path.relative_to(ROOT)),
                        "status": "ok"
                    })
                    
            except Exception as e:
                integrity["files_corrupted"] += 1
                integrity["details"].append({
                    "file": str(file_path.relative_to(ROOT)),
                    "status": "error",
                    "error": str(e)
                })
                self.alerts.append({
                    "severity": "high",
                    "type": "integrity",
                    "message": f"Erro ao ler arquivo: {file_path.name}",
                    "timestamp": datetime.now().isoformat()
                })
        
        integrity["timestamp"] = datetime.now().isoformat()
        return integrity
    
    def check_resources(self) -> dict:
        """Monitoramento de recursos (CPU, memória, disco)."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(ROOT))
            
            resources = {
                "cpu": {
                    "percent": cpu_percent,
                    "status": "ok" if cpu_percent < 80 else "warning" if cpu_percent < 95 else "critical"
                },
                "memory": {
                    "percent": memory.percent,
                    "available_gb": memory.available / (1024**3),
                    "total_gb": memory.total / (1024**3),
                    "status": "ok" if memory.percent < 80 else "warning" if memory.percent < 95 else "critical"
                },
                "disk": {
                    "percent": disk.percent,
                    "free_gb": disk.free / (1024**3),
                    "total_gb": disk.total / (1024**3),
                    "status": "ok" if disk.percent < 80 else "warning" if disk.percent < 95 else "critical"
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Gerar alertas se crítico
            if resources["cpu"]["status"] == "critical":
                self.alerts.append({
                    "severity": "critical",
                    "type": "resources",
                    "message": f"CPU crítica: {cpu_percent}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            if resources["memory"]["status"] == "critical":
                self.alerts.append({
                    "severity": "critical",
                    "type": "resources",
                    "message": f"Memória crítica: {memory.percent}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            if resources["disk"]["status"] == "critical":
                self.alerts.append({
                    "severity": "critical",
                    "type": "resources",
                    "message": f"Disco crítico: {disk.percent}%",
                    "timestamp": datetime.now().isoformat()
                })
            
            return resources
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def generate_alert(self, severity: str, message: str) -> dict:
        """Gera um alerta."""
        alert = {
            "severity": severity,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.alerts.append(alert)
        return alert
    
    def full_check(self) -> dict:
        """Health check completo de todos os componentes."""
        self.alerts = []  # Reset alertas
        
        # Check de serviços
        services = {}
        for service_name in SERVICES.keys():
            services[service_name] = self.check_service(service_name)
        
        # Check de integridade
        integrity = self.check_integrity()
        
        # Check de recursos
        resources = self.check_resources()
        
        self._last_check = datetime.now().isoformat()
        
        return {
            "services": services,
            "integrity": integrity,
            "resources": resources,
            "alerts": self.alerts,
            "last_check": self._last_check,
            "overall_status": "healthy" if not self.alerts else "degraded"
        }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python health_monitor.py check|check-service|monitor|status")
        sys.exit(1)
    
    command = sys.argv[1]
    monitor = HealthMonitor()
    
    if command == "check":
        result = monitor.full_check()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "check-service":
        if len(sys.argv) < 3:
            print("Uso: python health_monitor.py check-service <nome-servico>")
            sys.exit(1)
        service = sys.argv[2]
        result = monitor.check_service(service)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "status":
        resources = monitor.check_resources()
        print(json.dumps(resources, indent=2, ensure_ascii=False))
    
    elif command == "monitor":
        print("Modo monitoramento contínuo (Ctrl+C para parar)")
        try:
            while True:
                result = monitor.full_check()
                
                print(f"[{datetime.now().isoformat()}] Status geral: {result['overall_status']}")
                print(f"  Serviços: {sum(1 for s in result['services'].values() if s['status'] == 'healthy')}/{len(result['services'])} healthy")
                print(f"  Integridade: {result['integrity']['files_ok']}/{result['integrity']['files_checked']} arquivos OK")
                print(f"  Alertas: {len(result['alerts'])}")
                
                if result["alerts"]:
                    for alert in result["alerts"]:
                        print(f"  ALERTA [{alert['severity']}]: {alert['message']}")
                
                time.sleep(300)  # Verifica a cada 5 minutos
                
        except KeyboardInterrupt:
            print("\nMonitoramento encerrado")
    
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()