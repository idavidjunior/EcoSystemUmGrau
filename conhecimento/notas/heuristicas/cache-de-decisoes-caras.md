---
tags: [consistentes, explicitamente, heuristica, invalide, precisam, systemdesign]
aliases: [Cache de decisoes caras]
date: 2026-08-03
---

# Cache de decisoes caras

**Dominio:** system_design | **Fonte:** meta_cognition

Se uma computacao e deterministica e custosa, cacheie o resultado. Se o resultado pode mudar, invalide o cache explicitamente. Nunca confie em TTL para invalidação de dados que precisam ser consistentes.
## Conexoes

- [[cluster-hub-cognicao]]
- [[estrategia-de-fallback-em-cadeia-chain-of-responsibility]]
- [[estrategia-de-loop-autonomo-planejar-executar-verificar-corr]]
- [[heuristica-hub-heuristicas]]
- [[padrao-de-escrita-atomica-para-persistencia]]
- [[sempre-esperar-o-inesperado-em-es]]