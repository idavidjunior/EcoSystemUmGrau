---
tags: [heuristica, element-detection]
aliases: [Seletor mais especifico = mais fragil]
date: 2026-07-30
---

# Seletor mais especifico = mais fragil

**Dominio:** element-detection | **Fonte:** session

data-testid=product-123 e exato mas quebra se o ID mudar. Preferir seletores semanticos: [data-testid^=product-] ou .product-card capturam variacoes sem quebrar
