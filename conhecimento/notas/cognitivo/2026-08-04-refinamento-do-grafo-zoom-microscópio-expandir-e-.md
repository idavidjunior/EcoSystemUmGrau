---
tags: [cognitivo, dominio, general, interconectados, nós, viva]
aliases: [2026-08-04: Refinamento do grafo — zoom microscópio, expandi]
date: 2026-08-04
---

# 2026-08-04: Refinamento do grafo — zoom microscópio, expandir e cognição viva

**Dominio:** general

## Decisões técnicas validadas (online)

### vis-network physics (barnesHut)
- `stabilization: false` + `timestep: 0.2` + `maxVelocity: 6` + `minVelocity: 0` + `adaptiveTimestep: false` → movimento perpétuo e lento (nunca "congela").
- `barnesHut.avoidOverlap: 0.55` usa o raio do nó para evitar sobreposição (vis.js docs).
- `damping: 0.88` → balanço suave/amortecido.
- `improvedLayout` só funciona se passado **antes** de `new vis.Network()`, e pode falhar em grafos densos (>100 nós interconectados); com stabilization:false deixamos o balanço orgânico espalhar.

### Zoom microscópio (fonte legível ao ampliar)
- vis.js NÃO tem opção "fix label size" pronta. A compensação validada na comunidade:
  `font.size = base / scale` (aplica no evento `network.on('zoom')`).
- Implementado: `font.size = 13 / scale` (clamp 0.4 ≤ scale ≤ 22).

### Expandir (clustering por zoom)
- vis.js possui `network.cluster({joinCondition, clusterNode})` e `network.openCluster(id)`.
- Estratégia: em zoom-out, agrup
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]