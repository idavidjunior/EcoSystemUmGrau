---
tags: [123, element-detection, exato, heuristica, mudar, quebra]
aliases: [Seletor mais especifico = mais fragil]
date: 2026-08-08
---

# Seletor mais especifico = mais fragil

**Dominio:** element-detection | **Fonte:** session

data-testid=product-123 e exato mas quebra se o ID mudar. Preferir seletores semanticos: [data-testid^=product-] ou .product-card capturam variacoes sem quebrar
## Conexoes

- [[canvas-e-graficos-template-matching]]
- [[cluster-hub-navegacao]]
- [[heuristica-hub-heuristicas]]
- [[hierarquia-de-confianca-de-seletores]]