#!/usr/bin/env python3
"""Triagem periódica de organização do EcoSystemUmGrau.

Detecta dois tipos de acúmulo:
1. Scripts órfãos em scripts/ (sem referência externa real) -> candidatos a _legado
2. Artefatos rastreados no git que deveriam estar no .gitignore
   (logs, backups, html/png de teste, saídas efêmeras)

Uso:
  python scripts/audit_triagem.py              # apenas relatório (saída JSON)
  python scripts/audit_triagem.py --fix        # move órfãos confirmados para scripts/_legado
  python scripts/audit_triagem.py --text       # saída legível

Seguro por padrão: --fix só move para _legado (git mv, reversível), nunca apaga.
Artefatos do git são apenas reportados (decisão humana).
"""
import argparse
import io
import json
import os
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, "scripts")
LEGADO = os.path.join(SCRIPTS, "_legado")

# Referências que vêm de fora do repo (atalhos Startup, tarefas agendadas).
# Invisíveis para grep; nunca tratar como órfão.
PROTEGIDOS_EXTERNOS = {
    "watchdog_start.bat",        # atalho Startup EcoSystemUmGrau_Watchdog.lnk
    "opencode_desktop_guardian_start.bat",  # tarefa OpenCode-Desktop-Guardian
    "vigilante.ps1",             # tarefa EcoSystemVigilante
    "watchdog.ps1",              # chamado por watchdog_start.bat
    "grafico_widget.bat",        # atalho "Grafo do Conhecimento"
    "persistencia.ps1",          # gate, chamado por vigilante/watchdog
}

# Logs efêmeros que nunca devem ser referência válida
LOG_NAMES = {
    "bridge_log.txt", "bridge_err.txt", "bridge_out.txt",
    "serve_log.txt", "serve_sync_out.txt", "serve_sync_err.txt",
    "watchdog_log.txt", "scan_log.txt", "narrador_desktop_log.txt",
    "jarvis_voice_cmd_log.txt", "opencode_desktop_guardian_log.txt",
    "watchdog.log", "watchdog.lock", "watchdog.pid",
    "jarvis_output.log",
}

SKIP_DIRS = {'.git', 'node_modules', 'backups', '.venv', '__pycache__',
             'target', 'build', '.dart_tool', '.gradle', 'incremental',
             'deps', '.pub-cache', 'bin', 'obj', '_legado'}
SKIP_SUFFIX = {'.pyc', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.woff',
               '.woff2', '.mp3', '.wav', '.db', '.lock', '.pid'}

# Sub-repos incorporados: cada um cuida do próprio git (não são lixo do eco)
SUB_REPOS = ("Projetos/", "ferramentas/", "ler-runtime/", "ai-agents/")

# Padrões de artefato rastreado no git que deveriam estar fora (decisão humana)
GIT_SUSPEITO_PATTERNS = [
    (".log", "log"),
    ("__pycache__", "cache python"),
    (".pyc", "cache python"),
    (".bak", "backup"),
    (".npy", "dado gerado"),
    ("widget_log.txt", "log de widget"),
    ("widget_drag_result.json", "resultado de teste"),
    ("widget_e2e_result.json", "resultado de teste"),
    ("grafo_widget_geometria.json", "dado de teste"),
    ("shot_", "screenshot"),
    ("screen_full.png", "screenshot"),
    ("debug_output.txt", "saída de debug"),
    ("network_block.txt", "saída de teste"),
    ("test_github_integration.txt", "saída de teste"),
    ("widget_test_output.txt", "saída de teste"),
    ("_test_output.txt", "saída de teste"),
    ("_result.json", "resultado de teste"),
]


def collect_reference_map():
    """Mapeia scripts -> arquivos que os referenciam (excluindo logs/auto)."""
    script_names = [
        f for f in sorted(os.listdir(SCRIPTS))
        if os.path.isfile(os.path.join(SCRIPTS, f)) and f != "_legado"
    ]
    refs = {s: [] for s in script_names}
    for dirpath, dirnames, filenames in os.walk(BASE):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn in LOG_NAMES:
                continue
            ext = os.path.splitext(fn)[1].lower()
            if ext in SKIP_SUFFIX:
                continue
            fp = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(fp) > 4_000_000:
                    continue
                with open(fp, encoding="utf-8", errors="replace") as fh:
                    txt = fh.read()
            except Exception:
                continue
            base = os.path.basename(fp)
            for s in script_names:
                if s in txt and base != s:
                    refs[s].append(os.path.relpath(fp, BASE))
    return script_names, refs


def find_orfans():
    """Retorna scripts sem referência externa real (ou apenas self/legado)."""
    script_names, refs = collect_reference_map()
    orfaos = []
    for s in script_names:
        if s in PROTEGIDOS_EXTERNOS:
            continue
        if s == "audit_triagem.py":
            continue
        # referências que apontam apenas para dentro de _legado não contam
        refs_reais = [r for r in refs[s] if not r.startswith("scripts/_legado")]
        if not refs_reais:
            orfaos.append({"arquivo": s, "tamanho": os.path.getsize(os.path.join(SCRIPTS, s))})
    return orfaos


def find_artefatos_git():
    """Retorna arquivos rastreados no git que parecem artefato (reportar)."""
    r = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=BASE)
    if r.returncode != 0:
        return []
    arquivos = r.stdout.splitlines()
    suspeitos = []
    for f in arquivos:
        if f.startswith(SUB_REPOS):
            continue
        low = f.lower()
        ext = os.path.splitext(f)[1].lower()
        motivo = None
        for pat, label in GIT_SUSPEITO_PATTERNS:
            if pat in low:
                # "shot_*.ps1" é ferramenta de screenshot, não artefato
                if pat == "shot_" and ext not in (".png", ".jpg", ".jpeg"):
                    continue
                motivo = label
                break
        if motivo:
            # ignora se estiver em _legado (são renames legítimos)
            if f.startswith("scripts/_legado/"):
                continue
            suspeitos.append({"arquivo": f, "motivo": motivo})
    return suspeitos


def mover_para_legado(orfaos):
    """Move órfãos confirmados para scripts/_legado via git mv (reversível)."""
    if not os.path.isdir(LEGADO):
        os.makedirs(LEGADO)
    movidos = []
    for o in orfaos:
        src = os.path.join("scripts", o["arquivo"])
        dst = os.path.join("scripts", "_legado", o["arquivo"])
        r = subprocess.run(["git", "mv", src, dst], capture_output=True, text=True, cwd=BASE)
        if r.returncode == 0:
            movidos.append(o["arquivo"])
    return movidos


def main():
    parser = argparse.ArgumentParser(description="Triagem periódica de organização")
    parser.add_argument("--fix", action="store_true", help="move órfãos confirmados para _legado")
    parser.add_argument("--text", action="store_true", help="saída legível")
    args = parser.parse_args()

    orfaos = find_orfans()
    artefatos = find_artefatos_git()

    result = {
        "orfaos": orfaos,
        "artefatos_git": artefatos,
        "total_orfaos": len(orfaos),
        "total_artefatos": len(artefatos),
    }

    if args.fix:
        movidos = mover_para_legado(orfaos)
        result["movidos_legado"] = movidos
        result["total_movidos"] = len(movidos)
        if movidos:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.text:
        if orfaos:
            print("=== ORFAOS (candidatos a _legado) ===")
            for o in orfaos:
                print(f"  {o['arquivo']} ({o['tamanho']} B)")
        else:
            print("=== ORFAOS: nenhum ===")
        if artefatos:
            print("=== ARTEFATOS RASTREADOS NO GIT ===")
            for a in artefatos:
                print(f"  {a['arquivo']} ({a['motivo']})")
        else:
            print("=== ARTEFATOS NO GIT: nenhum ===")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
