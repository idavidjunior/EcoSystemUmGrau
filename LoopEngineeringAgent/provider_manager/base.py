"""Abstract base class for all LLM providers.

Every provider MUST implement:
- name, api_key_env, default_model (properties)
- is_available() -> bool
- complete(request) -> ProviderResponse
- list_models() -> List[ModelInfo]
- check_health() -> HealthStatus
"""

import json
import os
import time
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import List, Optional

from .models import ProviderResponse, ModelInfo, HealthStatus, CompletionRequest
from .errors import (
    ProviderError, RateLimitError, AuthError, TimeoutError,
    UnavailableError, BadRequestError, classify_http_error, classify_connection_error,
)


class LLMProvider(ABC):
    """Abstract base for all LLM providers."""

    def __init__(self):
        self._api_key = os.environ.get(self.api_key_env, "")
        self._last_error = None
        self._consecutive_failures = 0
        self._total_calls = 0
        self._total_errors = 0
        self._total_tokens = 0

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier (e.g., 'nvidia_build', 'openai')."""

    @property
    @abstractmethod
    def api_key_env(self) -> str:
        """Environment variable name for the API key."""

    @property
    @abstractmethod
    def default_model(self) -> str:
        """Default model identifier for this provider."""

    @property
    @abstractmethod
    def base_url(self) -> str:
        """Base API URL for completions."""

    @property
    def requires_api_key(self) -> bool:
        """Whether this provider requires an API key to function."""
        return True

    def is_available(self) -> bool:
        """Check if provider has configured API key and can be used."""
        if self.requires_api_key and not self._api_key:
            return False
        return True

    @abstractmethod
    def complete(self, request: CompletionRequest) -> ProviderResponse:
        """Send a completion request and return the response."""

    def list_models(self) -> List[ModelInfo]:
        """Return known models for this provider. Override for live discovery."""
        return []

    def check_health(self) -> HealthStatus:
        """Check if the provider is online and responsive."""
        start = time.time()
        try:
            models = self.list_models()
            elapsed = (time.time() - start) * 1000
            return HealthStatus(
                online=True,
                provider=self.name,
                latency_ms=round(elapsed, 1),
                model_count=len(models),
                last_check=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return HealthStatus(
                online=False,
                provider=self.name,
                latency_ms=round(elapsed, 1),
                error=str(e),
                last_check=time.strftime("%Y-%m-%dT%H:%M:%S"),
            )

    def stats(self) -> dict:
        """Return usage statistics for this provider."""
        return {
            "provider": self.name,
            "available": self.is_available(),
            "total_calls": self._total_calls,
            "total_errors": self._total_errors,
            "consecutive_failures": self._consecutive_failures,
            "total_tokens": self._total_tokens,
            "model": self.default_model,
            "last_error": str(self._last_error)[:200] if self._last_error else None,
        }

    def _http_post(self, url: str, payload: dict, headers: dict,
                   timeout: int = 60) -> dict:
        """Make an HTTP POST request and return parsed JSON."""
        if self._api_key and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self._api_key}"
        elif self._api_key:
            pass  # provider may set its own auth header
        headers.setdefault("Content-Type", "application/json")
        headers.setdefault("User-Agent", "ProviderManager/1.0")

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise classify_http_error(e.code, body, self.name)
        except urllib.error.URLError as e:
            raise classify_connection_error(str(e.reason), self.name)
        except Exception as e:
            raise ProviderError(str(e), "unknown", self.name)

    def _http_get(self, url: str, headers: dict = None,
                  timeout: int = 30) -> dict:
        """Make an HTTP GET request and return parsed JSON."""
        if headers is None:
            headers = {}
        if self._api_key and "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {self._api_key}"
        headers.setdefault("User-Agent", "ProviderManager/1.0")

        try:
            req = urllib.request.Request(url, headers=headers, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise classify_http_error(e.code, body, self.name)
        except urllib.error.URLError as e:
            raise classify_connection_error(str(e.reason), self.name)
        except Exception as e:
            raise ProviderError(str(e), "unknown", self.name)

    def _count_tokens(self, text: str) -> int:
        """Roughly estimate token count (4 chars per token)."""
        return len(text) // 4

    def _build_response(self, success: bool, provider: str, **kwargs) -> ProviderResponse:
        """Helper to build a ProviderResponse and update stats."""
        resp = ProviderResponse(success=success, provider=provider, **kwargs)
        self._total_calls += 1
        if not success:
            self._total_errors += 1
            self._consecutive_failures += 1
            self._last_error = resp.error
        else:
            self._consecutive_failures = 0
            self._total_tokens += resp.token_count_input + resp.token_count_output
        return resp
