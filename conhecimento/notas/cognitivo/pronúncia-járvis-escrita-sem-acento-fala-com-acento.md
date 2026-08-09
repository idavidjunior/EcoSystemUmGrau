---
tags: [assistente, cognitivo, general, jarvís, sílaba, última]
aliases: [Pronúncia "Járvis" (escrita sem acento, fala com acento)]
date: 2026-08-09
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

# PronÃºncia "JÃ¡rvis" (escrita sem acento, fala com acento)

- **Data:** 01/08/2026
- **SessÃ£o:** Pedido direto do usuÃ¡rio sobre pronÃºncia do nome do assistente

## Regra permanente
- **Escrita:** sempre "Jarvis", **sem acento**.
- **PronÃºncia (fala/TTS):** "JÃ¡rvis" â€” acento tÃ´nico no primeiro A (JA-rvis, fonÃ©tico: /ËˆÊ’aÊ.vis/).
- Nunca pronunciar "JÃ¡r-vis" com o segundo A fechado nem com acento na Ãºltima sÃ­laba ("JarvÃ­s").

## ImplementaÃ§Ã£o
- Registrado em `scripts/pronuncias

# 2026-08-02 - Regras em 3 camadas com sincronizaÃ§Ã£o e detecÃ§Ã£o de divergÃªncia

## Contexto
UsuÃ¡rio pediu: (1) garantir que ao atualizar/injetar regra, as 3 camadas sincronizem;
(2) detectar e avisar se algum modelo ignorar uma regra.

## SoluÃ§Ã£o: scripts/sync_rules.py
Fonte Ãºnica = `config/agents/00-system-rules.md` (ConstituiÃ§Ã£o).
Camadas:
1. **AGENTS.md** (raiz) â€” auto-carregado toda sessÃ£o. Blocos `<!-- RULES:START -->` e
   `<!-- SOURCES:START -->` sÃ£o regenerados automatica
## Conexoes

- [[cluster-hub-cognicao]]
- [[cognitivo-hub-cognitivo]]