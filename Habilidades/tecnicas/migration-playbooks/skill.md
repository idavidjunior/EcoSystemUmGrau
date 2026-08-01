---
name: migration-playbooks
description: |
  Playbooks de migração (REST->GraphQL, monólito->serviços, JS->TS) com fases, riscos e rollback.
  Trigger phrases: "migration", "playbook", "modernization", "incremental migration"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Migration Playbooks — Mudança Grande sem Aposta Cega

## Objetivo
Conduzir migrações estruturais em etapas seguras, com valor incremental e baixo risco.

## Modelo de execução
1. Baseline: métricas e riscos atuais
2. Fase piloto: escopo pequeno e representativo
3. Migração incremental: fatias por domínio
4. Cutover: transição controlada
5. Cleanup: remoção de legado

## Regras gerais
- Dual-run quando possível
- Feature flags para troca gradual
- Compatibilidade reversa durante transição
- Comunicação clara com stakeholders

## Checklist por fase
- Critério de sucesso definido?
- Telemetria suficiente para comparar antes/depois?
- Plano de rollback testado?
- Dependências externas alinhadas?

## Exemplos de trilha
- REST -> GraphQL: gateway paralelo + schema por domínio
- Monólito -> serviços: strangler pattern por capacidade
- JS -> TS: tipagem progressiva em fronteiras críticas

## Anti-patterns
- Big-bang sem fallback
- Migrar sem baseline de performance/erro
- Criar arquitetura nova sem estratégia operacional
- Subestimar treinamento do time

## Saída esperada do agente
- Playbook faseado com milestones
- Mapa de riscos e mitigação
- Indicadores de sucesso por etapa
- Plano de rollback e comunicação