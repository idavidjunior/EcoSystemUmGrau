"""Provider implementations registry."""

from .opencode_go import OpenCodeGoProvider
from .nvidia_build import NVIDIAProvider
from .openai_provider import OpenAIProvider
from .openrouter import OpenRouterProvider
from .anthropic import AnthropicProvider
from .gemini import GeminiProvider

# Registry: maps provider names to their classes
# Order matches default priority
PROVIDER_REGISTRY = [
    ("opencode_go", OpenCodeGoProvider),
    ("nvidia_build", NVIDIAProvider),
    ("openrouter", OpenRouterProvider),
    ("openai", OpenAIProvider),
    ("anthropic", AnthropicProvider),
    ("gemini", GeminiProvider),
]

__all__ = [
    "PROVIDER_REGISTRY",
    "OpenCodeGoProvider",
    "NVIDIAProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "AnthropicProvider",
    "GeminiProvider",
]
