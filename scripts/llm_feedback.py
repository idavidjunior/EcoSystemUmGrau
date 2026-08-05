"""Curadoria do pipeline multi-LLM: feedback persistido por modelo.

Reordena dinamicamente a cadeia de fallback com base em:
  - taxa de sucesso (sucessos / tentativas)
  - latencia media (ms)
  - penalizacao por falhas consecutivas

Arquivo: docs/llm_feedback.json
  {
    "<modelo>": {
      "sucessos": int, "falhas": int, "latencia_ms_total": int,
      "falhas_consecutivas": int, "ultima_atualizacao": iso
    }
  }
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path

BASE = str(Path(__file__).resolve().parent.parent)
FEEDBACK_FILE = os.path.join(BASE, 'docs', 'llm_feedback.json')

CADEIA_BASE = [
    'opencode/nemotron-3-ultra-free',
    'opencode/deepseek-v4-flash-free',
    'opencode/laguna-s-2.1-free',
    'opencode/ling-3.0-flash-free',
    'opencode/mimo-v2.5-free',
    'opencode/north-mini-code-free',
    'opencode/big-pickle',
]


def _load() -> dict:
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def _save(data: dict) -> None:
    os.makedirs(os.path.dirname(FEEDBACK_FILE), exist_ok=True)
    tmp = FEEDBACK_FILE + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, FEEDBACK_FILE)


def registrar(modelo: str, ok: bool, latencia_ms: int) -> None:
    """Registra resultado de uma chamada para reusar na curadoria."""
    data = _load()
    e = data.setdefault(modelo, {
        'sucessos': 0, 'falhas': 0, 'latencia_ms_total': 0,
        'falhas_consecutivas': 0, 'ultima_atualizacao': None,
    })
    if ok:
        e['sucessos'] += 1
        e['falhas_consecutivas'] = 0
    else:
        e['falhas'] += 1
        e['falhas_consecutivas'] += 1
    e['latencia_ms_total'] += max(0, int(latencia_ms))
    e['ultima_atualizacao'] = datetime.now().isoformat()
    _save(data)


def score(modelo: str, e: dict) -> float:
    """Score maior = melhor. Combina taxa de sucesso + velocidade - penalizacao."""
    e = e or {}
    total = e.get('sucessos', 0) + e.get('falhas', 0)
    if total == 0:
        return 0.5  # neutro para modelos sem dados
    taxa = e.get('sucessos', 0) / total
    suce = e.get('sucessos', 0)
    lat_media = e.get('latencia_ms_total', 0) / max(1, suce) if suce else 99999
    velocidade = max(0.1, 1.0 - (lat_media - 500) / 14500)
    penal = 0.1 * e.get('falhas_consecutivas', 0)
    return max(0.05, taxa * 0.8 + velocidade * 0.2 - penal)


def cadeia_ordenada() -> list:
    """Retorna a cadeia base reordenada por score descritivo."""
    data = _load()
    def chave(m):
        if m not in data:
            return (0.5, m)
        return (score(m, data[m]), m)
    return sorted(CADEIA_BASE, key=lambda m: -chave(m)[0])


def relatorio() -> list:
    data = _load()
    return [{
        'modelo': m,
        'sucessos': data.get(m, {}).get('sucessos', 0),
        'falhas': data.get(m, {}).get('falhas', 0),
        'falhas_consecutivas': data.get(m, {}).get('falhas_consecutivas', 0),
        'lat_media_ms': round(data.get(m, {}).get('latencia_ms_total', 0) /
                              max(1, data.get(m, {}).get('sucessos', 1)), 1),
        'score': round(score(m, data.get(m, {})), 4),
    } for m in CADEIA_BASE]


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'relatorio':
        for r in relatorio():
            print(f"  {r['score']:.4f} | ok={r['sucessos']} fail={r['falhas']} "
                  f"fc={r['falhas_consecutivas']} lat={r['lat_media_ms']}ms | {r['modelo']}")
        print('Ordem atual:', cadeia_ordenada())
    else:
        print('uso: llm_feedback.py relatorio')
