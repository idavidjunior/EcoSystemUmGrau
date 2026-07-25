"""
ProviderManager — Single entry point for all LLM provider interactions.

Features:
- Auto-discovery from env vars
- Priority-based routing (default: OpenCode Go > NVIDIA > OpenRouter > ...)
- Intelligent failover with error classification
- Auto-return when primary recovers (background health checks)
- Model discovery per provider
- Full event logging
- /provider-status generation

Usage:
    pm = ProviderManager()
    pm.initialize()
    result = pm.complete(CompletionRequest(messages=[...]))
"""

import os
import time
import json
import threading
from typing import Dict, List, Optional, Callable

from .base import LLMProvider
from .models import ProviderResponse, ModelInfo, HealthStatus, CompletionRequest
from .errors import ProviderError
from .providers import PROVIDER_REGISTRY
from .discovery import discover_available_providers, get_configured_providers
from .logger import ProviderLogger


# Default priority order — must match PROVIDER_REGISTRY names
DEFAULT_PRIORITY = [
    "opencode_go",
    "nvidia_build",
    "openrouter",
    "openai",
    "anthropic",
    "gemini",
]

# Error types that CAN trigger failover
FAILOVER_ERROR_TYPES = {"rate_limit", "timeout", "unavailable", "auth"}

# Interval in seconds to test if primary provider has recovered
AUTO_RETURN_INTERVAL = 120  # 2 minutes


class ProviderManager:
    """Central provider manager — the ONLY gateway to LLM providers."""

    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = config_dir
        self._providers: Dict[str, LLMProvider] = {}
        self._priority: List[str] = list(DEFAULT_PRIORITY)
        self._active_provider: Optional[str] = None
        self._fallback_provider: Optional[str] = None
        self._primary_provider: str = DEFAULT_PRIORITY[0]
        self._initialized = False
        self._lock = threading.Lock()

        # Logger
        log_dir = None
        if config_dir:
            log_dir = os.path.join(config_dir, "..", "memory")
        self.logger = ProviderLogger(log_dir)

        # Auto-return thread
        self._auto_return_thread: Optional[threading.Thread] = None
        self._auto_return_running = False
        self._health_check_interval = AUTO_RETURN_INTERVAL

    # ─── Initialization ──────────────────────────────────────────────

    def initialize(self, priority: Optional[List[str]] = None):
        """Initialize all providers and detect available ones.

        Args:
            priority: Optional custom priority list. If None, uses DEFAULT_PRIORITY.
        """
        with self._lock:
            if priority:
                self._priority = priority

            # Instantiate all providers from registry
            for name, provider_class in PROVIDER_REGISTRY:
                try:
                    self._providers[name] = provider_class()
                except Exception as e:
                    self.logger.log("error", provider=name,
                                    details=f"Failed to instantiate: {e}")

            # Discover which are available
            available = discover_available_providers()

            # Set active provider to highest-priority available one
            for name in self._priority:
                if name in self._providers and self._providers[name].is_available():
                    self._active_provider = name
                    self.logger.log("switch", from_provider="none", to_provider=name,
                                    reason="Initialization")
                    break
                elif name in self._providers:
                    env = self._providers[name].api_key_env
                    self.logger.log("error", provider=name,
                                    details=f"{env} not configured")

            # Set fallback as next available provider after active
            self._update_fallback()

            self._initialized = True

            # Start auto-return health checker in background
            self._start_auto_return()

    def _update_fallback(self):
        """Update the fallback provider (next available after active)."""
        found_active = False
        self._fallback_provider = None
        for name in self._priority:
            if name == self._active_provider:
                found_active = True
                continue
            if found_active and name in self._providers:
                if self._providers[name].is_available():
                    self._fallback_provider = name
                    break

    # ─── Core: Complete ──────────────────────────────────────────────

    def complete(self, request: CompletionRequest) -> ProviderResponse:
        """Send a completion request through the best available provider.

        Automatically handles failover to fallback providers on errors
        that permit it (rate_limit, timeout, unavailable, auth).
        """
        if not self._initialized:
            self.initialize()

        with self._lock:
            provider_name = self._active_provider or self._get_first_available()

        if not provider_name:
            return ProviderResponse(
                success=False, provider="", error="Nenhum provedor disponivel",
                error_type="unavailable",
            )

        # Try providers in order of priority, starting from the active one
        active_idx = self._get_priority_index(provider_name)
        errors = []

        for i in range(active_idx, len(self._priority)):
            name = self._priority[i]
            provider = self._providers.get(name)
            if not provider or not provider.is_available():
                continue

            start = time.time()
            try:
                response = provider.complete(request)
                elapsed = (time.time() - start) * 1000

                if response.success:
                    # Log success — if this isn't the normal active provider, log the switch
                    if name != self._active_provider:
                        old_active = self._active_provider
                        self.logger.log("switch", from_provider=old_active or "?",
                                        to_provider=name,
                                        reason=f"Failover from {old_active}",
                                        duration_ms=round(elapsed, 1))
                        self._active_provider = name
                        self._update_fallback()

                    return response
                else:
                    errors.append({"provider": name, "error": response.error,
                                   "error_type": response.error_type})
                    self.logger.log("error", provider=name,
                                    reason=response.error_type,
                                    details=response.error or "",
                                    success=False)

                    # Check if this error should trigger failover
                    if response.error_type not in FAILOVER_ERROR_TYPES:
                        # Non-failover error (e.g., bad_request) — stop trying
                        self.logger.log("error", provider=name,
                                        reason="non_failover_error",
                                        details=f"Error type {response.error_type} blocks failover")
                        break

                    self.logger.log("failover", from_provider=name,
                                    to_provider=self._get_next_available(i),
                                    reason=response.error_type,
                                    details=response.error or "")

            except Exception as e:
                elapsed = (time.time() - start) * 1000
                err_type = getattr(e, "error_type", "unknown")
                errors.append({"provider": name, "error": str(e), "error_type": err_type})
                self.logger.log("error", provider=name,
                                reason=err_type, details=str(e)[:200],
                                duration_ms=round(elapsed, 1), success=False)

                if err_type not in FAILOVER_ERROR_TYPES:
                    break

                self.logger.log("failover", from_provider=name,
                                to_provider=self._get_next_available(i),
                                reason=err_type, duration_ms=round(elapsed, 1))

        # All providers failed
        return ProviderResponse(
            success=False, provider="", error=f"All providers failed: {errors}",
            error_type="unavailable",
        )

    # ─── Health Checks & Auto-Return ────────────────────────────────

    def check_provider_health(self, name: str) -> HealthStatus:
        """Run a health check against a specific provider."""
        provider = self._providers.get(name)
        if not provider:
            return HealthStatus(online=False, provider=name,
                                error="Unknown provider")
        return provider.check_health()

    def check_all_health(self) -> Dict[str, HealthStatus]:
        """Run health checks against all available providers."""
        results = {}
        for name, provider in self._providers.items():
            if provider.is_available():
                results[name] = provider.check_health()
        return results

    def _start_auto_return(self):
        """Start background thread that periodically tests the primary provider."""
        if self._auto_return_running:
            return
        self._auto_return_running = True
        self._auto_return_thread = threading.Thread(
            target=self._auto_return_loop, daemon=True
        )
        self._auto_return_thread.start()

    def _auto_return_loop(self):
        """Background loop: every N seconds, test primary provider.

        If primary is back online and we're on a fallback, switch back.
        """
        while self._auto_return_running:
            time.sleep(self._health_check_interval)
            try:
                with self._lock:
                    if self._active_provider == self._primary_provider:
                        continue  # Already on primary

                    primary = self._providers.get(self._primary_provider)
                    if not primary or not primary.is_available():
                        continue

                    # Test the primary provider with a lightweight health check
                    health = primary.check_health()
                    if health.online:
                        # Primary is back — switch to it
                        old_active = self._active_provider
                        self._active_provider = self._primary_provider
                        self._update_fallback()
                        self.logger.log("return", from_provider=old_active or "?",
                                        to_provider=self._primary_provider,
                                        reason="Auto-return: primary recovered",
                                        duration_ms=health.latency_ms)
            except Exception:
                pass  # Silently retry next cycle

    # ─── Model Discovery ─────────────────────────────────────────────

    def get_models(self, provider_name: Optional[str] = None) -> Dict[str, List[ModelInfo]]:
        """Get available models from all providers or a specific one."""
        if provider_name:
            provider = self._providers.get(provider_name)
            if not provider:
                return {}
            return {provider_name: provider.list_models()}

        result = {}
        for name, provider in self._providers.items():
            if provider.is_available():
                try:
                    result[name] = provider.list_models()
                except Exception:
                    result[name] = []
        return result

    def get_best_model(self, task_type: str = "chat") -> str:
        """Select the best model for a given task type.

        Args:
            task_type: 'chat', 'vision', 'tools', 'code'

        Returns:
            Model ID string (e.g., 'gpt-4o')
        """
        active = self._providers.get(self._active_provider or "")
        if not active:
            return ""
        return active.default_model

    # ─── Status ─────────────────────────────────────────────────────

    def get_active_provider_name(self) -> Optional[str]:
        return self._active_provider

    def get_fallback_provider_name(self) -> Optional[str]:
        return self._fallback_provider

    def get_all_providers(self) -> Dict[str, LLMProvider]:
        return dict(self._providers)

    def get_priority_order(self) -> List[str]:
        return list(self._priority)

    @property
    def default_priority(self) -> List[str]:
        return list(DEFAULT_PRIORITY)

    def set_priority(self, priority: List[str]):
        """Update provider priority order at runtime."""
        with self._lock:
            # Only include known providers
            self._priority = [p for p in priority if p in self._providers]
            # Append any registered providers not in the custom list
            for name in DEFAULT_PRIORITY:
                if name in self._providers and name not in self._priority:
                    self._priority.append(name)
            self._update_fallback()
            self.logger.log("config", provider="system",
                            details=f"Priority updated: {self._priority}")

    def set_primary(self, provider_name: str):
        """Set which provider is considered 'primary' for auto-return purposes."""
        if provider_name in self._providers:
            self._primary_provider = provider_name

    # ─── Provider Stats ──────────────────────────────────────────────

    def get_stats(self) -> Dict[str, dict]:
        """Return usage statistics for all providers."""
        return {
            name: p.stats() for name, p in self._providers.items()
        }

    def reset_stats(self):
        """Reset all provider statistics."""
        for provider in self._providers.values():
            provider._total_calls = 0
            provider._total_errors = 0
            provider._consecutive_failures = 0
            provider._total_tokens = 0

    # ─── Internal ───────────────────────────────────────────────────

    def _get_first_available(self) -> Optional[str]:
        """Return the first available provider by priority."""
        for name in self._priority:
            p = self._providers.get(name)
            if p and p.is_available():
                return name
        return None

    def _get_next_available(self, current_idx: int) -> Optional[str]:
        """Return the next available provider after current_idx."""
        for i in range(current_idx + 1, len(self._priority)):
            name = self._priority[i]
            p = self._providers.get(name)
            if p and p.is_available():
                return name
        return None

    def _get_priority_index(self, name: str) -> int:
        try:
            return self._priority.index(name)
        except ValueError:
            return 0
