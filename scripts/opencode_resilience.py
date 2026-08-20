"""opencode_resilience.py — Resiliência do cache do OpenCode.

Detecta erros 'failed to fetch' no log e limpa cache quando necessário.
Pode ser executado manualmente ou pelo system_guardian.

Uso:
  python scripts/opencode_resilience.py          # verifica e limpa se necessário
  python scripts/opencode_resilience.py --clean  # limpa cache forçadamente
  python scripts/opencode_resilience.py --check  # apenas verifica, não limpa
"""
import os
import sys
import shutil
import json
import re
from pathlib import Path
from datetime import datetime, timedelta

OPENCODE_DATA = Path.home() / ".local" / "share" / "opencode"
OPENCODE_LOG = OPENCODE_DATA / "log" / "opencode.log"
OPENCODE_DB = OPENCODE_DATA / "opencode.db"
OPENCODE_WAL = OPENCODE_DATA / "opencode.db-wal"
CACHE_DIRS = ["log", "snapshot", "tool-output"]
STATE_FILE = Path(__file__).parent / "opencode_resilience_state.json"

MAX_LOG_AGE_HOURS = 24
MAX_WAL_SIZE_MB = 100  # WAL file máximo antes de limpar
FETCH_ERROR_PATTERN = re.compile(r"Failed to fetch|fetch failed|ENOTFOUND|ECONNREFUSED", re.IGNORECASE)


def get_log_errors(hours: int = MAX_LOG_AGE_HOURS) -> list:
    """Lê erros recentes do log do OpenCode (somente dentro da janela de horas)."""
    if not OPENCODE_LOG.exists():
        return []

    cutoff = datetime.now() - timedelta(hours=hours)
    errors = []

    try:
        with open(OPENCODE_LOG, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                # Ignora linhas de 'evaluated permission' (nossos próprios comandos
                # de diagnóstico com 'fetch' no texto aparecem como falso positivo)
                if "evaluated permission" in line:
                    continue
                if FETCH_ERROR_PATTERN.search(line):
                    # Extrai timestamp do log (formato: timestamp=2026-08-20T17:07:43.552Z)
                    m = re.search(r"timestamp=(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})", line)
                    if m:
                        try:
                            ts = datetime.strptime(m.group(1), "%Y-%m-%dT%H:%M:%S")
                            if ts < cutoff:
                                continue  # erro antigo, fora da janela
                        except ValueError:
                            pass
                    errors.append(line.strip())
    except Exception:
        pass

    return errors


def get_cache_size() -> dict:
    """Retorna tamanho dos diretórios de cache."""
    sizes = {}
    for d in CACHE_DIRS:
        path = OPENCODE_DATA / d
        if path.exists():
            total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            sizes[d] = total / (1024 * 1024)
        else:
            sizes[d] = 0
    # WAL file
    if OPENCODE_WAL.exists():
        sizes["wal"] = OPENCODE_WAL.stat().st_size / (1024 * 1024)
    return sizes


def find_corrupted_snapshots() -> list:
    """Detecta snapshots corrompidos (estrutura git incompleta, sem .git).

    O OpenCode cria um repo git em snapshot/<hash>/<hash> para cada mensagem.
    Se o repo ficar incompleto (sem .git), o cleanup do OpenCode falha com
    'fatal: not a git repository' e pode travar a sessão — forçando o usuário
    a deletar a pasta manualmente. Esta detecção evita esse retrabalho.
    """
    corrupted = []
    snap_root = OPENCODE_DATA / "snapshot"
    if not snap_root.exists():
        return corrupted

    for repo_dir in snap_root.rglob("*"):
        if not repo_dir.is_dir():
            continue
        # Um snapshot válido tem .git dentro OU é o próprio repo (com HEAD)
        has_git = (repo_dir / ".git").exists()
        has_head = (repo_dir / "HEAD").exists()
        has_objects = (repo_dir / "objects").exists()
        has_bare_ok = has_head and has_objects
        # Estrutura parcial (hooks/info/objects/refs sem HEAD/.git) = corrompido
        if not has_git and not has_bare_ok:
            children = [p.name for p in repo_dir.iterdir()] if repo_dir.is_dir() else []
            if any(c in children for c in ("objects", "refs", "hooks", "info")):
                corrupted.append(str(repo_dir))
                if len(corrupted) >= 5:
                    break
    return corrupted


def clean_snapshots(snapshot_dirs: list) -> dict:
    """Remove snapshots corrompidos para destravar o OpenCode."""
    cleaned = {}
    for path_str in snapshot_dirs:
        p = Path(path_str)
        try:
            size = sum(f.stat().st_size for f in p.rglob("*") if f.is_file()) / (1024 * 1024)
            shutil.rmtree(p)
            cleaned[path_str] = round(size, 2)
        except PermissionError:
            try:
                for f in p.rglob("*"):
                    if f.is_file():
                        try:
                            f.unlink()
                        except PermissionError:
                            pass
                cleaned[path_str] = "parcial (arquivos locked)"
            except Exception:
                cleaned[path_str] = "falhou (locked)"
        except Exception as e:
            cleaned[path_str] = f"erro: {e}"
    return cleaned


def is_desktop_running() -> bool:
    """Verifica se o desktop OpenCode (@opencode-aidesktop) está ativo.

    Se estiver ativo, snapshots corrompidos NÃO podem ser removidos: os
    arquivos estão em uso pela sessão atual e a exclusão quebraria a sessão.
    A limpeza é adiada até o desktop fechar (próximo ciclo do guardian).
    """
    try:
        import psutil
        for p in psutil.process_iter(["pid", "exe"]):
            try:
                exe = (p.info.get("exe") or "").lower()
                if "@opencode-aidesktop" in exe and exe.endswith("opencode.exe"):
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        pass
    return False


def clean_wal() -> dict:
    """Limpa WAL file se estiver muito grande ou corrompido."""
    result = {"cleaned": False, "size_mb": 0, "reason": ""}
    if not OPENCODE_WAL.exists():
        return result
    
    size_mb = OPENCODE_WAL.stat().st_size / (1024 * 1024)
    result["size_mb"] = round(size_mb, 2)
    
    if size_mb > MAX_WAL_SIZE_MB:
        result["reason"] = f"WAL muito grande ({size_mb:.1f} MB > {MAX_WAL_SIZE_MB} MB)"
        try:
            # Primeiro tenta checkpoint (compacta o WAL)
            import sqlite3
            conn = sqlite3.connect(str(OPENCODE_DB))
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
            conn.close()
            result["cleaned"] = True
            result["method"] = "checkpoint"
        except Exception as e:
            # Se checkpoint falhar, deleta o WAL diretamente
            try:
                OPENCODE_WAL.unlink()
                result["cleaned"] = True
                result["method"] = "delete"
            except PermissionError:
                result["reason"] = f"WAL locked: {e}"
    
    return result


def clean_cache(keep_logs: bool = True) -> dict:
    """Limpa cache do OpenCode, preservando logs se necessário."""
    cleaned = {}
    for d in CACHE_DIRS:
        if keep_logs and d == "log":
            continue
        path = OPENCODE_DATA / d
        if path.exists():
            size_before = sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) / (1024 * 1024)
            try:
                shutil.rmtree(path)
                path.mkdir(parents=True, exist_ok=True)
                cleaned[d] = round(size_before, 2)
            except PermissionError:
                # Arquivos podem estar locked pelo OpenCode
                # Tenta limpar apenas arquivos não-lockeados
                cleaned_files = 0
                for f in path.rglob("*"):
                    if f.is_file():
                        try:
                            f.unlink()
                            cleaned_files += 1
                        except PermissionError:
                            pass
                if cleaned_files > 0:
                    cleaned[d] = f"{cleaned_files} arquivos removidos"
                else:
                    cleaned[d] = "arquivos lockeados, pulando"
    return cleaned


def save_state(state: dict):
    """Salva estado da resiliência."""
    try:
        STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def load_state() -> dict:
    """Carrega estado anterior."""
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def main():
    args = sys.argv[1:]
    check_only = "--check" in args
    force_clean = "--clean" in args

    errors = get_log_errors()
    cache_sizes = get_cache_size()
    total_cache = sum(cache_sizes.values())
    
    # Verifica WAL file
    wal_result = clean_wal()
    if wal_result["cleaned"]:
        print(f"[WAL] {wal_result['reason']} - limpo via {wal_result.get('method', '?')}")

    # Verifica snapshots corrompidos (causa de travamento do OpenCode)
    corrupted_snapshots = find_corrupted_snapshots()

    state = load_state()
    last_clean = state.get("last_clean")
    last_error_count = state.get("error_count", 0)

    needs_clean = force_clean or (len(errors) > 5 and len(errors) > last_error_count)

    result = {
        "timestamp": datetime.now().isoformat(),
        "errors_found": len(errors),
        "cache_mb": round(total_cache, 2),
        "cache_detail": {k: round(v, 2) for k, v in cache_sizes.items()},
        "needs_clean": needs_clean,
        "cleaned": {},
        "corrupted_snapshots": len(corrupted_snapshots),
    }

    # Snapshot corrompido é correção crítica: limpa mesmo em --check.
    # Porém NUNCA enquanto o desktop estiver ativo (arquivos em uso pela
    # sessão atual — deletar quebraria a sessão). Adia até o desktop fechar.
    if corrupted_snapshots:
        if is_desktop_running():
            print(f"[SNAP] {len(corrupted_snapshots)} snapshot(s) corrompido(s) - limpeza adiada (desktop ativo)")
            result["cleaned"]["snapshot_corrompido"] = "adiado (desktop ativo)"
            result["corrupted_snapshots"] = len(corrupted_snapshots)
            result["deferred_clean"] = True
        else:
            print(f"[SNAP] {len(corrupted_snapshots)} snapshot(s) corrompido(s) detectado(s)")
            if not check_only:
                result["cleaned"]["snapshot_corrompido"] = clean_snapshots(corrupted_snapshots)
                print(f"[SNAP] Limpeza: {result['cleaned']['snapshot_corrompido']}")
            else:
                print("[SNAP] Limpeza recomendada (--clean para limpar)")

    if needs_clean and not check_only:
        result["cleaned"] = clean_cache(keep_logs=True)
        result["last_clean"] = datetime.now().isoformat()
        save_state({
            "last_clean": datetime.now().isoformat(),
            "error_count": len(errors),
            "last_cache_mb": total_cache,
        })
        print(f"[CLEAN] Cache limpo: {result['cleaned']}")
    elif check_only:
        print(f"[CHECK] Erros: {len(errors)}, Cache: {total_cache:.1f} MB")
        if needs_clean:
            print(f"[CHECK] Limpeza recomendada ({len(errors)} erros > {last_error_count} anteriores)")
    else:
        print(f"[OK] Sem necessidade de limpeza ({len(errors)} erros, cache {total_cache:.1f} MB)")
        save_state({
            "last_check": datetime.now().isoformat(),
            "error_count": len(errors),
            "last_cache_mb": total_cache,
        })

    # Só retorna 1 se houver limpeza REAL pendente (não quando apenas adiada
    # porque o desktop está ativo — nesse caso a limpeza rodará no próximo ciclo).
    actionable = needs_clean
    if corrupted_snapshots and not result.get("deferred_clean"):
        actionable = True
    return 0 if not actionable else 1


if __name__ == "__main__":
    sys.exit(main())
