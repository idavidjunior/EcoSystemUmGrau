---
name: cache-strategy-selector
description: |
  Seleção de estratégia de cache por caso de uso: HTTP/CDN, Redis, cache local, SWR e invalidação.
  Trigger phrases: "cache strategy", "redis", "cdn", "swr", "invalidation"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Cache Strategy Selector — Velocidade com Coerência

## Objetivo
Escolher o tipo de cache certo para reduzir latência sem corromper consistência.

## Escolha por camada
- HTTP/CDN: conteúdo público e estável
- Redis distribuído: leitura intensiva compartilhada
- In-memory local: hot path por instância
- SWR no cliente: UX rápida com atualização posterior

## Perguntas-chave
- Qual tolerância a staleness?
- Qual custo de miss?
- Quem invalida e quando?
- Há multi-tenant com risco de vazamento?

## Estratégias de invalidação
- TTL para simplicidade
- Event-driven para precisão
- Versioned keys para rollout seguro
- Cache-aside como padrão pragmático

## Métricas
- Hit rate por chave/endpoint
- Latência p95 com e sem cache
- Erros de invalidação
- Custo de memória e evictions

## Anti-patterns
- Cache sem política de invalidação
- Chaves sem namespace por tenant
- TTL arbitrário sem medição
- Cache de dados sensíveis sem controles

## Saída esperada do agente
- Tabela `dado -> camada de cache`
- Política de invalidação
- Métricas de sucesso
- Plano de rollout/rollback