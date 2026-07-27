---
name: developer-experience-dx
description: |
  Melhoria de experiência de desenvolvimento: onboarding, tooling, feedback loop e ergonomia de CLI/CI.
  Trigger phrases: "DX", "developer experience", "onboarding", "tooling"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Developer Experience (DX) — Velocidade Sustentável de Time

## Objetivo
Reduzir fricção diária para aumentar entrega com qualidade.

## Áreas de impacto
- Setup inicial e onboarding
- Ciclo local de build/teste
- Feedback de CI e revisão
- Documentação executável

## Práticas recomendadas
- `make`/scripts padrão para tarefas comuns
- Lint/format/test em comando único
- Templates de PR e commits consistentes
- Ambientes reprodutíveis (devcontainer/docker)

## Métricas de DX
- Time-to-first-PR
- Tempo de ciclo PR aberto -> merge
- Taxa de falha no CI por categoria
- Frequência de interrupções por toolchain

## Checklist
- Novo dev sobe projeto em menos de 30-60 min?
- Erros comuns têm mensagens acionáveis?
- Documentação está atualizada com comandos reais?
- Ferramentas são cross-platform quando possível?

## Anti-patterns
- Dependência de conhecimento tribal
- Comandos longos e inconsistentes
- CI lento sem segmentação de suites
- Documentação extensa sem validação prática

## Saída esperada do agente
- Diagnóstico de fricções prioritárias
- Backlog de melhorias de DX
- Métricas de acompanhamento
- Plano incremental de adoção