---
name: backend-patterns
description: |
  Padrões backend para serviços resilientes: contratos claros, separação de camadas, observabilidade e confiabilidade.
  Trigger phrases: "backend architecture", "service layer", "repository pattern", "API backend"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Backend Patterns — Serviços Confiáveis

## Objetivo
Projetar serviços legíveis e resilientes com baixo acoplamento e alta testabilidade.

## Estrutura sugerida
- Camada de apresentação (HTTP/transport)
- Camada de aplicação (casos de uso)
- Camada de domínio (regras centrais)
- Camada de infraestrutura (DB, filas, APIs externas)

## Pilares técnicos
- Contratos explícitos (DTOs, schemas, versionamento)
- Idempotência em operações críticas
- Controle de concorrência e retry seguro
- Observabilidade por default (logs, métricas, traces)

## Checklist operacional
- Timeouts e circuit breaker definidos?
- Erros mapeados para códigos coerentes?
- Queries críticas indexadas e paginadas?
- Segredos fora do código?
- Runbook de incidente disponível?

## Testes essenciais
- Unit para regras de domínio
- Integration para DB/externos
- Contract tests entre serviços
- Testes de carga básicos em endpoints críticos

## Anti-patterns
- Lógica de negócio no controller
- Dependência circular entre módulos
- Retries sem limite e sem jitter
- Erros genéricos sem contexto

## Saída esperada do agente
- Diagrama de camadas e responsabilidades
- Padrão de erro e observabilidade
- Matriz de riscos técnicos
- Plano de testes por camada