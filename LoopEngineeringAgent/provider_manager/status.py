"""Provider status report — generates the /provider-status output."""

from typing import List, Optional
from .models import ProviderStatus
from .manager import ProviderManager
from .providers import PROVIDER_REGISTRY


def generate_status(manager: ProviderManager) -> str:
    """Generate the /provider-status text output."""
    lines = []
    lines.append("=" * 60)
    lines.append("  PROVIDER STATUS")
    lines.append("=" * 60)
    lines.append("")

    all_providers = manager.get_all_providers()
    active = manager.get_active_provider_name()
    fallback = manager.get_fallback_provider_name()

    for name in manager.get_priority_order():
        provider = all_providers.get(name)
        if not provider:
            lines.append(f"  {name:20s} DESCONHECIDO")
            continue

        # Determine status text
        if provider.is_available():
            # Check health
            if name == active:
                status_text = "ATIVO"
            elif name == fallback:
                status_text = "FALLBACK"
            else:
                status_text = "ONLINE"
        else:
            status_text = "SEM API"

        model = provider.default_model
        stats = provider.stats()
        fails = stats.get("consecutive_failures", 0)
        tokens = stats.get("total_tokens", 0)
        last_err = stats.get("last_error") or ""

        lines.append(f"  {name:20s} {status_text:12s} modelo: {model}")
        if last_err and status_text != "ATIVO":
            lines.append(f"  {'':20s} ultimo erro: {last_err[:80]}")
        if name == active:
            lines.append(f"  {'':20s} chamadas: {stats.get('total_calls', 0)} | "
                         f"tokens: {tokens} | erros consecutivos: {fails}")
        lines.append("")

    # Active provider section
    lines.append("-" * 60)
    lines.append("  Provider ativo")
    lines.append(f"  {active or 'NENHUM'}")

    lines.append("")
    lines.append("  Fallback")
    lines.append(f"  {fallback or 'NENHUM'}")

    # Reason for fallback if not primary
    if fallback and active != manager.default_priority[0]:
        lines.append("")
        lines.append("  Motivo")
        last_fail = _get_last_fail_reason(manager)
        if last_fail:
            lines.append(f"  {last_fail}")
        else:
            lines.append("  Falha no provider primario")

    lines.append("")
    lines.append("-" * 60)
    lines.append("  Log de trocas")
    log_summary = manager.logger.summary()
    for line in log_summary.split("\n"):
        lines.append(f"  {line}" if not line.startswith("=") and not line.startswith("  ") else line)

    lines.append("=" * 60)
    return "\n".join(lines)


def _get_last_fail_reason(manager: ProviderManager) -> str:
    """Get the reason for the last failover."""
    for e in reversed(manager.logger.events):
        if e.event in ("failover", "switch"):
            return e.reason or e.details
    return ""


def status_as_dict(manager: ProviderManager) -> dict:
    """Return provider status as a structured dict (for programmatic use)."""
    all_providers = manager.get_all_providers()
    providers = []
    for name in manager.get_priority_order():
        p = all_providers.get(name)
        if not p:
            continue
        stats = p.stats()
        providers.append({
            "name": name,
            "available": p.is_available(),
            "status": _status_text(manager, name, p),
            "model": p.default_model,
            "total_calls": stats.get("total_calls", 0),
            "total_errors": stats.get("total_errors", 0),
            "consecutive_failures": stats.get("consecutive_failures", 0),
            "total_tokens": stats.get("total_tokens", 0),
            "last_error": stats.get("last_error"),
        })
    return {
        "active_provider": manager.get_active_provider_name(),
        "fallback_provider": manager.get_fallback_provider_name(),
        "providers": providers,
        "failover_count": manager.logger.get_failover_count(),
        "switch_count": manager.logger.get_switch_count(),
    }


def _status_text(manager, name, provider):
    active = manager.get_active_provider_name()
    fallback = manager.get_fallback_provider_name()
    if not provider.is_available():
        return "SEM API"
    if name == active:
        return "ATIVO"
    if name == fallback:
        return "FALLBACK"
    return "ONLINE"
