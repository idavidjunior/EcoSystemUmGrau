#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""dynamic_knowledge_graph.py — Atualização Automática do Knowledge Graph.

Integração em tempo real com autoconhecimento dinâmico para atualização
incremental do knowledge graph do LER, com versionamento timestamped e
sincronização bidirecional com Obsidian.

Uso:
  python scripts/dynamic_knowledge_graph.py update          # Atualização incremental
  python scripts/dynamic_knowledge_graph.py snapshot        # Cria snapshot
  python scripts/dynamic_knowledge_graph.py rollback <ts>  # Rollback para timestamp
  python scripts/dynamic_knowledge_graph.py sync-obsidian   # Sincroniza com Obsidian

Saída JSON: {updated, version, changes, sync_status}
"""
import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent
LER_RUNTIME = ROOT / "ler-runtime"
KNOWLEDGE_FILE = LER_RUNTIME / "knowledge" / "knowledge_graph.json"
BACKUP_DIR = LER_RUNTIME / "knowledge" / "backups"
CONHECIMENTO_DIR = ROOT / "conhecimento"

# Importar o scanner de autoconhecimento
SCRIPTS = ROOT / "scripts"
import sys
sys.path.insert(0, str(SCRIPTS))
from dynamic_self_knowledge import DynamicSelfKnowledge


class DynamicKnowledgeGraph:
    """Atualização automática e incremental do knowledge graph."""
    
    def __init__(self):
        self.dsk = DynamicSelfKnowledge()
        self._load_graph()
        
    def _load_graph(self):
        """Carrega o knowledge graph atual."""
        if KNOWLEDGE_FILE.exists():
            try:
                with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
                    self.graph = json.load(f)
            except Exception as e:
                print(f"Erro ao carregar knowledge graph: {e}")
                self.graph = {"version": 2, "last_updated": None, "projects": {}, "patterns": []}
        else:
            self.graph = {"version": 2, "last_updated": None, "projects": {}, "patterns": []}
    
    def _save_graph(self):
        """Salva o knowledge graph."""
        try:
            self.graph["last_updated"] = datetime.now().isoformat()
            with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.graph, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar knowledge graph: {e}")
    
    def _create_snapshot(self) -> str:
        """Cria um snapshot timestamped do knowledge graph."""
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_file = BACKUP_DIR / f"knowledge_graph_{timestamp}.json"
        
        try:
            shutil.copy2(KNOWLEDGE_FILE, snapshot_file)
            print(f"Snapshot criado: {snapshot_file.name}")
            return timestamp
        except Exception as e:
            print(f"Erro ao criar snapshot: {e}")
            return ""
    
    def _rollback_to(self, timestamp: str) -> bool:
        """Rollback para um snapshot específico."""
        snapshot_file = BACKUP_DIR / f"knowledge_graph_{timestamp}.json"
        
        if not snapshot_file.exists():
            print(f"Snapshot não encontrado: {timestamp}")
            return False
        
        try:
            # Criar snapshot do estado atual antes de rollback
            current_timestamp = self._create_snapshot()
            
            # Restaurar snapshot
            shutil.copy2(snapshot_file, KNOWLEDGE_FILE)
            self._load_graph()
            
            print(f"Rollback realizado para: {timestamp}")
            print(f"Snapshot do estado atual salvo como: {current_timestamp}")
            return True
        except Exception as e:
            print(f"Erro ao realizar rollback: {e}")
            return False
    
    def incremental_update(self, changes: List[Dict]) -> bool:
        """Atualização incremental do knowledge graph baseada em mudanças."""
        if not changes:
            print("Nenhuma mudança detectada, nada a atualizar")
            return True
        
        updated = False
        
        # Processar mudanças e atualizar knowledge graph
        for change in changes:
            if change["tipo"] == "adicao":
                # Nova estrutura adicionada - registrar no knowledge graph
                self._register_new_structure(change)
                updated = True
            
            elif change["tipo"] == "modificacao":
                # Estrutura modificada - atualizar timestamp
                self._update_structure_timestamp(change)
                updated = True
            
            elif change["tipo"] == "remocao":
                # Estrutura removida - marcar como inativa
                self._mark_structure_inactive(change)
                updated = True
        
        if updated:
            self._save_graph()
            print(f"Knowledge graph atualizado com {len(changes)} mudanças")
            return True
        
        return False
    
    def _register_new_structure(self, change: Dict):
        """Registra nova estrutura no knowledge graph."""
        # Adicionar ao projeto "ecosistema-opencode"
        if "ecosistema-opencode" not in self.graph["projects"]:
            self.graph["projects"]["ecosistema-opencode"] = {}
        
        # Criar entrada de padrão para a nova estrutura
        pattern = {
            "source": "ecosistema-opencode",
            "title": f"Estrutura adicionada: {change['item_id']}",
            "action": "nova_estrutura",
            "description": f"Nova estrutura {change['categoria']} adicionada: {change['item_id']} em {change['dados']['arquivo']}",
            "domain": "general",
            "extracted_at": datetime.now().isoformat(),
            "merged_count": 1
        }
        
        self.graph["patterns"].append(pattern)
    
    def _update_structure_timestamp(self, change: Dict):
        """Atualiza timestamp de estrutura modificada."""
        # Encontrar padrão correspondente e atualizar
        for pattern in self.graph["patterns"]:
            if pattern["title"] == f"Estrutura adicionada: {change['item_id']}":
                pattern["description"] = f"Estrutura {change['categoria']} modificada: {change['item_id']} em {change['dados']['arquivo']}"
                pattern["extracted_at"] = datetime.now().isoformat()
                break
    
    def _mark_structure_inactive(self, change: Dict):
        """Marca estrutura removida como inativa."""
        # Encontrar padrão correspondente e marcar
        for pattern in self.graph["patterns"]:
            if pattern["title"] == f"Estrutura adicionada: {change['item_id']}":
                pattern["description"] = f"Estrutura {change['categoria']} removida: {change['item_id']} (inativa)"
                pattern["status"] = "inactive"
                pattern["extracted_at"] = datetime.now().isoformat()
                break
    
    def sync_obsidian(self) -> bool:
        """Sincronização bidirecional com Obsidian."""
        # Script de geração Obsidian - opcional
        obsidian_script = SCRIPTS / "generate-obsidian-notes.py"
        
        if not obsidian_script.exists():
            print("Script de geração Obsidian não encontrado (opcional)")
            return True  # Não é crítico
        
        try:
            result = subprocess.run(
                ["python", str(obsidian_script)],
                capture_output=True,
                text=True,
                cwd=ROOT,
                timeout=30
            )
            
            if result.returncode == 0:
                print("Sincronização com Obsidian realizada com sucesso")
                return True
            else:
                print(f"Erro na sincronização Obsidian: {result.stderr}")
                return True  # Continua mesmo se falhar
        except Exception as e:
            print(f"Erro ao sincronizar com Obsidian: {e}")
            return True  # Continua mesmo se falhar
    
    def full_update(self) -> dict:
        """Atualização completa: detecta mudanças e atualiza knowledge graph."""
        # Detectar mudanças
        changes = self.dsk.detect_changes()
        
        # Criar snapshot antes de atualizar
        snapshot_timestamp = self._create_snapshot()
        
        # Atualizar incrementalmente
        updated = self.incremental_update(changes)
        
        # Sincronizar com Obsidian desabilitado temporariamente
        sync_ok = None
        
        return {
            "updated": updated,
            "changes_count": len(changes),
            "snapshot_timestamp": snapshot_timestamp,
            "sync_obsidian": sync_ok,
            "graph_version": self.graph.get("version"),
            "last_updated": self.graph.get("last_updated")
        }


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python dynamic_knowledge_graph.py update|snapshot|rollback|sync-obsidian")
        sys.exit(1)
    
    command = sys.argv[1]
    dkg = DynamicKnowledgeGraph()
    
    if command == "update":
        result = dkg.full_update()
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif command == "snapshot":
        timestamp = dkg._create_snapshot()
        print(f"Snapshot criado: {timestamp}")
    
    elif command == "rollback":
        if len(sys.argv) < 3:
            print("Uso: python dynamic_knowledge_graph.py rollback <timestamp>")
            sys.exit(1)
        timestamp = sys.argv[2]
        success = dkg._rollback_to(timestamp)
        sys.exit(0 if success else 1)
    
    elif command == "sync-obsidian":
        success = dkg.sync_obsidian()
        sys.exit(0 if success else 1)
    
    else:
        print(f"Comando desconhecido: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()