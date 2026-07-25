"""Auto-discovery of providers from environment variables.

Scans for known API key environment variables and returns
only the providers that have valid configuration.
"""

import os
from typing import Dict, Type, List

from .base import LLMProvider
from .providers import PROVIDER_REGISTRY


# Map of env vars to the human-readable provider name
KNOWN_API_KEYS = {
    "NVIDIA_API_KEY": "nvidia_build",
    "OPENAI_API_KEY": "openai",
    "OPENROUTER_API_KEY": "openrouter",
    "ANTHROPIC_API_KEY": "anthropic",
    "GEMINI_API_KEY": "gemini",
}


def discover_available_providers() -> Dict[str, bool]:
    """Scan env vars and return which providers are configured.

    Returns dict mapping provider name -> available (has API key or no key required).
    """
    available = {}
    for name, provider_class in PROVIDER_REGISTRY:
        # Instantiate to check — lightweight, no network calls
        provider = provider_class()
        available[name] = provider.is_available()
    return available


def get_configured_providers() -> list:
    """Return list of provider names that have env vars set (or no key needed)."""
    result = []
    for name, provider_class in PROVIDER_REGISTRY:
        provider = provider_class()
        if provider.is_available():
            result.append(name)
    return result


def get_missing_api_keys() -> List[str]:
    """Return list of env var names that are NOT set (for diagnostics)."""
    missing = []
    for env_var in KNOWN_API_KEYS:
        if not os.environ.get(env_var):
            missing.append(env_var)
    return missing


def summary() -> str:
    """Return a human-readable summary of provider availability."""
    lines = []
    lines.append("Provedores de IA detectados:")
    lines.append("")
    for name, cls in PROVIDER_REGISTRY:
        p = cls()
        available = p.is_available()
        env = p.api_key_env
        key_status = "configurada" if (not env or os.environ.get(env)) else "ausente"
        status = "DISPONIVEL" if available else "SEM API"
        model = p.default_model
        env_info = f"({env}={key_status})" if env else "(nativo)"
        lines.append(f"  {name:20s} {status:12s} {env_info:30s} modelo: {model}")
    return "\n".join(lines)
