import os, sys, json, collections
sys.path.insert(0, os.getcwd())
from importlib import util
spec = util.spec_from_file_location('g', 'scripts/generate-obsidian-notes.py')
g = util.module_from_spec(spec)
spec.loader.exec_module(g)

graph = json.load(open(g.GRAPH_FILE, encoding='utf-8'))
print('graph keys:', list(graph.keys())[:10])

sources = collections.Counter()
tags_all = collections.Counter()
for p in graph.get('patterns', []):
    for s in p.get('sources', []):
        sources[s] += 1
    for t in p.get('tags', []):
        tags_all[t] += 1
for c in graph.get('checkpoints', []):
    for s in c.get('sources', []):
        sources[s] += 1
    for t in c.get('tags', []):
        tags_all[t] += 1

print('\n=== top 60 sources ===')
for s, n in sources.most_common(60):
    print(f'{n:4d}  {s}')

print('\n=== fontes mapeadas? ===')
mapeadas = 0
nao = collections.Counter()
for s, n in sources.items():
    cl = g.cluster_of(s)
    if cl != 'geral':
        mapeadas += 1
    else:
        nao[s] += n
print(f'fontes mapeadas: {mapeadas} de {len(sources)}')
print('nao mapeadas (amostra):')
for s, n in nao.most_common(40):
    print(f'{n:4d}  {s}')
