---
tags: [decisao, ecosistema-opencode, errors, fonte, timeouts, ttft]
aliases: [2026-07-27: Fallback automático de modelo LLM com Bun + @raz]
date: 2026-08-20
---

# 2026-07-27: Fallback automático de modelo LLM com Bun + @razroo/opencode-model-fallback

**Fonte:** ecosistema-opencode

# 2026-07-27: Fallback automático de modelo LLM com Bun + @razroo/opencode-model-fallback

**Categoria:** decisao
**Contexto:** Necessidade de fallback automático quando o modelo primário do OpenCode bate limite de uso
**Agentes envolvidos:** Maestro

## Decisão

Instalamos Bun 1.3.14 e o plugin `@razroo/opencode-model-fallback` v0.3.2 para fallback automático de modelos LLM no OpenCode.

- Plugin adicionado ao `opencode.jsonc`
- Config global em `opencode-model-fallback.jsonc` com fallback para `nvidia/deepseek-ai/deepseek-v3.1`
- Cooldown de 60s com auto-recovery
- Notificações toast ativadas

## Por quê

O OpenCode 1.18.7 não suporta fallback nativo (PR #26292 ainda em andamento). A alternativa de troca manual via `/model` no TUI interrompe o fluxo de trabalho. O plugin da comunidade resolve isso com detecção automática de rate limits, quota errors e timeouts TTFT.

## Impacto

- Zero downtime quando o modelo primário atinge limite
- Troca transparente com replay automático da última mensagem
- Volta ao modelo primário automaticamente após cooldown
- Bun adicionado como runtime adicional no ecossistema

## Referências

- `~/.config/opencode/opencode.jsonc` (plugin array)
- `~/.config/opencode/opencode-model-fallback.jsonc`
- `~/.config/opencode/node_modules/@razroo/opencode-model-fallback/`
 // # 2026-07-27: Fallback automático de modelo LLM com Bun + @razroo/opencode-model-fallback

**Categoria:** decisao
**Contexto:** Necessidade de fallback automático quando o modelo primário do OpenCode bate limite de uso
**Agentes envolvidos:** Maestro

## Decisão

Instalamos Bun 1.3.14 e o plugin `@razroo/opencode-model-fallback` v0.3.2 para fallback automático de modelos LLM no OpenCode.

- Plugin adicionado ao `opencode.jsonc`
- Config global em `opencode-model-fallback.jsonc` com fallback para `nvidia/deepseek-ai/deepseek-v3.1`
- Cooldown de 60s com auto-recovery
- Notificações toast ativadas

## Por quê

O OpenCode 1.18.7 não suporta fallback nativo (PR #26292 ainda em andamento). A alternativa de troca manual via `/model` no TUI interrompe o fluxo de trabalho. O plugin da comunidade resolve isso com detecção automática de rate limits, quota errors e timeouts TTFT.

## Impacto

- Zero downtime quando o modelo primário atinge limite
- Troca transparente com replay automático da última mensagem
- Volta ao modelo primário automaticamente após cooldown
- Bun adicionado como runtime adicional no ecossistema

## Referências

- `~/.config/opencode/opencode.jsonc` (plugin array)
- `~/.config/opencode/opencode-model-fallback.jsonc`
- `~/.config/opencode/node_modules/@razroo/opencode-model-fallback/`

## Conexoes

- [[cluster-hub-ecossistema]]
- [[decisao-hub-decisoes]]
- [[ensureserve-spawns-opencode-serve-without-passing-env-contex]]
- [[geraraudio-blocks-until-full-tts-generation-no-streaming]]
- [[http-401-unauthorized-on-session-and-globalsessions]]
- [[pronuncia-do-nome-do-usuario-david-deivid]]