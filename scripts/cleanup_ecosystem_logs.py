#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpeza de logs do ecossistema
Cobre: logs/ + scripts/*_log.txt + scripts/*_log.txt (watchdog, guardian, etc.)
Remove logs > 30 dias ou > 2MB por arquivo (truncamento).
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path(__file__).resolve().parents[1]
LOGS_DIR = BASE / "logs"
SCRIPTS_DIR = BASE / "scripts"

SCRIPT_LOG_PATTERNS = [
    "watchdog_log.txt",
    "opencode_desktop_guardian_log.txt",
    "guardian_log.txt",
    "scrcpy_daemon.log",
]

MAX_LOG_BYTES = 2 * 1024 * 1024  # 2MB


def truncate_log(path: Path, keep_ratio: float = 0.5) -> int:
    """Truncate log to keep_ratio of its lines. Returns bytes freed."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        keep = int(len(lines) * keep_ratio)
        if keep < 1:
            keep = 1
        kept = lines[-keep:]
        old_size = path.stat().st_size
        path.write_text("\n".join(kept) + "\n", encoding="utf-8")
        return old_size - path.stat().st_size
    except Exception:
        return 0


def cleanup_ecosystem_logs(max_age_days: int = 30, max_total_mb: int = 100, dry_run: bool = False) -> dict:
    """Remove logs antigos e controla tamanho total."""
    removed = 0
    freed = 0
    remaining = 0
    total_size = 0
    truncated = 0

    # 1. Clean logs/ directory
    if LOGS_DIR.exists():
        all_logs = list(LOGS_DIR.glob("*.log")) + list(LOGS_DIR.glob("*.txt"))
        now = datetime.now()
        cutoff = now - timedelta(days=max_age_days)

        for log in all_logs:
            mtime = datetime.fromtimestamp(log.stat().st_mtime)
            if mtime < cutoff:
                size = log.stat().st_size
                if not dry_run:
                    log.unlink()
                removed += 1
                freed += size
            else:
                remaining += 1

        remaining_logs = sorted(
            [l for l in all_logs if datetime.fromtimestamp(l.stat().st_mtime) >= cutoff],
            key=lambda p: p.stat().st_mtime,
        )
        total_size = sum(l.stat().st_size for l in remaining_logs)
        max_bytes = max_total_mb * 1024 * 1024

        while total_size > max_bytes and remaining_logs:
            oldest = remaining_logs.pop(0)
            size = oldest.stat().st_size
            if not dry_run:
                oldest.unlink()
            removed += 1
            freed += size
            total_size -= size
            remaining -= 1

    # 2. Truncate oversized script logs
    for pattern in SCRIPT_LOG_PATTERNS:
        log_path = SCRIPTS_DIR / pattern
        if not log_path.exists():
            continue
        size = log_path.stat().st_size
        if size > MAX_LOG_BYTES:
            if not dry_run:
                freed_bytes = truncate_log(log_path)
                freed += freed_bytes
                truncated += 1
            else:
                truncated += 1

    return {
        "removed": removed,
        "freed_bytes": freed,
        "remaining": remaining,
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "truncated": truncated,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Limpa logs do ecossistema")
    parser.add_argument("--max-age-days", type=int, default=30, help="Idade máxima em dias (padrão: 30)")
    parser.add_argument("--max-mb", type=int, default=100, help="Tamanho total máximo em MB (padrão: 100)")
    parser.add_argument("--dry-run", action="store_true", help="Não remove, só mostra")
    args = parser.parse_args()

    result = cleanup_ecosystem_logs(args.max_age_days, args.max_mb, args.dry_run)
    print(
        f"Ecosystem logs: removidos {result['removed']}, "
        f"truncados {result['truncated']}, "
        f"liberados {result['freed_bytes']} bytes, "
        f"restantes {result['remaining']}, "
        f"total {result['total_size_mb']} MB"
    )
