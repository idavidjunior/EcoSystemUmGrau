"""MCP server — Observabilidade Nativa.

Expõe logs estruturados, métricas com percentis, health checks, tracing,
circuit breakers, incidentes e eventos de segurança via tools MCP.
Integra com scripts/observability_reliability.py (ETAPA 23).

Transporte: MCP stdio padrão (Content-Length framing + fallback line-delimited).

Tools:
  - log_query           — busca logs recentes (filtro: level, component, limit)
  - metrics_snapshot    — snapshot de métricas (contadores, gauges, timers p50/p95/p99)
  - health_report       — relatório de saúde global + componentes + dependências
  - trace_context       — obtém/contexto de trace atual (correlation_id, mission_id, trace_id)
  - incidents_list      — lista incidentes recentes/abertos + stats
  - security_events     — lista eventos de segurança recentes/por nível
  - circuit_breakers    — status de todos os circuit breakers
  - retry_stats         — estatísticas de retry (budget, tentativas, exaustão)
  - degraded_status     — status do modo degradado + restrições
  - recovery_history    — histórico de recuperações recentes
  - watchdog_status     — componentes com heartbeat stale
  - crash_loop_status   — contadores de crash loop por componente
"""
import json
import sys
from pathlib import Path

BASE = str(Path(__file__).resolve().parent)
sys.path.insert(0, BASE)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent.parent / "scripts"))

import observability_reliability as obs  # noqa: E402

TOOLS = [
    {
        "name": "log_query",
        "description": "Busca logs estruturados recentes com filtros opcionais. Retorna JSONL com timestamp, level, component, operation, message, correlation_id, trace_id, duration_ms, error, result, extra.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Máximo de entradas (padrão 100)", "default": 100, "minimum": 1, "maximum": 10000},
                "level": {"type": "string", "description": "Filtrar por nível: debug, info, warning, error, critical", "enum": ["debug", "info", "warning", "error", "critical"]},
                "component": {"type": "string", "description": "Filtrar por componente (substring)"},
                "since_seconds": {"type": "number", "description": "Filtrar últimos N segundos"},
            },
            "required": []
        },
    },
    {
        "name": "metrics_snapshot",
        "description": "Retorna snapshot das métricas: contadores, gauges, timers com p50/p95/p99/avg/min/max/count. Use para dashboards e alertas.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
    },
    {
        "name": "health_report",
        "description": "Relatório completo de saúde: global (healthy/degraded/unhealthy/critical/offline), liveness, readiness, componentes (level, liveness, readiness, probes, details), dependências (healthy, latency_ms, message), timestamp.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "check_dependencies": {"type": "boolean", "description": "Executar health checks das dependências registradas", "default": True},
            },
            "required": []
        },
    },
    {
        "name": "trace_context",
        "description": "Obtém contexto de trace atual (correlation_id, mission_id, trace_id, tool_execution_id) ou inicia novo contexto.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "mission_id": {"type": "string", "description": "ID da missão/operação (opcional)"},
                "correlation_id": {"type": "string", "description": "ID de correlação (opcional, gera se vazio)"},
                "trace_id": {"type": "string", "description": "ID de trace (opcional, gera se vazio)"},
                "action": {"type": "string", "description": "Ação: get (padrão), start, child", "enum": ["get", "start", "child"], "default": "get"},
            },
            "required": []
        },
    },
    {
        "name": "incidents_list",
        "description": "Lista incidentes recentes, abertos ou stats. Inclui: id, component, timestamp, severity, symptom, probable_cause, actions_taken, result, recovery, final_state, correlation_id, mission_id, resolved_at.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Máximo de entradas (padrão 20)", "default": 20, "minimum": 1, "maximum": 500},
                "open_only": {"type": "boolean", "description": "Apenas incidentes abertos", "default": False},
                "stats_only": {"type": "boolean", "description": "Apenas estatísticas agregadas", "default": False},
            },
            "required": []
        },
    },
    {
        "name": "security_events",
        "description": "Lista eventos de segurança recentes ou por threat_level. Inclui: id, timestamp, event_type, threat_level, component, description, source, blocked, correlation_id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Máximo de entradas (padrão 20)", "default": 20, "minimum": 1, "maximum": 500},
                "threat_level": {"type": "string", "description": "Filtrar por nível: LOW, MEDIUM, HIGH, CRITICAL", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
            },
            "required": []
        },
    },
    {
        "name": "circuit_breakers",
        "description": "Status de todos os circuit breakers registrados: name, state (closed/open/half_open), failure_count, success_count.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
    },
    {
        "name": "retry_stats",
        "description": "Estatísticas de retry: contadores de tentativas, exaustões, budget restante por política.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
    },
    {
        "name": "degraded_status",
        "description": "Status do modo degradado: degraded (bool), components (dict component->reason), since, duration_s, restrictions (list).",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
    },
    {
        "name": "recovery_history",
        "description": "Histórico de pipelines de recovery recentes. Cada entrada: success, incident_id, component, steps (name, status, result, duration_ms), duration_ms, escalated, degraded, used_fallback.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Máximo de entradas (padrão 20)", "default": 20, "minimum": 1, "maximum": 500},
            },
            "required": []
        },
    },
    {
        "name": "watchdog_status",
        "description": "Lista componentes com heartbeat stale (atrasados). Útil para detectar processos travados.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
    },
    {
        "name": "crash_loop_status",
        "description": "Contadores de crash/restart loop por componente (janela 5min, threshold 5). Retorna dict component->count e flag is_crash_loop.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        },
    },
]


def handle(req):
    rid = req.get("id")
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {"name": "mcp-observabilidade", "version": "1.0.0"},
            "capabilities": {"tools": {}}
        }}

    if method == "notifications/initialized":
        return None

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}

    if method == "tools/call":
        tool = params.get("name", "")
        args = params.get("arguments", {})
        return handle_tool(tool, args, rid)

    return None


def handle_tool(tool, args, rid):
    try:
        if tool == "log_query":
            limit = args.get("limit", 100)
            level = args.get("level")
            component = args.get("component")
            since_seconds = args.get("since_seconds")

            severity = None
            if level:
                severity = obs.Severity(level.upper())

            events = obs.log.get_recent(limit=limit, level=severity)

            if component:
                events = [e for e in events if component.lower() in e.get("component", "").lower()]

            if since_seconds:
                import time
                from datetime import datetime, timedelta
                cutoff = datetime.now() - timedelta(seconds=since_seconds)
                filtered = []
                for e in events:
                    try:
                        ts = datetime.fromisoformat(e.get("ts", ""))
                        if ts >= cutoff:
                            filtered.append(e)
                    except Exception:
                        pass
                events = filtered

            result = {"tool": "log_query", "count": len(events), "events": events}

        elif tool == "metrics_snapshot":
            snapshot = obs.metrics.snapshot()
            result = {"tool": "metrics_snapshot", **snapshot}

        elif tool == "health_report":
            check_deps = args.get("check_dependencies", True)
            report = obs.health.get_report()
            if not check_deps:
                report.pop("dependencies", None)
            result = {"tool": "health_report", **report}

        elif tool == "trace_context":
            action = args.get("action", "get")
            if action == "start":
                ctx = obs.TraceContext.start(
                    mission_id=args.get("mission_id"),
                    correlation_id=args.get("correlation_id"),
                    trace_id=args.get("trace_id"),
                )
            elif action == "child":
                ctx = obs.TraceContext.child()
            else:
                ctx = obs.TraceContext.current()
            result = {"tool": "trace_context", "action": action, "context": ctx}

        elif tool == "incidents_list":
            limit = args.get("limit", 20)
            open_only = args.get("open_only", False)
            stats_only = args.get("stats_only", False)

            if stats_only:
                result = {"tool": "incidents_list", "stats": obs.incidents.get_stats()}
            elif open_only:
                result = {"tool": "incidents_list", "open": obs.incidents.get_open()}
            else:
                result = {"tool": "incidents_list", "recent": obs.incidents.get_recent(limit)}

        elif tool == "security_events":
            limit = args.get("limit", 20)
            threat_level = args.get("threat_level")

            if threat_level:
                events = obs.security_events.get_by_level(threat_level)
            else:
                events = obs.security_events.get_recent(limit)

            result = {"tool": "security_events", "count": len(events), "events": events}

        elif tool == "circuit_breakers":
            import threading
            with obs._cb_lock:
                cbs = {name: cb.get_status() for name, cb in obs._circuit_breakers.items()}
            result = {"tool": "circuit_breakers", "breakers": cbs}

        elif tool == "retry_stats":
            # Coletar stats das políticas de retry conhecidas
            # Como RetryPolicy não tem registry global, retornamos métricas globais
            metrics_snap = obs.metrics.snapshot()
            counters = metrics_snap.get("counters", {})
            result = {
                "tool": "retry_stats",
                "retry_attempts": counters.get("retry.attempts", 0),
                "retry_exhausted": counters.get("retry.exhausted", 0),
                "incidents_total": counters.get("incidents.total", 0),
                "security_events": counters.get("security.events", 0),
            }

        elif tool == "degraded_status":
            result = {"tool": "degraded_status", **obs.degraded.get_status()}

        elif tool == "recovery_history":
            limit = args.get("limit", 20)
            result = {"tool": "recovery_history", "history": obs.recovery.get_history(limit)}

        elif tool == "watchdog_status":
            stale = obs.watchdog.get_stale()
            result = {"tool": "watchdog_status", "stale_components": stale, "count": len(stale)}

        elif tool == "crash_loop_status":
            counts = obs.crash_detector.get_crash_counts()
            loop_info = {}
            for comp, count in counts.items():
                loop_info[comp] = {
                    "count": count,
                    "is_crash_loop": obs.crash_detector.is_crash_loop(comp),
                }
            result = {"tool": "crash_loop_status", "components": loop_info}

        else:
            return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"Tool not found: {tool}"}}

    except Exception as e:
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps({"erro": str(e)}, ensure_ascii=False, indent=2)}]}}

    return {"jsonrpc": "2.0", "id": rid, "result": {
        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}}


def _read_frame(stream):
    """Lê UMA mensagem JSON-RPC de um stream stdio.

    Suporta os dois protocolos do ecossistema:
      - Framing MCP oficial (Content-Length: <n>\r\n\r\n<body>) — usado pelo opencode.
      - JSON por linha (sem header) — usado por preflight_check.py e servidores legados.
    """
    peek = stream.peek(1)
    if not peek:
        return None

    if peek.startswith(b'{'):
        line = stream.readline()
        if not line:
            return None
        line = line.rstrip(b"\r\n")
        if not line:
            return None
        try:
            return json.loads(line.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    first = stream.readline()
    if not first:
        return None
    first = first.rstrip(b"\r\n")
    if not first.startswith(b"Content-Length:"):
        return None

    headers = {}
    if b":" in first:
        key, value = first.split(b":", 1)
        headers[key.strip().lower()] = value.strip()
    while True:
        line = stream.readline()
        if not line:
            return None
        line = line.rstrip(b"\r\n")
        if not line:
            break
        if b":" in line:
            key, value = line.split(b":", 1)
            headers[key.strip().lower()] = value.strip()
    length = int(headers.get(b"content-length", b"0") or b"0")
    if length <= 0:
        return None
    body = stream.read(length)
    try:
        return json.loads(body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _write_frame(stream, obj):
    data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    stream.write(data + b"\n")
    stream.flush()


if __name__ == "__main__":
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        req = _read_frame(stdin)
        if req is None:
            break
        resp = handle(req)
        if resp is not None:
            _write_frame(stdout, resp)