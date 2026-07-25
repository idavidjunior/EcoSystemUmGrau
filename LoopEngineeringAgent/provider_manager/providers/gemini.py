"""
Google Gemini Provider — Gemini API.

Endpoint: https://generativelanguage.googleapis.com/v1beta
Auth: x-goog-api-key: ...
"""

from typing import List, Optional
import time
import json

from ..base import LLMProvider
from ..models import ProviderResponse, ModelInfo, CompletionRequest


class GeminiProvider(LLMProvider):
    """Provider for Google Gemini API."""

    @property
    def name(self) -> str:
        return "gemini"

    @property
    def api_key_env(self) -> str:
        return "GEMINI_API_KEY"

    @property
    def default_model(self) -> str:
        return "gemini-2.0-flash-001"

    @property
    def base_url(self) -> str:
        return "https://generativelanguage.googleapis.com/v1beta"

    def complete(self, request: CompletionRequest) -> ProviderResponse:
        if not self._api_key:
            return self._build_response(
                success=False, provider=self.name,
                error="GEMINI_API_KEY not configured", error_type="auth",
            )
        start = time.time()
        try:
            gemini_contents = self._convert_messages(request.messages)

            payload = {
                "contents": gemini_contents,
                "generationConfig": {
                    "temperature": request.temperature,
                    "maxOutputTokens": request.max_tokens,
                },
            }

            model = request.model or self.default_model
            url = f"{self.base_url}/models/{model}:generateContent?key={self._api_key}"

            data = self._http_post(url, payload, {}, timeout=60)

            elapsed = (time.time() - start) * 1000
            content = ""
            candidates = data.get("candidates", [])
            if candidates:
                for part in candidates[0].get("content", {}).get("parts", []):
                    if "text" in part:
                        content += part["text"]

            usage = data.get("usageMetadata", {})
            return self._build_response(
                success=True,
                provider=self.name,
                model=model,
                content=content,
                latency_ms=round(elapsed, 1),
                token_count_input=usage.get("promptTokenCount", 0),
                token_count_output=usage.get("candidatesTokenCount", 0),
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

    def _convert_messages(self, messages):
        """Convert OpenAI-format messages to Gemini format."""
        contents = []
        system_instruction = None

        for msg in messages:
            role = msg.get("role", "")
            if role == "system":
                system_instruction = {"parts": [{"text": msg.get("content", "")}]}
                continue

            gemini_role = "model" if role in ("assistant", "model") else "user"
            contents.append({
                "role": gemini_role,
                "parts": [{"text": msg.get("content", "")}],
            })

        return contents

    def list_models(self) -> List[ModelInfo]:
        return [
            ModelInfo(id="gemini-2.0-flash-001", provider=self.name,
                      context_window=1048576, supports_vision=True, supports_tools=True,
                      cost_per_1k_input=0.0001, cost_per_1k_output=0.0004,
                      description="Gemini 2.0 Flash (fast, 1M context)"),
            ModelInfo(id="gemini-2.0-flash-lite-001", provider=self.name,
                      context_window=1048576, supports_vision=True, supports_tools=False,
                      cost_per_1k_input=0.000075, cost_per_1k_output=0.0003,
                      description="Gemini 2.0 Flash Lite (cheapest)"),
            ModelInfo(id="gemini-2.5-pro-exp-03-25", provider=self.name,
                      context_window=1048576, supports_vision=True, supports_tools=True,
                      cost_per_1k_input=0.005, cost_per_1k_output=0.05,
                      description="Gemini 2.5 Pro (most capable)"),
        ]
