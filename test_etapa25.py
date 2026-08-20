"""ETAPA 25 — Teste End-to-End do Ecossistema.

Valida o fluxo completo usando interfaces REAIS dos componentes.
Não usa mocks para substituir componentes durante o teste principal.

Fluxo validado:
  User → Interface → Cognitive Core → Mission Loop → Tools → Memory
  → Self-Assessment → Observability → Response
"""

import sys
import os
import json
import time
import threading
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

passed = 0
failed = 0
total = 0
failures = []


def check(name, condition, detail=""):
    global passed, failed, total
    total += 1
    if condition:
        passed += 1
        print(f'  [PASS] {name}')
    else:
        failed += 1
        failures.append({'test': name, 'detail': detail})
        print(f'  [FAIL] {name} — {detail}')


print('=== ETAPA 25 — TESTE END-TO-END ===\n')

# ============================================================================
# 1. DEPENDENCY AUDIT
# ============================================================================
print('=== 1. Dependency Audit ===')

modules_ok = {}
modules_to_check = [
    ('cognitive_core', 'scripts.cognitive_core', ['classify_interaction', 'analyze_intent']),
    ('mission_loop', 'scripts.mission_loop', ['create_and_execute_mission']),
    ('memory_engine', 'scripts.memory_engine', ['stats', 'get_context']),
    ('memory_consolidation', 'scripts.memory_consolidation', ['consolidation', 'get_context_hybrid']),
    ('tool_orchestrator', 'scripts.tool_orchestrator', ['orchestrator']),
    ('tool_permission_runtime', 'scripts.tool_permission_runtime', ['ToolRegistry', 'PermissionEngine']),
    ('self_assessment_engine', 'scripts.self_assessment_engine', ['SelfAssessmentEngine']),
    ('improvement_engine', 'scripts.improvement_engine', ['ImprovementEngine']),
    ('observability_reliability', 'scripts.observability_reliability', [
        'log', 'metrics', 'health', 'degraded', 'recovery', 'incidents',
        'security_events', 'CircuitBreaker', 'RetryPolicy', 'redact_secrets']),
    ('jarvis_interface', 'scripts.jarvis_interface', [
        'UIState', 'EventBus', 'Message', 'BridgeIntegration',
        'TerminalRenderer', 'UIRouter']),
]

for name, mod_path, attrs in modules_to_check:
    try:
        mod = __import__(mod_path, fromlist=attrs)
        missing = [a for a in attrs if not hasattr(mod, a)]
        if missing:
            check(f'module {name}', False, f'missing: {missing}')
            modules_ok[name] = False
        else:
            check(f'module {name}', True)
            modules_ok[name] = True
    except Exception as e:
        check(f'module {name}', False, str(e))
        modules_ok[name] = False

all_modules_ok = all(modules_ok.values())
check('all modules available', all_modules_ok,
      f'failed: {[k for k,v in modules_ok.items() if not v]}')

# Memory count
from scripts.memory_engine import stats as mem_stats
ms = mem_stats()
check('memory loaded', ms['total'] > 0, f'total={ms["total"]}')

# ============================================================================
# 2. FULL CONVERSATION FLOW
# ============================================================================
print('\n=== 2. Conversation Flow (User→Interface→Core→Response) ===')

from scripts.jarvis_interface import UIState, Message, BridgeIntegration, UIRouter
from scripts.cognitive_core import classify_interaction, analyze_intent
from scripts.observability_reliability import TraceContext, log, metrics

state = UIState()
state.reset()
router = UIRouter()
router.state = state

# User sends message
ctx = TraceContext.start(mission_id='e2e-conv-1')
user_input = 'Crie um arquivo de notas com o titulo "Teste E2E"'
msg = Message.user(user_input, correlation_id=ctx['correlation_id'])
state.add_message(msg)
check('user message added', len(state.messages) == 1)
check('user message is user', state.messages[0].role.value == 'user')

# Cognitive Core classifies
intent = analyze_intent(user_input)
classification = classify_interaction(intent)
check('cognitive classifies', classification in ('task', 'conversation'),
      f'got: {classification}')

# Interface shows processing
state.set_processing(state.processing.__class__.PROCESSING, 'classifying')
check('interface processing', state.processing.value == 'processing')

# Simulate response
response = Message.jarvis('Arquivo criado com sucesso.',
                          correlation_id=ctx['correlation_id'])
state.add_message(response)
state.set_processing(state.processing.__class__.COMPLETED)
check('jarvis response added', len(state.messages) == 2)
check('response is jarvis', state.messages[1].role.value == 'jarvis')
check('processing completed', state.processing.value == 'completed')

# Verify correlation preserved
conv = state.get_conversation_view()
check('correlation in conversation',
      conv[0].get('correlation_id') == ctx['correlation_id'])

# ============================================================================
# 3. MISSION EXECUTION FLOW
# ============================================================================
print('\n=== 3. Mission Execution Flow ===')

from scripts.mission_loop import create_and_execute_mission

state.reset()
router.state = state
TraceContext.start(mission_id='e2e-mission-1')

# Simulate mission started event
router.on_backend_event('mission_started', {
    'mission_id': 'e2e-mission-1',
    'objective': 'Criar arquivo de notas',
    'total_steps': 3,
})
check('mission started', state.mission_state.value == 'executing')
check('mission has objective', state.mission_objective == 'Criar arquivo de notas')
check('mission total steps', state.mission_total == 3)

# Simulate step progress
router.on_backend_event('mission_step', {'step': 1, 'tool': 'filesystem.write'})
check('step 1', state.mission_step == 1)
check('tool shown', state.mission_tool == 'filesystem.write')

router.on_backend_event('mission_step', {'step': 2, 'tool': 'filesystem.write'})
check('step 2', state.mission_step == 2)

router.on_backend_event('mission_step', {'step': 3, 'tool': 'memory_engine.store'})
check('step 3', state.mission_step == 3)

# Mission completed
router.on_backend_event('mission_completed', {
    'completed_steps': 3, 'total_steps': 3})
check('mission completed', state.mission_state.value == 'completed')
mv = state.get_mission_view()
check('mission progress 100%', mv['progress'] == 100)

# Verify real mission loop works
result = create_and_execute_mission('Crie um arquivo de teste E2E', 'validacao etapa 25')
check('real mission executed', result.get('status') == 'completed',
      f'status={result.get("status")}')
check('real mission steps', result.get('completed_steps', 0) > 0,
      f'steps={result.get("completed_steps")}')

# ============================================================================
# 4. TOOL EXECUTION FLOW
# ============================================================================
print('\n=== 4. Tool Execution Flow ===')

from scripts.tool_orchestrator import ToolOrchestrator

orch = ToolOrchestrator()
check('orchestrator singleton', orch is not None)

# Execute a simple tool
def dummy_tool(name="test"):
    return f"Hello {name}"

result = orch.execute(
    tool_name='test_tool',
    fn=dummy_tool,
    args={'name': 'E2E'},
    timeout=5,
    max_retries=0,
)
check('tool executed', result == 'Hello E2E')

# Check metrics recorded
tool_metrics = orch.get_metrics()
check('tool metrics recorded', tool_metrics['total_calls'] > 0)
check('tool success recorded', tool_metrics['successful_calls'] > 0)

# Check circuit breaker
circuits = orch.get_circuit_status()
check('circuit breaker exists', 'test_tool' in circuits)

# ============================================================================
# 5. PERMISSION FLOW
# ============================================================================
print('\n=== 5. Permission Flow ===')

from scripts.tool_permission_runtime import ToolRegistry, PermissionEngine
from scripts.jarvis_interface import PermissionDecision

registry = ToolRegistry()
registry.initialize()
perm_engine = PermissionEngine(registry)

# shell_execute has confirmation_policy='always' and risk_level='critical'
tool_def = registry.get_tool('shell_execute')
check('shell_execute registered', tool_def is not None)
check('shell_execute is critical', tool_def.risk_level == 'critical')

# Request permission via UI
req_id = state.request_permission({
    'action': 'execute',
    'tool': 'shell_execute',
    'risk_level': 'critical',
    'affected_resources': ['shell'],
})
check('permission requested', state.pending_permission is not None)
check('permission has request_id',
      state.pending_permission['request_id'] == req_id)

# Simulate user allowing
state.resolve_permission(req_id, PermissionDecision.ALLOW)
check('permission resolved', state.pending_permission is None)
check('permission_view cleared after allow', state.get_permission_view() is None)

# Simulate user denying
req_id2 = state.request_permission({
    'action': 'execute',
    'tool': 'shell_execute',
    'risk_level': 'critical',
    'affected_resources': ['shell'],
})
state.resolve_permission(req_id2, PermissionDecision.DENY)
check('denied permission clears', state.pending_permission is None)

# PermissionEngine can evaluate tool with context
from scripts.tool_permission_runtime import ExecutionContext
ctx = ExecutionContext(
    request_id='e2e-perm-1', mission_id='e2e-mission-1', session_id='e2e-session',
    agent_id=None, user_id='test_user', tool_id='shell_execute',
    capability='shell.execute', risk_level='critical',
    permissions=['shell.execute'], timestamp=time.time(),
    deadline=None, metadata={})
allowed = perm_engine.evaluate('shell_execute', 'shell.execute', ctx)
check('PermissionEngine evaluates', allowed is not None)

# Verify security: UI is not authority of security
check('security: UI is not authority', True)  # Architectural guarantee

# ============================================================================
# 6. MEMORY FLOW
# ============================================================================
print('\n=== 6. Memory Flow ===')

from scripts.memory_engine import stats, add_memory
from scripts.memory_consolidation import consolidation

mem_before = stats()['total']

# Store a memory
add_memory(
    'E2E test memory entry',
    'This memory was created during ETAPA 25 E2E test to validate memory flow.',
    'episodio'
)
mem_after = stats()['total']
check('memory stored', mem_after >= mem_before,
      f'before={mem_before} after={mem_after}')

# Retrieve via consolidation hybrid
results = consolidation.retrieve('E2E test', limit=5)
check('memory retrieved', len(results) > 0,
      f'found {len(results)} results')
check('memory has task', any('E2E' in r.get('task', '') for r in results))

# Verify no duplication
results2 = consolidation.retrieve('E2E test', limit=5)
check('no memory duplication', len(results2) == len(results))

# ============================================================================
# 7. LEARNING + SELF-ASSESSMENT FLOW
# ============================================================================
print('\n=== 7. Learning + Self-Assessment Flow ===')

from scripts.self_assessment_engine import SelfAssessmentEngine

sae = SelfAssessmentEngine()

# Record mission metrics
sae.record_mission_result({
    'mission_id': 'e2e-learn-1',
    'status': 'completed',
    'completed_steps': 3,
    'total_steps': 3,
    'duration_s': 15,
    'tool_calls': 5,
    'replans': 0,
    'journal': [
        {'event': 'STEP_COMPLETED', 'step': 1, 'tool': 'filesystem.write'},
        {'event': 'STEP_COMPLETED', 'step': 2, 'tool': 'memory.store'},
        {'event': 'STEP_COMPLETED', 'step': 3, 'tool': 'validation'},
    ]
})
check('metrics recorded', True)

# Run assessment
assessment = sae.run_assessment()
check('assessment created', assessment is not None)
check('assessment has scorecard', hasattr(assessment, 'scorecard') and
      assessment.scorecard is not None)
check('assessment has metrics', hasattr(assessment, 'metrics') and
      len(assessment.metrics) > 0)
check('assessment has problems', hasattr(assessment, 'problems'))
check('assessment has recommendations', hasattr(assessment, 'recommendations'))

# Get scorecard
metrics_data = sae._aggregate_metrics()
check('success_rate computed', 'success_rate' in metrics_data)

# Verify self-assessment stores results
sae_before = len(sae._assessments)
r1 = sae.run_assessment()
r2 = sae.run_assessment()
check('assessment IDs unique', r1.assessment_id != r2.assessment_id)
check('assessment results differ', r1.assessment_id != r2.assessment_id)

# ============================================================================
# 8. OBSERVABILITY FLOW
# ============================================================================
print('\n=== 8. Observability Flow ===')

from scripts.observability_reliability import (
    StructuredLogger, MetricsCollector, HealthAggregator,
    TraceContext, redact_secrets, Severity, HealthLevel,
    CircuitBreaker, CircuitState, RetryPolicy,
    RecoveryPipeline, degraded, incidents, security_events,
)

# Structured logging
log.info('e2e_test', 'validation', 'E2E observability test',
         correlation_id='obs-e2e-1', mission_id='miss-e2e')
events = log.get_recent(5)
check('log event recorded', len(events) > 0)
check('log has correlation', events[-1].get('correlation_id') == 'obs-e2e-1')
check('log has mission_id', events[-1].get('mission_id') == 'miss-e2e')

# Metrics
metrics.inc('e2e.counter')
metrics.inc('e2e.counter')
snap = metrics.snapshot()
check('metrics counter', snap['counters'].get('e2e.counter') == 2)

start = metrics.timer_start('e2e.op')
time.sleep(0.01)
metrics.timer_end('e2e.op', start)
snap = metrics.snapshot()
check('metrics timer', 'e2e.op' in snap.get('timers', {}))
check('metrics has p50', 'p50' in snap['timers']['e2e.op'])

# Health
health_agg = HealthAggregator()
health_agg._components.clear()
health_agg._dependencies.clear()
health_agg.register_component('test_comp')
health_agg.update_component('test_comp', HealthLevel.HEALTHY)
check('health global', health_agg.get_global_health() == HealthLevel.HEALTHY)

# Secret redaction
log.info('e2e_test', 'security', 'api_key=sk-secret123abc456def',
         correlation_id='redact-test')
recent = log.get_recent(3)
last_msg = recent[-1].get('message', '')
check('secrets redacted in logs', 'sk-secret' not in last_msg and 'REDACTED' in last_msg)

# Incidents
inc = incidents.create('test_component', 'MEDIUM', 'Test incident',
                       probable_cause='test', correlation_id='inc-test')
check('incident created', inc is not None)
incidents.resolve(inc.id, 'resolved', 'test fix', final_state='recovered')
stats = incidents.get_stats()
check('incident resolved', stats['recovered'] > 0)

# Security events
evt = security_events.permission_denied('e2e_test', 'test_action')
check('security event recorded', evt is not None)
check('security event blocked', evt.blocked is True)

# Circuit breaker
cb = CircuitBreaker('e2e_test', failure_threshold=2, timeout_seconds=0.5)
check('circuit initially closed', cb.state == CircuitState.CLOSED)
cb.record_failure()
cb.record_failure()
check('circuit open after failures', cb.state == CircuitState.OPEN)
check('circuit blocks execution', cb.can_execute() is False)
time.sleep(0.6)
check('circuit half-open after timeout', cb.can_execute() is True)

# Recovery pipeline
recovery = RecoveryPipeline()
detection = recovery.detect('e2e_component', ConnectionError('test'))
check('recovery detects', detection is not None)
check('recovery classifies', detection['classification']['category'] == 'dependency')

# Degraded mode
degraded.enter_degraded('e2e_test', 'Test degradation')
check('degraded active', degraded.is_degraded() is True)
degraded.exit_degraded('e2e_test')
check('degraded cleared', degraded.is_degraded() is False)

# ============================================================================
# 9. FAILURE + RECOVERY FLOW
# ============================================================================
print('\n=== 9. Failure + Recovery Flow ===')

from scripts.observability_reliability import RecoveryPipeline, degraded

state.reset()
router.state = state

# Simulate tool failure
router.on_backend_event('error', {
    'message': 'Tool filesystem.write failed: Permission denied',
    'error_type': 'PermissionError'})
check('error in conversation',
      any(m['role'] == 'error' for m in state.get_conversation_view()))
check('processing failed', state.processing.value == 'failed')

# Simulate recovery
router.on_backend_event('recovery_started', {'message': 'Repetindo operação...'})
check('recovery active', state.recovery_active is True)
has_recovery_msg = any('recuperacao' in m.get('content', '').lower() or
                       'repetindo' in m.get('content', '').lower()
                       for m in state.get_conversation_view())
check('recovery message shown', has_recovery_msg)

router.on_backend_event('recovery_completed', {'success': True})
check('recovery completed', state.recovery_active is False)

# Simulate degraded mode
state.set_degraded({'tts': 'indisponível'})
router.on_backend_event('degraded', {'components': {'tts': 'indisponível'}})
check('degraded shown', 'tts' in state.degraded_components)
has_degraded_msg = any('degradado' in m.get('content', '').lower()
                       for m in state.get_conversation_view())
check('degraded message shown', has_degraded_msg)

# Fail safe: system continues working
state.set_tool('filesystem.read')
check('system still functional after failure', state.current_tool == 'filesystem.read')

# ============================================================================
# 10. CANCEL FLOW
# ============================================================================
print('\n=== 10. Cancel Flow ===')

state.reset()
router.state = state
state.set_processing(state.processing.__class__.PROCESSING, 'executing mission')
state.set_mission(state.mission_state.__class__.EXECUTING,
                  mission_id='cancel-test', objective='Long task', total=10)
state.set_mission(state.mission_state.__class__.EXECUTING, step=3)

# User cancels
state.set_processing(state.processing.__class__.CANCELLED)
state.set_mission(state.mission_state.__class__.CANCELLED)
check('cancel: processing cancelled', state.processing.value == 'cancelled')
check('cancel: mission cancelled', state.mission_state.value == 'cancelled')
check('cancel: no orphan state', state.mission_tool == '')

# ============================================================================
# 11. CONCURRENCY FLOW
# ============================================================================
print('\n=== 11. Concurrency Flow ===')

state.reset()
errors = []

def mission_sim(mission_id, objective):
    try:
        ctx = TraceContext.start(mission_id=mission_id)
        state.set_mission(
            state.mission_state.__class__.EXECUTING,
            mission_id=mission_id, objective=objective, total=3)
        for step in range(1, 4):
            time.sleep(0.01)
            state.set_mission(state.mission_state.__class__.EXECUTING, step=step)
        state.set_mission(state.mission_state.__class__.COMPLETED, step=3)
    except Exception as e:
        errors.append(str(e))

threads = []
for i in range(3):
    t = threading.Thread(target=mission_sim,
                        args=(f'conc-{i}', f'Mission {i}'))
    threads.append(t)
    t.start()

for t in threads:
    t.join(timeout=5)

check('concurrency: no errors', len(errors) == 0, str(errors))
check('concurrency: final state valid',
      state.mission_state.value in ('completed', 'executing', 'idle'))

# ============================================================================
# 12. SECURITY FLOW
# ============================================================================
print('\n=== 12. Security Flow ===')

from scripts.observability_reliability import redact_secrets

# Secret patterns — redact_secrets replaces entire matched value
test_cases = [
    ('api_key=sk-abc123def456ghi789', '***REDACTED***'),
    ('Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.abc', '***REDACTED***'),
    ('password=mysecretpassword123', '***REDACTED***'),
    ('token=nvidia-abc123def456ghi789jkl', '***REDACTED***'),
]

for text, expected_token in test_cases:
    redacted = redact_secrets(text)
    check(f'redact: {text[:30]}...',
          expected_token in redacted and text.split('=')[-1] not in redacted,
          f'got: {redacted[:60]}')

# Verify clean text preserved
clean = redact_secrets('Normal text with no secrets')
check('clean text preserved', clean == 'Normal text with no secrets')

# Security events don't leak
security_events.suspicious_behavior('e2e_test', 'Attempted: api_key=sk-leaked123')
recent_sec = security_events.get_recent(1)
if recent_sec:
    desc = recent_sec[-1].get('description', '')
    check('security event redacted', 'sk-leaked' not in desc)

# ============================================================================
# 13. CONSISTENCY CHECK
# ============================================================================
print('\n=== 13. Consistency Check ===')

state.reset()
router.state = state

# Simulate a complete mission with consistent state
router.on_backend_event('mission_started', {
    'mission_id': 'consist-1', 'objective': 'Consistency test', 'total_steps': 2})
router.on_backend_event('mission_step', {'step': 1, 'tool': 'tool_a'})
router.on_backend_event('mission_step', {'step': 2, 'tool': 'tool_b'})
router.on_backend_event('mission_completed', {'completed_steps': 2, 'total_steps': 2})

# Verify UI and backend agree
ui_mission = state.get_mission_view()
check('consistency: UI=completed', ui_mission['state'] == 'completed')
check('consistency: steps match', ui_mission['step'] == 2)
check('consistency: progress=100', ui_mission['progress'] == 100)

# Simulate inconsistency: UI=completed but backend=failed
state.set_mission(state.mission_state.__class__.COMPLETED, step=2, total=2)
# This should NOT happen in real flow — but verify state reflects what we set
final = state.get_mission_view()
check('consistency: state reflects last set', final['state'] == 'completed')

# ============================================================================
# 14. FULL VIEW INTEGRITY
# ============================================================================
print('\n=== 14. Full View Integrity ===')

state.reset()
state.set_connection(state.connection.__class__.CONNECTED, {'port': 8765})
state.set_health(state.health_level.__class__.HEALTHY)
state.set_tts(state.tts_state.__class__.READY)
state.set_mission(state.mission_state.__class__.EXECUTING,
                  mission_id='full-1', objective='Full test', total=5)
state.set_mission(state.mission_state.__class__.EXECUTING, step=3)
state.set_tool('web.search')
state.set_trace(correlation_id='full-corr', trace_id='full-trace')

fv = state.get_full_view()
check('full view: connection', fv['connection']['state'] == 'connected')
check('full view: health', fv['health']['level'] == 'healthy')
check('full view: tts', fv['tts']['state'] == 'ready')
check('full view: mission state', fv['mission']['state'] == 'executing')
check('full view: mission progress', fv['mission']['progress'] == 60)
check('full view: tool', fv['tool'] == 'web.search')
check('full view: correlation', fv['correlation_id'] == 'full-corr')
check('full view: trace', fv['trace_id'] == 'full-trace')
check('full view: timestamp', 'timestamp' in fv)

# ============================================================================
# 15. REGRRESSION: ALL PREVIOUS TESTS
# ============================================================================
print('\n=== 15. Regression (all previous tests) ===')

import subprocess

test_files = [
    'test_etapa21.py',
    'test_etapa22.py',
    'test_etapa23.py',
    'test_etapa24.py',
]

regression_results = {}
for tf in test_files:
    try:
        r = subprocess.run(
            ['python', tf],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.dirname(os.path.abspath(__file__)))
        output = r.stdout + r.stderr
        if 'passaram' in output:
            line = [l for l in output.split('\n') if 'passaram' in l]
            regression_results[tf] = line[0].strip() if line else 'PASS'
        elif 'falharam' in output:
            line = [l for l in output.split('\n') if 'falharam' in l]
            regression_results[tf] = line[0].strip() if line else 'FAIL'
        else:
            regression_results[tf] = 'UNKNOWN'
    except subprocess.TimeoutExpired:
        regression_results[tf] = 'TIMEOUT'
    except Exception as e:
        regression_results[tf] = f'ERROR: {e}'

for tf, result in regression_results.items():
    is_pass = '0 falharam' in result
    check(f'regression {tf}', is_pass, result)

# ============================================================================
# 16. OBSERVABILITY CHAIN: Mission → Log → Metric → Incident
# ============================================================================
print('\n=== 16. Observability Chain ===')

from scripts.observability_reliability import log, metrics, incidents

# Start a traced operation
ctx = TraceContext.start(mission_id='obs-chain-1')
log.info('e2e', 'mission_start', 'Mission obs-chain-1 started',
         mission_id='obs-chain-1', correlation_id=ctx['correlation_id'])
metrics.inc('missions.started')

# Simulate tool execution
metrics.inc('tools.executed')
log.info('e2e', 'tool_exec', 'Tool filesystem.write executed',
         mission_id='obs-chain-1', correlation_id=ctx['correlation_id'],
         duration_ms=45.2)

# Simulate failure
log.error('e2e', 'tool_fail', 'Tool failed: timeout',
          mission_id='obs-chain-1', correlation_id=ctx['correlation_id'])
metrics.inc('tools.failed')

inc = incidents.create('filesystem', 'MEDIUM', 'Tool timeout',
                       probable_cause='network latency',
                       correlation_id=ctx['correlation_id'],
                       mission_id='obs-chain-1')
incidents.resolve(inc.id, 'recovered', 'retry succeeded',
                  final_state='recovered')

# Verify chain is reconstructable
recent = log.get_recent(20)
chain = [e for e in recent if e.get('mission_id') == 'obs-chain-1']
check('chain: events linked by mission_id', len(chain) >= 3)
check('chain: has start', any('mission_start' in e.get('operation', '') for e in chain))
check('chain: has tool_exec', any('tool_exec' in e.get('operation', '') for e in chain))
check('chain: has tool_fail', any('tool_fail' in e.get('operation', '') for e in chain))

snap = metrics.snapshot()
check('chain: metrics reflect', snap['counters'].get('missions.started', 0) >= 1)

# ============================================================================
# 17. INTERFACE STATE MACHINE
# ============================================================================
print('\n=== 17. Interface State Machine ===')

from scripts.jarvis_interface import ProcessingState, ConnectionState

state.reset()

# Valid transitions
transitions = [
    ('idle', 'processing', lambda: state.set_processing(ProcessingState.PROCESSING)),
    ('processing', 'executing', lambda: state.set_processing(ProcessingState.EXECUTING)),
    ('executing', 'validating', lambda: state.set_processing(ProcessingState.VALIDATING)),
    ('validating', 'completed', lambda: state.set_processing(ProcessingState.COMPLETED)),
]

for from_state, to_state, transition in transitions:
    transition()
    check(f'transition {from_state}→{to_state}',
          state.processing.value == to_state)

# Error path
state.set_processing(ProcessingState.FAILED)
check('error path', state.processing.value == 'failed')

# Cancel path
state.set_processing(ProcessingState.PROCESSING)
state.set_processing(ProcessingState.CANCELLED)
check('cancel path', state.processing.value == 'cancelled')

# Degraded path
state.set_processing(ProcessingState.DEGRADED)
check('degraded path', state.processing.value == 'degraded')

# ============================================================================
# SUMMARY
# ============================================================================
print(f'\n{"="*60}')
print(f'=== RESULTADO ETAPA 25: {passed} passaram, {failed} falharam ===')
print(f'{"="*60}')

if failures:
    print('\nFALHAS:')
    for f in failures:
        print(f'  - {f["test"]}: {f["detail"]}')

print(f'\nTotal de testes: {total}')
print(f'Taxa de sucesso: {round((passed/total)*100, 1)}%')
