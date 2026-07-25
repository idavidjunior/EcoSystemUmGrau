"""
Anthropic Provider — Claude API.

Endpoint: https://api.anthropic.com/v1
Auth: x-api-key: sk-ant-...
"""

from typing import List, Optional
import time

from ..base import LLMProvider
from ..models import ProviderResponse, ModelInfo, CompletionRequest


class AnthropicProvider(LLMProvider):
    """Provider for Anthropic Claude API."""

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def api_key_env(self) -> str:
        return "ANTHROPIC_API_KEY"

    @property
    def default_model(self) -> str:
        return "claude-3-5-sonnet-20241022"

    @property
    def base_url(self) -> str:
        return "https://api.anthropic.com/v1"

    def complete(self, request: CompletionRequest) -> ProviderResponse:
        if not self._api_key:
            return self._build_response(
                success=False, provider=self.name,
                error="ANTHROPIC_API_KEY not configured", error_type="auth",
            )
        start = time.time()
        try:
            system_msg = None
            messages = []
            for m in request.messages:
                if m.get("role") == "system" and system_msg is None:
                    system_msg = m["content"]
                else:
                    messages.append({"role": m["role"], "content": m["content"]})

            payload = {
                "model": request.model or self.default_model,
                "messages": messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
            }
            if system_msg:
                payload["system"] = system_msg

            headers = {"x-api-key": self._api_key, "anthropic-version": "2023-06-01"}
            url = f"{self.base_url}/messages"
            data = self._http_post(url, payload, headers, timeout=60)

            elapsed = (time.time() - start) * 1000
            content = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    content += block.get("text", "")

            usage = data.get("usage", {})
            return self._build_response(
                success=True,
                provider=self.name,
                model=data.get("model", self.default_model),
                content=content,
                latency_ms=round(elapsed, 1),
                token_count_input=usage.get("input_tokens", 0),
                token_count_output=usage.get("output_tokens", 0),
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
        return [
            ModelInfo(id="claude-3-5-sonnet-20241022", provider=self.name,
                      context_window=200000, supports_vision=True, supports_tools=True,
                      cost_per_1k_input=0.003, cost_per_1k_output=0.015,
                      description="Claude 3.5 Sonnet (best balance)"),
            ModelInfo(id="claude-3-5-haiku-20241022", provider=self.name,
                      context_window=200000, supports_vision=True, supports_tools=True,
                      cost_per_1k_input=0.001, cost_per_1k_output=0.005,
                      description="Claude 3.5 Haiku (fast, cheap)"),
            ModelInfo(id="claude-opus-4-20250514", provider=self.name,
                      context_window=200000, supports_vision=True, supports_tools=True,
                      cost_per_1k_input=0.015, cost_per_1k_output=0.075,
                      description="Claude Opus 4 (most capable)"),
        ]
