"""agent_bootstrap.py — Bootstrap obrigatório para todos os agentes.

DEVE ser executado no início de TODA execução de agente.
Carrega perfil do usuário, restaura contexto, aplica preferências.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from runtime_state import load_state
from runtime_context import carregar_contexto
from runtime_auditor import auditar as runtime_auditar


def bootstrap_agent(agent_name: str) -> dict:
    """Bootstrap completo para agente.
    
    Returns:
        Dict com estado do runtime.
    """
    # 1. Boot do runtime (restaura estado, memória, regras)
    load_state()
    carregar_contexto("bootstrap", limite=0)
    runtime_auditar("bootstrap", "")
    
    # 2. Saudação espontânea na primeira mensagem da sessão
    try:
        from runtime_state import generate_spontaneous_greeting, mark_session_greeted
        state = load_state()
        greeting = generate_spontaneous_greeting(state)
        if greeting:
            mark_session_greeted()
    except Exception:
        pass  # Silencioso se falhar
    
    return {
        "agent": agent_name,
        "runtime_state": load_state(),
    }


# Auto-execução no import
bootstrap_result = bootstrap_agent("unknown")


if __name__ == "__main__":
    import json
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "bootstrap":
            result = bootstrap_agent(sys.argv[2] if len(sys.argv) > 2 else "cli")
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        else:
            print(json.dumps(bootstrap_result, ensure_ascii=False, indent=2, default=str))
    else:
        print(json.dumps(bootstrap_result, ensure_ascii=False, indent=2, default=str))