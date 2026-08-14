#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Rotação do knowledge graph (conhecimento/grafo/)
Mantém apenas o grafo mais recente + 1 anterior.
O grafo é regenerado periodicamente, não precisa de histórico profundo.
"""

import sys
import os
from pathlib import Path
import json

BASE = Path(__file__).resolve().parents[1]
GRAFO_DIR = BASE / "conhecimento" / "grafo"

def cleanup_knowledge_graph(keep: int = 2, dry_run: bool = False) -> dict:
    """Mantém apenas os 'keep' grafos mais recentes (por data no nome)."""
    graphs = sorted(GRAFO_DIR.glob("knowledge_graph_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    freed = 0
    for g in graphs[keep:]:
        size = g.stat().st_size
        if not dry_run:
            g.unlink()
        removed += 1
        freed += size
    return {"removed": removed, "freed_bytes": freed, "remaining": len(graphs) - removed}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Rotação do knowledge graph")
    parser.add_argument("--keep", type=int, default=2, help="Quantos grafos manter (padrão: 2)")
    parser.add_argument("--dry-run", action="store_true", help="Não remove, só mostra")
    args = parser.parse_args()

    result = cleanup_knowledge_graph(args.keep, args.dry_run)
    print(f"Knowledge graph: removidos {result['removed']}, liberados {result['freed_bytes']} bytes, restantes {result['remaining']}")