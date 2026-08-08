---
tags: [aprendizados, conectados, cores, decisao, frontmatter, opencode]
aliases: [vault obsidian cerebro vivo grafo]
date: 2026-08-08
---

# vault obsidian cerebro vivo grafo

**Fonte:** opencode

---
tipo: decisao
tags:
  - obsidian
  - knowledge-graph
  - grafo
  - links-bidirecionais
  - vault
  - visualizacao
  - clausula-petrea
data: 2026-08-02
contexto: Usuario perguntou se o ecossistema funciona como o Obsidian (cerebro vivo com grafo interativo). Diagnostico: tinhamos a camada de dados (knowledge_graph.json, 117KB, memorias) mas ZERO camada visual — notas geradas eram ilhas sem nenhum link [[...]].
decisao: Evoluimos scripts/generate-obsidian-notes.py (estrutura existente, nao criada nova) para gerar o vault vivo: (1) 294+ notas por categoria a partir do knowledge_graph.json, (2) 15 notas-hub (7 por categoria + 7 por cluster de projeto + home), (3) links bidirecionais [[...]] conectando notas por tag/fonte (273/279 notas conectadas), (4) injecao da secao "## Conexoes" nos aprendizados de conhecimento/aprendizados (11 conectados por cluster). Clusteres mapeiam fontes do graph para projetos: android, mp3player, ler, navegacao, ecossistema, cognicao. OBSIDIAN: abrir conhecimento/ como vault -> grafo force-directed automatico.
impacto: O conhecimento agora e uma teia navegavel (nao mais ilhas). 3 pilares do Obsidian atendidos: rastreamento de links bidirecionais (secao Conexoes), grafo force-directed (abrir vault), filtros/cores por tag (frontmatter tags ja existe). README atualizado com secao "Vault Obsidian (cerebro vivo)".
detalhe: Bug encontrado e corrigido: seccao_conexoes() gerava "## Conexoes\n\n- [[...]]" (linha em branco extra do join), mas a regex de remocao para idempotencia esperava "## Conexoes\n-". Fix: regex tolerante a linha em branco (r'\n## Conexoes\n+?(?:- \[\[[^\]]+\]\]\n?)+'). Resultado: idempotente, 0 duplicacoes.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]