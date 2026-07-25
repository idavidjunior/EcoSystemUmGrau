"""
OpenAI Provider — OpenAI API.

Endpoint: https://api.openai.com/v1
Auth: Authorization: Bearer sk-...
"""

from typing import List, Optional
import time

from ..base import LLMProvider
from ..models import ProviderResponse, ModelInfo, CompletionRequest


class OpenAIProvider(LLMProvider):
    """Provider for the OpenAI API."""

    @property
    def name(self) -> str:
        return "openai"

    @property
    def api_key_env(self) -> str:
        return "OPENAI_API_KEY"

    @property
    def default_model(self) -> str:
        return "gpt-4o"

    @property
    def base_url(self) -> str:
        return "https://api.openai.com/v1"

    def complete(self, request: CompletionRequest) -> ProviderResponse:
        if not self._api_key:
            return self._build_response(
                success=False, provider=self.name,
                error="OPENAI_API_KEY not configured", error_type="auth",
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

            url = f"{self.base_url}/chat/completions"
            data = self._http_post(url, payload, {}, timeout=60)

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
                if not mid or not any(k in mid for k in ("gpt-4", "gpt-3.5")):
                    continue
                models.append(ModelInfo(
                    id=mid,
                    provider=self.name,
                    context_window=128000 if "gpt-4" in mid else 16385,
                    supports_vision="vision" in mid.lower() or "gpt-4o" in mid.lower(),
                    supports_tools=True,
                    description=m.get("description", ""),
                ))
            return models if models else self._default_models()
        except Exception:
            return self._default_models()

    def _default_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(id="gpt-4o", provider=self.name,
                      context_window=128000, supports_vision=True, supports_tools=True,
                      cost_per_1k_input=0.01, cost_per_1k_output=0.03,
                      description="GPT-4o multimodal"),
            ModelInfo(id="gpt-4o-mini", provider=self.name,
                      context_window=128000, supports_vision=True, supports_tools=True,
                      cost_per_1k_input=0.0015, cost_per_1k_output=0.006,
                      description="GPT-4o Mini (fast, cheap)"),
            ModelInfo(id="gpt-4-turbo", provider=self.name,
                      context_window=128000, supports_vision=True, supports_tools=True,
                      description="GPT-4 Turbo"),
        ]
