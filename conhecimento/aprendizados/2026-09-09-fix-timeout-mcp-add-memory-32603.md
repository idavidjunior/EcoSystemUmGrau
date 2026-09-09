---
tipo: erro
tags: [mcp, timeout, memoria, add-memory, 32603, memory_engine, conhecimento]
data: 2026-09-09
contexto: O mapa do ecossistema (conhecimento/web) apontava "Busca MCP mcp-memoria com timeout (-32603)". Investigação ao vivo (09/09) para destravar o RAG.
decisao: Corrigida a causa raiz do -32603 no add-memory e eliminado o bloqueio do memory_semantic.search com rebuild denso síncrono.
impacto: add-memory via MCP passou a responder em ~60s (antes estourava timeout de 15s virava -32603); search nunca mais bloqueia por build denso.
---

# Fix timeout -32603 no MCP add-memory e busca de conhecimento

## Diagnóstico (com evidência, 2026-09-09)

1. `memory_engine.py add` NÃO é rápido: mediu-se ~62s com `Measure-Command`. O custo é o `reindexar_semantico()` → `build_index()` TF-IDF completo (corpus + notas), que roda a cada add quando o fingerprint muda.
2. `memory_semantic.search()` fazia `build_dense()` SÍNCRONO quando a matriz densa não existe (linha ~403). Cold start medido: ~54s. O modelo MiniLM não está em cache local (`dense_matrix.npy` nunca foi gerado), então cada buy disparava encode do corpus inteiro.
3. O servidor `scripts/mcp-knowledge-server.py` usava `timeout=15` no `add-memory` e `timeout=30` no `search-knowledge`. Como o subprocesso estourava o timeout, o `try/except` devolvia erro interno `-32603` (linha 68) — origem do sintoma reportado.

## Correções aplicadas (mudança mínima segura)

1. `scripts/memory_semantic.py`: `search()` não chama mais `build_dense()` síncrono. Se a matriz densa está ausente, dispara `_spawn_dense_background()` (subprocesso destacado, mesmo padrão do `memory_engine.reindexar_semantico`) e segue só com TF-IDF. Nunca bloqueia a busca.
2. `scripts/mcp-knowledge-server.py`: timeouts realinhados ao custo real das operações — `get-memory-context` 15→30s, `add-memory` 15→120s.
3. `scripts/memory_engine.py`: `_memory_lock` esperava só 10s pelo lock, mas cada `add` segura o lock ~60s (reindex) — qualquer gravação concorrente (ex.: ciclo contínuo preflight->add do próprio ecossistema) falhava com `TimeoutError`. Timeout de espera alinhado a 120s (mesmo valor do `stale_after`), permitindo fila. Validado com add #98318 e #98319.

## Validação (tudo ao vivo, via stdin do servidor MCP)

- `add-memory` via MCP retornou `result` normal (antes: -32603). Reindex rodou: "índice semântico atualizado: 1725 docs".
- `search-knowledge` via MCP retornou resultados, incluindo a memória recém-criada (id 98317, score 22.81).
- A memória de teste entrou como RASCUNHO (confidence 0.3, tag rascunho) — não polui a base ativa; será arquivada pelo decay.

## Observações adicionais (gargalos remanescentes, não bloqueantes)

- Cold start de `memory_semantic.search` continua ~37-78s por causa do pickle TF-IDF grande (ngram 1-2 sobre corpus extenso). Hot <50ms. Para o RAG, reusar o caminho rápido: `search_knowledge` via MCP (BM25, ~13s) ou cache quente por processo.
- `dense_matrix.npy` não foi gerado (modelo MiniLM sem cache local, `local_files_only`). O rebuild em background tenta e sai rápido; sem impacto na busca TF-IDF.
- Não há comando de remoção no memory_engine (add/query/context/reinforce/destroy no CLI) — testes geram memórias rascunho que só o decay arquiva.

## Conexoes

- [[2026-08-04-foco-vocal-via-jarvis-voz-orienta-o-grafo-do-conh]]