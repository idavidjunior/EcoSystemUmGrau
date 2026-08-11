---
tipo: decisao
tags: [memoria-semantica, tfidf, ranking, busca, obsidian]
data: 2026-08-07
---

# Busca semântica aprimorada — ranking ponderado (07/08/2026)

## Contexto
A busca semântica TF-IDF (memory_semantic.py) indexava memórias + notas Obsidian,
mas o ranking era puramente por similaridade cosseno — sem considerar recência,
domínio ou frequência de uso.

## Decisão
1. **Índice ampliado:** `NOTAS_DIRS` agora inclui `conhecimento/notas`, `conhecimento/aprendizados`, `docs/` e `documentos/`. Total: 612 documentos (133 memórias + 479 notas).
2. **Ranking ponderado** — o score final = TF-IDF + bônus:
   - `_boost_recencia()`: decaimento exponencial (meia-vida 60 dias, máx +0.15) usando data do filename/frontmatter/mtime.
   - `DOMAIN_BOOST`: aprendizados +0.12, docs +0.10, padroes +0.08, decisoes +0.05, notas +0.03, memoria 0.
   - `_boost_acesso()`: +0.01 por acesso (até +0.1), persistido em `conhecimento/memoria/tfidf_acesso.json`.
3. **Camada densa opcional:** `build_dense()` cria embeddings com `paraphrase-multilingual-MiniLM-L12-v2` (matriz em `dense_matrix.npy`). Só carrega se o modelo já estiver em cache local — nunca força download.

## Impacto
- Notas recentes e relevantes sobem no ranking (ex.: busca "TV LG webOS" retorna a nota de padrão certa no topo).
- Frequência de acesso reforça documentos mais usados ao longo do tempo.

## Validação
- `python scripts/memory_semantic.py build` → 612 docs, vocab 41015.
- Buscas reais validam o novo ranking (recência + domínio).
- Bridge (`jarvis_bridge.py:1171`) já usa o módulo cacheado — nova lógica vale sem mudança na ponte.

## Conexoes

- [[cluster-hub-programacao]]