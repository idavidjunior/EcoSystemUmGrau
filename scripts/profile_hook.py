"""profile_hook.py — Hook para aplicar perfil do usuário automaticamente nas respostas.

Uso: import profile_hook; profile_hook.apply_preferences(response_config)
"""
from user_profile import get_profile


def get_response_config() -> dict:
    """Retorna configuração de resposta baseada no perfil aprendido."""
    return get_profile().get_response_config()


def record_interaction(user_text: str, agent_response: str, metadata: dict = None):
    """Registra interação para aprendizado contínuo."""
    get_profile().record_interaction(user_text, agent_response, metadata)


def apply_correction(correction_type: str, detail: str = ""):
    """Aplica correção explícita do usuário."""
    get_profile().apply_correction(correction_type, detail)


def get_profile_stats() -> dict:
    return get_profile().get_stats()


def format_response_for_profile(text: str, config: dict = None) -> str:
    """Aplica preferências de formatação ao texto da resposta."""
    if config is None:
        config = get_response_config()

    # Remove markdown se profile não quer
    if not config.get("use_markdown", False):
        import re
        # Remove headers
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        # Remove bold/italic
        text = re.sub(r'(\*\*|__)', '', text)
        # Remove code blocks
        text = re.sub(r'```[\s\S]*?```', '', text, flags=re.DOTALL)
        # Remove inline code
        text = re.sub(r'`([^`]+)`', r'\1', text)
        # Remove links
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        # Remove horizontal rules
        text = re.sub(r'^[-*_]{3,}\s*$', '', text, flags=re.MULTILINE)

    # Remove tables se não quer
    if not config.get("use_tables", False):
        import re
        text = re.sub(r'\|.*\|', '', text)
        text = re.sub(r'^[-|\s]+\|', '', text, flags=re.MULTILINE)

    # Normaliza espaços
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    return text.strip()


if __name__ == "__main__":
    import sys
    p = __import__("scripts.user_profile", fromlist=["get_profile"]).get_profile()
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(__import__("json").dumps(p.get_stats(), ensure_ascii=False, indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "config":
        print(__import__("json").dumps(get_response_config(), ensure_ascii=False, indent=2))