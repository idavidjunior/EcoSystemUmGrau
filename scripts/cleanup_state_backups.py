#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpeza de backups antigos de runtime/state.json
Mantém apenas os últimos N backups (padrão: 10).
"""

import sys
import os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]  # EcoSystemUmGrau root
RUNTIME_DIR = BASE / "runtime"

def cleanup_state_backups(keep: int = 10, dry_run: bool = False) -> dict:
    """Remove backups antigos de state.json, mantém os 'keep' mais recentes."""
    backups = sorted(RUNTIME_DIR.glob("state.json.bak.*"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    freed = 0
    for bak in backups[keep:]:
        size = bak.stat().st_size
        if not dry_run:
            bak.unlink()
        removed += 1
        freed += size
    return {"removed": removed, "freed_bytes": freed, "remaining": len(backups) - removed}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Limpa backups antigos de state.json")
    parser.add_argument("--keep", type=int, default=10, help="Quantos backups manter (padrão: 10)")
    parser.add_argument("--dry-run", action="store_true", help="Não remove, só mostra o que faria")
    args = parser.parse_args()

    result = cleanup_state_backups(args.keep, args.dry_run)
    print(f"State backups: removidos {result['removed']}, liberados {result['freed_bytes']} bytes, restantes {result['remaining']}")