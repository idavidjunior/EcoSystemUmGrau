---
tipo: padrao
tags: [etapa23, observabilidade, reliability, logging, metrics, health, circuit-breaker, retry, recovery, degraded-mode, watchdog, incidents, security]
data: 2026-08-18
contexto: Implementação da Etapa 23 — Observability + Reliability no EcoSystemUmGrau
decisao: Criar módulo unificado observability_reliability.py com: StructuredLogger (JSON, 5 níveis, redação de segredos automática), MetricsCollector (contadores, timers, p50/p95/p99), TraceContext (correlation_id, mission_id, trace_id via thread-local), HealthAggregator (5 níveis, liveness vs readiness, dependências), CircuitBreaker (extraído de tool_orchestrator, generalizado), RetryPolicy (backoff exponencial + jitter + budget per minute), TimeoutManager, Watchdog (heartbeat + stale detection), CrashLoopDetector, DegradedMode (restricções por ação), RecoveryPipeline (detect→classify→diagnose→retry→fallback→recover→validate), IncidentRecorder (causa provável, nunca certeza), SecurityEventRecorder (7 tipos), 10 padrões de redação de segredos. 95 testes adversariais. Nenhum módulo existente alterado.
impacto: O ecossistema agora tem observabilidade unificada (logs estruturados, métricas com percentis, tracing cross-module), resiliência (circuit breaker, retry com budget, timeout, watchdog, crash-loop detection), recuperação (pipeline completo com incident recording), modo degradado controlado, e proteção contra exposição de segredos em logs. Falhas de componentes independentes não propagam.
```

## Aprendizado

1. **Secret redaction é transversal**: patterns de redação devem ser aplicados a TODO output de log, não apenas a memória. Um log com API key exposta é tão perigoso quanto um arquivo com a key.

2. **Retry budget previne thundering herd**: retry com backoff exponencial é necessário mas não suficiente. Um budget per minute (e.g., 10 retries/min por componente) evita que múltiplos clientes inundem um serviço degradado com retries simultâneos.

3. **Jitter é essencial**: retry determinístico (todos esperam 1s, 2s, 4s) cria sincronização indesejada. Jitter (0.5-1.0x do backoff) distribui retries no tempo.

4. **Liveness ≠ Readiness**: Liveness = "estou vivo?" (pelo menos um componente respondendo). Readiness = "estou pronto para receber tráfego?" (todos os componentes registrados prontos). Confundir as duas causa problemas: matar um processo que está vivo mas não pronto (readiness false) é desnecessário.

5. **Causa provável nunca é certeza**: incident recording deve declarar "PROBABLE CAUSE", não "CAUSE". Diagnosticar com certeza exige evidência que pode não estar disponível no momento do incidente.

6. **Degraded mode com restrições granulares**: não é binário (tudo funciona ou nada). O sistema pode degradar seletivamente (e.g., "TTS indisponível, mas texto funciona") com restrições por ação.

7. **Component isolation é arquitetural**: a falha de TTS não pode derrubar memory. A falha de bridge não pode derrubar cognitive core. Isso é achieved via try/except nas integrações, não via arquitetura de processos separados.

8. **Windows time.sleep é impreciso**: testes temporizados devem usar polling loops em vez de sleep fixo. `time.sleep(1.0)` pode dormir 0.9s ou1.1s no Windows.

## Conexões

- [[2026-08-18-etapa22-self-assessment-self-improvement]]
- [[2026-08-18-etapa21-memory-learning-consolidation]]

## Conexoes

- [[nunca-armazenar-api-keys-em-config-files]]