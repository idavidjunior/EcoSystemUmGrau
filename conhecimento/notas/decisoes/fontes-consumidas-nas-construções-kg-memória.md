---
tags: [contaminavam, decisao, livre, map, opencode, resultados]
aliases: [Fontes consumidas nas construções (KG + memória)]
date: 2026-09-03
---

# Fontes consumidas nas construções (KG + memória)

**Fonte:** opencode

## O que foi feito
O catálogo de 142 fontes agora alimenta o ecossistema em 3 pontos de construção.

## Detalhes da integração
- auto_evolution.py: cada Gap carrega `sources` (até 3 fontes autoritativas)
  mapeadas da categoria do gap para domínios relevantes via GAP_DOMAIN_MAP,
  com fallback que evita domínio `general` (Git/Vim contaminavam resultados).
- knowledge_graph.py: método `suggest_sources(query)` complementa a busca do
  grafo com fontes autoritativas do registry. Fail-soft (retorna vazio sem registry).
- memory_engine.py: `add_memory` e `_merge_memory` enriquecem cada memória com
  `source_refs` (proveniência de fontes). Fail-soft (retorna vazio sem registry).

## Bug corrigido
O matching de domínio em `get_relevant_sources` usava substring —
`'c' in 'database persistence'` era True (letra 'c' em 'database'). Isso fazia
fontes de C contaminarem buscas de qualquer domínio. Correção: fronteira de
palavra (domain_words) + penalização de domínios genéricos no texto livre.

## 
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]