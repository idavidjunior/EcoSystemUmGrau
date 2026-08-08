---
tags: [conversa, decisao, ecosistema-opencode, estruturado, extrair, tarefa]
aliases: [2026-07-27: Sistema automático de captura de conhecimento do]
date: 2026-08-08
---

# 2026-07-27: Sistema automático de captura de conhecimento do ecossistema

**Fonte:** ecosistema-opencode

# 2026-07-27: Sistema automático de captura de conhecimento do ecossistema

**Categoria:** decisao
**Contexto:** Implementação das três camadas de aprendizado contínuo para o ecossistema OpenCode + LER
**Agentes envolvidos:** Maestro, Aprendizado

## Decisão

Criamos um sistema de três camadas para garantir que todo aprendizado do ecossistema seja automaticamente capturado, persistido e reutilizado:

1. **Base de conhecimento local** (`EcoSystemUmGrau/conhecimento/`) — entradas markdown com metadados, categorizadas em aprendizados, decisões e padrões
2. **Agente 10-Aprendizado** — subagente OpenCode invocado pelo Maestro ao final de toda tarefa para extrair conhecimento estruturado da conversa
3. **Ponte LER** (`knowledge_bridge.py`) — sincroniza automaticamente os aprendizados com o `CONHECIMENTO.md` e `knowledge_graph.json` do LER

## Por quê

Antes desta implementação, cada interação com o ecossistema gerava conhecimento que era perdido após o término da sessão. Não havia:
- Persistência estruturada de decisões e padrões
- Contexto compartilhado entre sessões
- Alimentação automática do LER com aprendizados do OpenCode

## Impacto

- Toda interação agora deixa um registro permanente
- O LER é alimentado automaticamente sem intervenção manual
- Novas sessões carregam todo o histórico de aprendizado via `instructions` do `opencode.jsonc`
- O ecossistema se torna auto-documentante

## Referências

- `~/.config/opencode/agents/10-aprendizado.md`
- `~/.config/opencode/agents/00-maestro.md` (fluxo obrigatório atualizado)
- `EcoSystemUmGrau/conhecimento/INDEX.md`
- `~/.ler/integrations/opencode/knowledge_bridge.py`
 // ﻿# 2026-07-27: Sistema automÃ¡tico de captura de conhecimento do ecossistema

**Categoria:** decisao
**Contexto:** ImplementaÃ§Ã£o das trÃªs camadas de aprendizado contÃ­nuo para o ecossistema OpenCode + LER
**Agentes envolvidos:** Maestro, Aprendizado

## DecisÃ£o

Criamos um sistema de trÃªs camadas para garantir que todo aprendizado do ecossistema seja automaticamente capturado, persistido e reutilizado:

1. **Base de conhecimento local** (`EcoSystemUmGrau/conhecimento/`) â€” entradas markdown com metadados, categorizadas em aprendizados, decisÃµes e padrÃµes
2. **Agente 10-Aprendizado** â€” subagente OpenCode invocado pelo Maestro ao final de toda tarefa para extrair conhecimento estruturado da conversa
3. **Ponte LER** (`knowledge_bridge.py`) â€” sincroniza automaticamente os aprendizados com o `CONHECIMENTO.md` e `knowledge_graph.json` do LER

## Por quÃª

Antes desta implementaÃ§Ã£o, cada interaÃ§Ã£o com o ecossistema gerava conhecimento que era perdido apÃ³s o tÃ©rmino da sessÃ£o. NÃ£o havia:
- PersistÃªncia estruturada de decisÃµes e padrÃµes
- Contexto compartilhado entre sessÃµes
- AlimentaÃ§Ã£o automÃ¡tica do LER com aprendizados do OpenCode

## Impacto

- Toda interaÃ§Ã£o agora deixa um registro permanente
- O LER Ã© alimentado automaticamente sem intervenÃ§Ã£o manual
- Novas sessÃµes carregam todo o histÃ³rico de aprendizado via `instructions` do `opencode.jsonc`
- O ecossistema se torna auto-documentante

## ReferÃªncias

- `~/.config/opencode/agents/10-aprendizado.md`
- `~/.config/opencode/agents/00-maestro.md` (fluxo obrigatÃ³rio atualizado)
- `EcoSystemUmGrau/conhecimento/INDEX.md`
- `~/.ler/integrations/opencode/knowledge_bridge.py`

## Conexoes

- [[2026-07-27-fallback-automático-de-modelo-llm-com-bun-razrooo]]
- [[cluster-hub-ecossistema]]
- [[decisao-hub-decisoes]]
- [[ensureserve-spawns-opencode-serve-without-passing-env-contex]]
- [[geraraudio-blocks-until-full-tts-generation-no-streaming]]
- [[http-401-unauthorized-on-session-and-globalsessions]]