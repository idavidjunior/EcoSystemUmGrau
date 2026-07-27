---
name: edge-compute-patterns
description: |
  Padrões de edge computing: baixa latência global, limites de runtime, cache distribuído e consistência eventual.
  Trigger phrases: "edge", "cloudflare workers", "vercel edge", "deno deploy"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Edge Compute Patterns — Latência Global com Restrições Reais

## Objetivo
Executar lógica próxima ao usuário maximizando performance sem quebrar consistência.

## Casos ideais
- Personalização leve por região/idioma
- Autenticação e roteamento de borda
- Cache e reescrita de conteúdo
- Proteção inicial contra abuso

## Restrições comuns
- CPU/memória/tempo limitados
- APIs nativas parciais
- Storage local efêmero
- Debug distribuído mais difícil

## Estratégias
- Colocar no edge apenas lógica curta e determinística
- Persistência central para estado crítico
- Cache por região com invalidação controlada
- Fallback claro para origin

## Checklist
- Latência p95 melhorou de forma relevante?
- Lógica é stateless ou com estado controlado?
- Existe plano para cold starts/limites do provedor?
- Observabilidade por região está disponível?

## Anti-patterns
- Migrar lógica pesada para edge sem benchmark
- Misturar estado crítico em KV eventual sem cuidado
- Ignorar custo de invalidação global
- Ausência de fallback para origin

## Saída esperada do agente
- Decisão do que vai para edge vs origin
- Estratégia de cache/consistência
- Métricas de latência e erro por região
- Plano de rollout progressivo