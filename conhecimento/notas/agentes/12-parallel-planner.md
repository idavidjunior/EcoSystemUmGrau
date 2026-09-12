---
tags: [agente, planejamento, paralelo, decomposicao]
aliases: [Parallel Planner]
date: 2026-09-12
---

# 12-parallel-planner — Parallel Planner

**Categoria:** agentes
**Fonte:** config/agents/12-parallel-planner.md

## Papel

Divide tarefas grandes em subtarefas independentes para execução paralela.

## Responsabilidades

- Analisar dependências entre tarefas
- Identificar paralelismo seguro
- Criar plano de execução otimizado
- Balancear carga entre workers

## Conexões

- [[cluster-hub-ecossistema]] — hub do cluster ecossistema
- [[concurrent-computation-patterns]] — padrões de concorrência
- [[autonomous-loops]] — loops autônomos
- [[09-executor]] — executa o plano
- [[agent-orchestration]] — orquestração de agentes