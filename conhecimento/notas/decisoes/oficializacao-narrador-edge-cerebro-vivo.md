---
tags: [cobre, decisao, desatualizados, desk, opencode, removido]
aliases: [oficializacao narrador edge cerebro vivo]
date: 2026-08-28
---

# oficializacao narrador edge cerebro vivo

**Fonte:** opencode

Tipo: decisao

Tags: [narrador, widget, arquitetura, oficializacao, duplicidade, limpeza]

Data: 2026-08-28

contexto: Duplicidade de narradores (narrador_desktop.py standalone vs thread do widget_edge.py) gerava referências mortas, atalhos quebrados e checks de auditor desatualizados. O usuário decidiu: Narrador Edge (widget_edge.py) e Cérebro Vivo (widget_grafo.py) são os dois oficiais; qualquer outro é duplicidade.

decisao: , Narrador oficial é a thread interna de scripts/widget_edge.py (única implementação)., Cérebro Vivo oficial é scripts/widget_grafo.py., Duplicidades movidas para scripts/_legado/: narrador_desktop.py, narrador_start.bat, recreate_narrator_shortcut.ps1., Stub scripts/unified_bridge.py descontinuado (sem consumidores) aponta para tts_service.py + widget_edge.py., system_guardian.py: is_narrador_up() via runtime/narracao_estado.json; start_narrador() é no-op; proteção de kill cobre apenas tts_service, widget_edge, widget_grafo (removido narrador_desk
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]