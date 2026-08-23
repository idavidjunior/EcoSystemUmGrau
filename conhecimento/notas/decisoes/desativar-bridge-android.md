---
tags: [decisao, etc, inicia, local, opencode, vigilante]
aliases: [desativar bridge android]
date: 2026-08-23
---

# desativar bridge android

**Fonte:** opencode

---
tipo: decisao
tags: [bridge, jarvis-bridge, android, watchdog, duplicacao-voz]
data: 2026-08-18
contexto: >
  Jarvis falando duplicado. Investigacao revelou 3 fontes possiveis:
  (1) unified_bridge.py fala localmente via SpeechPipeline,
  (2) jarvis_bridge.py gera audio para clientes WebSocket (Android),
  (3) tts_service.py antigo (PID 4588) rodava sozinho com SpeechPipeline local.
  O watchdog.ps1 auto-reiniciava jarvis_bridge.py na porta 8765.
decisao: >
  Desativar jarvis_bridge.py via flag (runtime/bridge_enabled.flag).
  Modificar watchdog.ps1 para so reiniciar bridge quando flag existir.
  Flag nao existe = bridge desativado por padrao.
  Para reativar: criar runtime/bridge_enabled.flag e watchdog reinicia automaticamente.
  Atualizar architecture_integrity_monitor.py para reportar INFO quando bridge desativado.
impacto: >
  Elimina uma das fontes de voz duplicada.
  App Android so conecta quando bridge estiver ativo.
  Watchdog nao mata outros servicos (serve, vigilante, etc).
  Para reativar: usuario avisa, crio flag, watchdog inicia bridge.
---

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]