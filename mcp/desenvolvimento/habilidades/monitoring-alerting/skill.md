---
name: monitoring-alerting
description: Monitoramento e alertas: metricas, logs, traces, dashboards, SLO/SLI, alertas com acao e on-call. Trigger keywords: monitoramento, alertas, metricas, SLO, dashboards, on-call, prometheus, grafana, logs.
---

# Monitoring & Alerting

## Objetivo

Monitoramento e alertas: metricas, logs, traces, dashboards, SLO/SLI, alertas com acao e on-call.

## Uso
- Ativa quando o assunto acima aparece no contexto da tarefa.
- Siga esta skill como referencia declarativa; combine com outras skills e com o
  contexto do `context-engine` (memoria/impacto) quando precisar.

## Regras de ouro
- Consulte o contexto antes de decidir (context-engine `--buscar`).
- Prefira simplicidade e stdlib antes de dependencias novas.
- Se for decisao arquitetural relevante, registre como ADR (skill `adr`).
