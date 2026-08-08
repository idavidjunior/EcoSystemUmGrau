---
tags: [comandos, decisao, falando, opencode, ouvindo, resultados]
aliases: [﻿# DecisÃ£o: Arquitetura Jarvis App]
date: 2026-08-08
---

# ﻿# DecisÃ£o: Arquitetura Jarvis App

**Fonte:** opencode

﻿# DecisÃ£o: Arquitetura Jarvis App

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** jarvis, android, arquitetura, mcp, mobile

## Contexto
Necessidade de um app Android que funcione como assistente de voz (Jarvis) para o ecossistema, operando em segundo plano com tela desligada, falando resultados e ouvindo comandos.

## DecisÃ£o
Arquitetura em duas camadas:
- **PC (backend):** `notifier_bridge.py` (WebSocket) + `mcp-knowledge-server.py` (MCP, jÃ¡ existe)
- **Android (frontend):** Foreground Service + TTS/STT + MCP Client, comunicaÃ§Ã£o via WebSocket/HTTP em rede local

## RepositÃ³rios base identificados
1. **niki914/agentic-nexus** (MIT, Kotlin) â€” jÃ¡ tem MCP nativo, foreground service, agente. Ideal como base.
2. **yuga-hashimoto/OpenClawAssistant** â€” mais leve, wake word "Jarvis" embutido, conecta a qualquer backend via webhook.

## Impacto
App leve e eficiente, reaproveitando todo o ecossistema jÃ¡ construÃ­do. MÃ­nimo cÃ³digo novo necessÃ¡rio.
 // ﻿# DecisÃ£o: Arquitetura Jarvis App

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** jarvis, android, arquitetura, mcp, mobile

## Contexto
Necessidade de um app Android que funcione como assistente de voz (Jarvis) para o ecossistema, operando em segundo plano com tela desligada, falando resultados e ouvindo comandos.

## DecisÃ£o
Arquitetura em duas camadas:
- **PC (backend):** `notifier_bridge.py` (WebSocket) + `mcp-knowledge-server.py` (MCP, jÃ¡ existe)
- **Android (frontend):** Foreground Service + TTS/STT + MCP Client, comunicaÃ§Ã£o via WebSocket/HTTP em rede local

## RepositÃ³rios base identificados
1. **niki914/agentic-nexus** (MIT, Kotlin) â€” jÃ¡ tem MCP nativo, foreground service, agente. Ideal como base.
2. **yuga-hashimoto/OpenClawAssistant** â€” mais leve, wake word "Jarvis" embutido, conecta a qualquer backend via webhook.

## Impacto
App leve e eficiente, reaproveitando todo o ecossistema jÃ¡ construÃ­do. MÃ­nimo cÃ³digo novo necessÃ¡rio.

## Conexoes

- [[aprendizado-â-2026-07-31-â-pontuaãão-automãtica-de-transcriã]] // ﻿# DecisÃ£o: Arquitetura Jarvis App

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** jarvis, android, arquitetura, mcp, mobile

## Contexto
Necessidade de um app Android que funcione como assistente de voz (Jarvis) para o ecossistema, operando em segundo plano com tela desligada, falando resultados e ouvindo comandos.

## DecisÃ£o
Arquitetura em duas camadas:
- **PC (backend):** `notifier_bridge.py` (WebSocket) + `mcp-knowledge-server.py` (MCP, jÃ¡ existe)
- **Android (frontend):** Foreground Service + TTS/STT + MCP Client, comunicaÃ§Ã£o via WebSocket/HTTP em rede local

## RepositÃ³rios base identificados
1. **niki914/agentic-nexus** (MIT, Kotlin) â€” jÃ¡ tem MCP nativo, foreground service, agente. Ideal como base.
2. **yuga-hashimoto/OpenClawAssistant** â€” mais leve, wake word "Jarvis" embutido, conecta a qualquer backend via webhook.

## Impacto
App leve e eficiente, reaproveitando todo o ecossistema jÃ¡ construÃ­do. MÃ­nimo cÃ³digo novo necessÃ¡rio.

## Conexoes

- [[aprendizado-â-2026-07-31-â-pontuaãão-automãtica-de-transcriã]] // ﻿# DecisÃ£o: Arquitetura Jarvis App

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** jarvis, android, arquitetura, mcp, mobile

## Contexto
Necessidade de um app Android que funcione como assistente de voz (Jarvis) para o ecossistema, operando em segundo plano com tela desligada, falando resultados e ouvindo comandos.

## DecisÃ£o
Arquitetura em duas camadas:
- **PC (backend):** `notifier_bridge.py` (WebSocket) + `mcp-knowledge-server.py` (MCP, jÃ¡ existe)
- **Android (frontend):** Foreground Service + TTS/STT + MCP Client, comunicaÃ§Ã£o via WebSocket/HTTP em rede local

## RepositÃ³rios base identificados
1. **niki914/agentic-nexus** (MIT, Kotlin) â€” jÃ¡ tem MCP nativo, foreground service, agente. Ideal como base.
2. **yuga-hashimoto/OpenClawAssistant** â€” mais leve, wake word "Jarvis" embutido, conecta a qualquer backend via webhook.

## Impacto
App leve e eficiente, reaproveitando todo o ecossistema jÃ¡ construÃ­do. MÃ­nimo cÃ³digo novo necessÃ¡rio.

## Conexoes

- [[aprendizado-â-2026-07-31-â-pontuaãão-automãtica-de-transcriã]] // ﻿# DecisÃ£o: Arquitetura Jarvis App

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** jarvis, android, arquitetura, mcp, mobile

## Contexto
Necessidade de um app Android que funcione como assistente de voz (Jarvis) para o ecossistema, operando em segundo plano com tela desligada, falando resultados e ouvindo comandos.

## DecisÃ£o
Arquitetura em duas camadas:
- **PC (backend):** `notifier_bridge.py` (WebSocket) + `mcp-knowledge-server.py` (MCP, jÃ¡ existe)
- **Android (frontend):** Foreground Service + TTS/STT + MCP Client, comunicaÃ§Ã£o via WebSocket/HTTP em rede local

## RepositÃ³rios base identificados
1. **niki914/agentic-nexus** (MIT, Kotlin) â€” jÃ¡ tem MCP nativo, foreground service, agente. Ideal como base.
2. **yuga-hashimoto/OpenClawAssistant** â€” mais leve, wake word "Jarvis" embutido, conecta a qualquer backend via webhook.

## Impacto
App leve e eficiente, reaproveitando todo o ecossistema jÃ¡ construÃ­do. MÃ­nimo cÃ³digo novo necessÃ¡rio.

## Conexoes

- [[aprendizado-â-2026-07-31-â-pontuaãão-automãtica-de-transcriã]]
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]