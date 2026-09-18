#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""dynamic_self_knowledge.py — Autoconhecimento Dinâmico do Ecossistema.

Scanner contínuo de estruturas ativas (agentes, skills, scripts, MCPs) com
detecção de alterações em tempo real e atualização dinâmica do inventário.

Uso:
  python scripts/dynamic_self_knowledge.py scan          # Escaneia estruturas
  python scripts/dynamic_self_knowledge.py monitor       # Modo monitoramento contínuo
  python scripts/dynamic_self_knowledge.py status        # Status do autoconhecimento
  python scripts/dynamic_self_knowledge.py diff          # Detecta alterações desde último scan

Saída JSON: {estruturas, alteracoes, timestamp, inventario}
"""
import json
import os
import re
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
CONFIG = ROOT / "config"
MCP = ROOT / "mcp"
LER_RUNTIME = ROOT / "ler-runtime"
CONHECIMENTO = ROOT / "conhecimento"

# Estado persistente do autoconhecimento
STATE_FILE = ROOT / "runtime" / "dynamic_self_knowledge_state.json"

# Lock para evitar múltiplas instâncias
LOCK_FILE = ROOT / "runtime" / "dynamic_self_knowledge.lock"


class DynamicSelfKnowledge:
    """Scanner contínuo de estruturas do ecossistema."""
    
    def __init__(self):
        self.state = self._load_state()
        self._last_scan = self.state.get("last_scan", {})
        self._structures = self.state.get("structures", {})
        
    def _load_state(self) -> dict:
        """Carrega estado persistente do autoconhecimento."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "last_scan": {},
            "structures": {},
            "last_updated": None,
            "scan_count": 0
        }
    
    def _save_state(self):
        """Salva estado persistente do autoconhecimento."""
        self.state["last_updated"] = datetime.now().isoformat()
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar estado: {e}")
    
    def _calculate_hash(self, file_path: Path) -> str:
        """Calcula hash SHA256 de um arquivo."""
        if not file_path.exists():
            return ""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return ""
    
    def _scan_agents(self) -> dict:
        """Escaneia agentes em config/agents/."""
        agents_dir = CONFIG / "agents"
        agents = {}
        
        if not agents_dir.exists():
            return agents
        
        for agent_file in agents_dir.glob("*.md"):
            agent_id = agent_file.stem
            hash_val = self._calculate_hash(agent_file)
            
            # Extrai responsabilidade do arquivo
            responsabilidade = ""
            try:
                content = agent_file.read_text(encoding="utf-8")
                match = re.search(r"responsabilidade[:\s]*([^\n]+)", content, re.IGNORECASE)
                if match:
                    responsabilidade = match.group(1).strip()
            except Exception:
                pass
            
            agents[agent_id] = {
                "arquivo": str(agent_file.relative_to(ROOT)),
                "hash": hash_val,
                "responsabilidade": responsabilidade,
                "tipo": "agente",
                "modificado": agent_file.stat().st_mtime if agent_file.exists() else None
            }
        
        return agents
    
    def _scan_skills(self) -> dict:
        """Escaneia skills em mcp/*/habilidades/."""
        skills = {}
        
        if not MCP.exists():
            return skills
        
        for domain_dir in MCP.iterdir():
            if not domain_dir.is_dir():
                continue
            
            habilidades_dir = domain_dir / "habilidades"
            if not habilidades_dir.exists():
                continue
            
            for skill_dir in habilidades_dir.iterdir():
                if not skill_dir.is_dir():
                    continue
                
                skill_file = skill_dir / "skill.md"
                if not skill_file.exists():
                    skill_file = skill_dir / "SKILL.md"
                
                if skill_file.exists():
                    skill_id = skill_dir.name
                    hash_val = self._calculate_hash(skill_file)
                    
                    skills[skill_id] = {
                        "arquivo": str(skill_file.relative_to(ROOT)),
                        "hash": hash_val,
                        "dominio": domain_dir.name,
                        "tipo": "skill",
                        "modificado": skill_file.stat().st_mtime
                    }
        
        return skills
    
    def _scan_scripts(self) -> dict:
        """Escaneia scripts principais."""
        scripts_list = {}
        
        # Scripts principais (excluindo legado e testes)
        main_scripts = [
            "memory_engine.py",
            "response_normalizer.py",
            "validar_resposta.py",
            "validar_idioma.py",
            "validar_bajulacao.py",
            "jarvis_bridge.py",
            "dialogo.py",
            "vigilante.ps1",
            "runtime_kernel.py",
        ]
        
        for script_name in main_scripts:
            script_file = SCRIPTS / script_name
            if script_file.exists():
                hash_val = self._calculate_hash(script_file)
                scripts_list[script_name] = {
                    "arquivo": str(script_file.relative_to(ROOT)),
                    "hash": hash_val,
                    "tipo": "script",
                    "modificado": script_file.stat().st_mtime
                }
        
        return scripts_list
    
    def _scan_mcp_servers(self) -> dict:
        """Escaneia servidores MCP."""
        mcp_servers = {}
        
        if not MCP.exists():
            return mcp_servers
        
        for server_file in MCP.glob("*/server.py"):
            domain = server_file.parent.name
            hash_val = self._calculate_hash(server_file)
            
            mcp_servers[domain] = {
                "arquivo": str(server_file.relative_to(ROOT)),
                "hash": hash_val,
                "tipo": "mcp_server",
                "modificado": server_file.stat().st_mtime if server_file.exists() else None
            }
        
        return mcp_servers
    
    def scan_structures(self) -> dict:
        """Escaneia todas as estruturas do ecossistema."""
        timestamp = datetime.now().isoformat()
        
        structures = {
            "agents": self._scan_agents(),
            "skills": self._scan_skills(),
            "scripts": self._scan_scripts(),
            "mcp_servers": self._scan_mcp_servers(),
            "timestamp": timestamp
        }
        
        # Atualiza estado
        self._structures = structures
        self.state["structures"] = structures
        self.state["last_scan"] = structures
        self.state["scan_count"] = self.state.get("scan_count", 0) + 1
        self._save_state()
        
        return structures
    
    def detect_changes(self) -> list:
        """Detecta alterações desde o último scan."""
        current = self.scan_structures()
        previous = self._last_scan
        
        changes = []
        
        if not previous:
            return changes
        
        # Comparar cada categoria
        for category in ["agents", "skills", "scripts", "mcp_servers"]:
            current_items = current.get(category, {})
            previous_items = previous.get(category, {})
            
            # Detectar adições
            for item_id, item_data in current_items.items():
                if item_id not in previous_items:
                    changes.append({
                        "tipo": "adicao",
                        "categoria": category,
                        "item_id": item_id,
                        "dados": item_data
                    })
                elif item_data["hash"] != previous_items[item_id]["hash"]:
                    changes.append({
                        "tipo": "modificacao",
                        "categoria": category,
                        "item_id": item_id,
                        "dados": item_data,
                        "hash_anterior": previous_items[item_id]["hash"]
                    })
            
            # Detectar remoções
            for item_id in previous_items:
                if item_id not in current_items:
                    changes.append({
                        "tipo": "remocao",
                        "categoria": category,
                        "item_id": item_id,
                        "dados": previous_items[item_id]
                    })
        
        return changes
    
    def update_inventory(self) -> dict:
        """Atualiza inventário dinâmico."""
        structures = self.scan_structures()
        
        inventory = {
            "total_estruturas": sum(len(v) for v in structures.values() if isinstance(v, dict)),
            "por_categoria": {
                "agents": len(structures.get("agents", {})),
                "skills": len(structures.get("skills", {})),
                "scripts": len(structures.get("scripts", {})),
                "mcp_servers": len(structures.get("mcp_servers", {}))
            },
            "timestamp": structures["timestamp"],
            "scan_count": self.state["scan_count"]
        }
        
        return inventory
    
    def publish_state(self) -> dict:
        """Publica estado do autoconhecimento (simulado)."""
        state = {
            "autoconhecimento": {
                "status": "ativo",
                "last_scan": self.state.get("last_updated"),
                "scan_count": self.state.get("scan_count", 0),
                "inventory": self.update_inventory()
            }
        }
        
        # Em produção, isso publicaria via WebSocket
        print(f"[Autoconhecimento] Estado publicado: {json.dumps(state, ensure_ascii=False)}")
        
        return state


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python dynamic_self_knowledge.py scan|monitor|status|diff")
        sys.exit(1)
    
    command = sys.argv[1]
    dsk = DynamicSelfKnowledge()
    
    if command == "scan":
        result = dsk.scan_structures()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "diff":
        changes = dsk.detect_changes()
        print(json.dumps(changes, indent=2, ensure_ascii=False))
    
    elif command == "status":
        inventory = dsk.update_inventory()
        print(json.dumps(inventory, indent=2, ensure_ascii=False))
    
    elif command == "monitor":
        print("Modo monitoramento contínuo (Ctrl+C para parar)")
        try:
            while True:
                changes = dsk.detect_changes()
                if changes:
                    print(f"[{datetime.now().isoformat()}] Alterações detectadas: {len(changes)}")
                    for change in changes:
                        print(f"  - {change['tipo']}: {change['categoria']}/{change['item_id']}")
                else:
                    print(f"[{datetime.now().isoformat()}] Nenhuma alteração")
                
                time.sleep(60)  # Verifica a cada minuto
        except KeyboardInterrupt:
            print("\nMonitoramento encerrado")
    
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()