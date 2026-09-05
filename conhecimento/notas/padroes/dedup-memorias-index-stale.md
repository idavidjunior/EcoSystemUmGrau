---
tags: [antigos, desativados, monkeypatch, opencodeopencode, padrao, removidos]
aliases: [dedup memorias index stale]
date: 2026-09-05
---

# dedup memorias index stale

**Fonte:** opencode+opencode

Tipo: padrao

Tags: [memoria, dedup, index-stale, memory-semantic, tfidf, consolidacao, calibracao]

Data: 2026-09-05

Contexto: memories.json acumulava duplicatas de memórias (704 entradas, muitas com o mesmo título/summary). Além disso, o índice TF-IDF era reconstruído a cada checagem porque index_stale() retornava sempre True, e o rebuild denso ficava desatualizado.

Decisão: Três linhas de ataque. 1) Dedup determinístico: DEDUP_MIN_SCORE foi recalibrado de 0.80 para 0.50 (duplicatas de título idêntico mediam TF-IDF 0.40-0.54; não-duplicatas acima de 0.60 eram 0 de 99 pares amostrados). Camada 1: _normalizar_titulo (título normalizado idêntico -> merge imediato). Camada 2: _normalizar_titulo + busca TF-IDF com threshold 0.50. 2) Consolidação retroativa 704->637 (29 grupos, 67 duplicatas), canônica = mais recente por created_at (lista[-1] do grupo), ids antigos removidos, source_refs desativados via monkeypatch me._enrich_source_refs=lambda task,summary:[] porque SourceRegistry estou
## Conexoes

- [[aegis-barra-progresso-tempo-real]]
- [[certificacao-forense-de-processos-boot-do-watchdog]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-4-teste-do-ciclo-de-polling]]
- [[padrao-hub-padroes]]
- [[saudacoes-inteligentes-reconexao-vs-primeira-vez]]