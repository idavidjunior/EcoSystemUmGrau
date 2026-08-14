#!/usr/bin/env python3
"""
Monitor e limpeza do cache do OpenCode (~/.config/opencode/)
Evita conflitos com o EcoSystemUmGrau mantendo logs sob controle.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta

OPENCODE_CONFIG = Path.home() / ".config" / "opencode"
LOG_PATTERNS = [
    "opencode-model-fallback.log*",
    "*.log"
]
MAX_LOG_SIZE_MB = 50
MAX_LOG_AGE_DAYS = 7
MAX_TOTAL_LOGS_MB = 200


def get_log_files():
    """Retorna todos os arquivos de log do OpenCode."""
    files = []
    for pattern in LOG_PATTERNS:
        files.extend(OPENCODE_CONFIG.glob(pattern))
    return [f for f in files if f.is_file()]


def format_size(size_bytes):
    """Formata tamanho em MB."""
    return round(size_bytes / (1024 * 1024), 2)


def check_cache(verbose=False):
    """Verifica estado do cache."""
    if not OPENCODE_CONFIG.exists():
        return {"status": "OK", "msg": "Diretório não existe"}

    logs = get_log_files()
    total_size = sum(f.stat().st_size for f in logs)
    oversized = []
    old = []

    for f in logs:
        stat = f.stat()
        size_mb = format_size(stat.st_size)
        age_days = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days

        if size_mb > MAX_LOG_SIZE_MB:
            oversized.append((f.name, size_mb))
        if age_days > MAX_LOG_AGE_DAYS:
            old.append((f.name, age_days))

        if verbose:
            print(f"  {f.name}: {size_mb} MB, {age_days} dias")

    status = "OK"
    issues = []
    if oversized:
        status = "WARN"
        issues.append(f"Logs oversized: {oversized}")
    if old:
        status = "WARN"
        issues.append(f"Logs antigos: {old}")
    if total_size > MAX_TOTAL_LOGS_MB * 1024 * 1024:
        status = "WARN"
        issues.append(f"Total logs: {format_size(total_size)} MB > {MAX_TOTAL_LOGS_MB} MB")

    return {
        "status": status,
        "log_count": len(logs),
        "total_mb": format_size(total_size),
        "oversized": oversized,
        "old": old,
        "issues": issues
    }


def clean_cache(dry_run=False):
    """Remove logs antigos e oversized."""
    if not OPENCODE_CONFIG.exists():
        return {"removed": 0, "freed_mb": 0, "msg": "Diretório não existe"}

    logs = get_log_files()
    removed = 0
    freed = 0

    for f in logs:
        stat = f.stat()
        size_mb = format_size(stat.st_size)
        age_days = (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days

        should_remove = size_mb > MAX_LOG_SIZE_MB or age_days > MAX_LOG_AGE_DAYS

        if should_remove:
            if not dry_run:
                try:
                    f.unlink()
                    print(f"Removido: {f.name} ({size_mb} MB, {age_days} dias)")
                except Exception as e:
                    print(f"Erro ao remover {f.name}: {e}")
                    continue
            removed += 1
            freed += size_mb

    return {"removed": removed, "freed_mb": round(freed, 2)}


def main():
    parser = argparse.ArgumentParser(description="Monitor/limpeza do cache OpenCode")
    parser.add_argument("--check", action="store_true", help="Apenas verifica estado")
    parser.add_argument("--clean", action="store_true", help="Limpa logs antigos/oversized")
    parser.add_argument("--dry-run", action="store_true", help="Simula limpeza sem remover")
    parser.add_argument("--verbose", "-v", action="store_true", help="Detalhes")
    args = parser.parse_args()

    if args.check or (not args.clean and not args.check):
        result = check_cache(args.verbose)
        print(f"Status: {result['status']}")
        print(f"Logs: {result['log_count']} | Total: {result['total_mb']} MB")
        if result['issues']:
            for issue in result['issues']:
                print(f"  ��� {issue}")
        if result['status'] != "OK":
            sys.exit(1)

    if args.clean:
        result = clean_cache(args.dry_run)
        action = "Simulado" if args.dry_run else "Removido"
        print(f"{action}: {result['removed']} arquivos | Liberado: {result['freed_mb']} MB")


if __name__ == "__main__":
    # Garante stdout UTF-8
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()