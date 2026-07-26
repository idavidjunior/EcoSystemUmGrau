---
name: database-migrations
description: |
  Estratégia de migrações seguras: expansão/contração, zero-downtime e rollback planejado.
  Trigger phrases: "migration", "schema change", "zero downtime", "database rollout"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Database Migrations — Evoluir Schema sem Quebrar Produção

## Objetivo
Alterar banco de dados com segurança operacional e mínima indisponibilidade.

## Estratégia padrão (expand/contract)
1. Expand: adicionar estrutura compatível (nova coluna/tabela)
2. Backfill: preencher dados gradualmente
3. Dual-write/read: transição controlada na aplicação
4. Contract: remover legado após validação

## Práticas críticas
- Migrações pequenas e reversíveis
- Índices criados de forma online quando possível
- Locks longos evitados/monitorados
- Janela de execução e plano de rollback documentados

## Checklist pré-deploy
- Estimativa de impacto em tempo e lock?
- Backup/snapshot recente disponível?
- Scripts testados em cópia realista?
- Feature flags para ativação gradual?
- Métricas para detectar regressão?

## Rollback
- Definir rollback lógico e técnico
- Evitar mudanças irreversíveis no mesmo passo
- Validar rollback em ambiente de staging

## Anti-patterns
- Renomear/remover coluna usada sem fase de compatibilidade
- Backfill massivo sem limitação de batch
- Deploy de app dependente antes da migração expand
- Assumir rollback sem teste real

## Saída esperada do agente
- Plano de migração faseado
- Scripts de verificação/rollback
- Riscos operacionais e mitigação
- Critérios de pronto para contract