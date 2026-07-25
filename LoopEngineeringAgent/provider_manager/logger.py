"""Provider event logging — tracks all provider switches, errors, and health check results."""

import os
import json
import time
from datetime import datetime
from typing import List, Optional

from .models import ProviderLog


class ProviderLogger:
    """Logs all provider-related events for diagnostics and debugging."""

    def __init__(self, log_dir: Optional[str] = None):
        self.log_dir = log_dir
        self._events: List[ProviderLog] = []
        self._max_events = 1000

    @property
    def events(self) -> List[ProviderLog]:
        return list(self._events)

    def log(self, event: str, provider: str = "", **kwargs):
        """Log a provider event."""
        entry = ProviderLog(
            timestamp=datetime.now().isoformat(),
            event=event,
            provider=provider,
            from_provider=kwargs.get("from_provider", ""),
            to_provider=kwargs.get("to_provider", ""),
            reason=kwargs.get("reason", ""),
            duration_ms=kwargs.get("duration_ms", 0.0),
            success=kwargs.get("success", True),
            details=kwargs.get("details", ""),
        )
        self._events.append(entry)
        if len(self._events) > self._max_events:
            self._events.pop(0)

        # Persist if configured
        if self.log_dir:
            self._persist(entry)

    def _persist(self, entry: ProviderLog):
        """Append entry to the provider log file."""
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            log_file = os.path.join(self.log_dir, "provider_events.json")
            entries = []
            if os.path.exists(log_file):
                try:
                    with open(log_file, "r", encoding="utf-8") as f:
                        entries = json.load(f)
                except Exception:
                    entries = []
            entries.append(entry.__dict__)
            # Keep last 2000 entries
            if len(entries) > 2000:
                entries = entries[-2000:]
            tmp = log_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(entries, f, indent=2, ensure_ascii=False)
            os.replace(tmp, log_file)
        except Exception:
            pass  # Logging should never crash

    def get_recent(self, n: int = 20) -> List[ProviderLog]:
        """Return the most recent N events."""
        return self._events[-n:]

    def get_failover_count(self) -> int:
        """Count how many failover events occurred."""
        return sum(1 for e in self._events if e.event == "failover")

    def get_switch_count(self) -> int:
        """Count how many provider switches occurred."""
        return sum(1 for e in self._events if e.event == "switch")

    def get_error_count(self) -> int:
        """Count how many error events occurred."""
        return sum(1 for e in self._events if e.event == "error")

    def summary(self) -> str:
        """Return a summary of all logged events."""
        lines = []
        lines.append("=== Provedores: Log de Eventos ===")
        lines.append(f"Total de eventos: {len(self._events)}")
        lines.append(f"Trocas de provider: {self.get_switch_count()}")
        lines.append(f"Fallbacks: {self.get_failover_count()}")
        lines.append(f"Erros: {self.get_error_count()}")
        lines.append("")
        for e in self._events[-10:]:
            lines.append(
                f"  [{e.timestamp[-12:-7]}] {e.event:12s} "
                f"{e.provider or e.from_provider or '?':15s} -> "
                f"{e.to_provider or '':15s} "
                f"{e.reason[:60] if e.reason else ''}"
            )
        lines.append("")
        return "\n".join(lines)
