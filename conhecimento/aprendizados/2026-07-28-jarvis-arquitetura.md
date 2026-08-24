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

## Conexoes

- [[aprendizado-2026-07-31-horas-faladas-corretamente-no-tts-do-]]
- [[arquitetura-adrs-e-governança-de-decisões-por-que-e-como-reg]]
- [[arquitetura-camadas-vs-hexagonal-vs-clean-architecture-depen]]
- [[arquitetura-ddd-bounded-contexts-agregados-e-ubiquitous-lang]]
- [[arquitetura-estilos-de-arquitetura-monólito-soa-microserviço]]
- [[arquitetura-event-driven-e-mensageria-filas-tópicos-e-consis]]
- [[arquitetura-resiliência-retry-circuit-breaker-backoff-e-idem]]
- [[cluster-hub-programacao]]