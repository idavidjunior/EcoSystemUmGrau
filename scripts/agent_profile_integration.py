"""agent_profile_integration.py — Integração automática do perfil do usuário nos agentes.

Este módulo deve ser importado por todos os agentes no início da execução.
Fornece aplicação automática das preferências do usuário.
"""
from scripts.profile_hook import (
    get_response_config,
    format_response_for_profile,
    record_interaction,
    apply_correction,
    get_profile_stats,
)
from scripts.user_profile import get_profile


class AgentProfileMixin:
    """Mixin para agentes que querem integração automática com o perfil do usuário.
    
    Uso:
        class MeuAgente(AgentProfileMixin):
            def responder(self, user_text):
                # 1. Pega config do perfil
                config = self.get_profile_config()
                
                # 2. Gera resposta bruta
                raw = self.gerar_resposta_bruta(user_text)
                
                # 3. Aplica preferências do perfil
                response = self.format_for_profile(raw)
                
                # 4. Registra interação para aprendizado
                self.record(user_text, response)
                
                return response
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._profile_config = None
        self._profile_loaded = False
    
    def load_profile(self):
        """Carrega configuração do perfil (chamado uma vez no init)."""
        if not self._profile_loaded:
            self._profile_config = get_response_config()
            self._profile_loaded = True
        return self._profile_config
    
    def get_profile_config(self):
        """Retorna configuração atual do perfil."""
        if not self._profile_loaded:
            self.load_profile()
        return self._profile_config
    
    def format_for_profile(self, text: str) -> str:
        """Aplica preferências do perfil ao texto."""
        from scripts.profile_hook import format_response_for_profile
        config = self.get_profile_config()
        return format_response_for_profile(text, config)
    
    def record(self, user_text: str, agent_response: str, metadata: dict = None):
        """Registra interação para aprendizado contínuo."""
        meta = metadata or {}
        meta.setdefault("agent", self.__class__.__name__)
        record_interaction(user_text, self._last_response or "", metadata)
    
    def apply_correction(self, correction_type: str, detail: str = ""):
        """Aplica correção explícita do usuário."""
        apply_correction(correction_type, detail)
        # Recarrega config após correção
        self._profile_loaded = False
        self.load_profile()
    
    def get_stats(self):
        """Retorna estatísticas do perfil."""
        return get_profile_stats()
    
    def set_response(self, response: str):
        """Armazena resposta para registro posterior."""
        self._last_response = response
        return response


def create_profile_aware_agent(base_class):
    """Factory que adiciona integração de perfil a uma classe de agente existente.
    
    Uso:
        MeuAgenteComPerfil = create_profile_aware_agent(MeuAgente)
        agente = MeuAgenteComPerfil()
    """
    class ProfileAwareAgent(AgentProfileMixin, base_class):
        def __init__(self, *args, **kwargs):
            AgentProfileMixin.__init__(self)
            base_class.__init__(self, *args, **kwargs)
    
    return ProfileAwareAgent


# === Funções de conveniência para uso direto ===

def get_config() -> dict:
    """Retorna configuração do perfil para resposta."""
    return get_response_config()


def format_response(text: str) -> str:
    """Formata texto conforme perfil do usuário."""
    return format_response_for_profile(text, get_response_config())


def log_interaction(user_text: str, agent_response: str, metadata: dict = None):
    """Registra interação para aprendizado."""
    record_interaction(user_text, agent_response, metadata)


def correct(correction_type: str, detail: str = ""):
    """Aplica correção de preferência."""
    apply_correction(correction_type, detail)


def stats() -> dict:
    """Estatísticas do perfil."""
    return get_profile_stats()


# Auto-load no import (get_profile() já carrega automaticamente)
get_profile()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "config":
            import json
            print(json.dumps(get_response_config(), ensure_ascii=False, indent=2))
        elif sys.argv[1] == "stats":
            import json
            print(json.dumps(get_profile_stats(), ensure_ascii=False, indent=2))
        elif sys.argv[1] == "correct" and len(sys.argv) > 2:
            apply_correction(sys.argv[2])
            print(f"Correção aplicada: {sys.argv[2]}")
        elif sys.argv[1] == "test":
            # Teste de formatação
            test = """### Header
**Bold** and `code`

```python
print("hello")
```

| A | B |
|---|---|
| 1 | 2 |

Link: [test](http://example.com)"""
            print("ORIGINAL:")
            print("---")
            print(test)
            print("---")
            print("FORMATADO:")
            print("---")
            print(format_response(test))
    else:
        import json
        print(json.dumps(get_response_config(), ensure_ascii=False, indent=2))