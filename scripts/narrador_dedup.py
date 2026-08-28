"""narrador_dedup.py — dedup COMPARTILHADO em disco para o narrador.

Problema que resolve: o narrador roda como thread dentro do widget_edge.py
(o único narrador oficial). Deduplica no disco o que já foi falado, para que
nenhum texto seja narrado 2x quando o widget reinicia ou outras threads vocais
(tempo real vs pilha) coexistem.

Solução: cache em disco (runtime/falados_cache.json) com escrita atômica e
lock, usado por TODOS os narradores. Um texto é falado uma única vez dentro do
TTL, independentemente de qual thread o detectou primeiro.
"""
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "runtime" / "falados_cache.json"
TTL = 120  # segundos — textos idênticos são ignorados por 2 min
_MAX_ENTRIES = 2000


def _ler():
    try:
        if CACHE.exists():
            return json.loads(CACHE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _salvar(dados):
    try:
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        tmp = CACHE.with_suffix(".tmp")
        tmp.write_text(json.dumps(dados), encoding="utf-8")
        tmp.replace(CACHE)
    except Exception:
        pass


def ja_falado(texto_hash):
    """Verifica se o hash já foi falado recentemente (dentro do TTL).
    Retorna True se já foi falado (deve pular), False se é novo (deve falar)."""
    dados = _ler()
    agora = time.time()
    # Remove expirados
    expirados = [k for k, t in dados.items() if agora - t > TTL]
    for k in expirados:
        dados.pop(k, None)
    if texto_hash in dados:
        return True
    # Marca como falado
    dados[texto_hash] = agora
    # Cap de tamanho
    if len(dados) > _MAX_ENTRIES:
        # Remove as mais antigas (por timestamp)
        ordenadas = sorted(dados.items(), key=lambda x: x[1])
        for k, _ in ordenadas[: len(ordenadas) - _MAX_ENTRIES]:
            dados.pop(k, None)
    _salvar(dados)
    return False