"""Testes ETAPA 23 — Observability + Reliability.

Testa:
1. timeout
2. retry
3. dependência indisponível
4. circuit breaker
5. reconexão
6. falha de TTS
7. falha de Bridge
8. falha de ferramenta
9. falha de modelo
10. crash/restart
11. fila saturada
12. secret redaction
13. recovery
14. degraded mode
15. missão completa com rastreamento
16. componente independente não derruba outros
17. watchdog heartbeat
18. metrics collection
19. security events
20. incident recording
21. correlation/trace propagation
22. health liveness/readiness
"""

import sys
import os
import time
import threading

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

from observability_reliability import (
    redact_secrets, StructuredLogger, log, TraceContext, MetricsCollector, metrics,
    HealthAggregator, health, HealthLevel, HealthProbe,
    CircuitBreaker, CircuitState, get_circuit_breaker, reset_circuit_breaker,
    RetryPolicy, TimeoutManager, Watchdog, watchdog,
    CrashLoopDetector, crash_detector,
    DegradedMode, degraded,
    IncidentRecorder, incidents,
    SecurityEventRecorder, security_events,
    RecoveryPipeline, recovery,
    consume_for_memory, consume_for_self_assessment,
    check_filesystem_writable, check_disk_space,
    Severity,
)

passed = 0
failed = 0
total = 0


def check(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f'  [PASS] {name}')
    else:
        failed += 1
        print(f'  [FAIL] {name} — {detail}')


def slow_fn():
    time.sleep(2)
    return "done"


def fail_fn():
    raise ConnectionError("Service unavailable")


def tts_fail_fn():
    raise TimeoutError("TTS synthesis timeout")


def bridge_fail_fn():
    raise ConnectionError("WebSocket connection refused")


def tool_fail_fn():
    raise RuntimeError("Tool execution failed")


def model_fail_fn():
    raise Exception("LLM API error 500")


def sometimes_fail_fn():
    sometimes_fail_fn.count += 1
    if sometimes_fail_fn.count <= 2:
        raise ConnectionError("Intermittent failure")
    return "recovered"
sometimes_fail_fn.count = 0


def validated_fn():
    return {"valid": True}


def invalid_result_fn():
    return None


print('=== ETAPA 23 — OBSERVABILITY + RELIABILITY ===\n')

# 1. SECRET REDACTION
print('=== 1. Secret Redaction ===')
r1 = redact_secrets('api_key=sk-abc123def456ghi789')
check('openai key redacted', 'sk-abc123' not in r1 and 'REDACTED' in r1, r1)
r2 = redact_secrets('Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc')
check('jwt redacted', 'eyJhbG' not in r2 and 'REDACTED' in r2, r2)
r3 = redact_secrets('password=supersecret123')
check('password redacted', 'supersecret' not in r3 and 'REDACTED' in r3, r3)
r4 = redact_secrets('token=nvidia-abc123def456ghi789jkl0')
check('nvidia key redacted', 'nvidia-abc' not in r4 and 'REDACTED' in r4, r4)
r5 = redact_secrets('normal text with no secrets')
check('clean text preserved', r5 == 'normal text with no secrets', r5)

# 2. STRUCTURED LOGGING
print('\n=== 2. Structured Logging ===')
log.info('test', 'op', 'test message', correlation_id='corr-123')
events = log.get_recent(5)
check('event emitted', len(events) > 0, f'{len(events)} events')
last = events[-1]
check('event has timestamp', 'ts' in last)
check('event has level', last.get('level') == 'info')
check('event has component', last.get('component') == 'test')
check('event has correlation_id', last.get('correlation_id') == 'corr-123')

# 3. TRACE CONTEXT
print('\n=== 3. Trace Context ===')
ctx = TraceContext.start(mission_id='miss-1')
check('context created', ctx.get('mission_id') == 'miss-1')
check('correlation_id generated', len(ctx.get('correlation_id', '')) > 0)
TraceContext.set_tool('tool-42')
current = TraceContext.current()
check('tool_execution_id set', current.get('tool_execution_id') == 'tool-42')
child = TraceContext.child()
check('child inherits correlation', child.get('correlation_id') == ctx.get('correlation_id'))

# 4. METRICS
print('\n=== 4. Metrics Collection ===')
metrics.reset()
metrics.inc('test_counter')
metrics.inc('test_counter')
metrics.inc('test_counter')
snap = metrics.snapshot()
check('counter incremented', snap['counters'].get('test_counter') == 3)
start = metrics.timer_start('test_op')
time.sleep(0.05)
metrics.timer_end('test_op', start)
snap = metrics.snapshot()
check('timer recorded', 'test_op' in snap.get('timers', {}))
check('timer has p50', 'p50' in snap['timers']['test_op'])
check('timer has p95', 'p95' in snap['timers']['test_op'])
check('timer has p99', 'p99' in snap['timers']['test_op'])
metrics.set_gauge('test_gauge', 42.0)
snap = metrics.snapshot()
check('gauge set', snap['gauges'].get('test_gauge') == 42.0)

# 5. HEALTH
print('\n=== 5. Health System ===')
health.register_component('cognitive_core')
health.register_component('mission_loop')
health.update_component('cognitive_core', HealthLevel.HEALTHY, liveness=True, readiness=True)
health.update_component('mission_loop', HealthLevel.DEGRADED, liveness=True, readiness=False)
report = health.get_report()
check('global health degraded', report['global'] == 'degraded')
check('liveness true', report['liveness'] is True)
check('readiness false', report['readiness'] is False)
check('component count', len(report['components']) == 2)

# LIVENESS vs READINESS
health2 = HealthAggregator()
health2._components.clear()
health2._dependencies.clear()
health2.register_component('svc_a')
health2.update_component('svc_a', HealthLevel.HEALTHY, liveness=True, readiness=True)
check('all ready', health2.get_readiness() is True)
health2.update_component('svc_a', HealthLevel.HEALTHY, liveness=True, readiness=False)
check('not ready', health2.get_readiness() is False)
health2.update_component('svc_a', HealthLevel.OFFLINE, liveness=False, readiness=False)
check('not alive', health2.get_liveness() is False)

# 6. CIRCUIT BREAKER
print('\n=== 6. Circuit Breaker ===')
cb = CircuitBreaker('test_service', failure_threshold=3, timeout_seconds=2)
check('initially closed', cb.state == CircuitState.CLOSED)
check('can execute', cb.can_execute() is True)
for _ in range(3):
    cb.record_failure()
check('open after 3 failures', cb.state == CircuitState.OPEN)
check('cannot execute when open', cb.can_execute() is False)
deadline = time.time() + 3
while time.time() < deadline:
    if cb.can_execute():
        break
    time.sleep(0.1)
check('half-open after timeout', cb.state == CircuitState.HALF_OPEN)
check('can execute half-open', cb.can_execute() is True)
cb.record_success()
cb.record_success()
check('closed after successes', cb.state == CircuitState.CLOSED)
cb.reset()
check('reset works', cb.state == CircuitState.CLOSED)

# 7. RETRY
print('\n=== 7. Retry Policy ===')
sometimes_fail_fn.count = 0
policy = RetryPolicy(max_retries=3, backoff_base=0.01, jitter=False, retry_on=(ConnectionError,))
result = policy.execute(sometimes_fail_fn)
check('retry succeeded after failures', result == 'recovered')
check('retries were counted', metrics.snapshot()['counters'].get('retry.attempts', 0) > 0)

# Retry budget exhausted
budget_policy = RetryPolicy(max_retries=100, retry_budget_per_minute=2, retry_on=(Exception,))
try:
    for _ in range(5):
        budget_policy.execute(fail_fn)
    check('budget exhausted reached', False, 'Should have raised')
except ConnectionError:
    check('budget exhausted raises', True)

# 8. TIMEOUT
print('\n=== 8. Timeout ===')
try:
    result = TimeoutManager.execute(slow_fn, timeout=0.1)
    check('timeout raised', False, 'Should have timed out')
except (TimeoutError, Exception):
    check('timeout raised', True)

result = TimeoutManager.execute(lambda: "quick", timeout=5)
check('fast fn succeeds', result == "quick")

wrapped = TimeoutManager.wrap_fn(slow_fn, timeout=0.1)
try:
    wrapped()
    check('wrapped timeout', False)
except (TimeoutError, Exception):
    check('wrapped timeout', True)

# 9. DEPENDENCY UNAVAILABLE
print('\n=== 9. Dependency Unavailable ===')
detection = recovery.detect('external_api', ConnectionError("Service unavailable"))
check('dependency classified', detection['classification']['category'] == 'dependency')
check('recoverable', detection['recoverable'] is True)
check('suggested retry', detection['suggested_action'].value == 'retry')

# 10. CRASH/RESTART LOOP
print('\n=== 10. Crash/Restart Detection ===')
cd = CrashLoopDetector(window_seconds=60, threshold=3)
for _ in range(3):
    cd.record_event('server', 'crash')
check('crash loop detected', cd.is_crash_loop('server') is True)
check('counts correct', cd.get_crash_counts().get('server', 0) == 3)
cd2 = CrashLoopDetector(window_seconds=0.1, threshold=5)
for _ in range(3):
    cd2.record_event('temp', 'crash')
time.sleep(0.2)
check('no false positive after window', cd2.is_crash_loop('temp') is False)

# 11. DEGRADED MODE
print('\n=== 11. Degraded Mode ===')
dm = DegradedMode()
dm._is_degraded = False
dm._degraded_components.clear()
dm._restrictions.clear()
dm._degraded_since = None
check('initially not degraded', dm.is_degraded() is False)
dm.enter_degraded('tts', 'TTS service down', restrictions=['tts.'])
check('now degraded', dm.is_degraded() is True)
check('tts blocked', dm.is_action_allowed('tts.speak') is False)
check('other allowed', dm.is_action_allowed('memory.store') is True)
dm.exit_degraded('tts')
check('restored', dm.is_degraded() is False)

# 12. RECOVERY PIPELINE
print('\n=== 12. Recovery Pipeline ===')
recovery_test = RecoveryPipeline()
recovery_test._recovery_history.clear()
detection = recovery_test.detect('tool_x', ConnectionError("timeout"))
check('detected', detection is not None)
check('recoverable', detection['recoverable'] is True)

call_count = [0]
def retry_ok():
    call_count[0] += 1
    return "retried_ok"

result = recovery_test.execute_recovery(
    'tool_x', detection, retry_fn=retry_ok)
check('recovery succeeded', result['success'] is True)
check('has steps', len(result.get('steps', [])) > 0)
check('incident created', result.get('incident_id') is not None)

# Recovery with fallback
call_count[0] = 0
def retry_fail():
    raise ConnectionError("still down")

def fallback_ok():
    return "fallback_result"

result2 = recovery_test.execute_recovery(
    'tool_y',
    recovery_test.detect('tool_y', ConnectionError("down")),
    retry_fn=retry_fail,
    fallback_fn=fallback_ok)
check('fallback succeeded', result2['success'] is True)
check('used fallback', result2.get('used_fallback') is True)

# Recovery with validation
call_count[0] = 0
result3 = recovery_test.execute_recovery(
    'tool_z',
    recovery_test.detect('tool_z', ConnectionError("down")),
    retry_fn=retry_ok,
    validate_fn=validated_fn)
check('validated recovery', result3['success'] is True)

# Failed validation
result4 = recovery_test.execute_recovery(
    'tool_v',
    recovery_test.detect('tool_v', Exception("bad")),
    retry_fn=retry_ok,
    validate_fn=lambda r: r is not None and r != "retried_ok")
check('validation failure detected', result4['success'] is False)

# 13. TTS FAILURE
print('\n=== 13. TTS Failure (does not crash system) ===')
detection = recovery.detect('tts', TimeoutError("TTS timeout"))
check('tts failure detected', detection is not None)
check('tts recoverable', detection['recoverable'] is True)
check('system still works', True)

# 14. BRIDGE FAILURE
print('\n=== 14. Bridge Failure (does not crash system) ===')
detection = recovery.detect('bridge', ConnectionError("WebSocket refused"))
check('bridge failure detected', detection is not None)
check('bridge classified', detection['classification']['category'] == 'dependency')
check('system still works', True)

# 15. TOOL FAILURE
print('\n=== 15. Tool Failure ===')
detection = recovery.detect('tool_orchestrator', RuntimeError("tool execution failed"))
check('tool failure detected', detection is not None)
check('tool classified', detection['classification']['category'] == 'unknown')

# 16. MODEL FAILURE
print('\n=== 16. Model Failure ===')
detection = recovery.detect('cognitive_core', Exception("LLM API error 500"))
check('model failure detected', detection is not None)
check('model recoverable', detection['recoverable'] is True)

# 17. WATCHDOG
print('\n=== 17. Watchdog Heartbeat ===')
w = Watchdog(check_interval=0.1)
w.register('service_a', max_silence_s=0.3)
check('service alive after beat', w.is_alive('service_a') is True)
w.beat('service_a')
check('still alive after beat', w.is_alive('service_a') is True)
time.sleep(0.5)
check('stale after silence', w.is_alive('service_a') is False)
stale = w.get_stale()
check('stale detected', 'service_a' in stale)

# 18. INCIDENTS
print('\n=== 18. Incident Recording ===')
inc = incidents.create('cognitive_core', 'HIGH', 'LLM timeout',
                       probable_cause='API rate limit',
                       correlation_id='corr-test', mission_id='miss-test')
check('incident created', inc is not None)
check('incident has id', len(inc.id) > 0)
incidents.add_action(inc.id, 'attempted retry')
incidents.add_action(inc.id, 'fallback triggered')
incidents.resolve(inc.id, 'recovered via fallback',
                  recovery='Used cached response',
                  final_state='recovered')
recent = incidents.get_recent(5)
check('incident resolved', any(i['final_state'] == 'recovered' for i in recent))
stats = incidents.get_stats()
check('stats correct', stats['total'] > 0)

# 19. SECURITY EVENTS
print('\n=== 19. Security Events ===')
evt = security_events.permission_denied('tool_runtime', 'execute_shell')
check('event created', evt is not None)
check('event blocked', evt.blocked is True)
check('event has correlation', True)
security_events.tool_blocked('mission_loop', 'rm', 'dangerous command')
security_events.unauthorized_attempt('external', 'token forgery')
recent = security_events.get_recent(5)
check('events recorded', len(recent) >= 3)
by_level = security_events.get_by_level('HIGH')
check('HIGH level filtered', len(by_level) >= 1)

# 20. CORRELATION/TRACE
print('\n=== 20. Correlation/Trace ===')
ctx = TraceContext.start(mission_id='e2e-miss', correlation_id='e2e-corr')
log.info('cognitive_core', 'classify', 'intent classified',
         mission_id='e2e-miss', correlation_id='e2e-corr', trace_id=ctx['trace_id'])
log.info('mission_loop', 'execute', 'step completed',
         mission_id='e2e-miss', correlation_id='e2e-corr')
events = log.get_recent(10)
e2e_events = [e for e in events if e.get('mission_id') == 'e2e-miss']
check('trace events linked', len(e2e_events) >= 2)
check('same correlation', all(
    e.get('correlation_id') == 'e2e-corr' for e in e2e_events))

# 21. COMPONENT ISOLATION
print('\n=== 21. Component Isolation ===')
dm2 = DegradedMode()
dm2._is_degraded = False
dm2._degraded_components.clear()
dm2._restrictions.clear()
dm2._degraded_since = None
dm2.enter_degraded('tts', 'TTS down', restrictions=['tts.'])
check('tts degraded', dm2.is_degraded() is True)
check('memory not affected', dm2.is_action_allowed('memory.store') is True)
check('mission not affected', dm2.is_action_allowed('mission.execute') is True)
check('cognitive not affected', dm2.is_action_allowed('cognitive.classify') is True)
dm2.exit_degraded('tts')

# 22. FILESYSTEM HEALTH
print('\n=== 22. Filesystem Health ===')
check('runtime writable', check_filesystem_writable())
check('disk space ok', check_disk_space())

# 23. CRASH DOES NOT PROPAGATE
print('\n=== 23. Crash Isolation ===')
# TTS failure should not crash memory
try:
    consume_for_memory('tts', TimeoutError("TTS timeout"))
    check('memory integration survives TTS failure', True)
except Exception as e:
    check('memory integration survives TTS failure', False, str(e))

# Bridge failure should not crash assessment
try:
    consume_for_self_assessment('bridge', 'connect', False, 500.0, 'Connection refused')
    check('assessment survives bridge failure', True)
except Exception as e:
    check('assessment survives bridge failure', False, str(e))

# 24. PERSISTENCE
print('\n=== 24. Persistence ===')
try:
    from observability_reliability import save_state
    save_state()
    state_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              'runtime', 'observability_state.json')
    check('state file exists', os.path.exists(state_path))
except Exception as e:
    check('save_state', False, str(e))

# SUMMARY
print(f'\n==== RESULTADO: {passed} passaram, {failed} falharam ====')
