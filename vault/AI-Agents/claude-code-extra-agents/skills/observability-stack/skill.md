---
name: observability-stack
description: |
  Observabilidade ponta a ponta com logs, métricas, traces e SLOs para detectar e resolver incidentes rapidamente.
  Trigger phrases: "observability", "opentelemetry", "tracing", "slo", "grafana"
allowed-tools: Read, Grep, Bash
version: 1.1.0
---

# Observability Stack — Ver, Entender e Agir Rápido

## Objetivo
Reduzir MTTR com telemetria confiável e correlacionável entre serviços.

## Pilar triplo
- Logs estruturados com contexto
- Métricas de negócio e sistema
- Traces distribuídos com propagation ID

## SLO e alertas
- Definir SLI por jornada crítica
- SLO realista por impacto de negócio
- Alertas acionáveis (evitar ruído)
- Error budget para orientar priorização

## Instrumentação mínima
- Request ID/correlation ID em toda requisição
- Latência p50/p95/p99 por endpoint
- Taxa de erro por tipo/código
- Saturação de CPU/memória/fila

## Operação
- Dashboards por domínio, não só por tecnologia
- Runbooks vinculados aos alertas
- Pós-incidente com ações rastreáveis
- Retenção e custo de telemetria controlados

## Anti-patterns
- Alertar tudo, agir em nada
- Logs sem contexto de negócio
- Traces sem propagação entre serviços
- Métricas sem dono e sem meta

## Saída esperada do agente
- Mapa de telemetria por serviço
- SLO/SLI propostos
- Estratégia de alerting e runbooks
- Plano de maturidade de observabilidade