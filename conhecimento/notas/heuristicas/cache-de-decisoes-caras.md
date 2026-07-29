---
tags: [heuristica, systemdesign]
aliases: [Cache de decisoes caras]
date: 2026-07-29
---

# Cache de decisoes caras

**Dominio:** system_design | **Fonte:** meta_cognition

Se uma computacao e deterministica e custosa, cacheie o resultado. Se o resultado pode mudar, invalide o cache explicitamente. Nunca confie em TTL para invalidação de dados que precisam ser consistentes.
