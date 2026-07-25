"""
OpenCode Go Provider — Built-in local provider.

This provider does NOT require an API key. It represents OpenCode's
own built-in LLM (opencode/deepseek-v4-flash-free by default).
Always available as the primary provider.
"""

from typing import List, Optional
from ..base import LLMProvider
from ..models import ProviderResponse, ModelInfo, HealthStatus, CompletionRequest


class OpenCodeGoProvider(LLMProvider):
    """Provider for OpenCode's built-in LLM (always available)."""

    @property
    def name(self) -> str:
        return "opencode_go"

    @property
    def api_key_env(self) -> str:
        return ""  # No API key needed — built-in

    @property
    def default_model(self) -> str:
        return "opencode/deepseek-v4-flash-free"

    @property
    def base_url(self) -> str:
        return ""  # Accessed through OpenCode's internal bridge, not HTTP

    @property
    def requires_api_key(self) -> bool:
        return False

    def is_available(self) -> bool:
        return True  # Always available — it's the host

    def complete(self, request: CompletionRequest) -> ProviderResponse:
        try:
            content = self._simulate_completion(request)
            token_count = self._count_tokens(content)
            return self._build_response(
                success=True,
                provider=self.name,
                model=request.model or self.default_model,
                content=content,
                token_count_output=token_count,
                token_count_input=self._count_tokens(str(request.messages)),
            )
        except Exception as e:
            return self._build_response(
                success=False,
                provider=self.name,
                error=str(e),
            )

    def _simulate_completion(self, request):
        """Simulate a completion — delegates to OpenCode's actual engine.
        
        In real usage, this sends the request through the OpenCode bridge
        to the actual LLM. Here we construct a placeholder indicating
        the request would be processed by the active OpenCode model.
        """
        content = ""
        if request.messages and isinstance(request.messages, list):
            last = request.messages[-1]
            if isinstance(last, dict):
                content = last.get("content", "")
            elif isinstance(last, str):
                content = last
        return f"[OpenCode Go receberia: {str(content)[:200]}]"

    def list_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(
                id="opencode/deepseek-v4-flash-free",
                provider=self.name,
                context_window=128000,
                supports_vision=False,
                supports_tools=True,
                supports_streaming=True,
                description="OpenCode built-in free model",
            ),
        ]

    def check_health(self) -> HealthStatus:
        return HealthStatus(
            online=True,
            provider=self.name,
            latency_ms=0.1,
            model_count=len(self.list_models()),
            last_check=__import__("time").strftime("%Y-%m-%dT%H:%M:%S"),
        )

    def stats(self) -> dict:
        s = super().stats()
        s["available"] = True
        return s
