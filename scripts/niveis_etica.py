#!/usr/bin/env python3
"""
Níveis Éticos do EcoSystemUmGrau.

Define os padrões de rigor ético e o gerenciamento do nível atual.

NÍVEIS:
  desativado (PADRÃO) - Ética desativada: sem avisos e sem bloqueios.
  minimo               - Permite o tecnicamente viável com avisos mínimos.
  medio                - Exige avisos claros, consentimento e revisão.
  maximo               - Rigidez total; bloqueia incerteza até revisão humana.

Uso:
  python scripts/niveis_etica.py status          # mostra nível atual
  python scripts/niveis_etica.py set <nivel>     # muda o nível
  python scripts/niveis_etica.py list            # lista os níveis disponíveis
"""
import json
import sys
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
CONFIG_FILE = Path(BASE) / "conhecimento" / "etica" / "niveis_etica.json"


def carregar():
    if not CONFIG_FILE.exists():
        return None
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


def salvar(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def status():
    data = carregar()
    if not data:
        print("Sem configuracao de niveis eticos.")
        return 1
    atual = data.get("nivel_atual", "minimo")
    niveis = data.get("niveis", {})
    print(f"Nivel etico atual: {atual}")
    print(f"Descricao: {niveis.get(atual, {}).get('descricao', '')}")
    print(f"Bloqueia: {niveis.get(atual, {}).get('bloqueia', [])}")
    print(f"Avisa: {niveis.get(atual, {}).get('avisa', [])}")
    print(f"Exige avaliacao etica: {niveis.get(atual, {}).get('exige_avaliacao_etica', False)}")
    print("\nRegras imutaveis minimas (sempre valem):")
    for r in data.get("regras_imutaveis_minimas", []):
        print(f"  - {r}")
    return 0


def set_nivel(nivel):
    data = carregar()
    if not data:
        print("Configuracao nao encontrada.")
        return 1
    if nivel not in data.get("niveis", {}):
        print(f"Nivel invalido: {nivel}. Disponiveis: {list(data['niveis'].keys())}")
        return 1
    data["nivel_atual"] = nivel
    salvar(data)
    print(f"Nivel etico alterado para: {nivel}")
    return 0


def listar():
    data = carregar()
    if not data:
        print("Sem configuracao.")
        return 1
    print("Niveis eticos disponiveis:")
    for nome, info in data.get("niveis", {}).items():
        padrao = " (PADRAO)" if nome == data.get("nivel_atual") else ""
        print(f"  {nome}{padrao}: {info.get('descricao', '')}")


def get_nivel():
    """Retorna o nome do nivel atual (para uso por outros scripts)."""
    data = carregar()
    return data.get("nivel_atual", "minimo") if data else "minimo"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        status()
    elif sys.argv[1] == "status":
        status()
    elif sys.argv[1] == "set" and len(sys.argv) > 2:
        set_nivel(sys.argv[2])
    elif sys.argv[1] == "list":
        listar()
    else:
        print("Uso: python scripts/niveis_etica.py [status|set <nivel>|list]")
        sys.exit(1)
