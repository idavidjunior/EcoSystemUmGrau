---
tags: [calls, cognitivo, foit, fout, performance, variavel]
aliases: [Espera adaptativa por tipo de recurso]
date: 2026-08-12
---

# Espera adaptativa por tipo de recurso

**Dominio:** performance

Tempos de carregamento variam por tipo: HTML inicial (rede), CSS (bloqueante ate parsed), JS (bloqueante ate executed), imagens (nao bloqueantes), fontes (FOUT/FOIT), API calls (variavel). Navegacao so esta completa quando HTML+CSS+JS processaram. Imagens podem continuar carregando
## Conexoes

- [[cluster-hub-navegacao]]
- [[cognitivo-hub-cognitivo]]
- [[performance-caching-em-camadas-e-invalidação]]
- [[performance-complexidade-assintótica-vs-custo-real]]
- [[performance-concorrência-e-paralelismo-quando-vale-a-pena]]
- [[performance-profiling-primeiro-onde-o-tempo-realmente-vai]]