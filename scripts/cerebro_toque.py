#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Registra atividade real do agente para o Cerebro Vivo.

Uso:
  python scripts/cerebro_toque.py leitura slug-da-nota [slug2 ...]
  python scripts/cerebro_toque.py cognicao -- slug-a slug-b
  python scripts/cerebro_toque.py escrita caminho/para/nota.md

Tipos: leitura (padrao), escrita, cognicao.
Aceita slugs ou caminhos; normaliza para o id da nota no grafo.
Escreve runtime/cerebro_atividade.json de forma atomica; a sentinela do
widget detecta em ate 0.5s e dispara o anel branco sobre o neuronio.
"""
import json
import sys
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ATIV = BASE / "runtime" / "cerebro_atividade.json"
DADOS = BASE / "runtime" / "cerebro_dados.json"
TIPOS = {"leitura", "escrita", "cognicao"}


def main(argv):
    args = list(argv)
    tipo = "leitura"
    if args and args[0] in TIPOS:
        tipo = args.pop(0)

    notas = []
    for a in args:
        if a == "--":
            continue
        s = a.replace("\\", "/").rsplit("/", 1)[-1]
        if s.endswith(".md"):
            s = s[:-3]
        if s and s not in notas:
            notas.append(s)
    if not notas:
        print("uso: cerebro_toque.py [leitura|escrita|cognicao] slug [slug...]")
        return 1

    validas, desconhecidas = [], []
    try:
        ids = {n["id"] for n in json.loads(
            DADOS.read_text(encoding="utf-8"))["payload"]["nos"]}
        validas = [s for s in notas if s in ids]
        desconhecidas = [s for s in notas if s not in ids]
    except Exception:
        validas = notas  # sem cache: deixa a sentinela decidir

    if not validas:
        print("nenhuma nota conhecida no grafo: "
              + ", ".join(desconhecidas or notas))
        return 1

    tmp = ATIV.with_suffix(".tmp")
    tmp.write_text(json.dumps(
        {"tipo": tipo, "notas": validas, "quando": time.time()},
        ensure_ascii=False), encoding="utf-8")
    tmp.replace(ATIV)

    extra = (" | fora do grafo: " + ", ".join(desconhecidas)) \
        if desconhecidas else ""
    print(f"cognicao registrada [{tipo}]: {', '.join(validas)}{extra}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
