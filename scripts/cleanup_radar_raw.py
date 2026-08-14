#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Limpeza de JSONL bruto do Evolution Radar (conhecimento/evolution-radar/bruto/)
Mantém apenas os últimos N arquivos (padrão: 5).
"""

import sys
import os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
RAW_DIR = BASE / "conhecimento" / "evolution-radar" / "bruto"

def cleanup_radar_raw(keep: int = 5, dry_run: bool = False) -> dict:
    """Mantém apenas os 'keep' arquivos brutos mais recentes."""
    if not RAW_DIR.exists():
        return {"removed": 0, "freed_bytes": 0, "remaining": 0}

    raw_files = sorted(RAW_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    freed = 0
    for f in raw_files[keep:]:
        size = f.stat().st_size
        if not dry_run:
            f.unlink()
        removed += 1
        freed += size
    return {"removed": removed, "freed_bytes": freed, "remaining": len(raw_files) - removed}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Limpa JSONL bruto do Evolution Radar")
    parser.add_argument("--keep", type=int, default=5, help="Quantos arquivos manter (padrão: 5)")
    parser.add_argument("--dry-run", action="store_true", help="Não remove, só mostra")
    args = parser.parse_args()

    result = cleanup_radar_raw(args.keep, args.dry_run)
    print(f"Radar raw: removidos {result['removed']}, liberados {result['freed_bytes']} bytes, restantes {result['remaining']}")