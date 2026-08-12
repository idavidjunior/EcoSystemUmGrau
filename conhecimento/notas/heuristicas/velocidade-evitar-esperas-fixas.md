---
tags: [10s, dominio, efficiency, heuristica, operacao, timeout]
aliases: [Velocidade = evitar esperas fixas]
date: 2026-08-12
---

# Velocidade = evitar esperas fixas

**Dominio:** efficiency | **Fonte:** session

Esperar 10s 'para garantir' custa 10s por operacao. Usar waitForElement com polling a cada 100ms e timeout de 10s: se elemento aparece em 200ms, voce ganhou 9.8s
## Conexoes

- [[30s-regra-de-timeout-maximo]]
- [[cluster-hub-navegacao]]
- [[heuristica-de-densidade-de-informacao]]
- [[heuristica-hub-heuristicas]]
- [[primeiro-scan-depois-interaja]]