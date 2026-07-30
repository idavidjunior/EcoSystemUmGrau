---
tags: [heuristica, efficiency]
aliases: [Primeiro scan, depois interaja]
date: 2026-07-30
---

# Primeiro scan, depois interaja

**Dominio:** efficiency | **Fonte:** session

Antes de qualquer acao, faca um scan completo do estado atual: elementos visiveis, modais, estado de loading. Agir cegamente leva a 3x mais retries. 1 scan evita 3 falhas
