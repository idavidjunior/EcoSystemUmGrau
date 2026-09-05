---
tags: [gasto, opencode, padrao, retido, sessao, titulo]
aliases: [suggestions hermes itens 1 3]
date: 2026-09-02
---

# suggestions hermes itens 1 3

**Fonte:** opencode

Tipo: padrao

Tags: [hermes, skill_recorrente, tts, audio, dedup, metrica, backlog]

Data: 2026-09-02

Contexto: Tres sugestoes de melhoria do Hermes pendentes no EcoSystemUmGrau: (1) regra de skill com repeticao 3+ criando/atualizando skill com deduplicacao (se existe atualiza, se nao existe cria), (2) verificacao de dispositivo de audio antes do TTS reproduzir, (3) metrica de contexto gasto vs retido da sessao.

Decisão: Implementar (1) em scripts/skill_recorrente.py com dedup robusto: _buscar_similar combina difflib + bonus de tokens comuns + trigger keywords por palavra inteira (2+ palavras-trigger >=4 chars no pedido, OU 1 trigger que coincide com titulo/id da skill). _trigger_keywords usa regex r"Trigger keywords:\s*([^.\n]+)" (corrigido do lazy bugado que capturava 1 char), filtra stopwords e keywords <3 chars. Se skill similar existe, atualiza; senao cria e registra no inventario (inventory_manager). Implementar (2) em scripts/tts_service.py com _audio_disponivel(): verifica di
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[padrao-hub-padroes]]
- [[secrets-guard-no-preflightcheck]]