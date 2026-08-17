#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Retagulagem de memórias sem tags semânticas.
Usa extrair_tags (RAKE leve) para gerar tags para memórias que não possuem.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from semantic_tags import extrair_tags

BASE = Path(__file__).resolve().parents[1]
MEMORIES_FILE = BASE / "conhecimento" / "memoria" / "memories.json"


def retag_memories(dry_run: bool = False) -> dict:
    memories = json.loads(MEMORIES_FILE.read_text(encoding="utf-8"))
    tagged = 0
    total_tags = 0

    for m in memories:
        if m.get("tags"):
            continue
        text = f"{m.get('task', '')} {m.get('summary', '')}"
        tags = extrair_tags(text, max_tags=5)
        if tags:
            tagged += 1
            total_tags += len(tags)
            if not dry_run:
                m["tags"] = tags
            print(f"  [{m.get('id', '?')}] {m.get('task', '')[:60]} → {tags}")

    if not dry_run and tagged > 0:
        MEMORIES_FILE.write_text(
            json.dumps(memories, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    return {"tagged": tagged, "total_tags": total_tags, "total_memories": len(memories)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Retag memórias sem tags semânticas")
    parser.add_argument("--dry-run", action="store_true", help="Não altera, só mostra")
    args = parser.parse_args()

    result = retag_memories(dry_run=args.dry_run)
    action = "Simular" if args.dry_run else "Taggei"
    print(f"\n{action} {result['tagged']} memórias, {result['total_tags']} tags geradas, {result['total_memories']} total")
