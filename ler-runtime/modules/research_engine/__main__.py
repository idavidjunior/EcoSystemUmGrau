"""CLI — ponto de entrada para pesquisas sob demanda.

Uso:
    python -m research_engine "tema da pesquisa"
    python -m research_engine "tema" --context "contexto do projeto"
    python -m research_engine --list
    python -m research_engine --status
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

from .engine import ResearchEngine
from .graph_writer import DEFAULT_VAULT


def main():
    parser = argparse.ArgumentParser(
        description="Deep Research Engine — pesquisa técnica automatizada"
    )
    parser.add_argument("theme", nargs="?", help="Tema a pesquisar")
    parser.add_argument("--context", "-c", default="", help="Contexto do projeto")
    parser.add_argument("--vault", default=DEFAULT_VAULT, help="Caminho do vault")
    parser.add_argument("--kg", default=None, help="Caminho do Knowledge Graph")
    parser.add_argument("--list", action="store_true", help="Lista pesquisas salvas")
    parser.add_argument("--status", action="store_true", help="Status do módulo")
    parser.add_argument("--verbose", "-v", action="store_true", help="Log detalhado")
    args = parser.parse_args()

    # Logging
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    if args.list:
        _list_research(args.vault)
        return

    if args.status:
        _show_status(args.vault, args.kg)
        return

    if not args.theme:
        parser.print_help()
        sys.exit(1)

    # Executa pesquisa
    print(f"Pesquisando: {args.theme}")
    print()

    config = {"vault_path": args.vault}
    if args.kg:
        config["kg_path"] = args.kg

    engine = ResearchEngine(config=config)
    start = time.time()
    report = engine.research(args.theme, args.context)
    elapsed = time.time() - start

    # Resumo
    print()
    print("=" * 60)
    print(f"CONCLUIDO EM {elapsed:.1f}s")
    print("=" * 60)
    print(f"Secoes:  {len(report.sections)}")
    print(f"Insights: {len(report.main_insights)}")
    print(f"Fontes:  {len(report.sources)}")
    print(f"Gaps:    {len(report.gaps)}")
    print(f"Confianca: {report.overall_confidence:.0%}")
    print()

    for s in report.sections:
        print(f"  [{s.confidence:.0%}] {s.title}")
    print()

    # Caminho do relatório salvo
    safe_name = __import__("re").sub(r'[^\w\s-]', '', report.theme).strip().replace(' ', '-')
    report_path = os.path.join(args.vault, "Research", f"{safe_name}.md")
    if os.path.exists(report_path):
        print(f"Relatorio: {report_path}")


def _list_research(vault_path: str):
    """Lista pesquisas salvas no vault."""
    research_dir = os.path.join(vault_path, "Research")
    if not os.path.exists(research_dir):
        print("Nenhuma pesquisa salva.")
        return

    files = sorted([f for f in os.listdir(research_dir) if f.endswith(".md")])
    if not files:
        print("Nenhuma pesquisa salva.")
        return

    print(f"Research/ ({len(files)} pesquisas):")
    for f in files:
        print(f"  {f}")


def _show_status(vault_path: str, kg_path: str = None):
    """Mostra status do módulo."""
    print("Research Engine — Status")
    print()

    # Vault
    research_dir = os.path.join(vault_path, "Research")
    n_reports = 0
    if os.path.exists(research_dir):
        n_reports = len([f for f in os.listdir(research_dir) if f.endswith(".md")])
    print(f"  Vault: {vault_path}")
    print(f"  Relatorios salvos: {n_reports}")

    # KG
    kg = kg_path or os.path.join(
        str(Path(__file__).resolve().parents[3]),
        "ler-runtime", "knowledge", "knowledge_graph.json"
    )
    if os.path.exists(kg):
        with open(kg, "r", encoding="utf-8") as f:
            data = json.load(f)
        n_kg = len(data.get("research", []))
        print(f"  Knowledge Graph: {n_kg} entradas")
    else:
        print(f"  Knowledge Graph: nao encontrado")


if __name__ == "__main__":
    main()
