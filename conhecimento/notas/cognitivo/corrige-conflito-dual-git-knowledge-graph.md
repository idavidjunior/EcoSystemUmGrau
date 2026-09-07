---
tags: [cima, cognitivo, general, qualquer, restauracao, runtime]
aliases: [corrige conflito dual git knowledge graph]
date: 2026-09-05
---

# corrige conflito dual git knowledge graph

**Dominio:** general

---
tipo: erro
tags: [git, persistencia, knowledge-graph, double-tracking, vigia]
data: 2026-09-05
contexto: knowledge_graph.json era versionado simultaneamente por dois repositorios (repo filho ler-runtime com .git proprio e repo pai EcoSystemUmGrau). O repo filho teve o graph truncado (722KB) commitado no HEAD local e no remote; o vigilante rodava git pull --ff-only e merges que recomitavam o estado truncado por cima de qualquer restauracao.
decisao: Restaurar o graph da fonte saudavel .bak_sa
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]