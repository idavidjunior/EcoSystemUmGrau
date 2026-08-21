---
tags: [comandos, decisao, falando, opencode, ouvindo, resultados]
aliases: [# Decisão: Arquitetura Jarvis App]
date: 2026-08-21
---

# # Decisão: Arquitetura Jarvis App

**Fonte:** opencode

# Decisão: Arquitetura Jarvis App

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** jarvis, android, arquitetura, mcp, mobile

## Contexto
Necessidade de um app Android que funcione como assistente de voz (Jarvis) para o ecossistema, operando em segundo plano com tela desligada, falando resultados e ouvindo comandos.

## Decisão
Arquitetura em duas camadas:
- **PC (backend):** `notifier_bridge.py` (WebSocket) + `mcp-knowledge-server.py` (MCP, já existe)
- **Android (frontend):** Foreground Service + TTS/STT + MCP Client, comunicação via WebSocket/HTTP em rede local

## Repositórios base identificados
1. **niki914/agentic-nexus** (MIT, Kotlin) — já tem MCP nativo, foreground service, agente. Ideal como base.
2. **yuga-hashimoto/OpenClawAssistant** — mais leve, wake word "Jarvis" embutido, conecta a qualquer backend via webhook.

## Impacto
App leve e eficiente, reaproveitando todo o ecossistema já construído. Mínimo código novo necessário.
 // # Decisão: Arquitetura Jarvis App

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** jarvis, android, arquitetura, mcp, mobile

## Contexto
Necessidade de um app Android que funcione como assistente de voz (Jarvis) para o ecossistema, operando em segundo plano com tela desligada, falando resultados e ouvindo comandos.

## Decisão
Arquitetura em duas camadas:
- **PC (backend):** `notifier_bridge.py` (WebSocket) + `mcp-knowledge-server.py` (MCP, já existe)
- **Android (frontend):** Foreground Service + TTS/STT + MCP Client, comunicação via WebSocket/HTTP em rede local

## Repositórios base identificados
1. **niki914/agentic-nexus** (MIT, Kotlin) — já tem MCP nativo, foreground service, agente. Ideal como base.
2. **yuga-hashimoto/OpenClawAssistant** — mais leve, wake word "Jarvis" embutido, conecta a qualquer backend via webhook.

## Impacto
App leve e eficiente, reaproveitando todo o ecossistema já construído. Mínimo código novo necessário.

## Conexoes

- [[aprendizado-â-2026-07-31-â-pontuaãão-automãtica-de-transcriã]] // # Decisão: Arquitetura Jarvis App

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** jarvis, android, arquitetura, mcp, mobile

## Contexto
Necessidade de um app Android que funcione como assistente de voz (Jarvis) para o ecossistema, operando em segundo plano com tela desligada, falando resultados e ouvindo comandos.

## Decisão
Arquitetura em duas camadas:
- **PC (backend):** `notifier_bridge.py` (WebSocket) + `mcp-knowledge-server.py` (MCP, já existe)
- **Android (frontend):** Foreground Service + TTS/STT + MCP Client, comunicação via WebSocket/HTTP em rede local

## Repositórios base identificados
1. **niki914/agentic-nexus** (MIT, Kotlin) — já tem MCP nativo, foreground service, agente. Ideal como base.
2. **yuga-hashimoto/OpenClawAssistant** — mais leve, wake word "Jarvis" embutido, conecta a qualquer backend via webhook.

## Impacto
App leve e eficiente, reaproveitando todo o ecossistema já construído. Mínimo código novo necessário.

## Conexoes

- [[aprendizado-â-2026-07-31-â-pontuaãão-automãtica-de-transcriã]] // # Decisão: Arquitetura Jarvis App

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** jarvis, android, arquitetura, mcp, mobile

## Contexto
Necessidade de um app Android que funcione como assistente de voz (Jarvis) para o ecossistema, operando em segundo plano com tela desligada, falando resultados e ouvindo comandos.

## Decisão
Arquitetura em duas camadas:
- **PC (backend):** `notifier_bridge.py` (WebSocket) + `mcp-knowledge-server.py` (MCP, já existe)
- **Android (frontend):** Foreground Service + TTS/STT + MCP Client, comunicação via WebSocket/HTTP em rede local

## Repositórios base identificados
1. **niki914/agentic-nexus** (MIT, Kotlin) — já tem MCP nativo, foreground service, agente. Ideal como base.
2. **yuga-hashimoto/OpenClawAssistant** — mais leve, wake word "Jarvis" embutido, conecta a qualquer backend via webhook.

## Impacto
App leve e eficiente, reaproveitando todo o ecossistema já construído. Mínimo código novo necessário.

## Conexoes

- [[aprendizado-â-2026-07-31-â-pontuaãão-automãtica-de-transcriã]] // # Decisão: Arquitetura Jarvis App

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** jarvis, android, arquitetura, mcp, mobile

## Contexto
Necessidade de um app Android que funcione como assistente de voz (Jarvis) para o ecossistema, operando em segundo plano com tela desligada, falando resultados e ouvindo comandos.

## Decisão
Arquitetura em duas camadas:
- **PC (backend):** `notifier_bridge.py` (WebSocket) + `mcp-knowledge-server.py` (MCP, já existe)
- **Android (frontend):** Foreground Service + TTS/STT + MCP Client, comunicação via WebSocket/HTTP em rede local

## Repositórios base identificados
1. **niki914/agentic-nexus** (MIT, Kotlin) — já tem MCP nativo, foreground service, agente. Ideal como base.
2. **yuga-hashimoto/OpenClawAssistant** — mais leve, wake word "Jarvis" embutido, conecta a qualquer backend via webhook.

## Impacto
App leve e eficiente, reaproveitando todo o ecossistema já construído. Mínimo código novo necessário.

## Conexoes

- [[aprendizado-â-2026-07-31-â-pontuaãão-automãtica-de-transcriã]]
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]