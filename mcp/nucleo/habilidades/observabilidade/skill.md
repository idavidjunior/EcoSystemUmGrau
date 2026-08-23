# Observabilidade Nativa — MCP Server

## Como usar
Servidor MCP que expõe toda a stack de observabilidade (ETAPA 23) via tools padronizadas.

```bash
# Testar servidor
python mcp/nucleo/habilidades/observabilidade/server.py
# → espera JSON-RPC no stdio
```

## Tools disponíveis

| Tool | Descrição |
|------|-----------|
| `log_query` | Busca logs estruturados recentes (filtro: level, component, limit, since_seconds) |
| `metrics_snapshot` | Snapshot de métricas: contadores, gauges, timers com p50/p95/p99 |
| `health_report` | Saúde global + componentes + dependências (liveness/readiness) |
| `trace_context` | Obtém/inicia contexto de trace (correlation_id, mission_id, trace_id) |
| `incidents_list` | Incidentes recentes/abertos + stats |
| `security_events` | Eventos de segurança recentes/por threat_level |
| `circuit_breakers` | Status de todos os circuit breakers |
| `retry_stats` | Estatísticas de retry (tentativas, exaustão, budget) |
| `degraded_status` | Status do modo degradado + restrições |
| `recovery_history` | Histórico de pipelines de recovery |
| `watchdog_status` | Componentes com heartbeat stale |
| `crash_loop_status` | Contadores de crash loop por componente |

## Integração no opencode.jsonc

```jsonc
{
  "mcp": {
    "servers": {
      "observabilidade": {
        "command": "python",
        "args": ["mcp/nucleo/habilidades/observabilidade/server.py"],
        "env": {}
      }
    }
  }
}
```

## Dependências
- `scripts/observability_reliability.py` (ETAPA 23 — já implementado)
- Python stdlib apenas (json, sys, pathlib, threading, datetime, collections, uuid, time, random, math, logging, re, concurrent.futures)

## Exemplos de uso via MCP

```json
// Health check completo
{"method": "tools/call", "params": {"name": "health_report", "arguments": {"check_dependencies": true}}}

// Métricas para dashboard
{"method": "tools/call", "params": {"name": "metrics_snapshot", "arguments": {}}}

// Logs de erro dos últimos 5 minutos
{"method": "tools/call", "params": {"name": "log_query", "arguments": {"level": "error", "since_seconds": 300}}}

// Incidentes abertos
{"method": "tools/call", "params": {"name": "incidents_list", "arguments": {"open_only": true}}}
```

## Auto-instrumentação (Python)

```python
from scripts.observability_reliability import log, metrics, TraceContext, obs_decorators

# Decorator para log + métricas + trace automático
@obs_decorators.observed(component="meu_modulo", operation="processar")
def processar_dados(dados):
    # log, métricas e trace automáticos
    return resultado

# Context manager para operações manuais
with obs_decorators.trace("minha_operacao", component="meu_modulo"):
    fazer_algo()

# Timer manual
start = metrics.timer_start("minha_operacao")
fazer_algo()
metrics.timer_end("minha_operacao", start)
```