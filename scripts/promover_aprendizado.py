#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""promover_aprendizado.py — Gate de validação de aprendizados.

REGRA DE OURO: nenhum aprendizado vira memória/base sem o usuário autorizar.

Fluxo:
1. Mudança fica em conhecimento/rascunhos/<slug>.md com status=RASCUNHO
2. Quando o usuário pede "@promover <slug>", este script:
   - Mostra o conteúdo do rascunho
   - Pergunta se foi validado (testes passaram, mudança funciona)
   - Se sim: move para conhecimento/aprendizados/, registra memória
   - Se não: mantém como rascunho com nota

Uso:
    python scripts/promover_aprendizado.py --listar
    python scripts/promover_aprendizado.py --arquivo conhecimento/rascunhos/2026-08-31-foo.md
    python scripts/promover_aprendizado.py --slug foo
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RASCUNHOS = ROOT / "conhecimento" / "rascunhos"
APRENDIZADOS = ROOT / "conhecimento" / "aprendizados"
MEMORY_FILE = ROOT / "conhecimento" / "memoria" / "memories.json"


def listar_rascunhos():
    """Lista rascunhos pendentes de validação."""
    if not RASCUNHOS.exists():
        print(f"Pasta {RASCUNHOS} nao existe")
        return []
    rascunhos = []
    for f in sorted(RASCUNHOS.glob("*.md")):
        if f.name.startswith("_"):
            continue
        conteudo = f.read_text(encoding="utf-8")
        status = "RASCUNHO"
        if "status: VALIDADO" in conteudo.lower():
            status = "VALIDADO"
        elif "status: REJEITADO" in conteudo.lower():
            status = "REJEITADO"
        rascunhos.append((f, status))
    return rascunhos


def mostrar(arquivo: Path):
    """Mostra conteúdo do rascunho."""
    print(f"\n=== {arquivo.name} ===")
    print(arquivo.read_text(encoding="utf-8"))


def validar(arquivo: Path):
    """Move rascunho para aprendizados e registra memória.

    Só executa se o usuário confirmar via flag --sim. Sem --sim, mostra
    o que SERIA feito e pede confirmação.
    """
    conteudo = arquivo.read_text(encoding="utf-8")

    # Extrai campos do frontmatter
    frontmatter = {}
    if conteudo.startswith("---"):
        try:
            fim = conteudo.index("---", 3)
            bloco = conteudo[3:fim]
            for linha in bloco.split("\n"):
                if ":" in linha:
                    k, v = linha.split(":", 1)
                    frontmatter[k.strip()] = v.strip()
        except ValueError:
            pass

    slug = arquivo.stem
    task = frontmatter.get("titulo", arquivo.stem)
    tipo = frontmatter.get("tipo", "padrao")
    tags_str = frontmatter.get("tags", "")
    tags = [t.strip() for t in tags_str.strip("[]").split(",") if t.strip()]
    data = frontmatter.get("data", datetime.now().strftime("%Y-%m-%d"))
    resumo = frontmatter.get("resumo", "")

    print("\n=== ACAO QUE SERA EXECUTADA ===")
    print(f"  1. Mover {arquivo.name}")
    print(f"     -> {APRENDIZADOS / arquivo.name}")
    print(f"  2. Registrar memoria: id=novo, tipo={tipo}")
    print(f"     task='{task[:60]}'")
    print(f"     tags={tags}")
    print(f"  3. Marcar rascunho original como VALIDADO")
    print()


def promover(arquivo: Path, sim: bool = False):
    """Move para aprendizados/ + grava memoria."""
    if not arquivo.exists():
        print(f"ERRO: {arquivo} nao existe")
        return False

    conteudo = arquivo.read_text(encoding="utf-8")

    # Extrai frontmatter
    fm = {}
    body = conteudo
    if conteudo.startswith("---"):
        try:
            fim = conteudo.index("---", 3)
            bloco = conteudo[3:fim]
            body = conteudo[fim + 3 :].lstrip()
            for linha in bloco.split("\n"):
                if ":" in linha:
                    k, v = linha.split(":", 1)
                    fm[k.strip()] = v.strip()
        except ValueError:
            pass

    task = fm.get("titulo", arquivo.stem)
    tipo = fm.get("tipo", "padrao")
    tags_str = fm.get("tags", "")
    tags = [t.strip() for t in tags_str.strip("[]").split(",") if t.strip()]
    data = fm.get("data", datetime.now().strftime("%Y-%m-%d"))

    # Resumo: primeira linha do body ou campo resumo
    resumo = fm.get("resumo", "")
    if not resumo:
        for linha in body.split("\n"):
            linha = linha.strip()
            if linha and not linha.startswith("#"):
                resumo = linha[:300]
                break

    print(f"\nPromovendo: {arquivo.name}")
    print(f"  task: {task}")
    print(f"  tipo: {tipo}")
    print(f"  tags: {tags}")
    print(f"  resumo: {resumo[:100]}...")

    if not sim:
        resp = input("\nConfirma promocao? (s/N): ").strip().lower()
        if resp not in ("s", "sim", "y", "yes"):
            print("Cancelado pelo usuario.")
            return False

    # 1. Move para aprendizados/
    destino = APRENDIZADOS / arquivo.name
    if destino.exists():
        print(f"AVISO: {destino} ja existe, sobrescrevendo")
    arquivo.replace(destino)
    print(f"  OK: movido para {destino}")

    # 2. Registra memoria
    try:
        mems = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        mems = []

    novo_id = max((m.get("id", 0) for m in mems), default=0) + 1
    nova = {
        "id": novo_id,
        "kind": tipo if tipo in ("decisao", "erro", "padrao", "episodio", "preferencia") else "padrao",
        "task": task,
        "summary": resumo,
        "project": "",
        "tags": tags + ["validado"],
        "metadata": {
            "data": data,
            "origem": arquivo.name,
            "validado_por": "usuario",
            "validado_em": datetime.now().isoformat(),
        },
        "strength": 1.0,
        "access_count": 0,
        "created_at": datetime.now().isoformat(),
        "last_accessed": datetime.now().isoformat(),
        "confidence": 1.0,
        "source_type": "VALIDATED",
    }
    mems.append(nova)
    MEMORY_FILE.write_text(
        json.dumps(mems, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  OK: memoria #{novo_id} registrada (source=VALIDATED)")

    return True


def rejeitar(arquivo: Path, motivo: str):
    """Marca como rejeitado (mantém na pasta rascunhos mas não promove)."""
    conteudo = arquivo.read_text(encoding="utf-8")
    if not conteudo.startswith("---"):
        conteudo = "---\nstatus: REJEITADO\n---\n" + conteudo
    else:
        conteudo = re.sub(
            r"^status:.*$",
            "status: REJEITADO",
            conteudo.split("---")[1],
            flags=re.MULTILINE,
        )
    arquivo.write_text(conteudo, encoding="utf-8")
    (RASCUNHOS / "_validacoes" / f"{arquivo.stem}.rejeitado.txt").write_text(
        f"Rejeitado em {datetime.now().isoformat()}\nMotivo: {motivo}\n",
        encoding="utf-8",
    )
    print(f"Rejeitado: {arquivo.name}")


def main():
    parser = argparse.ArgumentParser(description="Gate de validacao de aprendizados")
    parser.add_argument("--listar", action="store_true", help="Lista rascunhos")
    parser.add_argument("--arquivo", type=Path, help="Arquivo de rascunho")
    parser.add_argument("--slug", help="Slug do rascunho (busca em rascunhos/)")
    parser.add_argument("--sim", action="store_true", help="Confirma sem perguntar")
    parser.add_argument("--rejeitar", help="Rejeita com motivo")
    args = parser.parse_args()

    if args.listar:
        rascunhos = listar_rascunhos()
        if not rascunhos:
            print("Nenhum rascunho encontrado.")
            return 0
        for f, status in rascunhos:
            print(f"  [{status}] {f.name}")
        return 0

    arquivo = None
    if args.arquivo:
        arquivo = args.arquivo
    elif args.slug:
        arquivo = RASCUNHOS / f"{args.slug}.md"

    if not arquivo:
        parser.print_help()
        return 1

    if not arquivo.exists():
        print(f"ERRO: {arquivo} nao existe")
        return 1

    mostrar(arquivo)

    if args.rejeitar:
        rejeitar(arquivo, args.rejeitar)
        return 0

    if not args.sim:
        validar(arquivo)

    return 0 if promover(arquivo, sim=args.sim) else 1


if __name__ == "__main__":
    sys.exit(main())
