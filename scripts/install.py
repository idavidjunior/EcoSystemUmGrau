#!/usr/bin/env python3
"""
EcoSystemUmGrau — Instalador / Bootstrap completo (single command).

Uso:
    python scripts/install.py              # instala com venv + validacao
    python scripts/install.py --no-venv    # instala no Python global
    python scripts/install.py --check      # apenas verifica integridade
    python scripts/install.py --sync       # apenas sincroniza
"""

import os
import sys
import json
import shutil
import subprocess
import platform
from pathlib import Path

# ─── Constants ───────────────────────────────────────
ECO_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ECO_DIR / "scripts"
CONFIG_DIR = ECO_DIR / "config"
OCODE_DIR = Path.home() / ".config" / "opencode"
VENV_DIR = ECO_DIR / ".venv"
REQ_FILE = ECO_DIR / "requirements.txt"

WIN = platform.system() == "Windows"
BOLD = "\033[1m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"
DIM = "\033[2m"


def ok(msg):
    print(f"  {GREEN}[OK]{RESET} {msg}")


def warn(msg):
    print(f"  {YELLOW}[!!]{RESET} {msg}")


def fail(msg):
    print(f"  {RED}[ERRO]{RESET} {msg}")


def info(msg):
    print(f"  {DIM}[..]{RESET} {msg}")


def step(n, msg):
    print(f"\n{CYAN}>>> [{n}] {msg}{RESET}")


def run(cmd, cwd=None, capture=False):
    try:
        r = subprocess.run(
            cmd, shell=True, cwd=cwd, capture_output=capture, text=True, timeout=300
        )
        return r.returncode, r.stdout.strip() if capture else "", r.stderr.strip() if capture else ""
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def check_python():
    v = sys.version_info
    if v < (3, 10):
        fail(f"Python {v.major}.{v.minor} detectado. Necessario 3.10+.")
        sys.exit(1)
    ok(f"Python {v.major}.{v.minor}.{v.micro}")


def check_git():
    code, out, _ = run("git --version", capture=True)
    if code != 0:
        fail("Git nao encontrado. Instale: https://git-scm.com")
        sys.exit(1)
    ok(f"Git {out.replace('git version ', '')}")


def check_node():
    code, out, _ = run("node --version", capture=True)
    if code != 0:
        warn("Node.js nao encontrado (necessario para plugins npm)")
    else:
        ok(f"Node.js {out}")


# ─── Steps ───────────────────────────────────────────

def step_repo():
    step(1, "Repositorio")
    git_dir = ECO_DIR / ".git"
    if git_dir.exists():
        info("Repo encontrado, atualizando...")
        code, out, err = run("git pull --ff-only", cwd=ECO_DIR, capture=True)
        if code == 0:
            ok("Repo atualizado")
        else:
            warn(f"Pull falhou (pode ter conflito): {err or out}")
    else:
        fail(f"Nao e um repositorio git: {ECO_DIR}")
        info("Clone com: git clone https://github.com/idavidjunior/EcoSystemUmGrau.git")


def step_venv(no_venv=False):
    step(2, "Virtualenv Python")
    if no_venv:
        warn("Pulando venv (--no-venv)")
        return False

    if not VENV_DIR.exists():
        info("Criando .venv...")
        code, _, err = run(f'"{sys.executable}" -m venv "{VENV_DIR}"')
        if code != 0:
            warn(f"Falha ao criar venv: {err}. Continuando no global.")
            return False
        ok("Virtualenv criado")
    else:
        ok("Virtualenv ja existe")

    # Return the venv python path
    if WIN:
        venv_python = VENV_DIR / "Scripts" / "python.exe"
        venv_pip = VENV_DIR / "Scripts" / "pip.exe"
    else:
        venv_python = VENV_DIR / "bin" / "python"
        venv_pip = VENV_DIR / "bin" / "pip"

    if not venv_python.exists():
        warn("Venv corrompido, recriando...")
        shutil.rmtree(VENV_DIR)
        run(f'"{sys.executable}" -m venv "{VENV_DIR}"')
        if not venv_python.exists():
            return False

    ok(f"Venv ativo: {venv_python}")
    return str(venv_python)


def step_deps(python_path=None):
    step(3, "Dependencias Python")
    py = python_path or sys.executable

    # Upgrade pip first
    info("Atualizando pip...")
    run(f'"{py}" -m pip install --upgrade pip', capture=True)

    if not REQ_FILE.exists():
        warn("requirements.txt nao encontrado, pulando deps")
        return

    info("Instalando dependencias do requirements.txt...")
    code, out, err = run(f'"{py}" -m pip install -r "{REQ_FILE}" --quiet', capture=True)
    if code == 0:
        ok("Todas as dependencias instaladas")
    else:
        warn(f"Algumas deps podem ter falhado: {err}")

    # Verify critical deps
    critical = ["requests", "pyyaml", "httpx", "websockets"]
    for pkg in critical:
        code, _, _ = run(f'"{py}" -c "import {pkg.replace(chr(45), chr(95))}"', capture=True)
        if code == 0:
            ok(f"  {pkg}")
        else:
            fail(f"  {pkg} falhou")


def step_sync_config():
    step(4, "Deploy de configuracao")
    oc_dir = Path.home() / ".config" / "opencode"
    oc_dir.mkdir(parents=True, exist_ok=True)
    agents_dir = oc_dir / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Render opencode.jsonc template
    template_file = CONFIG_DIR / "opencode.jsonc"
    if template_file.exists():
        up = str(Path.home()).replace("\\", "/")
        # Detect LLM model choice
        choice_file = CONFIG_DIR / ".llm-choice.json"
        llm_model = "opencode/deepseek-v4-flash-free"
        if choice_file.exists():
            try:
                with open(choice_file) as f:
                    llm_model = json.load(f).get("model", llm_model)
            except Exception:
                pass

        content = template_file.read_text(encoding="utf-8")
        content = content.replace("{{USERPROFILE}}", up).replace("{{LLM_MODEL}}", llm_model)
        target = oc_dir / "opencode.jsonc"
        target.write_text(content, encoding="utf-8")
        ok(f"opencode.jsonc -> {target} (model: {llm_model})")
    else:
        warn("config/opencode.jsonc template nao encontrado")

    # Deploy agents
    agents_src = CONFIG_DIR / "agents"
    if agents_src.exists():
        count = 0
        for f in agents_src.glob("*.md"):
            shutil.copy2(f, agents_dir / f.name)
            count += 1
        ok(f"{count} agent(s) deployado(s)")

    # Deploy fallback
    fb_src = CONFIG_DIR / "opencode-model-fallback.jsonc"
    if fb_src.exists():
        shutil.copy2(fb_src, oc_dir / "opencode-model-fallback.jsonc")
        ok("Model fallback deployado")


def step_sync_rules():
    step(5, "Sincronizar regras")
    sync_script = SCRIPTS_DIR / "sync_rules.py"
    if sync_script.exists():
        info("Rodando sync_rules.py update...")
        code, out, err = run(f'"{sys.executable}" "{sync_script}" update', capture=True)
        if code == 0:
            ok("Regras sincronizadas (3 camadas)")
        else:
            warn(f"Sync rules: {err or out}")
    else:
        warn("sync_rules.py nao encontrado")


def step_mcp_preflight():
    step(6, "Preflight tecnico")
    pf = SCRIPTS_DIR / "preflight_check.py"
    if pf.exists():
        info("Rodando preflight_check.py...")
        code, out, err = run(f'"{sys.executable}" "{pf}"', capture=True)
        output = out + err
        if "TODOS TESTES PASSARAM" in output or code == 0:
            ok("Preflight: PASS")
        else:
            warn("Preflight: verifique os logs acima")
    else:
        warn("preflight_check.py nao encontrado")


def step_boot():
    step(7, "Runtime boot")
    boot = SCRIPTS_DIR / "runtime_boot.py"
    if boot.exists():
        info("Rodando runtime_boot.py --check...")
        code, out, err = run(f'"{sys.executable}" "{boot}" --check', capture=True)
        output = out + err
        if "OK" in output or code == 0:
            ok("Bootloader: OK")
        else:
            warn(f"Boot: {err or out}")
    else:
        warn("runtime_boot.py nao encontrado")


def step_powershell_profile():
    step(8, "PowerShell profile")
    if not WIN:
        info("Pulando (nao e Windows)")
        return

    prof_dir = Path.home() / "Documents" / "WindowsPowerShell"
    prof_file = prof_dir / "profile.ps1"
    prof_dir.mkdir(parents=True, exist_ok=True)

    marker = "EcoSystemUmGrau"
    existing = ""
    if prof_file.exists():
        existing = prof_file.read_text(encoding="utf-8", errors="ignore")

    if marker in existing:
        ok("Profile ja configurado")
        return

    eco = str(ECO_DIR).replace("\\", "\\\\")
    additions = [
        f'',
        f'# EcoSystemUmGrau — Generated by install.py',
        f'$env:EcoSystemUmGrau = "{eco}"',
        f'function env-eco {{ ecosystem sync; python (join-path $env:EcoSystemUmGrau \'scripts\\runtime_boot.py\') }}',
        f'function env-sync {{ ecosystem sync }}',
        f'',
    ]
    with open(prof_file, "a", encoding="utf-8") as f:
        f.write("\n".join(additions))
    ok("Profile atualizado (env-eco, env-sync)")


def step_scheduled_task():
    step(9, "Scheduled task (Vigilante)")
    if not WIN:
        info("Pulando (nao e Windows)")
        return

    task_name = "EcoSystemVigilante"
    code, _, _ = run(f'schtasks /Query /TN "{task_name}"', capture=True)
    if code == 0:
        ok("Task ja existe")
        return

    info("Criando task Vigilante...")
    vigilante = SCRIPTS_DIR / "vigilante.ps1"
    if not vigilante.exists():
        warn("vigilante.ps1 nao encontrado")
        return

    cmd = (
        f'schtasks /Create /TN "{task_name}" '
        f'/TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File \\"{vigilante}\\"" '
        f'/SC ONLOGON /F'
    )
    code, _, _ = run(cmd, capture=True)
    if code == 0:
        ok("Task Vigilante criada")
    else:
        warn("Nao foi possivel criar a task (execute como admin)")


def step_validate():
    step(10, "Validacao final")
    checks = [
        ("Constituicao", CONFIG_DIR / "agents" / "00-system-rules.md"),
        ("AGENTS.md", ECO_DIR / "AGENTS.md"),
        ("memory_engine", SCRIPTS_DIR / "memory_engine.py"),
        ("runtime_boot", SCRIPTS_DIR / "runtime_boot.py"),
        ("preflight_check", SCRIPTS_DIR / "preflight_check.py"),
        ("persistencia", SCRIPTS_DIR / "persistencia.ps1"),
        ("sync_rules", SCRIPTS_DIR / "sync_rules.py"),
        ("requirements.txt", REQ_FILE),
    ]
    all_ok = True
    for name, path in checks:
        if path.exists():
            ok(name)
        else:
            fail(f"{name}: {path}")
            all_ok = False

    return all_ok


def print_summary(no_venv):
    py = sys.executable
    if not no_venv and VENV_DIR.exists():
        if WIN:
            py = str(VENV_DIR / "Scripts" / "python.exe")
        else:
            py = str(VENV_DIR / "bin" / "python")

    print(f"""
{CYAN}{'='*50}
  EcoSystemUmGrau — Instalacao concluida!
{'='*50}{RESET}

  Para ativar o ecossistema:
    {BOLD}python scripts/runtime_boot.py{RESET}

  Para sincronizar tudo:
    {BOLD}python scripts/sync_rules.py update{RESET}

  Para validar integridade:
    {BOLD}python scripts/preflight_check.py{RESET}

  Python do venv:
    {BOLD}{py}{RESET}

  Repo: https://github.com/idavidjunior/EcoSystemUmGrau
""")


# ─── Main ────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    no_venv = "--no-venv" in args
    check_only = "--check" in args
    sync_only = "--sync" in args

    print(f"{CYAN}{'='*50}")
    print(f"  EcoSystemUmGrau — Instalador / Bootstrap")
    print(f"{'='*50}{RESET}")

    # Always check basics
    check_python()
    check_git()
    check_node()

    if check_only:
        step_validate()
        return

    if sync_only:
        step_repo()
        step_sync_config()
        step_sync_rules()
        step_mcp_preflight()
        step_boot()
        return

    # Full install flow
    venv_python = step_venv(no_venv=no_venv)
    step_deps(python_path=venv_python)
    step_repo()
    step_sync_config()
    step_sync_rules()
    step_mcp_preflight()
    step_boot()
    step_powershell_profile()
    step_scheduled_task()

    all_ok = step_validate()
    print_summary(no_venv)

    if all_ok:
        print(f"{GREEN}Tudo pronto. O ecossistema esta operacional.{RESET}")
    else:
        print(f"{YELLOW}Instalacao concluida com avisos. Verifique os itens marcados.{RESET}")


if __name__ == "__main__":
    main()
