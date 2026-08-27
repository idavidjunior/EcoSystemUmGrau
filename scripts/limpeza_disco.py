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

NÃO mexe em: pagefile, WSL vhdx, opencode.db, ProgramData/Microsoft,
Programs instalados, modelos Ollama (já na E:), builds/target de projetos.
"""
import argparse
import json
import os
import shutil
import sys
import time
from pathlib import Path

BASE_USER = Path(os.environ.get("USERPROFILE", r"C:\Users\David Jr"))
ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "runtime" / "limpeza_disco.log"


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
    args = p.parse_args()

    if args.limpar:
        cmd_limpar(args)
    else:
        cmd_diagnostico()


if __name__ == "__main__":
    main()