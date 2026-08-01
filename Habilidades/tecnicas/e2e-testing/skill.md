---
name: e2e-testing
description: |
  Estratégia de testes E2E com Playwright: cobertura de fluxos críticos, estabilidade, isolamento e diagnóstico.
  Trigger phrases: "E2E", "end to end", "Playwright", "page object", "teste de interface"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# E2E Testing — Playwright e Confiabilidade de Fluxos

## Objetivo
Validar jornadas reais de usuário com testes estáveis e informativos em CI.

## Escopo recomendado
- Fluxos críticos de receita/risco (login, checkout, pagamento)
- Integrações sensíveis (auth, permissões, sessão)
- Caminhos de recuperação de erro

## Arquitetura de suíte
- Testes por jornada (não por página isolada)
- Fixtures para setup idempotente
- Dados de teste efêmeros por execução
- Separação entre smoke, regressão e full-suite

## Práticas Playwright
- Preferir `getByRole`, `getByLabel`, `getByTestId`
- Esperas baseadas em condição, nunca `sleep`
- `trace`, `video` e screenshot em falha
- Retry apenas para flaky conhecido e monitorado

## Checklist de estabilidade
- Cada teste roda independente de ordem?
- Estado inicial é garantido por fixture?
- Dependências externas estão mockadas quando apropriado?
- Timeout calibrado por operação real?
- Falha aponta causa raiz com evidência útil?

## Pipeline CI
- Execução headless obrigatória
- Paralelismo controlado por capacidade do ambiente
- Artefatos publicados em toda falha
- Gate de merge com smoke mínimo

## Anti-patterns
- Cobertura visual superficial sem regra de negócio
- Mockar tudo e perder valor de integração
- Testes acoplados ao layout frágil
- Ignorar quarantine/flaky backlog

## Saída esperada do agente
- Matriz de cenários críticos
- Plano de suíte (smoke/regressão)
- Convenções de locator e fixture
- Estratégia de debug e redução de flaky