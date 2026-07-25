"""
ProviderManager — Intelligent LLM Provider Management for OpenCode.

Single entry point for all AI provider interactions. Handles:
- Auto-discovery from environment variables
- Priority-based routing
- Intelligent failover (rate limit, auth, timeout, unavailable)
- Auto-return when primary recovers
- Model discovery per provider
- Provider status reporting
- Full event logging
"""

from .manager import ProviderManager
from .base import LLMProvider
from .models import ProviderResponse, ModelInfo, HealthStatus, ProviderStatus
from .errors import ProviderError, RateLimitError, AuthError, TimeoutError, UnavailableError

__all__ = [
    "ProviderManager",
    "LLMProvider",
    "ProviderResponse",
    "ModelInfo",
    "HealthStatus",
    "ProviderStatus",
    "ProviderError",
    "RateLimitError",
    "AuthError",
    "TimeoutError",
    "UnavailableError",
]
