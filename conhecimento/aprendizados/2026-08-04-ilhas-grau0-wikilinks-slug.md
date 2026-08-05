---
tipo: padrao
tags: [grafo, obsidian, wikilinks, conectividade, grau0, debug]
data: 2026-08-04
contexto: Usuario viu 6 ilhas (componentes desconexos) no grafo do cerebro e perguntou como verificar e se sao uteis.
decisao: Diagnosticar ilhas como notas com grau 0 e integrar/deletar conforme o valor do conteudo.
impacto: Grafo conectado (0 ilhas, 0 grau 0); aprendizado sobre como wikilinks viram arestas.
---

# Ilhas no grafo: notas com grau 0 e como conecta-las

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
Se voce escreve `[[padroes/foo]]`, `padroes/foo` NAO existe em `id_set` -> aresta nao criada.
Escreva **so o slug**: `[[foo]]`.

Primeira tentativa usei caminhos `[[padroes/electron-app-gpu-disable-flags]]` e as arestas NAO
foram criadas. Correto: `[[electron-app-gpu-disable-flags]]`.

## O que foi feito
- **Deletadas 2 notas-templates vazias**: `bugs/-.md` ("Bug: -------", sem conteudo) e
  `padroes/pattern.md` (so "Pattern" com tag `lermemory...`, sem conteudo).
- **Conectadas 4 notas uteis** acrescentando secoes "## Ver tambem" com wikilinks (slug):
  - `bugs/opencode-desktop-renderer-crash-gpu-antiga-memoria-critica.md` <-> `padroes/electron-app-gpu-disable-flags.md` e `cognitivo/2026-08-01-opencode-desktop-crash-do-renderer-por-gpu-fecham.md`
  - `decisoes/-encoding-utf-8-...md` -> heuristicas/padroes de encoding
  - `decisoes/2026-07-31-habilidades-catalogo-unico-jarvis.md` -> padroes de habilidades
- Regenerado grafo: 339 - 2 = 337 nos, arestas 1519 -> 1527, **GIGANTE 337, ILHAS 0, GRAU 0**.

## Validacao
- `preflight_check.py`: TODOS TESTES PASSARAM.
- Widget reiniciado como pythonw (PID 6152, "Cerebro Vivo").
- Memory #87.