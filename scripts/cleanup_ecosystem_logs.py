#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpeza de logs do ecossistema (logs/ fora do OpenCode)
Remove logs > 30 dias ou > 100MB total.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path(__file__).resolve().parents[1]
LOGS_DIR = BASE / "logs"

def cleanup_ecosystem_logs(max_age_days: int = 30, max_total_mb: int = 100, dry_run: bool = False) -> dict:
    """Remove logs antigos e controla tamanho total."""
    if not LOGS_DIR.exists():
        return {"removed": 0, "freed_bytes": 0, "remaining": 0, "total_size_mb": 0}

    all_logs = list(LOGS_DIR.glob("*.log")) + list(LOGS_DIR.glob("*.txt"))
    now = datetime.now()
    cutoff = now - timedelta(days=max_age_days)

    removed = 0
    freed = 0
    remaining = 0

    # 1. Remove por idade
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

    # 2. Se ainda excede tamanho total, remove os mais antigos restantes
    remaining_logs = sorted([l for l in all_logs if datetime.fromtimestamp(l.stat().st_mtime) >= cutoff],
                           key=lambda p: p.stat().st_mtime)
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

    return {"removed": removed, "freed_bytes": freed, "remaining": remaining, "total_size_mb": round(total_size / 1024 / 1024, 2)}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Limpa logs do ecossistema")
    parser.add_argument("--max-age-days", type=int, default=30, help="Idade máxima em dias (padrão: 30)")
    parser.add_argument("--max-mb", type=int, default=100, help="Tamanho total máximo em MB (padrão: 100)")
    parser.add_argument("--dry-run", action="store_true", help="Não remove, só mostra")
    args = parser.parse_args()

    result = cleanup_ecosystem_logs(args.max_age_days, args.max_mb, args.dry_run)
    print(f"Ecosystem logs: removidos {result['removed']}, liberados {result['freed_bytes']} bytes, restantes {result['remaining']}, total {result['total_size_mb']} MB")