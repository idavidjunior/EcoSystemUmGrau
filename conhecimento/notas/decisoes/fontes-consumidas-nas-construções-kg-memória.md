---
tags: [decisao, github, opencode, primários, resultados, vim]
aliases: [Fontes consumidas nas construções (KG + memória)]
date: 2026-09-03
---

# Fontes consumidas nas construções (KG + memória)

**Fonte:** opencode

---
tipo: decisao
tags: [fontes, source-registry, knowledge-graph, memory-engine, auto-evolution]
data: 2026-09-03
contexto: >
  Decision de garantir que as 142+ fontes do catálogo (config/programming_sources.yaml)
  sejam consumidas nas construções do ecossistema, não apenas decorativas.
decisao: >
  Integrar o source_registry em 3 pontos de consumo:
  (1) auto_evolution.py — Gap.sources enriquecido via _enrich_gaps_with_sources
  com GAP_DOMAIN_MAP (fallback preferindo domínios primários sobre general);
  (2) knowledge_graph.py — novo método suggest_sources() que surfacia fontes
  autoritativas como referências nas consultas (fail-soft);
  (3) memory_engine.py — add_memory e _merge_memory enriquecem cada memória
  com source_refs automáticos (proveniência) via _enrich_source_refs (fail-soft).
  Corrigido bug em source_registry.get_relevant_sources: matching por domínio
  usava substring ('c' casava com 'database', 'security'). Agora usa fronteira
  de palavra (domain_words), e fontes de domínio genérico (c, general, git, vim)
  só pontuam via texto livre se o tópico claramente as mencionar.
impacto: >
  Buscas de fontes agora retornam o domínio correto (ex.: 'security' → OWASP/CVE/NVD;
  'database persistence' → PostgreSQL/SQLite/MySQL). Teste E2E validou os 3 pontos.
---
# Fontes consumidas nas construções (KG + memória)

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

## Validação
Teste E2E confirmou: gaps 26/26 com fontes; suggest_sources('security') →
OWASP/CVE/NVD; memória nova enriquecida com source_refs (cppreference, Python GitHub).
Preflight técnico e ético passaram.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]