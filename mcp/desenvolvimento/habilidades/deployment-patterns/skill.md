---
name: deployment-patterns
description: |
  Estratégias de deploy confiável com CI/CD, health checks, rollout gradual e rollback operacional.
  Trigger phrases: "deploy", "CI/CD", "health check", "rollback", "blue green", "canary"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Deployment Patterns — Entrega Confiável em Produção

## Objetivo
Publicar mudanças com segurança, observabilidade e recuperação rápida.

## Pipeline mínimo
1. Build (compilação, lint, tipos)
2. Test (unit, integração, smoke)
3. Security (SAST/SCA/secrets)
4. Package (imagem/artefato versionado)
5. Deploy (staging -> produção)
6. Verify (health checks + métricas)

## Estratégias de rollout
- Rolling update: padrão de baixo risco
- Blue-green: troca rápida de tráfego
- Canary: validação progressiva em produção
- Recreate: apenas quando downtime é aceitável

## Checklist operacional
- Staging representa produção?
- Health/readiness/liveness configurados?
- Feature flags para desacoplar release/deploy?
- Rollback testado e documentado?
- Observabilidade habilitada desde o primeiro request?

## Regras de ouro
- Migração de banco com estratégia expand/contract
- Secrets fora de código e imagem
- Deploy em janela com suporte disponível
- Critério de abort explícito por SLO

## Anti-patterns
- Deploy sem plano de rollback
- Mudar app + schema de forma acoplada e irreversível
- Ignorar smoke pós-deploy
- Diferença grande entre staging e produção

## Saída esperada do agente
- Plano de pipeline e gates
- Estratégia de rollout/rollback
- Checklist de readiness operacional
- Métricas de sucesso pós-deploy