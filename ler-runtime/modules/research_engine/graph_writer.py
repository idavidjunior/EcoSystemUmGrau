"""GraphWriter — persiste relatório no vault Obsidian e no Knowledge Graph."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, Any

from .models import ResearchReport

log = logging.getLogger("research.graph_writer")

DEFAULT_VAULT = r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\conhecimento"
DEFAULT_KG = r"C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau\ler-runtime\knowledge\knowledge_graph.json"


def persist(report: ResearchReport, markdown: str,
            vault_path: str = DEFAULT_VAULT, kg_path: str = DEFAULT_KG) -> bool:
    """Persiste relatório no vault e no Knowledge Graph.

    Returns:
        True se pelo menos uma persistência foi bem-sucedida
    """
    ok_vault = False
    ok_kg = False

    # 1. Salva Markdown no vault
    try:
        _save_to_vault(report, markdown, vault_path)
        ok_vault = True
    except Exception as e:
        log.warning("GraphWriter: falha ao salvar no vault (%s)", e)

    # 2. Registra no Knowledge Graph
    try:
        _register_in_kg(report, kg_path)
        ok_kg = True
    except Exception as e:
        log.warning("GraphWriter: falha ao registrar no KG (%s)", e)

    # 3. Busca notas relacionadas para links bidirecionais
    try:
        _find_related_notes(report, vault_path)
    except Exception as e:
        log.debug("GraphWriter: busca de notas relacionadas falhou (%s)", e)

    success = ok_vault or ok_kg
    if success:
        log.info("GraphWriter: persistido (vault=%s, kg=%s)", ok_vault, ok_kg)
    else:
        log.error("GraphWriter: falha em todas as persistências")
    return success


def _save_to_vault(report: ResearchReport, markdown: str, vault_path: str):
    """Salva Markdown como nota na pasta Research do vault."""
    research_dir = os.path.join(vault_path, "Research")
    os.makedirs(research_dir, exist_ok=True)

    safe_name = re.sub(r'[^\w\s-]', '', report.theme).strip().replace(' ', '-')
    safe_name = safe_name[:80]  # limita tamanho
    filename = f"{safe_name}.md"

    filepath = os.path.join(research_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown)

    log.info("  Vault: %s", filepath)


def _register_in_kg(report: ResearchReport, kg_path: str):
    """Registra entrada no Knowledge Graph."""
    kg = {}
    if os.path.exists(kg_path):
        with open(kg_path, 'r', encoding='utf-8', errors='replace') as f:
            kg = json.load(f)

    # Garante seção 'research'
    if "research" not in kg:
        kg["research"] = []

    entry_id = f"research_{int(__import__('time').time())}"
    entry = {
        "id": entry_id,
        "type": "research",
        "theme": report.theme,
        "objective": report.objective,
        "main_insights": report.main_insights,
        "confidence": report.overall_confidence,
        "gaps": report.gaps,
        "sources_count": len(report.sources),
        "created_at": report.generated_at,
        "tags": ["deep-research", "auto-generated"],
    }

    kg["research"].append(entry)
    kg["last_updated"] = report.generated_at

    with open(kg_path, 'w', encoding='utf-8') as f:
        json.dump(kg, f, indent=2, ensure_ascii=False)

    log.info("  KG: entrada %s registrada", entry_id)


def _find_related_notes(report: ResearchReport, vault_path: str):
    """Busca notas existentes com trechos dos insights e cria links."""
    # Busca simples: procura por palavras-chave dos insights no vault
    if not report.main_insights:
        return

    related = []
    keywords = set()
    for insight in report.main_insights[:3]:
        words = re.findall(r'\b\w{4,}\b', insight.lower())
        keywords.update(list(words)[:5])

    # Busca em notas .md do vault
    for root, dirs, files in os.walk(vault_path):
        for fname in files:
            if not fname.endswith('.md') or 'Research' in root:
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, 'r', encoding='utf-8') as f:
                    content = f.read(5000).lower()
                matches = sum(1 for kw in keywords if kw in content)
                if matches >= 2:
                    note_name = fname.replace('.md', '')
                    related.append(f"[[{note_name}]]")
            except Exception:
                continue

        if len(related) >= 10:
            break

    if related:
        log.info("  Notas relacionadas encontradas: %d", len(related))
