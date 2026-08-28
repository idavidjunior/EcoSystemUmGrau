---
tags: [decisao, nesta, opencode, regressão, removido, tarefa]
aliases: [oficializacao narrador edge cerebro vivo]
date: 2026-08-28
---

# oficializacao narrador edge cerebro vivo

**Fonte:** opencode

---
tipo: decisao
tags: [narrador, widget, arquitetura, oficializacao, duplicidade, limpeza]
data: 2026-08-28
contexto: Duplicidade de narradores (narrador_desktop.py standalone vs thread do widget_edge.py) gerava referências mortas, atalhos quebrados e checks de auditor desatualizados. O usuário decidiu: Narrador Edge (widget_edge.py) e Cérebro Vivo (widget_grafo.py) são os dois oficiais; qualquer outro é duplicidade.
decisao:
  - Narrador oficial é a thread interna de scripts/widget_edge.py (única implementação).
  - Cérebro Vivo oficial é scripts/widget_grafo.py.
  - Duplicidades movidas para scripts/_legado/: narrador_desktop.py, narrador_start.bat, recreate_narrator_shortcut.ps1.
  - Stub scripts/unified_bridge.py descontinuado (sem consumidores) aponta para tts_service.py + widget_edge.py.
  - system_guardian.py: is_narrador_up() via runtime/narracao_estado.json; start_narrador() é no-op; proteção de kill cobre apenas tts_service, widget_edge, widget_grafo (removido narrador_desktop).
  - scripts/jarvis_audio.py: NARRADOR = scripts/widget_edge.py; iniciar_narrador inicia o widget quando o narrador não está ativo.
  - scripts/reiniciarjarvis.bat: inicia widget_edge.py + widget_grafo.py (substitui narrador_desktop.py e widget_controle_jarvis.py inexistente).
  - scripts/frases_manager.py e scripts/narrador_dedup.py: docstrings corrigidas para refletir implementação única no widget.
  - config/inventario_estruturas.json: entrada narrador_desktop → narrador_desktop_legado (scripts/_legado/narrador_desktop.py), marcada DESCONTINUADO.
  - scripts/audit_eco.py: probes honestas — narrador via widget_edge.py + STOP_FLAG (runtime/parar_fala.flag); duplicidade sinalizada como WARN se narrador_desktop rodar; integração de tema como WARN (escopo delegado, sem reimplementar ler_tema_sincronizado).
impacto:
  - Auditor: score 93/100, 0 erros, 15 warnings (pré-existentes de UI/tema ou pendências honradas).
  - Fonte única do narrador reduz ambiguidade, atalhos quebrados e falsos processos.
  - py_compile OK em todos os scripts alterados.
nota: Reset de posição no startup segue como pendência conhecida no widget (WARN), sem regressão nesta tarefa. // ---
tipo: decisao
tags: [narrador, widget, arquitetura, oficializacao, duplicidade, limpeza]
data: 2026-08-28
contexto: Duplicidade de narradores (narrador_desktop.py standalone vs thread do widget_edge.py) gerava referências mortas, atalhos quebrados e checks de auditor desatualizados. O usuário decidiu: Narrador Edge (widget_edge.py) e Cérebro Vivo (widget_grafo.py) são os dois oficiais; qualquer outro é duplicidade.
decisao:
  - Narrador oficial é a thread interna de scripts/widget_edge.py (única implementação).
  - Cérebro Vivo oficial é scripts/widget_grafo.py.
  - Duplicidades movidas para scripts/_legado/: narrador_desktop.py, narrador_start.bat, recreate_narrator_shortcut.ps1.
  - Stub scripts/unified_bridge.py descontinuado (sem consumidores) aponta para tts_service.py + widget_edge.py.
  - system_guardian.py: is_narrador_up() via runtime/narracao_estado.json; start_narrador() é no-op; proteção de kill cobre apenas tts_service, widget_edge, widget_grafo (removido narrador_desktop).
  - scripts/jarvis_audio.py: NARRADOR = scripts/widget_edge.py; iniciar_narrador inicia o widget quando o narrador não está ativo.
  - scripts/reiniciarjarvis.bat: inicia widget_edge.py + widget_grafo.py (substitui narrador_desktop.py e widget_controle_jarvis.py inexistente).
  - scripts/frases_manager.py e scripts/narrador_dedup.py: docstrings corrigidas para refletir implementação única no widget.
  - config/inventario_estruturas.json: entrada narrador_desktop → narrador_desktop_legado (scripts/_legado/narrador_desktop.py), marcada DESCONTINUADO.
  - scripts/audit_eco.py: probes honestas — narrador via widget_edge.py + STOP_FLAG (runtime/parar_fala.flag); duplicidade sinalizada como WARN se narrador_desktop rodar; integração de tema como WARN (escopo delegado, sem reimplementar ler_tema_sincronizado).
impacto:
  - Auditor: score 93/100, 0 erros, 15 warnings (pré-existentes de UI/tema ou pendências honradas).
  - Fonte única do narrador reduz ambiguidade, atalhos quebrados e falsos processos.
  - py_compile OK em todos os scripts alterados.
nota: Reset de posição no startup segue como pendência conhecida no widget (WARN), sem regressão nesta tarefa.

## Conexoes

- [[2026-08-04-tamanho-por-uso-real-iniciar-gui-com-pythonw-impl]]
- [[arquitetura-adrs-e-governança-de-decisões-por-que-e-como-reg]]
- [[arquitetura-camadas-vs-hexagonal-vs-clean-architecture-depen]]
- [[arquitetura-ddd-bounded-contexts-agregados-e-ubiquitous-lang]]
- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[arquitetura-event-driven-e-mensageria-filas-tópicos-e-consis]]
- [[arquitetura-resiliência-retry-circuit-breaker-backoff-e-idem]]
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]