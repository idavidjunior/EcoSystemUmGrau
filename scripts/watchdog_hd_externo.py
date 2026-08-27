"""Watchdog HD Externo - Mantem copia espelhada automaticamente.

Monitora o repo original (C:) e sincroniza o HD externo (E:) quando
detecta novos commits no GitHub ou mudancas locais.

Uso:
  python scripts/watchdog_hd_externo.py              # roda em loop
  python scripts/watchdog_hd_externo.py --once        # roda uma vez
  python scripts/watchdog_hd_externo.py --status      # mostra status
  python scripts/watchdog_hd_externo.py --interval 120  # intervalo em seg
"""

import os
import sys
import json
import time
import subprocess
import argparse
from datetime import datetime
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
SCRIPTS = os.path.join(BASE, 'scripts')
STATE_FILE = os.path.join(SCRIPTS, 'watchdog_hd_state.json')

ORIGEM = BASE
DESTINO = r"E:\Default Project\EcoSystemUmGrau"
DEFAULT_INTERVAL = 1800  # 30 minutos (checagem periodica leve)


def _git(repo: str, *args) -> tuple:
    """Executa comando git. Retorna (stdout, stderr, returncode)."""
    cmd = ["git", "-C", repo] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


def _load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            pass
    return {"last_sync": None, "last_commit_origem": None, "syncs_ok": 0, "syncs_fail": 0}


def _save_state(state: dict):
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except:
        pass


def _ensure_safe_directory():
    """Garante que o diretorio do HD externo e trusted pelo git."""
    subprocess.run(
        ["git", "config", "--global", "--add", "safe.directory", DESTINO.replace("\\", "/")],
        capture_output=True, timeout=10
    )


def get_current_commit(repo: str) -> str:
    """Retorna hash do commit HEAD."""
    out, _, rc = _git(repo, "rev-parse", "--short", "HEAD")
    return out if rc == 0 else ""


def get_remote_latest(repo: str) -> str:
    """Busca commits remotos e retorna o hash mais recente."""
    _git(repo, "fetch", "origin", "--quiet")
    out, _, rc = _git(repo, "rev-parse", "--short", "origin/opencode/mighty-meadow")
    return out if rc == 0 else ""


def sync(origem: str, destino: str) -> dict:
    """Sincroniza destino com origem via GitHub (fetch + pull).

    Returns:
        dict com status da operacao
    """
    _ensure_safe_directory()

    result = {
        "timestamp": datetime.now().isoformat(timespec='seconds'),
        "action": "none",
        "success": False,
        "commit_before": get_current_commit(destino),
        "commit_after": "",
        "error": "",
    }

    try:
        # Stash alteracoes locais do destino
        _, _, rc_stash = _git(destino, "stash", "push", "-m", "watchdog-auto-sync", "--quiet")
        had_stash = rc_stash == 0 and "No local changes" not in _

        # Pull
        out, err, rc = _git(destino, "pull", "--ff-only", "--quiet")
        if rc == 0:
            result["action"] = "pull"
            result["success"] = True
        else:
            result["action"] = "pull_failed"
            result["error"] = err[:200]

        # Restaura stash se havia
        if had_stash:
            _git(destino, "stash", "pop", "--quiet")

    except Exception as e:
        result["error"] = str(e)[:200]

    result["commit_after"] = get_current_commit(destino)
    return result


def check_status() -> dict:
    """Verifica status de sincronizacao."""
    _ensure_safe_directory()

    commit_origem = get_current_commit(ORIGEM)
    commit_destino = get_current_commit(DESTINO)
    remote_latest = get_remote_latest(ORIGEM)

    # Verifica se ha commits locais nao pushados
    _, _, rc_ahead = _git(ORIGEM, "rev-list", "--count", "origin/opencode/mighty-meadow..HEAD")
    ahead = 0
    if rc_ahead == 0:
        try:
            ahead = int(_git(ORIGEM, "rev-list", "--count", "origin/opencode/mighty-meadow..HEAD")[0])
        except:
            pass

    state = _load_state()

    return {
        "origem_commit": commit_origem,
        "destino_commit": commit_destino,
        "remote_latest": remote_latest,
        "in_sync": commit_origem == commit_destino,
        "ahead_commits": ahead,
        "last_sync": state.get("last_sync"),
        "total_syncs": state.get("syncs_ok", 0),
    }


def run_watchdog(interval: int = DEFAULT_INTERVAL):
    """Loop principal do watchdog."""
    print(f"[Watchdog HD] Iniciado. Intervalo: {interval}s")
    print(f"[Watchdog HD] Origem: {ORIGEM}")
    print(f"[Watchdog HD] Destino: {DESTINO}")
    print(f"[Watchdog HD] Ctrl+C para parar")

    state = _load_state()

    while True:
        try:
            # Verifica se destino existe
            if not os.path.exists(os.path.join(DESTINO, ".git")):
                print(f"[Watchdog HD] ERRO: Destino nao encontrado: {DESTINO}")
                time.sleep(interval)
                continue

            # Verifica commits remotos
            remote = get_remote_latest(ORIGEM)
            local = get_current_commit(DESTINO)

            if remote and remote != local:
                print(f"[Watchdog HD] Desatualizado! Origem: {local} -> Remoto: {remote}")
                result = sync(ORIGEM, DESTINO)

                if result["success"]:
                    state["syncs_ok"] = state.get("syncs_ok", 0) + 1
                    state["last_sync"] = result["timestamp"]
                    state["last_commit_origem"] = result["commit_after"]
                    print(f"[Watchdog HD] Sincronizado! Commit: {result['commit_after']}")
                else:
                    state["syncs_fail"] = state.get("syncs_fail", 0) + 1
                    print(f"[Watchdog HD] ERRO: {result['error']}")

                _save_state(state)
            else:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"[Watchdog HD] [{ts}] OK - {local}")

        except KeyboardInterrupt:
            print("\n[Watchdog HD] Encerrado.")
            break
        except Exception as e:
            print(f"[Watchdog HD] Excecao: {e}")

        time.sleep(interval)


def main():
    parser = argparse.ArgumentParser(description='Watchdog HD Externo')
    parser.add_argument('--once', action='store_true', help='Roda uma vez e sai')
    parser.add_argument('--status', action='store_true', help='Mostra status')
    parser.add_argument('--interval', type=int, default=DEFAULT_INTERVAL, help='Intervalo em segundos')

    args = parser.parse_args()

    if args.status:
        status = check_status()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return 0

    if args.once:
        result = sync(ORIGEM, DESTINO)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0

    run_watchdog(args.interval)
    return 0


if __name__ == '__main__':
    sys.exit(main())
