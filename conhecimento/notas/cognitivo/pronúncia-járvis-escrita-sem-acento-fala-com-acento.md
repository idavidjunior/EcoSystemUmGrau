---
tags: [cognitivo, dominio, general, jarvís, sílaba, última]
aliases: [Pronúncia "Járvis" (escrita sem acento, fala com acento)]
date: 2026-08-23
---

# Pronúncia "Járvis" (escrita sem acento, fala com acento)

**Dominio:** general

# Pronúncia "Járvis" (escrita sem acento, fala com acento)

- **Data:** 01/08/2026
- **Sessão:** Pedido direto do usuário sobre pronúncia do nome do assistente

## Regra permanente
- **Escrita:** sempre "Jarvis", **sem acento**.
- **Pronúncia (fala/TTS):** "Járvis" — acento tônico no primeiro A (JA-rvis, fonético: /ˈʒaʁ.vis/).
- Nunca pronunciar "Jár-vis" com o segundo A fechado nem com acento na última sílaba ("Jarvís").

## Implementação
- Registrado em `scripts/pronuncias.json`:
  `"jarvis": 

# Pronúncia "Járvis" (escrita sem acento, fala com acento)

- **Data:** 01/08/2026
- **Sessão:** Pedido direto do usuário sobre pronúncia do nome do assistente

## Regra permanente
- **Escrita:** sempre "Jarvis", **sem acento**.
- **Pronúncia (fala/TTS):** "Járvis" — acento tônico no primeiro A (JA-rvis, fonético: /ËˆÊ’aÊ.vis/).
- Nunca pronunciar "Jár-vis" com o segundo A fechado nem com acento na última sílaba ("Jarvís").

## Implementação
- Registrado em `scripts/pronuncias

# 2026-08-02 - Regras em 3 camadas com sincronização e detecção de divergência

## Contexto
Usuário pediu: (1) garantir que ao atualizar/injetar regra, as 3 camadas sincronizem;
(2) detectar e avisar se algum modelo ignorar uma regra.

## Solução: scripts/sync_rules.py
Fonte única = `config/agents/00-system-rules.md` (Constituição).
Camadas:
1. **AGENTS.md** (raiz) — auto-carregado toda sessão. Blocos `<!-- RULES:START -->` e
   `<!-- SOURCES:START -->` são regenerados automatica
## Conexoes

- [[cluster-hub-ecossistema]]
- [[cognitivo-hub-cognitivo]]