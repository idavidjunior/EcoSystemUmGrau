---
name: concurrent-computation-patterns
description: |
  Padrões de concorrência e paralelismo para throughput com segurança: filas, workers, goroutines, async runtimes.
  Trigger phrases: "concurrency", "parallelism", "workers", "goroutines", "tokio"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Concurrent Computation Patterns — Escalar sem Corrupção

## Objetivo
Aumentar throughput preservando corretude, previsibilidade e observabilidade.

## Padrões recomendados
- Producer-consumer com fila limitada
- Worker pool com backpressure
- Fan-out/fan-in para tarefas independentes
- Batch processing quando latência permite

## Controles críticos
- Limites de concorrência por recurso
- Cancelamento e timeout por tarefa
- Idempotência em reprocessamento
- Isolamento de falhas por worker

## Checklist de segurança de concorrência
- Estado compartilhado protegido?
- Ordem importa? Se sim, está explícita?
- Retries podem duplicar efeitos?
- Deadlock/starvation monitorados?

## Observabilidade
- Queue depth e tempo de espera
- Taxa de sucesso/falha por worker
- Latência de execução por tipo de job
- Saturação CPU/memória/IO

## Anti-patterns
- Paralelizar sem gargalo medido
- Concorrência ilimitada
- Locks globais extensos
- Retry sem jitter e sem limite

## Saída esperada do agente
- Modelo de execução concorrente
- Limites e políticas de retry
- Métricas operacionais mínimas
- Testes de carga e race conditions