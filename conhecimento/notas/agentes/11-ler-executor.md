---
tags: [agente, ler, executor, missao]
aliases: [LER Executor]
date: 2026-09-12
---

# 11-ler-executor — LER Executor

**Categoria:** agentes
**Fonte:** config/agents/11-ler-executor.md

## Papel

Delega tarefas complexas ao Loop Engineering Runtime (LER) e garante execução autônoma até resultado.

## Responsabilidades

- Invocar `ler "missao"` para tarefas complexas
- Monitorar execução do LER
- Coletar resultado e evidências
- Fallback se LER falhar

## Conexões

- [[cluster-hub-ecossistema]] — hub do cluster ecossistema
- [[ler-runtime]] — runtime LER
- [[ler-arquitetura]] — arquitetura do LER
- [[09-executor]] — executor que delega ao LER
- [[missao-permanente]] — missões do ecossistema