#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
architecture_integrity_monitor.py — Monitor de Integridade Arquitetural
======================================================================

Verifica a saude estrutural completa do EcoSystemUmGrau em 5 camadas:

  1. ESTRUTURA: arquivos criticos existem e sao validos
  2. SINCRONIZACAO: dados consistentes entre camadas (regras, config, inventario)
  3. SERVICOS: processos essenciais estao rodando
  4. FLUXO DE DADOS: cadeias de dados estao vivas (grafo, memoria, aprendizados)
  5. LIMPEZA: crescimento controlado (logs, checkpoints, snapshots)

Cada check retorna: PASS / WARN / FAIL com detalhes.

Uso:
  python scripts/architecture_integrity_monitor.py           # executa todos os checks
  python scripts/architecture_integrity_monitor.py --json   # saida JSON
  python scripts/architecture_integrity_monitor.py --fix    # tenta corrigir automaticamente
"""

import json
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

BASE = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = BASE / "scripts"
CONFIG_DIR = BASE / "config"
KNOWLEDGE_DIR = BASE / "conhecimento"
RUNTIME_DIR = BASE / "runtime"
CONNECTIVITY_DIR = BASE / "connectivity"
DOCS_DIR = BASE / "docs"

# ─── Utility ───────────────────────────────────────────────────────────────

class Check:
    def __init__(self, layer: str, name: str, status: str, detail: str = "", fixable: bool = False):
        self.layer = layer
        self.name = name
        self.status = status  # PASS / WARN / FAIL
        self.detail = detail
        self.fixable = fixable

    def to_dict(self):
        return {"layer": self.layer, "name": self.name, "status": self.status, "detail": self.detail, "fixable": self.fixable}

    def __repr__(self):
        icon = {"PASS": "+", "WARN": "!", "FAIL": "X"}[self.status]
        return f"[{icon}] {self.name}: {self.detail}" if self.detail else f"[{icon}] {self.name}"


def _exists(p: Path) -> bool:
    return p.exists() and p.is_file()

def _dir_count(p: Path, pattern: str) -> int:
    return len(list(p.glob(pattern))) if p.exists() else 0

def _file_age_hours(p: Path) -> float:
    if not p.exists():
        return float("inf")
    return (datetime.now().timestamp() - p.stat().st_mtime) / 3600

def _file_size_mb(p: Path) -> float:
    return p.stat().st_size / (1024 * 1024) if p.exists() else 0

def _read_json(p: Path) -> Any:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None

def _run_python(script: str, args: list = None, timeout: int = 30) -> tuple:
    """Returns (returncode, stdout, stderr)."""
    cmd = [sys.executable, str(SCRIPTS_DIR / script)] + (args or [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=str(BASE))
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return -1, "", str(e)

def _check_port(port: int) -> bool:
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex(("127.0.0.1", port))
        s.close()
        return result == 0
    except Exception:
        return False


# ─── Layer 1: Structural Integrity ─────────────────────────────────────────

def check_structure() -> list[Check]:
    checks = []

    # Critical config files
    critical_files = [
        (CONFIG_DIR / "opencode.jsonc", "Config template"),
        (CONFIG_DIR / "opencode.jsonc.bak", "Config backup"),
        (CONFIG_DIR / "inventario_estruturas.json", "Structure inventory"),
        (CONFIG_DIR / "persistencia.json", "Persistence config"),
        (CONFIG_DIR / "agents" / "00-system-rules.md", "Constitution"),
        (CONFIG_DIR / "agents" / "00-maestro.md", "Maestro agent"),
    ]
    for path, label in critical_files:
        ok = _exists(path)
        checks.append(Check("estrutura", f"Arquivo critico: {label}", "PASS" if ok else "FAIL", str(path.relative_to(BASE)), fixable=not ok))

    # Agent files
    agent_count = _dir_count(CONFIG_DIR / "agents", "*.md")
    checks.append(Check("estrutura", "Agentes configurados", "PASS" if agent_count >= 15 else "WARN" if agent_count >= 10 else "FAIL", f"{agent_count} agentes em config/agents/"))

    # Memory files
    memory_files = [
        (KNOWLEDGE_DIR / "memoria" / "memories.json", "Memory store"),
        (KNOWLEDGE_DIR / "memoria" / "index.json", "Tag index"),
        (KNOWLEDGE_DIR / "memoria" / "tfidf_matrix.npz", "TF-IDF matrix"),
        (KNOWLEDGE_DIR / "memoria" / "dense_matrix.npy", "Dense matrix"),
    ]
    for path, label in memory_files:
        ok = _exists(path)
        checks.append(Check("estrutura", f"Memoria: {label}", "PASS" if ok else "WARN", str(path.relative_to(BASE))))

    # Knowledge vault
    vault_count = _dir_count(KNOWLEDGE_DIR / "notas" / "**" / "**", "*.md") + _dir_count(KNOWLEDGE_DIR / "notas" / "**", "*.md")
    # Deduplicate by counting unique files
    if (KNOWLEDGE_DIR / "notas").exists():
        vault_count = len(set((KNOWLEDGE_DIR / "notas").rglob("*.md")))
    checks.append(Check("estrutura", "Vault de conhecimento", "PASS" if vault_count >= 100 else "WARN" if vault_count >= 50 else "FAIL", f"{vault_count} notas markdown"))

    # Critical scripts
    critical_scripts = [
        "vigilante.ps1", "watchdog.ps1", "persistencia.ps1", "sync_rules.py",
        "preflight_check.py", "memory_engine.py", "runtime_boot.py",
        "generate-graph-html.py", "widget_grafo.py",
    ]
    missing_scripts = [s for s in critical_scripts if not _exists(SCRIPTS_DIR / s)]
    checks.append(Check("estrutura", "Scripts criticos", "PASS" if not missing_scripts else "FAIL", f"{len(critical_scripts) - len(missing_scripts)}/{len(critical_scripts)} presentes", fixable=bool(missing_scripts)))

    # Runtime state
    state = _read_json(RUNTIME_DIR / "state.json")
    checks.append(Check("estrutura", "Runtime state", "PASS" if state else "FAIL", "state.json valido" if state else "state.json ausente ou corrompido"))

    # Deployed config
    deployed = Path.home() / ".config" / "opencode" / "opencode.jsonc"
    checks.append(Check("estrutura", "Config deployed", "PASS" if _exists(deployed) else "WARN", str(deployed)))

    # Deployed agents
    deployed_agents = Path.home() / ".config" / "opencode" / "agents"
    deployed_count = _dir_count(deployed_agents, "*.md")
    checks.append(Check("estrutura", "Agentes deployed", "PASS" if deployed_count >= 15 else "WARN" if deployed_count >= 10 else "FAIL", f"{deployed_count} agentes em ~/.config/opencode/agents/"))

    return checks


# ─── Layer 2: Synchronization Integrity ────────────────────────────────────

def check_sync() -> list[Check]:
    checks = []

    # Rules sync (3 layers)
    rc, out, err = _run_python("sync_rules.py", ["check"], timeout=15)
    if rc == 0:
        checks.append(Check("sincronizacao", "Regras 3 camadas", "PASS", out[:200] if out else "Consistentes"))
    else:
        detail = err[:200] if err else out[:200]
        checks.append(Check("sincronizacao", "Regras 3 camadas", "WARN" if "divergencia" in detail.lower() else "FAIL", detail, fixable=True))

    # Inventory vs actual files
    inv = _read_json(CONFIG_DIR / "inventario_estruturas.json")
    if inv and isinstance(inv, dict):
        all_entries = []
        for key, val in inv.items():
            if isinstance(val, list):
                all_entries.extend([e for e in val if isinstance(e, dict) and e.get("arquivo")])
        missing = [e for e in all_entries if not _exists(BASE / e["arquivo"])]
        total = len(all_entries)
        found = total - len(missing)
        status = "PASS" if not missing else "WARN" if len(missing) <= 3 else "FAIL"
        detail = f"{found}/{total} estruturas no inventario existem no disco"
        if missing:
            detail += f" | ausentes: {[e.get('arquivo') for e in missing[:5]]}"
        checks.append(Check("sincronizacao", "Inventario vs disco", status, detail))
    else:
        checks.append(Check("sincronizacao", "Inventario vs disco", "FAIL", "inventario_estruturas.json invalido"))

    # Config template vs deployed structure
    template = _read_json(CONFIG_DIR / "opencode.jsonc")
    deployed_path = Path.home() / ".config" / "opencode" / "opencode.jsonc"
    deployed = _read_json(deployed_path)
    if template and deployed:
        template_keys = set(template.keys()) if isinstance(template, dict) else set()
        deployed_keys = set(deployed.keys()) if isinstance(deployed, dict) else set()
        missing_keys = template_keys - deployed_keys
        extra_keys = deployed_keys - template_keys
        if not missing_keys and not extra_keys:
            checks.append(Check("sincronizacao", "Config template vs deployed", "PASS", "Chaves consistentes"))
        else:
            checks.append(Check("sincronizacao", "Config template vs deployed", "WARN",
                               f"missing={list(missing_keys)[:5]} extra={list(extra_keys)[:5]}"))
    else:
        checks.append(Check("sincronizacao", "Config template vs deployed", "WARN", "Nao foi possivel comparar"))

    # Constitution vs AGENTS.md: check that rule titles from Constitution exist in AGENTS.md
    constitution = (CONFIG_DIR / "agents" / "00-system-rules.md").read_text(encoding="utf-8") if (CONFIG_DIR / "agents" / "00-system-rules.md").exists() else ""
    agents_md = (BASE / "AGENTS.md").read_text(encoding="utf-8") if (BASE / "AGENTS.md").exists() else ""
    if constitution and agents_md:
        # Extract rule titles (lines starting with # )
        import re
        rule_titles = re.findall(r'^# (.+)', constitution, re.MULTILINE)
        missing_rules = [t for t in rule_titles if t not in agents_md]
        if not missing_rules:
            checks.append(Check("sincronizacao", "Constitution vs AGENTS.md", "PASS", f"{len(rule_titles)} regras presentes"))
        else:
            checks.append(Check("sincronizacao", "Constitution vs AGENTS.md", "FAIL",
                               f"{len(missing_rules)} regras ausentes: {missing_rules[:3]}", fixable=True))
    else:
        checks.append(Check("sincronizacao", "Constitution vs AGENTS.md", "WARN", "Arquivos ausentes"))

    # Memory tags health
    memories = _read_json(KNOWLEDGE_DIR / "memoria" / "memories.json")
    if memories:
        no_tags = sum(1 for m in memories if not m.get("tags"))
        checks.append(Check("sincronizacao", "Memorias com tags", "PASS" if no_tags == 0 else "WARN",
                           f"{len(memories) - no_tags}/{len(memories)} com tags", fixable=no_tags > 0))
    else:
        checks.append(Check("sincronizacao", "Memorias com tags", "FAIL", "memories.json invalido"))

    return checks


# ─── Layer 3: Service Health ───────────────────────────────────────────────

def check_services() -> list[Check]:
    checks = []

    # Bridge (port 8765)
    bridge_up = _check_port(8765)
    checks.append(Check("servicos", "Bridge Jarvis (8765)", "PASS" if bridge_up else "WARN", "Online" if bridge_up else "Offline"))

    # Serve (port 8767)
    serve_up = _check_port(8767)
    checks.append(Check("servicos", "OpenCode Serve (8767)", "PASS" if serve_up else "WARN", "Online" if serve_up else "Offline"))

    # Vigilante process
    vigilante_pid = Path.home() / ".vigilante.pid"
    if vigilante_pid.exists():
        try:
            pid = int(vigilante_pid.read_text().strip())
            import ctypes
            alive = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid) is not None
            checks.append(Check("servicos", "Vigilante", "PASS" if alive else "WARN", f"PID {pid} {'ativo' if alive else 'morto'}"))
        except Exception:
            checks.append(Check("servicos", "Vigilante", "WARN", "PID file existe mas nao verificavel"))
    else:
        checks.append(Check("servicos", "Vigilante", "WARN", "PID file ausente"))

    # System guardian
    guardian_pid = SCRIPTS_DIR / "guardian.pid"
    if guardian_pid.exists():
        try:
            pid = int(guardian_pid.read_text().strip())
            import ctypes
            alive = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid) is not None
            checks.append(Check("servicos", "System Guardian", "PASS" if alive else "WARN", f"PID {pid} {'ativo' if alive else 'morto'}"))
        except Exception:
            checks.append(Check("servicos", "System Guardian", "WARN", "PID file existe mas nao verificavel"))
    else:
        checks.append(Check("servicos", "System Guardian", "WARN", "Guardian nao iniciado (sera iniciado pelo vigilante)"))

    # Desktop guardian (scheduled task)
    try:
        r = subprocess.run(["schtasks", "/query", "/tn", "OpenCode-Desktop-Guardian", "/fo", "CSV"],
                          capture_output=True, text=True, timeout=10)
        active = "Pronto" in r.stdout or "Running" in r.stdout
        checks.append(Check("servicos", "Desktop Guardian (scheduled)", "PASS" if active else "WARN", "Ativo" if active else "Inativo"))
    except Exception:
        checks.append(Check("servicos", "Desktop Guardian (scheduled)", "WARN", "Nao foi possivel verificar scheduled task"))

    # Tailscale
    try:
        r = subprocess.run(["tailscale", "status"], capture_output=True, text=True, timeout=10)
        online = "online" in r.stdout.lower() or "100." in r.stdout
        checks.append(Check("servicos", "Tailscale", "PASS" if online else "WARN", "Conectado" if online else "Desconectado"))
    except Exception:
        checks.append(Check("servicos", "Tailscale", "WARN", "Nao foi possivel verificar"))

    return checks


# ─── Layer 4: Data Flow Integrity ──────────────────────────────────────────

def check_dataflow() -> list[Check]:
    checks = []

    # Graph generation
    grafo = DOCS_DIR / "grafo.html"
    age = _file_age_hours(grafo)
    if age < 24:
        checks.append(Check("fluxo", "Grafo do conhecimento", "PASS", f"Gerado ha {age:.1f}h"))
    elif age < 72:
        checks.append(Check("fluxo", "Grafo do conhecimento", "WARN", f"Gerado ha {age:.1f}h (atualizar)"))
    else:
        checks.append(Check("fluxo", "Grafo do conhecimento", "FAIL", f"Gerado ha {age:.1f}h (desatualizado)"))

    # Graph can regenerate
    rc, out, err = _run_python("generate-graph-html.py", [str(DOCS_DIR / "grafo_test_integrity.html")], timeout=60)
    if rc == 0:
        checks.append(Check("fluxo", "Geracao do grafo", "PASS", "Geracao OK"))
        # Cleanup test file
        test_file = DOCS_DIR / "grafo_test_integrity.html"
        if test_file.exists():
            test_file.unlink()
    else:
        checks.append(Check("fluxo", "Geracao do grafo", "FAIL", f"Falha: {err[:200]}", fixable=True))

    # Learning flow: recent aprendizados
    aprendizados = sorted((KNOWLEDGE_DIR / "aprendizados").glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True) if (KNOWLEDGE_DIR / "aprendizados").exists() else []
    if aprendizados:
        last_age = _file_age_hours(aprendizados[0])
        checks.append(Check("fluxo", "Fluxo de aprendizados", "PASS" if last_age < 48 else "WARN",
                           f"{len(aprendizados)} aprendizados, ultimo ha {last_age:.1f}h"))
    else:
        checks.append(Check("fluxo", "Fluxo de aprendizados", "WARN", "Nenhum aprendizado encontrado"))

    # Session logging
    sessions_dir = KNOWLEDGE_DIR / "memoria" / "sessions"
    if sessions_dir.exists():
        sessions = sorted(sessions_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
        if sessions:
            last_age = _file_age_hours(sessions[0])
            checks.append(Check("fluxo", "Session logging", "PASS" if last_age < 72 else "WARN",
                               f"{len(sessions)} sessoes, ultima ha {last_age:.1f}h"))
        else:
            checks.append(Check("fluxo", "Session logging", "WARN", "Nenhuma sessao registrada"))
    else:
        checks.append(Check("fluxo", "Session logging", "WARN", "Diretorio sessions/ inexistente"))

    # Memory index freshness
    tfidf_meta = KNOWLEDGE_DIR / "memoria" / "tfidf_meta.json"
    if tfidf_meta.exists():
        meta = _read_json(tfidf_meta)
        if meta and "last_reindex" in meta:
            try:
                last = datetime.fromisoformat(meta["last_reindex"])
                age_h = (datetime.now() - last).total_seconds() / 3600
                checks.append(Check("fluxo", "Indice semantico", "PASS" if age_h < 48 else "WARN", f"Ultima reindexacao ha {age_h:.1f}h"))
            except Exception:
                checks.append(Check("fluxo", "Indice semantico", "WARN", "Metadata incompleta"))
        else:
            checks.append(Check("fluxo", "Indice semantico", "WARN", "tfidf_meta.json sem last_reindex"))
    else:
        checks.append(Check("fluxo", "Indice semantico", "WARN", "tfidf_meta.json ausente"))

    # Bridge health chain
    health_dir = CONNECTIVITY_DIR / "bridge" / "health"
    if health_dir.exists():
        health_files = sorted(health_dir.glob("health_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        if health_files:
            last_age = _file_age_hours(health_files[0])
            checks.append(Check("fluxo", "Bridge health chain", "PASS" if last_age < 4 else "WARN",
                               f"{len(health_files)} registros, ultimo ha {last_age:.1f}h"))
        else:
            checks.append(Check("fluxo", "Bridge health chain", "WARN", "Nenhum health check registrado"))
    else:
        checks.append(Check("fluxo", "Bridge health chain", "WARN", "Diretorio health/ inexistente"))

    # Checkpoint chain
    checkpoints_dir = RUNTIME_DIR / "checkpoints"
    if checkpoints_dir.exists():
        cps = list(checkpoints_dir.glob("*.json"))
        if cps:
            last = max(cps, key=lambda p: p.stat().st_mtime)
            last_age = _file_age_hours(last)
            checks.append(Check("fluxo", "Checkpoint chain", "PASS" if last_age < 48 else "WARN",
                               f"{len(cps)} checkpoints, ultimo ha {last_age:.1f}h"))
        else:
            checks.append(Check("fluxo", "Checkpoint chain", "WARN", "Nenhum checkpoint"))
    else:
        checks.append(Check("fluxo", "Checkpoint chain", "WARN", "Diretorio checkpoints/ inexistente"))

    return checks


# ─── Layer 5: Cleanup Health ───────────────────────────────────────────────

def check_cleanup() -> list[Check]:
    checks = []

    # Script logs
    log_patterns = [
        (SCRIPTS_DIR / "watchdog_log.txt", "Watchdog log", 2.0),
        (SCRIPTS_DIR / "opencode_desktop_guardian_log.txt", "Guardian log", 2.0),
        (SCRIPTS_DIR / "guardian_log.txt", "System guardian log", 2.0),
        (SCRIPTS_DIR / "bridge_log.txt", "Bridge log", 2.0),
    ]
    for path, label, max_mb in log_patterns:
        if _exists(path):
            size = _file_size_mb(path)
            status = "PASS" if size < max_mb * 0.8 else "WARN" if size < max_mb else "FAIL"
            checks.append(Check("limpeza", label, status, f"{size:.2f} MB (max {max_mb} MB)"))
        else:
            checks.append(Check("limpeza", label, "PASS", "Inexistente (ok)"))

    # Checkpoints count
    cps_dir = RUNTIME_DIR / "checkpoints"
    if cps_dir.exists():
        count = len(list(cps_dir.glob("*.json")))
        checks.append(Check("limpeza", "Checkpoints", "PASS" if count <= 30 else "WARN" if count <= 50 else "FAIL",
                           f"{count} arquivos (max 30)"))
    else:
        checks.append(Check("limpeza", "Checkpoints", "PASS", "Diretorio inexistente"))

    # Health snapshots
    health_dir = CONNECTIVITY_DIR / "bridge" / "health"
    if health_dir.exists():
        count = len(list(health_dir.glob("health_*.json")))
        checks.append(Check("limpeza", "Health snapshots", "PASS" if count <= 50 else "WARN" if count <= 100 else "FAIL",
                           f"{count} arquivos (max 50)"))
    else:
        checks.append(Check("limpeza", "Health snapshots", "PASS", "Diretorio inexistente"))

    # Radar raw
    radar_dir = KNOWLEDGE_DIR / "evolution-radar" / "bruto"
    if radar_dir.exists():
        count = len(list(radar_dir.glob("*.jsonl")))
        checks.append(Check("limpeza", "Radar raw", "PASS" if count <= 5 else "WARN" if count <= 10 else "FAIL",
                           f"{count} arquivos (max 5)"))
    else:
        checks.append(Check("limpeza", "Radar raw", "PASS", "Diretorio inexistente"))

    # State backups
    backups = list(RUNTIME_DIR.glob("state.json.bak.*"))
    checks.append(Check("limpeza", "State backups", "PASS" if len(backups) <= 10 else "WARN",
                       f"{len(backups)} backups (max 10)"))

    # Total logs size in scripts/
    total_log_mb = sum(_file_size_mb(f) for f in SCRIPTS_DIR.glob("*log*") if f.is_file())
    checks.append(Check("limpeza", "Total logs scripts/", "PASS" if total_log_mb < 10 else "WARN" if total_log_mb < 20 else "FAIL",
                       f"{total_log_mb:.2f} MB"))

    # Knowledge graph backups
    graph_dir = KNOWLEDGE_DIR / "grafo"
    if graph_dir.exists():
        count = len(list(graph_dir.glob("knowledge_graph_*.json")))
        checks.append(Check("limpeza", "Knowledge graph backups", "PASS" if count <= 2 else "WARN",
                           f"{count} backups (max 2)"))
    else:
        checks.append(Check("limpeza", "Knowledge graph backups", "PASS", "Diretorio inexistente"))

    # Session files
    sessions_dir = KNOWLEDGE_DIR / "memoria" / "sessions"
    if sessions_dir.exists():
        count = len(list(sessions_dir.glob("*.jsonl")))
        checks.append(Check("limpeza", "Session files", "PASS" if count <= 30 else "WARN" if count <= 60 else "FAIL",
                           f"{count} arquivos (max 30)"))
    else:
        checks.append(Check("limpeza", "Session files", "PASS", "Diretorio inexistente"))

    # TTS cache
    tts_cache = RUNTIME_DIR / "tts_cache"
    if tts_cache.exists():
        count = len(list(tts_cache.glob("*.mp3")))
        total_mb = sum(_file_size_mb(f) for f in tts_cache.glob("*.mp3"))
        checks.append(Check("limpeza", "TTS cache", "PASS" if total_mb < 50 else "WARN" if total_mb < 100 else "FAIL",
                           f"{count} arquivos, {total_mb:.2f} MB"))
    else:
        checks.append(Check("limpeza", "TTS cache", "PASS", "Diretorio inexistente"))

    return checks


# ─── Fix Layer ─────────────────────────────────────────────────────────────

def auto_fix(checks: list[Check]) -> list[str]:
    fixes = []

    for c in checks:
        if not c.fixable or c.status == "PASS":
            continue

        if c.name == "Regras 3 camadas":
            rc, out, err = _run_python("sync_rules.py", ["update"], timeout=15)
            if rc == 0:
                fixes.append(f"Corrigido: {c.name} via sync_rules.py update")

        elif c.name == "Blocos RULES:START identicos":
            rc, out, err = _run_python("sync_rules.py", ["update"], timeout=15)
            if rc == 0:
                fixes.append(f"Corrigido: {c.name} via sync_rules.py update")

        elif c.name == "Memorias com tags":
            rc, out, err = _run_python("retag_memories.py", [], timeout=30)
            if rc == 0:
                fixes.append(f"Corrigido: {c.name} via retag_memories.py")

        elif c.name == "Config deployed":
            rc, out, err = _run_python("deploy-config.py", [], timeout=15)
            if rc == 0:
                fixes.append(f"Corrigido: {c.name} via deploy-config.py")

        elif c.name == "Grafo do conhecimento":
            rc, out, err = _run_python("generate-graph-html.py", [str(DOCS_DIR / "grafo.html")], timeout=60)
            if rc == 0:
                fixes.append(f"Corrigido: {c.name} via generate-graph-html.py")

        elif c.name == "Geracao do grafo":
            rc, out, err = _run_python("generate-graph-html.py", [str(DOCS_DIR / "grafo.html")], timeout=60)
            if rc == 0:
                fixes.append(f"Corrigido: {c.name} via generate-graph-html.py")

    return fixes


# ─── Main ──────────────────────────────────────────────────────────────────

def run_all(fix: bool = False) -> dict:
    all_checks = []
    all_checks.extend(check_structure())
    all_checks.extend(check_sync())
    all_checks.extend(check_services())
    all_checks.extend(check_dataflow())
    all_checks.extend(check_cleanup())

    fixes = auto_fix(all_checks) if fix else []

    summary = {
        "timestamp": datetime.now().isoformat(),
        "total": len(all_checks),
        "pass": sum(1 for c in all_checks if c.status == "PASS"),
        "warn": sum(1 for c in all_checks if c.status == "WARN"),
        "fail": sum(1 for c in all_checks if c.status == "FAIL"),
        "fixes_applied": len(fixes),
        "layers": {},
    }

    # Group by layer
    for c in all_checks:
        if c.layer not in summary["layers"]:
            summary["layers"][c.layer] = {"pass": 0, "warn": 0, "fail": 0, "checks": []}
        summary["layers"][c.layer][c.status.lower()] += 1
        summary["layers"][c.layer]["checks"].append(c.to_dict())

    return {"summary": summary, "checks": [c.to_dict() for c in all_checks], "fixes": fixes}


def print_report(result: dict):
    s = result["summary"]
    print(f"\n{'='*70}")
    print(f"  MONITOR DE INTEGRIDADE ARQUITETURAL — EcoSystemUmGrau")
    print(f"  {s['timestamp']}")
    print(f"{'='*70}")
    print(f"\n  RESUMO: {s['total']} checks | PASS: {s['pass']} | WARN: {s['warn']} | FAIL: {s['fail']}")
    if s["fixes_applied"] > 0:
        print(f"  CORRECOES: {s['fixes_applied']} aplicadas")
    print()

    layer_names = {"estrutura": "1. ESTRUTURA", "sincronizacao": "2. SINCRONIZACAO",
                   "servicos": "3. SERVICOS", "fluxo": "4. FLUXO DE DADOS", "limpeza": "5. LIMPEZA"}

    for layer_key, layer_name in layer_names.items():
        if layer_key not in s["layers"]:
            continue
        layer = s["layers"][layer_key]
        total = layer["pass"] + layer["warn"] + layer["fail"]
        print(f"  {layer_name} ({layer['pass']}/{total} pass)")
        for c in layer["checks"]:
            icon = {"PASS": "+", "WARN": "!", "FAIL": "X"}[c["status"]]
            print(f"    [{icon}] {c['name']}: {c['detail']}")
        print()

    if result["fixes"]:
        print(f"  CORRECOES APLICADAS:")
        for f in result["fixes"]:
            print(f"    + {f}")
        print()

    # Overall health
    if s["fail"] == 0 and s["warn"] <= 3:
        print(f"  VEREDICTO: ECOSSISTEMA SAUDAVEL")
    elif s["fail"] <= 2:
        print(f"  VEREDICTO: ECOSSISTEMA COM PROBLEMAS MENORES ({s['fail']} fail, {s['warn']} warn)")
    else:
        print(f"  VEREDICTO: ECOSSISTEMA COM PROBLEMAS ({s['fail']} fail, {s['warn']} warn)")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Monitor de integridade arquitetural")
    parser.add_argument("--json", action="store_true", help="Saida JSON")
    parser.add_argument("--fix", action="store_true", help="Tenta corrigir problemas automaticamente")
    args = parser.parse_args()

    result = run_all(fix=args.fix)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_report(result)

    # Exit code: 0=pass, 1=warn, 2=fail
    if result["summary"]["fail"] > 0:
        sys.exit(2)
    elif result["summary"]["warn"] > 3:
        sys.exit(1)
    else:
        sys.exit(0)
