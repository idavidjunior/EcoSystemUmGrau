"""agent_bootstrap.py — Bootstrap obrigatório para todos os agentes.

DEVE ser executado no início de TODA execução de agente.
Carrega perfil do usuário, restaura contexto, aplica preferências.
"""
from scripts.runtime_state import load as load_state, get_state as get_state
from scripts.runtime_context import load as load_context, get_context
from scripts.runtime_auditor import RuntimeAuditor
from scripts.agent_profile_integration import (
    load_profile,
    get_response_config,
    format_response_for_profile,
    record_interaction,
    apply_correction,
    get_profile_stats,
)


def bootstrap_agent(agent_name: str) -> dict:
    """Bootstrap completo para agente.
    
    Returns:
        Dict com config do perfil e estado do runtime.
    """
    # 1. Boot do runtime (restaura estado, memória, regras)
    load_state()
    load_context()
    RuntimeAuditor()
    
    # 2. Carrega perfil do usuário
    load_profile()
    
    # 3. Config do perfil para respostas
    profile_config = get_response_config()
    
    return {
        "agent": agent_name,
        "runtime_state": get_state(),
        "profile_config": profile_config,
        "profile_stats": get_profile_stats(),
    }


def format_response(text: str, config: dict = None) -> str:
    """Aplica preferências do perfil ao texto da resposta."""
    from scripts.profile_hook import format_response_for_profile
    if config is None:
        config = get_response_config()
    return format_response_for_profile(text, config)


def log_interaction(user_text: str, agent_response: str, metadata: dict = None):
    """Registra interação para aprendizado contínuo."""
    from scripts.profile_hook import record_interaction
    record_interaction(user_text, agent_response, metadata)


def apply_user_correction(correction_type: str, detail: str = ""):
    """Aplica correção explícita do usuário."""
    apply_correction(correction_type, detail)


def get_agent_config() -> dict:
    """Configuração completa para agente usar nas respostas."""
    return get_response_config()


# Auto-execução no import
bootstrap_result = bootstrap_agent("unknown")


if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "bootstrap":
            result = bootstrap_agent(sys.argv[2] if len(sys.argv) > 2 else "cli")
            print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
        elif sys.argv[1] == "config":
            print(json.dumps(get_response_config(), ensure_ascii=False, indent=2))
        elif sys.argv[1] == "test":
            test = """### Header
**Bold** and `code`

```python
print("hello")
```

| A | B |
|---|---|
| 1 | 2 |

Link: [test](http://example.com)"""
            print("FORMATADO:")
            print(format_response(test))
    else:
        print(json.dumps(bootstrap_result, ensure_ascii=False, indent=2, default=str))