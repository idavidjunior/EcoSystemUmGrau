#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""limpeza_disco.py — Diagnóstico e limpeza segura de espaço no disco do sistema (Windows).

Ferramenta permanente do ecossistema para liberar espaço no C: sem risco.

Uso:
    python scripts/limpeza_disco.py --diagnostico          # relatório dos alvos (padrão)
    python scripts/limpeza_disco.py --limpar               # executa limpeza segura
    python scripts/limpeza_disco.py --limpar --simular     # mostra o que faria, sem executar
    python scripts/limpeza_disco.py --limpar --gradle      # inclui caches antigos do Gradle

Alvos de limpeza segura (regeneráveis, zero risco):
  - AppData/Local/npm-cache          (npm recria)
  - AppData/Local/Temp               (temporários, ignora em uso)
  - Ollama lib cuda_v13 is-*.tmp     (lixo de instalação)
  - .flutter_auto/*.zip              (SDKs já extraídos)
  - balena_etcher packages/*.nupkg   (instalador já aplicado)
  - Roaming/Code/CachedExtensionVSIXs (VS Code re-baixa)
  - --gradle: caches antigos (8.x)   (re-baixados sob demanda)

Retenção do banco do OpenCode (--opencode-db [--dias N]):
  Apaga sessões inativas há mais de N dias (padrão 7) e todo o conteúdo
  associado: mensagens, partes, todos, eventos e sequências. Preserva a
  sessão ativa (mais recente). Faz backup do opencode.db antes de apagar
  e roda VACUUM para devolver espaço ao arquivo.

NÃO mexe em: pagefile, WSL vhdx, ProgramData/Microsoft, Programs instalados,
modelos Ollama (já na E:), builds/target de projetos, secrets, contas,
projetos e permissões do opencode (tabelas account/credential/permission).
"""
import argparse
import json
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path

BASE_USER = Path(os.environ.get("USERPROFILE", r"C:\Users\David Jr"))
ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "runtime" / "limpeza_disco.log"

OPENCODE_DB = BASE_USER / ".local/share/opencode/opencode.db"
RETENCAO_DIAS_PADRAO = 7
MS_POR_DIA = 86400 * 1000


def _log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _size_gb(path: Path) -> float:
    if not path.exists():
        return 0.0
    if path.is_file():
        try:
            return path.stat().st_size / (1024 ** 3)
        except OSError:
            return 0.0
    total = 0
    for root, dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(Path(root) / f)
            except OSError:
                pass
    return total / (1024 ** 3)


def _rm_force(target: Path) -> int:
    """Remove arquivo ou pasta; retorna bytes liberados. Ignora erros de acesso."""
    if not target.exists():
        return 0
    size = 0
    if target.is_file():
        try:
            size = target.stat().st_size
            target.unlink(missing_ok=True)
            return size if not target.exists() else 0
        except OSError:
            return 0
    size = _size_gb(target) * (1024 ** 3)
    try:
        shutil.rmtree(target, ignore_errors=True)
        return size if not target.exists() else 0
    except OSError:
        return 0


ALVOS_DIAGNOSTICO = [
    ("npm-cache", BASE_USER / "AppData/Local/npm-cache"),
    ("Temp (usuário)", BASE_USER / "AppData/Local/Temp"),
    ("Android SDK", BASE_USER / "AppData/Local/Android"),
    ("WSL vhdx", BASE_USER / "AppData/Local/wsl"),
    ("ms-playwright", BASE_USER / "AppData/Local/ms-playwright"),
    ("balena_etcher", BASE_USER / "AppData/Local/balena_etcher"),
    ("pip cache", BASE_USER / "AppData/Local/pip"),
    ("Pub cache", BASE_USER / "AppData/Local/Pub"),
    ("Programs (apps)", BASE_USER / "AppData/Local/Programs"),
    ("Gradle caches", BASE_USER / ".gradle/caches"),
    ("Flutter zips", BASE_USER / ".flutter_auto"),
    ("VSIX cache", BASE_USER / "AppData/Roaming/Code/CachedExtensionVSIXs"),
    ("opencode.db", BASE_USER / ".local/share/opencode/opencode.db"),
]


def itens_limpeza_simples() -> list:
    """Lista (label, caminho) dos alvos regeneráveis de remoção simples."""
    items = [
        ("npm-cache", BASE_USER / "AppData/Local/npm-cache"),
        ("Temp (usuário)", BASE_USER / "AppData/Local/Temp"),
        ("VSIX cache", BASE_USER / "AppData/Roaming/Code/CachedExtensionVSIXs"),
        ("balena nupkg", BASE_USER / "AppData/Local/balena_etcher/packages"),
    ]
    # Lixo de instalação do Ollama (is-*.tmp) em cuda_v13
    cuda13 = BASE_USER / "AppData/Local/Programs/Ollama/lib/ollama/cuda_v13"
    if cuda13.exists():
        for f in cuda13.iterdir():
            if f.suffix == ".tmp":
                items.append((f"Ollama lixo ({f.name})", f))
    # Zips do Flutter já extraídos
    flutter_auto = BASE_USER / ".flutter_auto"
    if flutter_auto.exists():
        for f in flutter_auto.rglob("*.zip"):
            items.append((f"Flutter zip ({f.name})", f))
        # Pasta 'flutter' gerada pelo auto-installer: só remove zips, NUNCA o SDK
    return items


def itens_gradle_antigo() -> list:
    """Caches de versões antigas do Gradle (re-baixados sob demanda)."""
    gradle = BASE_USER / ".gradle/caches"
    items = []
    if gradle.exists():
        for sub in gradle.iterdir():
            if sub.is_dir() and sub.name.startswith("8."):
                items.append((f"Gradle cache {sub.name}", sub))
    return items


# ---------------------------------------------------------------------------
# Retenção do banco do OpenCode (opencode.db)
# ---------------------------------------------------------------------------
# O banco guarda sessões, mensagens, partes, todos e eventos (telemetria que
# repete o payload da sessão) e cresce sem limite. Não há retenção nativa.
# A poda apaga o conteúdo de sessões inativas há mais de N dias, preservando
# a sessão ativa (a mais recente). Tabelas de configuração/credenciais
# (account, credential, permission, project, workspace) nunca são tocadas.

def _cutoff_ms(dias: int) -> int:
    return int(time.time() * 1000 - dias * MS_POR_DIA)


def _poda_stats(cur: sqlite3.Cursor, dias: int) -> dict:
    """Conta o que seria removido para a retenção de N dias (não apaga nada)."""
    cut = _cutoff_ms(dias)
    cur.execute(
        """SELECT COUNT(*) FROM session
           WHERE time_updated < ?
             AND id != (SELECT id FROM session ORDER BY time_updated DESC LIMIT 1)""",
        (cut,))
    sessioes = cur.fetchone()[0]
    queries = {
        "mensagens": "SELECT COUNT(*), COALESCE(SUM(LENGTH(data)),0) FROM message"
                     " WHERE session_id IN (SELECT id FROM session WHERE"
                     " time_updated < ? AND id != (SELECT id FROM session"
                     " ORDER BY time_updated DESC LIMIT 1))",
        "partes": "SELECT COUNT(*), COALESCE(SUM(LENGTH(data)),0) FROM part"
                  " WHERE session_id IN (SELECT id FROM session WHERE"
                  " time_updated < ? AND id != (SELECT id FROM session"
                  " ORDER BY time_updated DESC LIMIT 1))",
        "todos": "SELECT COUNT(*), 0 FROM todo WHERE session_id IN"
                 " (SELECT id FROM session WHERE time_updated < ? AND"
                 " id != (SELECT id FROM session ORDER BY time_updated DESC LIMIT 1))",
        "eventos": "SELECT COUNT(*), COALESCE(SUM(LENGTH(data)),0) FROM event"
                   " WHERE aggregate_id IN (SELECT id FROM session WHERE"
                   " time_updated < ? AND id != (SELECT id FROM session"
                   " ORDER BY time_updated DESC LIMIT 1))",
        "event_sequence": "SELECT COUNT(*), 0 FROM event_sequence WHERE"
                          " aggregate_id IN (SELECT id FROM session WHERE"
                          " time_updated < ? AND id != (SELECT id FROM session"
                          " ORDER BY time_updated DESC LIMIT 1))",
    }
    rows = {}
    for nome, sql in queries.items():
        cur.execute(sql, (cut,))
        n, b = cur.fetchone()
        rows[nome] = (n or 0, b or 0)
    return {"sessioes": sessioes, "por_tabela": rows}


def _poda_executar(cur: sqlite3.Cursor, dias: int) -> dict:
    """Apaga sessões inativas há mais de N dias e todo o conteúdo associado."""
    cut = _cutoff_ms(dias)
    ids = (
        "SELECT id FROM session WHERE time_updated < ? AND"
        " id != (SELECT id FROM session ORDER BY time_updated DESC LIMIT 1)")
    tabelas = [
        ("todo", "session_id"),
        ("message", "session_id"),
        ("part", "session_id"),
        ("session_context_epoch", "session_id"),
        ("event", "aggregate_id"),
        ("event_sequence", "aggregate_id"),
        ("session_share", "session_id"),
    ]
    removidos = {"sessioes": 0, "linhas_tabelas": 0}
    for tabela, coluna in tabelas:
        cur.execute(f"DELETE FROM {tabela} WHERE {coluna} IN ({ids})", (cut,))
        removidos["linhas_tabelas"] += cur.rowcount
    cur.execute(f"DELETE FROM session WHERE id IN ({ids})", (cut,))
    removidos["sessioes"] = cur.rowcount
    return removidos


def cmd_opencode_db(args) -> None:
    """Retenção do opencode.db: apaga sessões inativas há mais de N dias.

    Sempre tenta VACUUM ao final (mesmo sem nada a remover, para recuperar a
    freelist de podas anteriores), a menos que --no-vacuum seja usado (útil
    com o OpenCode aberto, quando o lock exclusivo do VACUUM é impossível).
    """
    dias = args.dias if args.dias is not None else RETENCAO_DIAS_PADRAO
    if not OPENCODE_DB.exists():
        _log(f"opencode.db não encontrado: {OPENCODE_DB}")
        return

    tamanho_inicial = OPENCODE_DB.stat().st_size / (1024 ** 3)
    label = "SIMULAÇÃO" if args.simular else "RETENÇÃO"
    _log(f"=== {label} OPENCODE.DB ({dias} dias) ===")
    _log(f"  banco: {OPENCODE_DB}")
    _log(f"  tamanho atual: {tamanho_inicial:.2f} GB")

    try:
        conn = sqlite3.connect(str(OPENCODE_DB), timeout=60)
        conn.execute("PRAGMA busy_timeout = 60000")
    except sqlite3.Error as e:
        _log(f"  ERRO ao abrir o banco: {e}")
        return

    try:
        cur = conn.cursor()
        # Sessão ativa (para reportar qual será preservada)
        cur.execute("SELECT id FROM session ORDER BY time_updated DESC LIMIT 1")
        sessao_ativa = cur.fetchone()[0]
        _log(f"  sessão ativa preservada: {sessao_ativa}")
        stats = _poda_stats(cur, dias)
        _log(f"  sessões a remover (inativas > {dias} dias): {stats['sessioes']}")
        for nome, (n, b) in stats["por_tabela"].items():
            _log(f"  {nome:16s} {n:6d} linhas  {b / (1024**3):6.2f} GB payload")

        if stats["sessioes"] > 0:
            if args.simular:
                _log("  Simulação: nenhuma linha será apagada. "
                     "Rode --opencode-db sem --simular para executar.")
                return

            # Backup antes de apagar (--no-backup pula quando já existe backup)
            if args.no_backup:
                _log("  backup pulado (--no-backup): confiando em backup anterior.")
            else:
                backup = OPENCODE_DB.with_name(
                    f"opencode.db.bak.{time.strftime('%Y%m%d_%H%M%S')}")
                _log(f"  backup em: {backup}")
                try:
                    shutil.copy2(OPENCODE_DB, backup)
                    _log(f"  backup OK ({backup.stat().st_size / (1024**3):.2f} GB)")
                except OSError as e:
                    _log(f"  ERRO de backup — abortando sem apagar: {e}")
                    return

            removidos = _poda_executar(cur, dias)
            _log(f"  removidos: {removidos['sessioes']} sessões, "
                 f"{removidos['linhas_tabelas']} linhas em tabelas filhas")
            conn.commit()
        else:
            _log("  Nada a remover. Retenção em dia ✓")

        # VACUUM devolve espaço ao arquivo (skip com --no-vacuum: exige
        # lock exclusivo, impossível com o OpenCode aberto). Como sempre:
        # sem nada a remover, ainda recupera a freelist de podas anteriores.
        if not args.no_vacuum:
            if args.simular:
                _log("  Simulação: VACUUM seria executado em execução real.")
            else:
                try:
                    _log("  VACUUM (devolvendo espaço ao arquivo)...")
                    conn.execute("VACUUM")
                    _log("  VACUUM OK")
                except sqlite3.Error as e:
                    _log(f"  AVISO: VACUUM falhou ({e}). "
                         "O espaço será liberado em uma próxima abertura/VACUUM.")
        else:
            _log("  VACUUM pulado (--no-vacuum): arquivo só encolhe "
                 "com o OpenCode fechado.")

        tamanho_final = OPENCODE_DB.stat().st_size / (1024 ** 3)
        _log(f"  tamanho após retenção: {tamanho_final:.2f} GB "
             f"(-{tamanho_inicial - tamanho_final:.2f} GB)")
    finally:
        conn.close()


def cmd_diagnostico() -> None:
    _log("=== DIAGNÓSTICO DE ESPAÇO ===")
    total = 0.0
    for label, path in ALVOS_DIAGNOSTICO:
        gb = _size_gb(path)
        total += gb
        _log(f"  {label:22s} {gb:8.2f} GB   {path}")
    # freedisk
    import ctypes
    free = ctypes.c_ulonglong(0)
    ctypes.windll.kernel32.GetDiskFreeSpaceExW(
        "C:\\", None, None, ctypes.byref(free))
    _log(f"  Espaço livre em C: {free.value / (1024**3):.2f} GB")
    _log(f"  Soma dos alvos: {total:.2f} GB")


def cmd_limpar(args) -> None:
    if not args.simular:
        _log("=== LIMPEZA SEGURA ===")
    else:
        _log("=== SIMULAÇÃO (nada será removido) ===")

    freed = 0
    for label, path in itens_limpeza_simples() + (itens_gradle_antigo() if args.gradle else []):
        gb = _size_gb(path)
        if not args.simular:
            freed += _rm_force(path)
        _log(f"  {label:28s} {gb:8.2f} GB   -> {path}" + ("  [SIM] " if args.simular else ""))
    if args.simular:
        _log("Simulação concluída. Rode --limpar sem --simular para executar.")
        return
    _log(f"Limpeza concluída. Liberados: {freed / (1024**3):.2f} GB")
    _log('Conferindo espaço livre após limpeza...')
    cmd_diagnostico()


def main() -> None:
    p = argparse.ArgumentParser(description="Diagnóstico e limpeza segura do disco.")
    p.add_argument("--diagnostico", action="store_true", help="Relatório de espaço (padrão).")
    p.add_argument("--limpar", action="store_true", help="Executa limpeza segura.")
    p.add_argument("--simular", action="store_true", help="Apenas mostra o que seria feito.")
    p.add_argument("--gradle", action="store_true", help="Inclui caches antigos do Gradle (8.x).")
    p.add_argument("--opencode-db", action="store_true",
                   help="Retenção do banco: apaga sessões inativas há mais de N dias.")
    p.add_argument("--dias", type=int, default=None,
                   help=f"Dias de retenção (padrão {RETENCAO_DIAS_PADRAO}). Usado com --opencode-db.")
    p.add_argument("--no-vacuum", action="store_true",
                   help="Pula o VACUUM ao final da retenção (útil com o OpenCode aberto).")
    p.add_argument("--no-backup", action="store_true",
                   help="Pula o backup do opencode.db antes da poda (quando já existe "
                        "backup recente do gate de retenção).")
    args = p.parse_args()

    if args.opencode_db:
        cmd_opencode_db(args)
    elif args.limpar:
        cmd_limpar(args)
    else:
        cmd_diagnostico()


if __name__ == "__main__":
    main()