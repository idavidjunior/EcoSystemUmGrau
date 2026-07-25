"""
NVIDIA Build Provider — NVIDIA Inference API (OpenAI-compatible).

Endpoint: https://integrate.api.nvidia.com/v1
Auth: Authorization: Bearer nvapi-...
"""

from typing import List, Optional
import time

from ..base import LLMProvider
from ..models import ProviderResponse, ModelInfo, HealthStatus, CompletionRequest


class NVIDIAProvider(LLMProvider):
    """Provider for NVIDIA Build API (OpenAI-compatible)."""

    @property
    def name(self) -> str:
        return "nvidia_build"

    @property
    def api_key_env(self) -> str:
        return "NVIDIA_API_KEY"

    @property
    def default_model(self) -> str:
        return "nvidia/llama-3.1-nemotron-70b-instruct"

    @property
    def base_url(self) -> str:
        return "https://integrate.api.nvidia.com/v1"

    def complete(self, request: CompletionRequest) -> ProviderResponse:
        if not self._api_key:
            return self._build_response(
                success=False, provider=self.name,
                error="NVIDIA_API_KEY not configured", error_type="auth",
            )
        start = time.time()
        try:
            payload = {
                "model": request.model or self.default_model,
                "messages": request.messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "stream": False,
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
                if not mid:
                    continue
                models.append(ModelInfo(
                    id=mid,
                    provider=self.name,
                    context_window=128000,
                    supports_vision="vision" in mid.lower() or "vlm" in mid.lower(),
                    supports_tools=True,
                    description=m.get("description", ""),
                ))
            return models if models else self._default_models()
        except Exception:
            return self._default_models()

    def _default_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(id="nvidia/llama-3.1-nemotron-70b-instruct",
                      provider=self.name, context_window=128000, supports_tools=True,
                      description="NVIDIA Nemotron 70B Instruct"),
            ModelInfo(id="nvidia/llama-3.1-nemotron-8b-instruct",
                      provider=self.name, context_window=128000, supports_tools=True,
                      description="NVIDIA Nemotron 8B Instruct"),
            ModelInfo(id="mistralai/mixtral-8x22b-instruct",
                      provider=self.name, context_window=65536, supports_tools=True,
                      description="Mixtral 8x22B"),
        ]
