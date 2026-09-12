#!/usr/bin/env python3
"""Força atualização do cache do Cerebro Vivo (runtime/cerebro_dados.json)."""

import sys
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / 'scripts'))

import importlib.util
spec = importlib.util.spec_from_file_location('wg', str(BASE / 'scripts' / 'widget_grafo.py'))
wg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wg)

# Inicializa GEN (carregado em main())
wg.GEN = wg.carregar_gerador()

# Gera payload combinado (vault + memórias) como o vigia faz
payload = wg.montar_payload_combined(wg.GEN)

# Atualiza cache do widget
DADOS_FILE = BASE / 'runtime' / 'cerebro_dados.json'
sig = (len(payload['nos']), max((n.get('tm', 0) for n in payload['nos']), default=0))
cache = {
    'sig': list(sig),
    '_pos': wg.ULTIMA_POS,
    '_mtimes': wg.mapa_mtimes(),
    'payload': payload
}
DADOS_FILE.write_text(json.dumps(cache, ensure_ascii=False), encoding='utf-8')

clusters = {}
for n in payload['nos']:
    c = n.get('cl', 'geral')
    clusters[c] = clusters.get(c, 0) + 1

print(f'Cache atualizado: {len(payload["nos"])} nos, {len(payload["ar"])} arestas')
for c, cnt in sorted(clusters.items()):
    print(f'  {c}: {cnt}')

print('\nAgora feche e reabra o widget com @ecow para ver os agentes.')