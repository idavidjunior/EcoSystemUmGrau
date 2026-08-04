---
name: python-patterns
description: |
  Padrões Python para código limpo, tipado, testável e pronto para produção.
  Trigger phrases: "python best practices", "python architecture", "type hints", "python patterns"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Python Patterns — Simples, Tipado e Mantível

## Objetivo
Produzir código Python legível e robusto, com baixo custo de manutenção.

## Princípios
- Funções pequenas e coesas
- Tipagem progressiva (`typing`) nas fronteiras
- Separar lógica de domínio de infraestrutura
- Preferir clareza a metaprogramação avançada

## Estrutura recomendada
- Módulos por domínio, não por tipo genérico
- `services/`, `repositories/`, `schemas/` quando fizer sentido
- Config centralizada e validada
- Erros de domínio explícitos

## Qualidade
- Lint + format no CI
- Testes unitários para regras críticas
- Testes de integração para I/O
- Cobertura de casos de erro e borda

## Performance pragmática
- Medir antes de otimizar
- Evitar N+1 e loops custosos em dados grandes
- Usar async apenas quando I/O-bound justificar
- Cache com política de invalidação clara

## Anti-patterns
- Script monolítico sem fronteiras
- `except Exception` sem contexto
- Estado global mutável sem controle
- Otimização prematura sem profiling

## Saída esperada do agente
- Refatorações orientadas a legibilidade
- Estratégia de tipagem e testes
- Padrões de erro e logging
- Backlog técnico priorizado