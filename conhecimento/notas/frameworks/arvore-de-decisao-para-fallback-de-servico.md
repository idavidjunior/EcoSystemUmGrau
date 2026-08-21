---
tags: [framework, modo, preferencia, relaxado, secundaria]
aliases: [Arvore de Decisao para Fallback de Servico]
date: 2026-08-20
---

# Arvore de Decisao para Fallback de Servico

Estrategia para servicos com multiplas fontes de dados em ordem de preferencia.

1. Tente fonte primaria (mais precisa). Se sucesso com score >= threshold, retorne. 2. Se falhou ou score baixo, armazene melhor resultado ate agora e tente fonte secundaria. 3. Compare scores, fique com o maior. 4. Se nenhuma fonte atingiu threshold minimo, retorne null (ou tente modo relaxado). 5. Registre metricas: qual fonte venceu, scores, tempo de resposta. Isso permite ajustar thresholds e ordem das fontes baseado em dados reais.
## Conexoes

- [[cluster-hub-cognicao]]
- [[framework-hub-frameworks]]