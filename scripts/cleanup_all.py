#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""cleanup_all.py — Limpeza unificada sob demanda.

Compoe todos os cleaners existentes + novos:
- logs antigos (cleanup_ecosystem_logs)
- backups de estado (cleanup_state_backups)
- grafos de conhecimento (cleanup_knowledge_graph)
- respostas TTS antigas (tts_resp_*.json)
- caches Python (__pycache__)
- backups antigos em backups/ (retencao configuravel)
- arquivos temporarios .tmp

Uso:
    python scripts/cleanup_all.py [--dry-run] [--dias-backups N] [--dias-logs N] [--verbose]
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / "runtime"
SCRIPTS = ROOT / "scripts"
BACKUPS = ROOT / "backups"

sys.path.insert(0, str(SCRIPTS))

def _log(msg, verbose):
    if verbose:
        print(msg, flush=True)

def cleanup_tts_responses(max_age_sec: int = 600, dry_run: bool = False, verbose: bool = False) -> dict:
    """Remove tts_resp_*.json mais velhos que max_age_sec."""
    removed = 0
    freed = 0
    now = time.time()
    for f in RUNTIME.glob("tts_resp_*.json"):
        try:
            age = now - f.stat().st_mtime
            if age > max_age_sec:
                size = f.stat().st_size
                if not dry_run:
                    f.unlink(missing_ok=True)
                removed += 1
                freed += size
                _log(f"  tts_resp removido: {f.name} (idade {age:.0f}s)", verbose)
        except Exception:
            pass
    return {"removed": removed, "freed_bytes": freed}

def cleanup_pycache(dry_run: bool = False, verbose: bool = False) -> dict:
    """Remove pastas __pycache__."""
    removed = 0
    for d in ROOT.rglob("__pycache__"):
        if d.is_dir():
            if not dry_run:
                import shutil
                shutil.rmtree(d, ignore_errors=True)
            removed += 1
            _log(f"  __pycache__ removido: {d.relative_to(ROOT)}", verbose)
    return {"removed": removed}

def cleanup_tmp_files(dry_run: bool = False, verbose: bool = False) -> dict:
    """Remove arquivos .tmp orfãos em runtime/."""
    removed = 0
    freed = 0
    for f in RUNTIME.glob("*.tmp"):
        try:
            size = f.stat().st_size
            if not dry_run:
                f.unlink(missing_ok=True)
            removed += 1
            freed += size
            _log(f"  .tmp removido: {f.name}", verbose)
        except Exception:
            pass
    return {"removed": removed, "freed_bytes": freed}

def cleanup_old_backups(dias: int = 7, dry_run: bool = False, verbose: bool = False) -> dict:
    """Remove backups/ mais antigos que dias."""
    removed = 0
    freed = 0
    if not BACKUPS.exists():
        return {"removed": 0, "freed_bytes": 0}
    cutoff = time.time() - (dias * 86400)
    for d in BACKUPS.iterdir():
        if d.is_dir():
            try:
                mtime = d.stat().st_mtime
                if mtime < cutoff:
                    # Calcula tamanho
                    total = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
                    if not dry_run:
                        import shutil
                        shutil.rmtree(d, ignore_errors=True)
                    removed += 1
                    freed += total
                    _log(f"  backup antigo removido: {d.name}", verbose)
            except Exception:
                pass
    return {"removed": removed, "freed_bytes": freed}

def run_existing_cleaner(module_name: str, func_name: str, args: list, dry_run: bool, verbose: bool) -> dict:
    """Executa um cleaner existente via import dinamico."""
    try:
        mod = __import__(module_name, fromlist=[func_name])
        func = getattr(mod, func_name)
        if dry_run and "dry_run" in func.__code__.co_varnames:
            return func(dry_run=True)
        return func(*args)
    except Exception as e:
        return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description="Limpeza unificada do ecossistema")
    parser.add_argument("--dry-run", action="store_true", help="So mostra o que seria removido")
    parser.add_argument("--dias-backups", type=int, default=7, help="Dias de retencao para backups/ (padrao 7)")
    parser.add_argument("--dias-logs", type=int, default=30, help="Dias de retencao para logs (passado para cleaners existentes)")
    parser.add_argument("--max-age-tts", type=int, default=600, help="Idade maxima em segundos para tts_resp (padrao 600s = 10 min)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Saida detalhada")
    args = parser.parse_args()

    if args.dry_run:
        print("=== DRY RUN: nada sera removido ===")

    resultados = {}
    total_removed = 0
    total_freed = 0

    print("\n--- Cleaners novos ---")

    # 1. tts_resp
    print("\n[1/6] Limpando tts_resp_*.json antigos...")
    r = cleanup_tts_responses(args.max_age_tts, args.dry_run, args.verbose)
    resultados["tts_resp"] = r
    total_removed += r.get("removed", 0)
    total_freed += r.get("freed_bytes", 0)

    # 2. __pycache__
    print("[2/6] Limpando __pycache__...")
    r = cleanup_pycache(args.dry_run, args.verbose)
    resultados["pycache"] = r
    total_removed += r.get("removed", 0)

    # 3. .tmp
    print("[3/6] Limpando .tmp orfãos...")
    r = cleanup_tmp_files(args.dry_run, args.verbose)
    resultados["tmp"] = r
    total_removed += r.get("removed", 0)
    total_freed += r.get("freed_bytes", 0)

    # 4. Backups antigos
    print(f"[4/6] Limpando backups/ mais antigos que {args.dias_backups} dias...")
    r = cleanup_old_backups(args.dias_backups, args.dry_run, args.verbose)
    resultados["backups"] = r
    total_removed += r.get("removed", 0)
    total_freed += r.get("freed_bytes", 0)

    # 5. Cleaners existentes - logs
    print(f"[5/6] Limpando logs do ecossistema (>{args.dias_logs} dias)...")
    try:
        from cleanup_ecosystem_logs import cleanup_ecosystem_logs
        r = cleanup_ecosystem_logs(max_age_days=args.dias_logs, dry_run=args.dry_run)
        resultados["ecosystem_logs"] = r
        total_removed += r.get("removed", 0)
        total_freed += r.get("freed_bytes", 0)
    except Exception as e:
        resultados["ecosystem_logs"] = {"error": str(e)}

    # 6. Cleaners existentes - state backups
    print("[6/6] Limpando backups de state.json antigos...")
    try:
        from cleanup_state_backups import cleanup_state_backups
        r = cleanup_state_backups(keep=10, dry_run=args.dry_run)
        resultados["state_backups"] = r
        total_removed += r.get("removed", 0)
    except Exception as e:
        resultados["state_backups"] = {"error": str(e)}

    # Cleaners opcionais (knowledge graph, etc) - so se existirem
    print("\n--- Cleaners opcionais ---")
    try:
        from cleanup_knowledge_graph import cleanup_knowledge_graph
        r = cleanup_knowledge_graph(keep=2, dry_run=args.dry_run)
        resultados["knowledge_graph"] = r
        total_removed += r.get("removed", 0)
        total_freed += r.get("freed_bytes", 0)
    except Exception:
        pass

    # Resumo
    print("\n=== RESUMO ===")
    if args.dry_run:
        print("DRY RUN - nada removido")
    for k, v in resultados.items():
        if isinstance(v, dict) and "error" in v:
            print(f"  {k}: ERRO - {v['error']}")
        else:
            rem = v.get("removed", 0) if isinstance(v, dict) else 0
            fb = v.get("freed_bytes", 0) if isinstance(v, dict) else 0
            if rem or fb:
                print(f"  {k}: {rem} removidos, {fb/1024:.1f} KB liberados")
    print(f"\nTotal: {total_removed} itens removidos, {total_freed/1024:.1f} KB liberados")

    if args.dry_run:
        print("\nRode sem --dry-run para executar a limpeza real.")

    return 0

if __name__ == "__main__":
    sys.exit(main())