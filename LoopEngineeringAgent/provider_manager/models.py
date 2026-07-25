"""Data models for ProviderManager."""

from dataclasses import dataclass, field
from typing import Optional, List, Any
from datetime import datetime


@dataclass
class ModelInfo:
    """Information about a specific model available through a provider."""
    id: str
    provider: str
    context_window: int = 0
    supports_vision: bool = False
    supports_tools: bool = False
    supports_streaming: bool = True
    cost_per_1k_input: Optional[float] = None
    cost_per_1k_output: Optional[float] = None
    description: str = ""


@dataclass
class ProviderResponse:
    """Standard response from any LLM provider."""
    success: bool
    provider: str
    model: str = ""
    content: str = ""
    error: Optional[str] = None
    error_type: str = ""  # "rate_limit", "auth", "timeout", "unavailable", "bad_request", ""
    latency_ms: float = 0.0
    token_count_input: int = 0
    token_count_output: int = 0
    raw: Optional[Any] = None


@dataclass
class HealthStatus:
    """Result of a health check against a provider."""
    online: bool
    provider: str
    latency_ms: float = 0.0
    model_count: int = 0
    error: Optional[str] = None
    last_check: str = ""


@dataclass
class ProviderStatus:
    """Full status of a single provider for /provider-status output."""
    name: str
    status: str  # "ONLINE", "OFFLINE", "SEM API", "DISABLED"
    priority: int = 99
    model: str = ""
    latency_ms: float = 0.0
    error: Optional[str] = None


@dataclass
class ProviderLog:
    """A single provider event log entry."""
    timestamp: str = ""
    event: str = ""  # "switch", "failover", "return", "error", "health_check"
    provider: str = ""
    from_provider: str = ""
    to_provider: str = ""
    reason: str = ""
    duration_ms: float = 0.0
    success: bool = True
    details: str = ""


@dataclass
class CompletionRequest:
    """A request to complete a conversation through any provider."""
    messages: List[dict] = field(default_factory=list)
    model: Optional[str] = None
    provider: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    stream: bool = False
    tools: Optional[List[dict]] = None
    session_id: Optional[str] = None
