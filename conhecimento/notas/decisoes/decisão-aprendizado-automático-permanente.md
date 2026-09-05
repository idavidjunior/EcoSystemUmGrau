---
tags: [decisao, explícita, necessidade, opencode, solicitação, tarefa]
aliases: [# Decisão: Aprendizado automático permanente]
date: 2026-08-20
---

# # Decisão: Aprendizado automático permanente

**Fonte:** opencode

# Decisão: Aprendizado automático permanente

**Data:** 2026-07-28
**Tipo:** decisao
**Tags:** aprendizado, automacao, regra, petrea

## Contexto
Usuário instruiu que o aprendizado deve ser feito automaticamente ao final de cada tarefa, sem necessidade de solicitação explícita. Isso é instrução permanente e pétrea.

## Decisão
Todo agente do ecossistema deve, ao final de cada tarefa concluída:

1. **Registrar memória** via `memory_engine.py add` com tipo apropriado (decisao, erro, padrao, episodio)
2. **Criar arquivo** em `conhecimento/aprendizados/` com formato `YYYY-MM-DD-titulo.md`
3. **Atualizar knowledge graph** via `KnowledgeConsolidator` se aplicável
4. **Sincronizar com GitHub** para persistência entre sessões

Não esperar o usuário pedir. Aprender é parte do fluxo de trabalho, não uma etapa opcional.

## Impacto
Ecossistema evolui sozinho. Cada sessão adiciona ao conhecimento coletivo automaticamente.
 // # Decisão: Aprendizado automático permanente

**Data:** 2026-07-28
**Tip
## Conexoes

- [[2026-08-02-aprendizado-da-tv-lg-50ut8050psa-webos]]
- [[cluster-hub-ecossistema]]
- [[config-2026-07-27-5-teste-final-do-vigilante-em-processo-rea]]
- [[controle-da-tv-lg-webos-via-ssap]]
- [[decisao-hub-decisoes]]
- [[secrets-guard-no-preflightcheck]]