"""Error types for provider classification and failover decision."""


class ProviderError(Exception):
    """Base error for all provider failures."""
    def __init__(self, message, error_type="unknown", provider=""):
        super().__init__(message)
        self.error_type = error_type
        self.provider = provider

    def can_failover(self):
        """Determines if this error should trigger failover to next provider."""
        return self.error_type in ("rate_limit", "timeout", "unavailable", "auth")


class RateLimitError(ProviderError):
    """Rate limit or quota exceeded (HTTP 429, 402)."""
    def __init__(self, message, provider="", retry_after=0):
        super().__init__(message, "rate_limit", provider)
        self.retry_after = retry_after


class AuthError(ProviderError):
    """Authentication failure (HTTP 401, 403)."""
    def __init__(self, message, provider=""):
        super().__init__(message, "auth", provider)


class TimeoutError(ProviderError):
    """Connection or response timeout."""
    def __init__(self, message, provider=""):
        super().__init__(message, "timeout", provider)


class UnavailableError(ProviderError):
    """Service unavailable (HTTP 503, connection refused, DNS failure)."""
    def __init__(self, message, provider=""):
        super().__init__(message, "unavailable", provider)


class BadRequestError(ProviderError):
    """Bad request — should NOT trigger failover (HTTP 400)."""
    def __init__(self, message, provider=""):
        super().__init__(message, "bad_request", provider)

    def can_failover(self):
        return False


def classify_http_error(status_code, body="", provider=""):
    """Classify an HTTP error response into the appropriate ProviderError type."""
    if status_code == 429:
        return RateLimitError("Rate limit exceeded", provider)
    elif status_code == 401 or status_code == 403:
        return AuthError("Authentication failed", provider)
    elif status_code == 402:
        return RateLimitError("Quota exceeded", provider)
    elif status_code == 503 or status_code == 502:
        return UnavailableError("Service unavailable", provider)
    elif status_code == 400:
        return BadRequestError(f"Bad request: {body[:200]}", provider)
    elif status_code >= 500:
        return UnavailableError(f"Server error ({status_code})", provider)
    else:
        return ProviderError(f"HTTP {status_code}: {body[:200]}", "unknown", provider)


def classify_connection_error(error_msg, provider=""):
    """Classify connection-level errors (timeouts, DNS, connection refused)."""
    msg = error_msg.lower()
    if "timeout" in msg or "timed out" in msg:
        return TimeoutError(error_msg, provider)
    if "refused" in msg or "connection refused" in msg or "econnrefused" in msg:
        return UnavailableError(error_msg, provider)
    if "dns" in msg or "name or service not known" in msg or "resolve" in msg:
        return UnavailableError(error_msg, provider)
    if "certificate" in msg or "ssl" in msg:
        return AuthError(error_msg, provider)
    return ProviderError(error_msg, "unknown", provider)
