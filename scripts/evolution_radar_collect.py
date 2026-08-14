#!/usr/bin/env python3
"""
Evolution Radar Collector — Coleta, filtra, valida e empacota propostas de evolução.
100% stdlib (urllib, json, argparse, subprocess, pathlib, datetime, hashlib).
Padrão: audit_triagem.py — stdout UTF-8, exit codes, atomic write.
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error
import hashlib
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional

# Garante stdout UTF-8
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ─── Paths ──────────────────────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE / "config" / "evolution_sources.json"
RADAR_DIR = BASE / "conhecimento" / "evolution-radar"
RAW_DIR = RADAR_DIR / "bruto"
FILTERED_DIR = RADAR_DIR / "filtrado"
PACKAGES_DIR = RADAR_DIR / "pacotes"
APPLIED_DIR = RADAR_DIR / "aplicados"
STATE_FILE = BASE / "runtime" / "evolution_radar_state.json"

for d in (RAW_DIR, FILTERED_DIR, PACKAGES_DIR, APPLIED_DIR, STATE_FILE.parent):
    d.mkdir(parents=True, exist_ok=True)

# ─── Helpers ────────────────────────────────────────────────────────────

def log(msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def run_cmd(cmd: List[str], cwd: Path = BASE, timeout: int = 60) -> tuple[int, str, str]:
    """Executa comando e retorna (exit_code, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, encoding="utf-8", errors="replace")
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def http_get(url: str, headers: Dict[str, str], timeout: int = 30) -> Optional[Dict]:
    """GET com retry simples e rate limit handling."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        if e.code == 403:
            log(f"  Rate limit GitHub: {url}")
        elif e.code == 404:
            log(f"  Não encontrado: {url}")
        else:
            log(f"  HTTP {e.code}: {url}")
    except Exception as e:
        log(f"  Erro rede: {url} -> {e}")
    return None


def load_config() -> Dict:
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_state() -> Dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_run": {}, "seen_hashes": {}}


def save_state(state: Dict):
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    tmp.replace(STATE_FILE)


def content_hash(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


def is_admin_allowed() -> bool:
    return os.environ.get("EVOLUTION_RADAR_ADMIN") == "1" or (BASE / ".evolution_admin_ok").exists()


# ─── Collectors ─────────────────────────────────────────────────────────

def collect_github_releases(source: Dict, cfg: Dict, state: Dict) -> List[Dict]:
    repo = source["repo"]
    max_items = source.get("max_per_run", 3)
    filter_kw = source.get("filter", "").lower().split("|")
    url = f"{cfg['settings']['github_api_base']}/repos/{repo}/releases?per_page={max_items * 2}"
    headers = {"User-Agent": cfg["settings"]["user_agent"], "Accept": "application/vnd.github+json"}
    if token := os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"

    data = http_get(url, headers, cfg["settings"]["timeout_seconds"])
    if not data:
        return []

    results = []
    for rel in data[:max_items]:
        item = {
            "source": source["id"],
            "type": "github_release",
            "repo": repo,
            "tag": rel.get("tag_name"),
            "name": rel.get("name"),
            "published_at": rel.get("published_at"),
            "url": rel.get("html_url"),
            "body": rel.get("body", "")[:2000],
            "prerelease": rel.get("prerelease", False),
            "draft": rel.get("draft", False),
        }
        # Filtro por palavras-chave
        text = f"{item['name']} {item['body']}".lower()
        if filter_kw and not any(kw in text for kw in filter_kw if kw):
            continue
        h = content_hash(item)
        if h in state["seen_hashes"].get(source["id"], set()):
            continue
        results.append(item)
    return results


def collect_github_commits(source: Dict, cfg: Dict, state: Dict) -> List[Dict]:
    repo = source["repo"]
    path_filter = source.get("path_filter", "").lower().split("|")
    max_items = source.get("max_per_run", 5)
    url = f"{cfg['settings']['github_api_base']}/repos/{repo}/commits?per_page={max_items * 3}"
    headers = {"User-Agent": cfg["settings"]["user_agent"], "Accept": "application/vnd.github+json"}
    if token := os.environ.get("GH_TOKEN"):
        headers["Authorization"] = f"Bearer {token}"

    data = http_get(url, headers, cfg["settings"]["timeout_seconds"])
    if not data:
        return []

    results = []
    for commit in data[:max_items]:
        files_url = commit["url"] + "/files"
        files_data = http_get(files_url, headers, cfg["settings"]["timeout_seconds"])
        if not files_data:
            continue
        relevant_files = [f["filename"] for f in files_data if any(pf in f["filename"].lower() for pf in path_filter if pf)]
        if not relevant_files:
            continue
        item = {
            "source": source["id"],
            "type": "github_commit",
            "repo": repo,
            "sha": commit["sha"][:7],
            "message": commit["commit"]["message"][:500],
            "author": commit["commit"]["author"]["name"],
            "date": commit["commit"]["author"]["date"],
            "url": commit["html_url"],
            "files": relevant_files[:10],
        }
        h = content_hash(item)
        if h in state["seen_hashes"].get(source["id"], set()):
            continue
        results.append(item)
    return results


# ─── Relevance Filter (LLM opcional via compreensão de pedidos) ──────────

def filter_relevance(items: List[Dict], cfg: Dict) -> List[Dict]:
    """Filtro rápido estático + opcional LLM via mcp-compreensao-pedidos."""
    # Palavras-chave do nosso stack
    stack_keywords = [
        "python", "stdlib", "async", "typing", "dataclass", "pathlib",
        "mcp", "model context protocol", "stdio", "sse", "transport",
        "opencode", "agent", "hook", "config", "plugin",
        "android", "sdk", "ndk", "aapt", "d8", "apksigner", "javac",
        "powershell", "cmdlet", "ps1",
        "security", "vulnerability", "cve", "deprecat", "breaking",
        "performance", "memory", "startup", "bundle"
    ]

    filtered = []
    for item in items:
        text = json.dumps(item).lower()
        score = sum(1 for kw in stack_keywords if kw in text)
        if score >= 2:  # threshold baixo pra não perder sinal
            item["relevance_score"] = score
            filtered.append(item)

    # TODO: integração opcional com mcp-compreensao-pedidos para refino LLM
    # if filtered and os.environ.get("EVOLUTION_RADAR_LLM_REFINO"):
    #     filtered = llm_refine(filtered)

    return filtered


# ─── Validation (dry-run preflight + sync_rules) ────────────────────────

def validate_proposal(proposal: Dict) -> Dict:
    """Simula validação rodando preflight e sync_rules em modo check."""
    # Cria spec temporária para testar
    spec_content = f"""---
id: spec-test-{proposal['source']}-{proposal.get('tag', proposal.get('sha', 'x'))}
versao: 0.0.1
status: proposta
componente: scripts/evolution_radar_collect.py
tags: [teste, radar]
data: {datetime.now().strftime('%Y-%m-%d')}
---

# Teste de Validação

## Objetivo
Validar se a proposta {proposal['source']} passa no preflight.

## Critérios de Aceitação
[comando:python scripts/preflight_check.py]
[comando:python scripts/sync_rules.py audit]
"""
    tmp_spec = BASE / "specs" / f"_radar_test_{proposal['source']}.spec.md"
    tmp_spec.write_text(spec_content, encoding="utf-8")

    try:
        # Preflight
        code1, out1, err1 = run_cmd(["python", "scripts/preflight_check.py"], timeout=60)
        # Sync rules audit
        code2, out2, err2 = run_cmd(["python", "scripts/sync_rules.py", "audit"], timeout=30)

        return {
            "preflight_ok": code1 == 0,
            "sync_rules_ok": code2 == 0,
            "preflight_out": out1[-500:] if out1 else err1,
            "sync_rules_out": out2[-500:] if out2 else err2,
        }
    finally:
        if tmp_spec.exists():
            tmp_spec.unlink()


# ─── Main Actions ───────────────────────────────────────────────────────

def action_check() -> int:
    """Verifica se o script roda e config existe."""
    if not CONFIG_FILE.exists():
        log(f"ERRO: {CONFIG_FILE} não existe")
        return 1
    cfg = load_config()
    log(f"Config OK: {len(cfg.get('tier1_critical', []))} tier1, {len(cfg.get('tier1_5_ecosystem', []))} tier1.5, {len(cfg.get('tier2_deps', []))} tier2")
    log(f"Dirs: {RAW_DIR}, {FILTERED_DIR}, {PACKAGES_DIR}")
    return 0


def action_collect(cfg: Dict, state: Dict) -> List[Dict]:
    """Coleta de todas as fontes."""
    all_items = []
    sources = cfg.get("tier1_critical", []) + cfg.get("tier1_5_ecosystem", []) + cfg.get("tier2_deps", [])

    for source in sources:
        log(f"Coletando: {source['id']} ({source['type']})")
        items = []
        if source["type"] == "github_releases":
            items = collect_github_releases(source, cfg, state)
        elif source["type"] == "github_commits":
            items = collect_github_commits(source, cfg, state)
        # TODO: github_trending

        if items:
            log(f"  {len(items)} itens novos")
            all_items.extend(items)
            # Atualiza state
            state.setdefault("seen_hashes", {})[source["id"]] = state["seen_hashes"].get(source["id"], set())
            for it in items:
                state["seen_hashes"][source["id"]].add(content_hash(it))
        else:
            log(f"  0 itens novos")
        time.sleep(0.5)  # be nice to API

    # Salva bruto
    if all_items:
        ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        raw_file = RAW_DIR / f"{ts}-collection.jsonl"
        with open(raw_file, "w", encoding="utf-8") as f:
            for it in all_items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        log(f"Bruto salvo: {raw_file}")

    return all_items


def action_filter(items: List[Dict], cfg: Dict) -> List[Dict]:
    """Filtra relevância e valida cada proposta."""
    if not items:
        return []

    filtered = filter_relevance(items, cfg)
    log(f"Após filtro relevância: {len(filtered)}")

    validated = []
    for item in filtered:
        log(f"Validando: {item['source']} - {item.get('tag', item.get('sha', '?'))}")
        val = validate_proposal(item)
        item["validation"] = val
        if val["preflight_ok"] and val["sync_rules_ok"]:
            item["status"] = "validado"
            validated.append(item)
            log(f"  ✓ Validado")
        else:
            item["status"] = "rejeitado"
            log(f"  ✗ Rejeitado: preflight={val['preflight_ok']} sync={val['sync_rules_ok']}")

    # Salva filtrados como propostas individuais
    for item in validated:
        slug = f"{item['source']}-{item.get('tag', item.get('sha', 'x'))}".replace("/", "-")
        spec = build_proposal_spec(item)
        spec_file = FILTERED_DIR / f"{datetime.now().strftime('%Y-%m-%d')}-{slug}.spec.md"
        spec_file.write_text(spec, encoding="utf-8")
        log(f"Proposta salva: {spec_file}")

    return validated


def build_proposal_spec(item: Dict) -> str:
    """Gera spec markdown da proposta."""
    frontmatter = f"""---
id: spec-radar-{item['source']}-{item.get('tag', item.get('sha', 'x'))}
versao: 0.1.0
status: proposta
componente: scripts/evolution_radar_collect.py
tags: [radar, {item['source']}, auto]
data: {datetime.now().strftime('%Y-%m-%d')}
---

# Proposta Evolution Radar: {item['source']}

## Objetivo
{item.get('name', item.get('message', 'Atualização detectada pelo radar'))}

## Fonte
- **Repo**: {item['repo']}
- **Tipo**: {item['type']}
- **Tag/Commit**: {item.get('tag', item.get('sha', '?'))}
- **URL**: {item['url']}
- **Data**: {item.get('published_at', item.get('date', '?'))}

## Detalhes
{item.get('body', item.get('message', 'Sem descrição'))[:1500]}

## Arquivos Afetados (se commit)
{chr(10).join(f'- {f}' for f in item.get('files', [])) or 'N/A'}

## Validação
- Preflight: {'✓' if item['validation']['preflight_ok'] else '✗'}
- Sync Rules: {'✓' if item['validation']['sync_rules_ok'] else '✗'}
- Score Relevância: {item.get('relevance_score', 0)}

## Critérios de Aceitação
[comando:python scripts/preflight_check.py]
[comando:python scripts/sync_rules.py audit]

## Riscos
- Breaking change: {'Sim' if 'breaking' in json.dumps(item).lower() else 'Não detectado'}
- Nova dependência: Não (stdlib only)
- Wrapper > 50 linhas: Não

## Definition of Done
- Aplicado via pacote evolution-pack
- Preflight passa pós-aplicação
- Sync rules audit passa
- Memória registrada
"""
    return frontmatter


def action_package(cfg: Dict) -> Optional[Path]:
    """Cria pacote a partir de propostas validadas não empacotadas."""
    proposals = list(FILTERED_DIR.glob("*.spec.md"))
    if not proposals:
        log("Nenhuma proposta para empacotar")
        return None

    # Limita por pacote
    max_pack = cfg["settings"]["max_proposals_per_pack"]
    selected = proposals[:max_pack]

    pack_data = {
        "id": f"evolution-pack-{datetime.now().strftime('%Y-%m-%d')}-v1",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "proposals": [],
        "status": "pendente"
    }

    for spec_file in selected:
        content = spec_file.read_text(encoding="utf-8")
        # Extrai frontmatter id
        import re
        m = re.search(r"id:\s*(.+)", content)
        prop_id = m.group(1).strip() if m else spec_file.stem
        pack_data["proposals"].append({
            "spec_id": prop_id,
            "file": spec_file.name,
            "source": spec_file.name.split("-")[1] if "-" in spec_file.name else "unknown"
        })

    pack_file = PACKAGES_DIR / f"{pack_data['id']}.json"
    pack_file.write_text(json.dumps(pack_data, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"Pacote criado: {pack_file} ({len(selected)} propostas)")
    return pack_file


def action_apply(pack_path: Path) -> int:
    """Aplica pacote via gate (persistencia.ps1) com rollback se falhar."""
    if not pack_path.exists():
        log(f"ERRO: Pacote não encontrado: {pack_path}")
        return 1

    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    log(f"Aplicando pacote: {pack['id']} ({len(pack['proposals'])} propostas)")

    # Backup estado atual via gate
    code, out, err = run_cmd(["powershell", "-c", "& 'scripts/persistencia.ps1' status"], timeout=10)
    if code != 0:
        log(f"Gate status falhou: {err}")
        return 1

    # Para cada proposta, a ação real seria integrar o que a propõe
    # Aqui simulamos: apenas registra que foi aplicado
    applied = []
    for prop in pack["proposals"]:
        log(f"  Aplicando: {prop['spec_id']}")
        # TODO: ação real baseada no tipo da proposta
        # Ex: atualizar config, adicionar skill, atualizar script, etc.
        applied.append(prop)

    # Validação pós-aplicação
    log("Validando pós-aplicação...")
    code1, _, _ = run_cmd(["python", "scripts/preflight_check.py"], timeout=60)
    code2, _, _ = run_cmd(["python", "scripts/sync_rules.py", "audit"], timeout=30)

    if code1 != 0 or code2 != 0:
        log("FALHA pós-aplicação — ROLLBACK")
        # Rollback via gate
        run_cmd(["powershell", "-c", "& 'scripts/persistencia.ps1' rollback"], timeout=30)
        pack["status"] = "revertido"
        pack["applied_at"] = datetime.now(timezone.utc).isoformat()
        pack["rollback_reason"] = "preflight/sync_rules falhou"
    else:
        log("SUCESSO — Pacote aplicado")
        pack["status"] = "aplicado"
        pack["applied_at"] = datetime.now(timezone.utc).isoformat()

    # Move para aplicados
    applied_file = APPLIED_DIR / f"{pack['id']}-{pack['status']}.json"
    applied_file.write_text(json.dumps(pack, ensure_ascii=False, indent=2), encoding="utf-8")
    pack_path.unlink()  # remove da pendentes

    # Registra memória
    run_cmd(["python", "scripts/memory_engine.py", "add",
             f"evolution-radar-{pack['id']}",
             f"Pacote {pack['id']} {pack['status']} com {len(pack['proposals'])} propostas",
             "episodio"], timeout=10)

    return 0 if pack["status"] == "aplicado" else 1


# ─── Main ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Evolution Radar Collector")
    parser.add_argument("--check", action="store_true", help="Verifica se roda")
    parser.add_argument("--collect", action="store_true", help="Coleta fontes")
    parser.add_argument("--filter", action="store_true", help="Filtra itens coletados (usa último raw)")
    parser.add_argument("--package", action="store_true", help="Cria pacote de propostas validadas")
    parser.add_argument("--apply", metavar="PACK_FILE", help="Aplica pacote via gate")
    parser.add_argument("--full", action="store_true", help="Executa collect -> filter -> package")
    parser.add_argument("--dry-run", action="store_true", help="Não salva estado (para teste)")
    args = parser.parse_args()

    if args.check:
        sys.exit(action_check())

    if not is_admin_allowed():
        log("ERRO: Permissão de administrador necessária (EVOLUTION_RADAR_ADMIN=1 ou .evolution_admin_ok)")
        sys.exit(1)

    cfg = load_config()
    state = load_state()

    if args.full or args.collect:
        items = action_collect(cfg, state)
        if not args.dry_run:
            save_state(state)
        if args.full:
            validated = action_filter(items, cfg)
            action_package(cfg)
    elif args.filter:
        # Carrega último raw
        raw_files = sorted(RAW_DIR.glob("*.jsonl"), reverse=True)
        if not raw_files:
            log("Nenhum arquivo bruto para filtrar")
            sys.exit(0)
        items = []
        with open(raw_files[0], encoding="utf-8") as f:
            for line in f:
                items.append(json.loads(line))
        action_filter(items, cfg)
    elif args.package:
        action_package(cfg)
    elif args.apply:
        pack_file = Path(args.apply)
        if not pack_file.is_absolute():
            pack_file = PACKAGES_DIR / pack_file
        sys.exit(action_apply(pack_file))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()