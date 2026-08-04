---
name: resilience-engineering
description: |
  Engenharia de resiliência para falhar com segurança: retries, circuit breakers, bulkheads, timeouts e chaos testing.
  Trigger phrases: "resilience", "circuit breaker", "chaos engineering", "fault tolerance"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Resilience Engineering — Falhar Bem para Continuar Operando

## Objetivo
Manter serviço útil sob falhas parciais, picos e degradação de dependências.

## Mecanismos fundamentais
- Timeout explícito por chamada
- Retry com limite + backoff + jitter
- Circuit breaker para dependência instável
- Bulkhead para evitar falha em cascata

## Estratégias de degradação
- Fallback funcional mínimo
- Feature shedding por criticidade
- Read-only mode temporário
- Filas para absorver picos

## Checklist
- Dependências externas têm budget de tempo?
- Retries são idempotentes?
- Há proteção contra thundering herd?
- Degradação preserva jornada crítica?

## Validação
- Testes de falha injetada (chaos)
- Simulação de latência e timeout
- Runbooks de recuperação
- Métricas de saturação e erro por dependência

## Anti-patterns
- Retry infinito sem jitter
- Timeout implícito default
- Fallback sem monitoramento
- Falha silenciosa sem telemetria

## Saída esperada do agente
- Mapa de dependências e riscos
- Políticas de timeout/retry/circuit
- Plano de chaos tests
- Critérios de degradação aceitável