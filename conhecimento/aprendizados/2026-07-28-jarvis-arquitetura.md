# DecisÃ£o: Arquitetura Jarvis App

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

- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[cluster-hub-programacao]]