"""migrate_solutions.py — Migra memórias de erro existentes, vinculando soluções.

Lê as memórias de erro e, baseado no summary (que já descreve a solução),
cria o campo solucao_aplicada para erros que claramente foram resolvidos.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from memory_engine import _load_memories, _save_memories

def migrate():
    memories = _load_memories()
    migrated = 0
    
    for m in memories:
        if m.get('kind') != 'erro':
            continue
        if m.get('solucao_aplicada'):
            continue
            
        summary = m.get('summary', '')
        task = m.get('task', '')
        
        # Padrões que indicam solução aplicada
        solution_patterns = [
            'corrigido', 'corrigir', 'fix', 'solução', 'resolvido',
            'substituir', 'usar', 'mudar', 'ajustar', 'implementar',
            'adicionar', 'remover', 'criar', 'configurar', 'ajuste'
        ]
        
        has_solution = any(p in summary.lower() for p in solution_patterns)
        
        if has_solution:
            m['solucao_aplicada'] = {
                'desc': summary[:500],
                'script': None,
                'data': m.get('created_at', ''),
                'validado': False,
                'tags': m.get('tags', [])
            }
            migrated += 1
    
    if migrated > 0:
        _save_memories(memories)
        print(f"[MIGRATE] {migrated} memórias de erro migradas com soluções")
    else:
        print("[MIGRATE] Nenhuma memória para migrar")
    
    return migrated

if __name__ == "__main__":
    migrate()
