"""
OpenRouter Provider — Multi-model gateway (OpenAI-compatible).

Endpoint: https://openrouter.ai/api/v1
Auth: Authorization: Bearer sk-or-v1-...
"""

from typing import List, Optional
import time

from ..base import LLMProvider
from ..models import ProviderResponse, ModelInfo, CompletionRequest


class OpenRouterProvider(LLMProvider):
    """Provider for OpenRouter API (OpenAI-compatible)."""

    @property
    def name(self) -> str:
        return "openrouter"

    @property
    def api_key_env(self) -> str:
        return "OPENROUTER_API_KEY"

    @property
    def default_model(self) -> str:
        return "openrouter/auto"

    @property
    def base_url(self) -> str:
        return "https://openrouter.ai/api/v1"

    def complete(self, request: CompletionRequest) -> ProviderResponse:
        if not self._api_key:
            return self._build_response(
                success=False, provider=self.name,
                error="OPENROUTER_API_KEY not configured", error_type="auth",
            )
        start = time.time()
        try:
            payload = {
                "model": request.model or self.default_model,
                "messages": request.messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }
            if request.tools:
                payload["tools"] = request.tools

            headers = {
                "Authorization": f"Bearer {self._api_key}",
                "HTTP-Referer": "https://opencode.ai",
                "X-Title": "OpenCode",
            }
            url = f"{self.base_url}/chat/completions"
            data = self._http_post(url, payload, headers, timeout=60)

            elapsed = (time.time() - start) * 1000
            choice = data.get("choices", [{}])[0]
            content = choice.get("message", {}).get("content", "")
            usage = data.get("usage", {})

            return self._build_response(
                success=True,
                provider=self.name,
                model=data.get("model", self.default_model),
                content=content,
                latency_ms=round(elapsed, 1),
                token_count_input=usage.get("prompt_tokens", 0),
                token_count_output=usage.get("completion_tokens", 0),
                raw=data,
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            err_type = getattr(e, "error_type", "unknown")
            return self._build_response(
                success=False, provider=self.name,
                error=str(e), error_type=err_type,
                latency_ms=round(elapsed, 1),
            )

    def list_models(self) -> List[ModelInfo]:
        try:
            url = f"{self.base_url}/models"
            data = self._http_get(url, timeout=15)
            models = []
            for m in data.get("data", []):
                mid = m.get("id", "")
                if not mid:
                    continue
                context = m.get("context_length", 0) or m.get("max_context", 0) or 8192
                models.append(ModelInfo(
                    id=mid,
                    provider=self.name,
                    context_window=context,
                    supports_vision="vision" in str(m.get("description", "")).lower() or
                                    any(v in mid.lower() for v in ("vision", "vl")),
                    supports_tools=True,
                    cost_per_1k_input=m.get("pricing", {}).get("prompt"),
                    cost_per_1k_output=m.get("pricing", {}).get("completion"),
                    description=m.get("description", ""),
                ))
            return models if models else self._default_models()
        except Exception:
            return self._default_models()

    def _default_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(id="openrouter/auto", provider=self.name,
                      context_window=128000, supports_tools=True,
                      description="OpenRouter auto-routing"),
            ModelInfo(id="anthropic/claude-3.5-sonnet", provider=self.name,
                      context_window=200000, supports_vision=True, supports_tools=True,
                      description="Claude 3.5 Sonnet via OpenRouter"),
            ModelInfo(id="google/gemini-2.0-flash-001", provider=self.name,
                      context_window=1048576, supports_vision=True, supports_tools=True,
                      description="Gemini 2.0 Flash via OpenRouter"),
        ]
