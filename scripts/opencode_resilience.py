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

# Raiz de snapshot válida tem nome hex (hash do opencode). Nomes como
# objects/refs/hooks/info/pack são internals de git, nunca raiz.
HEX_NAME = re.compile(r"^[0-9a-f]{32,64}$", re.IGNORECASE)


def snapshot_referenciado(hash40: str) -> bool:
    """True se part/message do banco citam o hash do snapshot.

    Snapshot citado no banco pertence ao histórico/sessão viva: nunca mexer,
    mesmo parecendo corrompido (estrutura parcial é estado normal de snapshot
    em uso). Falha ao consultar = conservador: assume referenciado.
    """
    import sqlite3
    try:
        con = sqlite3.connect(f"file:{OPENCODE_DB}?mode=ro", uri=True, timeout=10)
        cur = con.cursor()
        pref = hash40[:24]
        ref = False
        for tab in ("part", "message"):
            try:
                cur.execute(f"SELECT 1 FROM {tab} WHERE data LIKE ? LIMIT 1", (f"%{pref}%",))
                if cur.fetchone():
                    ref = True
                    break
            except sqlite3.OperationalError:
                continue
        con.close()
        return ref
    except Exception:
        return True


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

    for repo_dir in sorted(snap_root.rglob("*")):
        if not repo_dir.is_dir():
            continue
        # Ignora internals de git (objects/refs/hooks/info/pack) e qualquer
        # diretório aninhado sob um snapshot já reportado.
        if not HEX_NAME.match(repo_dir.name):
            continue
        if any(str(repo_dir).startswith(str(c) + os.sep) for c in corrupted):
            continue
        # Um snapshot válido tem .git dentro OU é repo bare (com HEAD+objects)
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

    # Snapshot corrompido é correção crítica — MAS só se for órfão real.
    # Referenciado no banco (part/message) = histórico/sessão viva: nunca tocar.
    # Órfãos limpam com desktop fechado; com desktop ativo, adiam.
    orfaos_restantes = []
    if corrupted_snapshots:
        protegidos, orfaos = [], []
        for s in corrupted_snapshots:
            if snapshot_referenciado(Path(s).name):
                protegidos.append(s)
            else:
                orfaos.append(s)
        if protegidos:
            print(f"[SNAP] {len(protegidos)} snapshot(s) referenciado(s) pelo historico - nao tocar")
            result["cleaned"]["snapshot_protegido"] = len(protegidos)
            result["corrupted_snapshots"] = len(corrupted_snapshots)
        if orfaos:
            if is_desktop_running():
                print(f"[SNAP] {len(orfaos)} snapshot(s) órfão(s) - limpeza adiada (desktop ativo)")
                result["cleaned"]["snapshot_orfao"] = "adiado (desktop ativo)"
                result["deferred_clean"] = True
                orfaos_restantes.extend(orfaos)
            elif not check_only:
                print(f"[SNAP] {len(orfaos)} snapshot(s) órfão(s) - limpando")
                resultado_limpeza = clean_snapshots(orfaos)
                result["cleaned"]["snapshot_orfao"] = resultado_limpeza
                print(f"[SNAP] Limpeza: {resultado_limpeza}")
            else:
                print(f"[SNAP] {len(orfaos)} snapshot(s) órfão(s) - --clean para limpar")
                orfaos_restantes.extend(orfaos)

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

    # Exit 1 apenas quando sobrou pendência REAL sem solução neste ciclo:
    # órfãos adiados pelo desktop ativo (ou aguardando --check). Snapshot
    # referenciado pelo histórico é estado normal, não pendência. Limpeza de
    # cache executada com sucesso também não é falha.
    return 1 if orfaos_restantes else 0


if __name__ == "__main__":
    sys.exit(main())
