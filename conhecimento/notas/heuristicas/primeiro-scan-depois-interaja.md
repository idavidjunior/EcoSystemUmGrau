---
tags: [atual, completo, efficiency, estado, faca, heuristica]
aliases: [Primeiro scan, depois interaja]
date: 2026-08-13
---

# Primeiro scan, depois interaja

**Dominio:** efficiency | **Fonte:** session

Antes de qualquer acao, faca um scan completo do estado atual: elementos visiveis, modais, estado de loading. Agir cegamente leva a 3x mais retries. 1 scan evita 3 falhas
## Conexoes

- [[30s-regra-de-timeout-maximo]]
- [[cluster-hub-navegacao]]
- [[heuristica-de-densidade-de-informacao]]
- [[heuristica-hub-heuristicas]]
- [[velocidade-evitar-esperas-fixas]]