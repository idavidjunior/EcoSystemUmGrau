---
name: tdd-workflow
description: |
  Fluxo TDD completo (Red-Green-Refactor) com foco em comportamento, segurança de refactor e feedback rápido.
  Trigger phrases: "TDD", "test driven", "red green refactor", "escreva um teste", "cobertura de teste"
allowed-tools: Read, Grep, Bash, Write, Edit
version: 1.1.0
---

# TDD Workflow — Red, Green, Refactor com Disciplina

## Objetivo
Guiar implementação por comportamento observável, reduzindo regressões e aumentando confiança de mudança.

## Ciclo base
1. Red: escreva um teste que falha pelo motivo certo
2. Green: implemente o mínimo para passar
3. Refactor: melhore design mantendo testes verdes

## Regras práticas
- Um comportamento por teste
- Nomes orientados a intenção de negócio
- Testes rápidos e independentes
- Refactor só com suíte verde

## Pirâmide recomendada
- Unitários: maioria, execução muito rápida
- Integração: contratos e fronteiras reais
- E2E: fluxos críticos de ponta a ponta

## Checklist de qualidade
- O teste falhou antes da implementação?
- O cenário cobre caso feliz e borda principal?
- O teste valida comportamento, não detalhes internos?
- O feedback local está rápido o suficiente para manter cadência?

## Anti-patterns
- Escrever muito código antes do primeiro teste
- Mockar em excesso e perder sinal real
- Testes lentos que ninguém roda localmente
- Cobertura alta com baixo valor comportamental

## Saída esperada do agente
- Sequência de testes por incremento
- Critérios de aceitação verificáveis
- Estratégia de refactor seguro
- Plano de evolução da suíte