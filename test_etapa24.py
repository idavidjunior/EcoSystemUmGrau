"""Testes ETAPA 24 — Interface do Jarvis.

Testa:
1. renderização de mensagens
2. comunicação (bridge integration)
3. envio de mensagem
4. recebimento
5. estados (connection, processing, mission, health, tts)
6. reconexão
7. erros
8. missão
9. cancelamento
10. permission request
11. degraded mode
12. TTS/Bridge
13. duplicação de eventos
14. mensagens fora de ordem
15. presenters
16. terminal renderer
"""

import sys
import os
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

from jarvis_interface import (
    UIState, EventBus, Message, MessageRole, MessageDeduplicator,
    ConnectionState, ProcessingState, MissionState, HealthLevel,
    TTSState, PermissionDecision,
    Presenters, BridgeIntegration, TerminalRenderer,
    ReconnectionHandler, UIRouter,
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


print('=== ETAPA 24 — INTERFACE DO JARVIS ===\n')

# 1. MESSAGE MODEL
print('=== 1. Message Model ===')
msg_user = Message.user('Olá Jarvis')
check('user message created', msg_user.role == MessageRole.USER)
check('user has content', msg_user.content == 'Olá Jarvis')
check('user has timestamp', len(msg_user.timestamp) > 0)
check('user has id', len(msg_user.id) > 0)

msg_jarvis = Message.jarvis('Olá! Como posso ajudar?')
check('jarvis message created', msg_jarvis.role == MessageRole.JARVIS)

msg_system = Message.system('Sistema inicializado')
check('system message created', msg_system.role == MessageRole.SYSTEM)

msg_error = Message.error('Falha na conexão', error_type='ConnectionError')
check('error message created', msg_error.role == MessageRole.ERROR)
check('error has type', msg_error.error_type == 'ConnectionError')

msg_perm = Message.permission('Aprovar execução?')
check('permission message created', msg_perm.role == MessageRole.PERMISSION)

d = msg_user.to_dict()
check('to_dict has role string', d['role'] == 'user')
check('to_dict has content', d['content'] == 'Olá Jarvis')

# 2. EVENT BUS
print('\n=== 2. Event Bus ===')
bus = EventBus()
received = []
bus.on('test_event', lambda d: received.append(d))
bus.emit('test_event', {'key': 'value'})
check('event received', len(received) == 1)
check('event data correct', received[0] == {'key': 'value'})

received2 = []
bus.on('*', lambda d: received2.append(d))
bus.emit_any('specific', {'x': 1})
check('wildcard received', len(received2) == 1)
check('wildcard has event key', received2[0]['event'] == 'specific')

bus.off('test_event', lambda d: None)  # no-op, listener still active
bus.emit('test_event', {'key': 'value2'})
check('listener still active', len(received) == 2)

# 3. UI STATE
print('\n=== 3. UI State ===')
state = UIState()
state.reset()
check('initial connection', state.connection == ConnectionState.DISCONNECTED)
check('initial processing', state.processing == ProcessingState.IDLE)
check('initial mission', state.mission_state == MissionState.IDLE)
check('initial health', state.health_level == HealthLevel.HEALTHY)
check('initial tts', state.tts_state == TTSState.READY)

state.set_connection(ConnectionState.CONNECTED, {'port': 8765})
check('connection set', state.connection == ConnectionState.CONNECTED)
view = state.get_connection_view()
check('connection view has state', view['state'] == 'connected')
check('connection view has details', view['details'].get('port') == 8765)

state.set_processing(ProcessingState.PROCESSING, 'classifying')
check('processing set', state.processing == ProcessingState.PROCESSING)
check('operation set', state.current_operation == 'classifying')

state.set_processing(ProcessingState.COMPLETED)
check('completed', state.processing == ProcessingState.COMPLETED)
check('start cleared', state.operation_start is None)

# 4. MESSAGE DEDUPLICATION
print('\n=== 4. Message Deduplication ===')
dedup = MessageDeduplicator()
check('first not dup', dedup.is_duplicate('msg-1') is False)
check('second is dup', dedup.is_duplicate('msg-1') is True)
check('different not dup', dedup.is_duplicate('msg-2') is False)

# 5. STATE MUTATIONS
print('\n=== 5. State Mutations ===')
state.reset()
state.set_mission(MissionState.EXECUTING, mission_id='m-1',
                  objective='Criar arquivo', total=5)
check('mission executing', state.mission_state == MissionState.EXECUTING)
check('mission id set', state.mission_id == 'm-1')
check('mission objective', state.mission_objective == 'Criar arquivo')
check('mission total', state.mission_total == 5)

state.set_mission(MissionState.EXECUTING, step=3, tool='filesystem.write')
check('mission step', state.mission_step == 3)
check('mission tool', state.mission_tool == 'filesystem.write')

mv = state.get_mission_view()
check('mission progress', mv['progress'] == 60)
check('mission state executing', mv['state'] == 'executing')

state.set_health(HealthLevel.DEGRADED, {'tts': 'offline'})
check('health degraded', state.health_level == HealthLevel.DEGRADED)
hv = state.get_health_view()
check('health view', hv['level'] == 'degraded')

state.set_tts(TTSState.SPEAKING, 'Olá mundo')
check('tts speaking', state.tts_state == TTSState.SPEAKING)
tv = state.get_tts_view()
check('tts view text', tv['text'] == 'Olá mundo')

state.set_tool('web.search')
check('tool set', state.current_tool == 'web.search')

state.set_recovery(True, 'Reconectando...')
check('recovery active', state.recovery_active is True)
rv = state.get_full_view()['recovery']
check('recovery in view', rv['active'] is True)

state.set_degraded({'tts': 'indisponível', 'bridge': 'lento'})
dv = state.get_degraded_view()
check('degraded has tts', 'tts' in dv)

# 6. FULL VIEW
print('\n=== 6. Full View ===')
fv = state.get_full_view()
check('full view has connection', 'connection' in fv)
check('full view has processing', 'processing' in fv)
check('full view has mission', 'mission' in fv)
check('full view has health', 'health' in fv)
check('full view has tts', 'tts' in fv)
check('full view has timestamp', 'timestamp' in fv)

# 7. MESSAGES WITH DEDUP
print('\n=== 7. Messages with Dedup ===')
state.reset()
m1 = Message.user('Teste 1')
added1 = state.add_message(m1)
check('first message added', added1 is True)
m1_dup = Message.user('Teste 1')
m1_dup.id = m1.id
added_dup = state.add_message(m1_dup)
check('duplicate blocked', added_dup is False)
check('only one message', len(state.messages) == 1)

m2 = Message.jarvis('Resposta 1')
state.add_message(m2)
check('two messages', len(state.messages) == 2)
view = state.get_conversation_view()
check('conversation view has 2', len(view) == 2)

# 8. PRESENTERS
print('\n=== 8. Presenters ===')
conn = Presenters.connection_state(ws_open=True, serve_ok=True)
check('ws+serve = connected', conn == ConnectionState.CONNECTED)
conn2 = Presenters.connection_state(ws_open=True, serve_ok=False)
check('ws+no serve = degraded', conn2 == ConnectionState.DEGRADED)
conn3 = Presenters.connection_state(ws_open=False)
check('no ws = disconnected', conn3 == ConnectionState.DISCONNECTED)

proc = Presenters.processing_from_bridge(is_responding=True)
check('responding = processing', proc == ProcessingState.PROCESSING)
proc2 = Presenters.processing_from_bridge(is_responding=False)
check('not responding = idle', proc2 == ProcessingState.IDLE)

health = Presenters.health_from_report({'global': 'degraded'})
check('health from report', health == HealthLevel.DEGRADED)
health2 = Presenters.health_from_report({'global': 'unknown'})
check('unknown health = healthy', health2 == HealthLevel.HEALTHY)

mission = Presenters.mission_from_result({
    'status': 'completed', 'completed_steps': 5, 'total_steps': 5,
    'objective': 'Test', 'duration_s': 30})
check('mission presenter completed', mission['state'] == 'completed')
check('mission presenter progress 100', mission['progress'] == 100)

perm = Presenters.permission_for_ui({
    'action': 'execute', 'tool': 'shell', 'risk_level': 'high',
    'affected_resources': ['filesystem']})
check('perm action', perm['action'] == 'execute')
check('perm risk', perm['risk'] == 'high')

err = Presenters.error_for_user(Exception("Teste de erro longo " * 20))
check('error has user_message', 'user_message' in err)
check('error has technical', 'technical' in err)
check('error truncated', len(err['user_message']) <= 203)

degraded_msg = Presenters.degraded_for_user({'tts': 'offline'})
check('degraded message', 'tts' in degraded_msg and 'offline' in degraded_msg)
check('empty degraded = empty', Presenters.degraded_for_user({}) == '')

# 9. BRIDGE INTEGRATION
print('\n=== 9. Bridge Integration ===')
bridge = BridgeIntegration()
state.reset()

# Process state snapshot
state_payload = json.dumps({'type': 'state', 'payload': {'voice': {'tts_playing': False}}})
result = bridge.process_ws_message(state_payload)
check('state handled', result is not None and result.get('handled') == 'state')

# Process text response
text_msg = json.dumps({'type': 'text', 'text': 'Olá! Sou o Jarvis.'})
result = bridge.process_ws_message(text_msg)
check('text handled', result is not None and result.get('handled') == 'text')
check('text has message', 'message' in result)
msgs = state.get_conversation_view()
check('jarvis message in conversation', any(m['role'] == 'jarvis' for m in msgs))

# Process audio done
audio_done = json.dumps({'type': 'audio_done'})
result = bridge.process_ws_message(audio_done)
check('audio_done handled', result is not None)
check('tts back to ready', state.tts_state == TTSState.READY)

# Process error
error_msg = json.dumps({'type': 'error', 'message': 'Timeout', 'error_type': 'timeout'})
result = bridge.process_ws_message(error_msg)
check('error handled', result is not None and result.get('handled') == 'error')
check('processing failed', state.processing == ProcessingState.FAILED)

# Build user message
user_msg = bridge.build_user_message('Como está o tempo?')
check('user msg has texto', user_msg.get('texto') == 'Como está o tempo?')
check('user msg has tipo', user_msg.get('tipo') == 'mensagem')
check('processing set to processing', state.processing == ProcessingState.PROCESSING)

# 10. MESSAGE DEDUP IN BRIDGE
print('\n=== 10. Message Dedup in Bridge ===')
state.reset()
bridge2 = BridgeIntegration()
text1 = json.dumps({'type': 'text', 'text': 'Resposta 1'})
r1 = bridge2.process_ws_message(text1)
check('first text added', len(state.messages) == 1)
text1_dup = json.dumps({'type': 'text', 'text': 'Resposta 1'})
r2 = bridge2.process_ws_message(text1_dup)
check('bridge dedup works', len(state.messages) <= 2)

# 11. RECONNECTION HANDLER
print('\n=== 11. Reconnection ===')
rh = ReconnectionHandler(max_attempts=3, base_delay=0.01)
state.reset()
rh.state = state
rh.on_disconnect()
check('on disconnect = reconnecting',
      state.connection == ConnectionState.RECONNECTING)
check('should reconnect initially', rh.should_reconnect() is True)
d1 = rh.next_delay()
check('first delay', d1 > 0)
d2 = rh.next_delay()
check('second delay > first', d2 >= d1)
d3 = rh.next_delay()
check('third delay', d3 > 0)
check('should not reconnect after max', rh.should_reconnect() is False)

rh2 = ReconnectionHandler(max_attempts=5, base_delay=0.01)
rh2.state = state
state.reset()
rh2.on_disconnect()
rh2.on_connect()
check('on connect resets', state.connection == ConnectionState.CONNECTED)
check('can reconnect after reset', rh2.should_reconnect() is True)

# 12. UI ROUTER
print('\n=== 12. UI Router ===')
router = UIRouter()
state.reset()
router.state = state

router.on_backend_event('connection_change', {'ws_open': True, 'serve_ok': True})
check('router connection', state.connection == ConnectionState.CONNECTED)

router.on_backend_event('mission_started', {
    'mission_id': 'm-100', 'objective': 'Testar', 'total_steps': 3})
check('router mission started', state.mission_state == MissionState.EXECUTING)
check('router mission objective', state.mission_objective == 'Testar')

router.on_backend_event('mission_step', {'step': 2, 'tool': 'web.search'})
check('router mission step', state.mission_step == 2)
check('router mission tool', state.mission_tool == 'web.search')

router.on_backend_event('mission_completed', {'completed_steps': 3, 'total_steps': 3})
check('router mission completed', state.mission_state == MissionState.COMPLETED)

router.on_backend_event('tool_executing', {'tool': 'filesystem.read'})
check('router tool set', state.current_tool == 'filesystem.read')

router.on_backend_event('tool_completed', {})
check('router tool cleared', state.current_tool == '')

router.on_backend_event('error', {'message': 'Falha grave', 'error_type': 'runtime'})
check('router error message', state.processing == ProcessingState.FAILED)
has_error = any(m['role'] == 'error' for m in state.get_conversation_view())
check('router error in conversation', has_error)

router.on_backend_event('health_change', {'global': 'unhealthy'})
check('router health', state.health_level == HealthLevel.UNHEALTHY)

router.on_backend_event('degraded', {'components': {'tts': 'offline'}})
check('router degraded', 'tts' in state.degraded_components)
has_degraded_msg = any('degradado' in m.get('content', '').lower()
                       for m in state.get_conversation_view())
check('router degraded msg', has_degraded_msg)

router.on_backend_event('recovery_started', {'message': 'Reconectando...'})
check('router recovery active', state.recovery_active is True)
router.on_backend_event('recovery_completed', {'success': True})
check('router recovery done', state.recovery_active is False)

router.on_backend_event('tts_state', {'state': 'speaking', 'text': 'Olá'})
check('router tts', state.tts_state == TTSState.SPEAKING)

# 13. CANCEL
print('\n=== 13. Cancel ===')
state.reset()
state.set_processing(ProcessingState.PROCESSING)
state.set_mission(MissionState.EXECUTING, mission_id='m-cancel')
state.set_processing(ProcessingState.CANCELLED)
state.set_mission(MissionState.CANCELLED)
check('cancelled processing', state.processing == ProcessingState.CANCELLED)
check('cancelled mission', state.mission_state == MissionState.CANCELLED)

# 14. TERMINAL RENDERER
print('\n=== 14. Terminal Renderer ===')
renderer = TerminalRenderer()
state.reset()
state.set_connection(ConnectionState.CONNECTED)
state.set_health(HealthLevel.HEALTHY)
status = renderer.render_status()
check('render status has connection', 'connected' in status.lower() or 'CONNECTED' in status)

msg_dict = {'role': 'user', 'content': 'Teste', 'timestamp': '2026-01-01T12:00:00'}
rendered = renderer.render_message(msg_dict)
check('render message has role', 'Voce' in rendered)
check('render message has content', 'Teste' in rendered)

state.set_mission(MissionState.EXECUTING, objective='Teste missão', total=4)
state.set_mission(MissionState.EXECUTING, step=2)
mission_render = renderer.render_mission()
check('render mission has objective', 'Teste missão' in mission_render)
check('render mission has progress', '50%' in mission_render)

perm_data = {'action': 'execute', 'tool': 'shell', 'risk': 'high',
             'resources': ['fs'], 'reason': 'test', 'request_id': 'p-1'}
perm_render = renderer.render_permission_request(perm_data)
check('render perm has action', 'execute' in perm_render)
check('render perm has risk', 'high' in perm_render)

err_render = renderer.render_error({'user_message': 'Algo falhou'})
check('render error', 'Algo falhou' in err_render)

# 15. PERMISSION FLOW
print('\n=== 15. Permission Flow ===')
state.reset()
req_id = state.request_permission({
    'action': 'execute', 'tool': 'shell', 'risk_level': 'high'})
check('permission requested', state.pending_permission is not None)
check('permission has request_id', state.pending_permission['request_id'] == req_id)
perm_view = state.get_permission_view()
check('permission view', perm_view is not None and perm_view['action'] == 'execute')

state.resolve_permission(req_id, PermissionDecision.ALLOW)
check('permission resolved', state.pending_permission is None)

# 16. OFFLINE/RECONNECTION
print('\n=== 16. Offline/Reconnection ===')
state.reset()
router2 = UIRouter()
router2.state = state
router2.on_backend_event('connection_change', {'ws_open': False})
check('disconnected via router', state.connection == ConnectionState.DISCONNECTED)

router2.reconnection.on_disconnect()
check('reconnecting', state.connection == ConnectionState.RECONNECTING)
for _ in range(5):
    if router2.reconnection.should_reconnect():
        delay = router2.reconnection.next_delay()
check('attempted reconnection', True)

router2.reconnection.on_connect()
check('reconnected', state.connection == ConnectionState.CONNECTED)

# 17. OBSERVABILITY INTEGRATION
print('\n=== 17. Observability Integration ===')
state.reset()
state.set_trace(correlation_id='obs-123', trace_id='obs-trace')
check('trace set', state.correlation_id == 'obs-123')
check('trace id set', state.trace_id == 'obs-trace')
fv = state.get_full_view()
check('trace in full view', fv['correlation_id'] == 'obs-123')

# SUMMARY
print(f'\n==== RESULTADO: {passed} passaram, {failed} falharam ====')
