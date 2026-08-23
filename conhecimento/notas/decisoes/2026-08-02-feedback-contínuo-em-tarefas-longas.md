---
tags: [curtas, decisao, opencode, progresso, relatório, único]
aliases: [# 2026-08-02 - Feedback contínuo em tarefas longas]
date: 2026-08-22
---

# # 2026-08-02 - Feedback contínuo em tarefas longas

**Fonte:** opencode

# 2026-08-02 - Feedback contínuo em tarefas longas

**Categoria:** decisao
**Fonte:** sessao_jarvis_vox
**Gravidade:** baixa

## Contexto

O usuário pediu mais transparência durante tarefas demoradas: não queria ficar
esperando em silêncio sem saber o que o Jarvis está fazendo ou se há progresso.

## Decisão

Adicionada regra permanente de **feedback contínuo** em `JARVIS_SYSTEM.md`:
- Regra 16 em "Regras de Resposta".
- Nova seção "Regra de Feedback Contínuo (02/08/2026)".

O que mudou na prática:
- Antes de agir: avisar o plano.
- Durante: relatar descobertas, bloqueios e decisões em voz.
- Em esperas longas (LLM 20-30s, builds, testes): enviar status intermediário.
- Ao concluir: resumir resultado.

## Lição

O usuário prefere receber atualizações frequentes e curtas a um único relatório
final longo. Transparência durante a execução reduz a sensação de espera inútil.

## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]