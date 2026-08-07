#!/usr/bin/env python3
"""
Rotação de Dados - EcoSystemUmGrau
Aplica a Política de Retenção (conhecimento/etica/POLITICA_RETENCAO.md).

Prazos:
  - Logs operacionais: 30 dias
  - Sessões de conversa: 90 dias
  - Memórias: 180 dias
  - Áudio: 7 dias
  - Configurações: enquanto ativo

Uso:
  python scripts/rotacao_dados.py              # aplica rotação
  python scripts/rotacao_dados.py --dry-run    # apenas lista o que apagaria
"""
import os
import sys
import time
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
DRY_RUN = '--dry-run' in sys.argv

PRAZOS = {
    'connectivity/bridge/health': 30 * 86400,
    'connectivity/bridge/events.jsonl': 30 * 86400,
    'connectivity/logs': 30 * 86400,
    'connectivity/bridge/learning': 180 * 86400,
    'conhecimento/memoria/sessions': 90 * 86400,
    'connectivity/bridge/tmp_audio': 7 * 86400,
}


def expirado(path, prazo):
    try:
        idade = time.time() - os.path.getmtime(path)
        return idade > prazo
    except Exception:
        return False


def rotacionar():
    agora = time.time()
    total = 0
    for alvo, prazo in PRAZOS.items():
        caminho = os.path.join(BASE, alvo)
        if os.path.isdir(caminho):
            for root, _, files in os.walk(caminho):
                for fname in files:
                    fp = os.path.join(root, fname)
                    if expirado(fp, prazo):
                        total += 1
                        if DRY_RUN:
                            print(f'[DRY] apagaria: {os.path.relpath(fp, BASE)}')
                        else:
                            os.remove(fp)
                            print(f'[OK] apagado: {os.path.relpath(fp, BASE)}')
        elif os.path.isfile(caminho):
            if expirado(caminho, prazo):
                total += 1
                if DRY_RUN:
                    print(f'[DRY] apagaria: {alvo}')
                else:
                    os.remove(caminho)
                    print(f'[OK] apagado: {alvo}')

    print(f'Total: {total} item(ns) {"a remover" if DRY_RUN else "removidos"}.')
    return total


if __name__ == '__main__':
    sys.exit(0 if rotacionar() else 0)
