---
tags: [devops, jornada, msg, padrao, sistema, todo]
aliases: [DevOps: observabilidade — logs estruturados, métricas e trac]
date: 2026-08-10
---

# DevOps: observabilidade — logs estruturados, métricas e tracing (OTel)

**Fonte:** devops

Monitoring pergunta \"está no ar?\"; observabilidade permite descobrir POR QUE quebrou sem prever a pergunta antes. Os três pilares conversam: métricas dizem que algo mudou, logs dão detalhe, tracing liga a jornada de uma request por todo o sistema.

**Logs estruturados:** JSON, nunca free-text (grep de log não escala). Campos padrão: `timestamp` (ISO 8601 UTC), `level`, `service`, `env`, `request_id`/`trace_id`, `msg` e contexto do negócio. Regras: nunca logue segredos/PII sem redação; nível consistente (debug/info/warn/error); `info` para eventos de negócio relevantes, `error` para falhas com stack e contexto suficiente para reproduzir; logs em stdout (contêiner) para o coletor (OpenTelemetry collector, Fluent Bit) capturar. Log aggregation com retenção e busca (Loki, ELK, Datadog).

**Métricas:** séries temporais com cardinalidade controlada (Prometheus + Grafana). Instrumente RED (Rate, Errors, Duration) para requests e USE (Utilization, Saturation, Errors) para recursos. Alertas: 4 golden signals — latência, tráfego, erros, saturação. SLO (objetivo: 99.9% de requests < 200ms) → error budget decide quando parar de lançar. Cuidado com cardinalidade alta (labels com user_id/URL cheia explodem o TSDB) — agregue.

**Tracing (distributed):** OpenTelemetry (OTel) é o padrão aberto: SDK instrumenta código e envia spans → collector → backend (Jaeger, Tempo, Datadog, Honeycomb). Cada request ganha `trace_id` propagado via headers (`traceparent`), spans com operação, duração, atributos e status; visualize cascata para achar latência dominante. Exemplo de debugging: \"pagamento está lento\" → trace mostra 90% do tempo no `postgres.charge` → query lenta → índices.

**Juntando os três:** sempre correlacione por `trace_id`/`request_id` em logs, métricas e traces. Prática: 1) instrumente na entrada de cada serviço; 2) cada erro loga o `trace_id`; 3) dashboard por serviço (RED) + dashboard por fluxo de negócio (funnel); 4) teste de observabilidade: interrompa um serviço em staging e veja se consegue responder \"o que quebrou\" em 5 min; 5) comece com OTel + Prometheus/Loki/Tempo auto-hospedados se não houver budget de vendor.
## Conexoes

- [[cluster-hub-programacao]]
- [[devops-containers-camadas-imagens-mínimas-e-non-root]]
- [[devops-infraestrutura-como-código-terraform-e-imutabilidade]]
- [[devops-pipelines-de-cicd-artefatos-ambientes-e-promoção]]
- [[padrao-hub-padroes]]