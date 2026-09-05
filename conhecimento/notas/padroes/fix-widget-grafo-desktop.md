---
tags: [efeito, geometria, opencode, padrao, real, sai]
aliases: [fix widget grafo desktop]
date: 2026-08-09
---

# fix widget grafo desktop

**Fonte:** opencode

Tipo: padrao

Tags: [widget, grafo, pywebview, vis-network, fix]

Data: 2026-08-09

Contexto: Varedura do widget desktop "Cerebro Vivo" (scripts/widget_grafo.py) identificou 8 problemas; todos corrigidos.

Decisão: Substituir polling JS (api-inject.js) por watcher Python com lock; criar handles mk-drag/mk-resize via resize.js injetado no body; bridge expoe mover/redimensionar; tema via CSS vars + data-theme; guardar_geo ignora (0,0) e clampeia a tela.

Impacto: Widget agora move/redimensiona de verdade, reflete mudancas do vault ao vivo, nao tem reload em loop, tema tem efeito real e geometria nunca sai da tela.
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]