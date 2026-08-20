"""solution_index.py — Índice cruzado problema→solução do ecossistema.

Gera e mantém um índice de todas as memórias de erro e suas soluções
vinculadas. Pode ser executado manualmente ou pelo audit.

Uso:
  python scripts/solution_index.py              # gera índice e mostra stats
  python scripts/solution_index.py --json       # saída JSON
  python scripts/solution_index.py --link ID "solução"  # vincula solução
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from memory_engine import (
    get_unsolved_errors, get_solved_errors, build_solution_index,
    link_solution, _load_memories
)

INDEX_FILE = Path(__file__).parent.parent / "conhecimento" / "memoria" / "solution_index.json"


def save_index(index: dict):
    """Salva índice cruzado."""
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = INDEX_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(INDEX_FILE)


def get_stats() -> dict:
    """Retorna estatísticas do índice."""
    solved = get_solved_errors()
    unsolved = get_unsolved_errors()
    total = len(solved) + len(unsolved)
    return {
        "total_erros": total,
        "resolvidos": len(solved),
        "nao_resolvidos": len(unsolved),
        "taxa_resolucao": f"{len(solved)/total*100:.1f}%" if total > 0 else "0%"
    }


def main():
    args = sys.argv[1:]

    if "--link" in args:
        idx = args.index("--link")
        if idx + 2 >= len(args):
            print("Uso: python solution_index.py --link ID \"descrição da solução\"")
            return 1
        memory_id = int(args[idx + 1])
        desc = args[idx + 2]
        script = args[idx + 3] if idx + 3 < len(args) else None
        ok = link_solution(memory_id, desc, script=script, validado=True)
        if ok:
            print(f"[OK] Solução vinculada ao erro #{memory_id}")
        else:
            print(f"[ERRO] Erro #{memory_id} não encontrado ou não é tipo 'erro'")
        return 0 if ok else 1

    # Gera índice
    index = build_solution_index()
    save_index(index)
    stats = get_stats()

    if "--json" in args:
        output = {"stats": stats, "index": index}
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(f"Erros totais: {stats['total_erros']}")
        print(f"Resolvidos: {stats['resolvidos']}")
        print(f"Não resolvidos: {stats['nao_resolvidos']}")
        print(f"Taxa de resolução: {stats['taxa_resolucao']}")
        if index["cruzamento"]:
            print("\nCruzamentos problema→solução:")
            for c in index["cruzamento"][:10]:
                print(f"  #{c['erro_id']}: {c['erro_task'][:60]}")
                print(f"    → {c['solucao_desc'][:80]}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
