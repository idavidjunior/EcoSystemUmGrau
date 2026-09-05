---
tags: [ares, caminho, extensao, opencode, padrao, todo]
aliases: [Ilhas no grafo: notas com grau 0 e como conecta-las]
date: 2026-08-05
---

# Ilhas no grafo: notas com grau 0 e como conecta-las

**Fonte:** opencode

## O que sao as ilhas
Ilhas = componentes conexos separados do componente gigante. No grafo de conhecimento,
todas as ilhas eram **notas com grau 0**: arquivos .md sem NENHUM `[[wikilink]]` e sem serem
linkadas por ninguem. Nao e bug do grafo — e dado real do vault (gera no para todo .md,
aresta so via wikilink).

## Como diagnosticar (BFS por componentes conexos)
```python
adj = defaultdict(set)
for a, b in arestas: adj[a].add(b); adj[b].add(a)
gigante = max(componentes, key=len)
ilhas = [c for c in componentes if c is not gigante]
grau0 = [nid for nid in ids if len(adj[nid]) == 0]
```

## LICAO CRITICA — wikilink alvo deve ser o SLUG, nao o caminho
O gerador (`scripts/generate-graph-html.py`) extrai wikilinks sim.
generate-graph-html.py:142-144 `_extract_wikilinks` -> pega `link_slug = link.split('|')[0].strip()`
e procura em `id_set` (o conjunto de **slugs**, ou seja, nome do arquivo sem pasta/extensao).
Se voce escreve `[[padroes/foo]]`, `padroes/foo` NAO existe em `id_set` -> ares
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]