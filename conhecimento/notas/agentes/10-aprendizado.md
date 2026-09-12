---
tags: [agente, aprendizado, memoria, consolidacao]
aliases: [Aprendizado]
date: 2026-09-12
---

# 10-aprendizado — Agente de Aprendizado

**Categoria:** agentes
**Fonte:** config/agents/10-aprendizado.md

## Papel

Extrai e persiste conhecimento automaticamente ao final de cada tarefa. Cláusula de aprendizado permanente.

## Responsabilidades

- Registrar memória via `memory_engine.py add`
- Criar arquivo em `conhecimento/aprendizados/`
- Sincronizar via gate `persistencia.ps1`
- Atualizar índice semântico

## Conexões

- [[cluster-hub-ecossistema]] — hub do cluster ecossistema
- [[memory-engine]] — engine de memória
- [[aprendizado-automatico]] — cláusula de aprendizado
- [[cluster-mapper]] — mapper de clusters
- [[sentinela-aprendizado]] — sentinela de aprendizado