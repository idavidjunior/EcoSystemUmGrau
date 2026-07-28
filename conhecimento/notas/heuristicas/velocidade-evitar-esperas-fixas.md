---
tags: [heuristica, efficiency]
aliases: [Velocidade = evitar esperas fixas]
date: 2026-07-27
---

# Velocidade = evitar esperas fixas

**Dominio:** efficiency | **Fonte:** session

Esperar 10s 'para garantir' custa 10s por operacao. Usar waitForElement com polling a cada 100ms e timeout de 10s: se elemento aparece em 200ms, voce ganhou 9.8s
