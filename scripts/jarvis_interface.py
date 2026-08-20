"""ETAPA 24 — Interface do Jarvis.

Camada de apresentação e interação sobre o núcleo existente.
A interface NÃO é o cérebro — apenas recebe eventos, apresenta estado,
envia intenção do usuário e recebe resultado.

Separação arquitetural:
  UI → State/Presentation → Communication → Jarvis Core

Integra com:
  - jarvis_bridge.py (WebSocket port 8765) via protocolo existente
  - ETAPA 23 (observability) via observability_reliability.py
  - ETAPA 19 (permissions) via tool_permission_runtime.py
  - ETAPA 20 (missions) via mission_loop.py
  - ETAPA 21 (memory) via memory_engine.py
  - ETAPA 22 (self-assessment) via self_assessment_engine.py
"""

import os
import sys
import json
import time
import uuid
import threading
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

try:
    from observability_reliability import (
        log, metrics, health, degraded, incidents, security_events,
        TraceContext, Severity, HealthLevel, redact_secrets,
    )
    OBS_AVAILABLE = True
except ImportError:
    OBS_AVAILABLE = False


# ============================================================================
# 1. ENUMS
# ============================================================================

class ConnectionState(Enum):
    CONNECTED = "connected"
    CONNECTING = "connecting"
    RECONNECTING = "reconnecting"
    DEGRADED = "degraded"
    DISCONNECTED = "disconnected"


class ProcessingState(Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    DEGRADED = "degraded"


class MessageRole(Enum):
    USER = "user"
    JARVIS = "jarvis"
    SYSTEM = "system"
    ERROR = "error"
    PERMISSION = "permission"


class MissionState(Enum):
    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TTSState(Enum):
    READY = "ready"
    SPEAKING = "speaking"
    PROCESSING = "processing"
    ERROR = "error"
    OFFLINE = "offline"


class PermissionDecision(Enum):
    ALLOW = "allow"
    DENY = "deny"
    CANCEL = "cancel"


# ============================================================================
# 2. MESSAGE MODEL
# ============================================================================

@dataclass
class Message:
    id: str
    role: MessageRole
    content: str
    timestamp: str
    correlation_id: str = ""
    mission_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    tool_name: str = ""
    error_type: str = ""
    display_only: bool = False

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['role'] = self.role.value
        return d

    @classmethod
    def user(cls, content: str, **kw) -> 'Message':
        return cls(id=str(uuid.uuid4())[:8], role=MessageRole.USER,
                   content=content, timestamp=datetime.now().isoformat(), **kw)

    @classmethod
    def jarvis(cls, content: str, **kw) -> 'Message':
        return cls(id=str(uuid.uuid4())[:8], role=MessageRole.JARVIS,
                   content=content, timestamp=datetime.now().isoformat(), **kw)

    @classmethod
    def system(cls, content: str, **kw) -> 'Message':
        return cls(id=str(uuid.uuid4())[:8], role=MessageRole.SYSTEM,
                   content=content, timestamp=datetime.now().isoformat(), **kw)

    @classmethod
    def error(cls, content: str, error_type: str = "", **kw) -> 'Message':
        return cls(id=str(uuid.uuid4())[:8], role=MessageRole.ERROR,
                   content=content, timestamp=datetime.now().isoformat(),
                   error_type=error_type, **kw)

    @classmethod
    def permission(cls, content: str, **kw) -> 'Message':
        return cls(id=str(uuid.uuid4())[:8], role=MessageRole.PERMISSION,
                   content=content, timestamp=datetime.now().isoformat(), **kw)


# ============================================================================
# 3. EVENT BUS
# ============================================================================

class EventBus:
    """Event bus interno para comunicação entre componentes da UI."""

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.Lock()

    def on(self, event: str, callback: Callable):
        with self._lock:
            self._listeners.setdefault(event, []).append(callback)

    def off(self, event: str, callback: Callable):
        with self._lock:
            if event in self._listeners:
                self._listeners[event] = [
                    c for c in self._listeners[event] if c != callback]

    def emit(self, event: str, data: Any = None):
        with self._lock:
            listeners = list(self._listeners.get(event, []))
        for cb in listeners:
            try:
                cb(data)
            except Exception:
                pass

    def emit_any(self, event: str, data: Any = None):
        """Emite para o evento específico e para '*' (wildcard)."""
        self.emit(event, data)
        self.emit('*', {'event': event, 'data': data})


# ============================================================================
# 4. UI STATE (Central State)
# ============================================================================

class UIState:
    """Estado central da interface. Fonte confiável para todos os componentes."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.bus = EventBus()

        # Connection
        self.connection: ConnectionState = ConnectionState.DISCONNECTED
        self.connection_details: Dict[str, Any] = {}

        # Processing
        self.processing: ProcessingState = ProcessingState.IDLE
        self.current_operation: str = ""
        self.operation_start: Optional[float] = None

        # Conversation
        self.messages: deque = deque(maxlen=500)
        self.conversation_id: str = ""

        # Mission
        self.mission_state: MissionState = MissionState.IDLE
        self.mission_id: str = ""
        self.mission_objective: str = ""
        self.mission_step: int = 0
        self.mission_total: int = 0
        self.mission_tool: str = ""
        self.mission_start: Optional[float] = None
        self.mission_history: deque = deque(maxlen=50)

        # Health
        self.health_level: HealthLevel = HealthLevel.HEALTHY
        self.health_details: Dict[str, Any] = {}

        # TTS
        self.tts_state: TTSState = TTSState.READY
        self.tts_current_text: str = ""

        # Permissions
        self.pending_permission: Optional[Dict] = None

        # Recovery
        self.recovery_active: bool = False
        self.recovery_message: str = ""

        # Degraded
        self.degraded_components: Dict[str, str] = {}

        # Tool in use
        self.current_tool: str = ""

        # Trace
        self.correlation_id: str = ""
        self.trace_id: str = ""

        # Message dedup
        self._seen_ids: set = set()

        self._thread_lock = threading.Lock()

    # --- State Mutations ---

    def set_connection(self, state: ConnectionState, details: Dict = None):
        with self._thread_lock:
            self.connection = state
            if details:
                self.connection_details = details
        self.bus.emit_any('connection', {
            'state': state.value, 'details': details or {}})
        if OBS_AVAILABLE:
            log.info('ui', 'connection', f'Connection: {state.value}')

    def set_processing(self, state: ProcessingState, operation: str = ""):
        with self._thread_lock:
            self.processing = state
            self.current_operation = operation
            if state == ProcessingState.PROCESSING:
                self.operation_start = time.time()
            elif state in (ProcessingState.COMPLETED, ProcessingState.FAILED,
                           ProcessingState.CANCELLED):
                self.operation_start = None
        self.bus.emit_any('processing', {
            'state': state.value, 'operation': operation})

    def add_message(self, msg: Message) -> bool:
        """Adiciona mensagem com deduplicação. Retorna True se adicionada."""
        with self._thread_lock:
            if msg.id in self._seen_ids:
                return False
            self._seen_ids.add(msg.id)
            self.messages.append(msg)
            if len(self._seen_ids) > 2000:
                self._seen_ids = set(list(self._seen_ids)[-1000:])
        self.bus.emit_any('message', msg.to_dict())
        return True

    def set_mission(self, state: MissionState, mission_id: str = "",
                    objective: str = "", step: int = 0, total: int = 0,
                    tool: str = ""):
        with self._thread_lock:
            self.mission_state = state
            if mission_id:
                self.mission_id = mission_id
            if objective:
                self.mission_objective = objective
            if step > 0:
                self.mission_step = step
            if total > 0:
                self.mission_total = total
            if tool:
                self.mission_tool = tool
            if state == MissionState.EXECUTING and not self.mission_start:
                self.mission_start = time.time()
            elif state in (MissionState.COMPLETED, MissionState.FAILED,
                           MissionState.CANCELLED):
                self.mission_start = None
        self.bus.emit_any('mission', self.get_mission_view())

    def set_health(self, level: HealthLevel, details: Dict = None):
        with self._thread_lock:
            self.health_level = level
            if details:
                self.health_details = details
        self.bus.emit_any('health', {
            'level': level.value, 'details': details or {}})

    def set_tts(self, state: TTSState, text: str = ""):
        with self._thread_lock:
            self.tts_state = state
            if text:
                self.tts_current_text = text
        self.bus.emit_any('tts', {'state': state.value, 'text': text})

    def request_permission(self, permission_data: Dict) -> str:
        """Apresenta solicitação de permissão. Retorna request_id."""
        request_id = str(uuid.uuid4())[:8]
        with self._thread_lock:
            self.pending_permission = {
                **permission_data, 'request_id': request_id,
                'timestamp': datetime.now().isoformat()}
        self.bus.emit_any('permission_request', self.pending_permission)
        return request_id

    def resolve_permission(self, request_id: str, decision: PermissionDecision):
        with self._thread_lock:
            if self.pending_permission and \
               self.pending_permission.get('request_id') == request_id:
                self.pending_permission = None
        self.bus.emit_any('permission_resolved', {
            'request_id': request_id, 'decision': decision.value})

    def set_recovery(self, active: bool, message: str = ""):
        with self._thread_lock:
            self.recovery_active = active
            self.recovery_message = message
        self.bus.emit_any('recovery', {'active': active, 'message': message})

    def set_degraded(self, components: Dict[str, str]):
        with self._thread_lock:
            self.degraded_components = dict(components)
        self.bus.emit_any('degraded', {'components': components})

    def set_tool(self, tool_name: str):
        with self._thread_lock:
            self.current_tool = tool_name
        self.bus.emit_any('tool', {'name': tool_name})

    def set_trace(self, correlation_id: str = "", trace_id: str = ""):
        with self._thread_lock:
            if correlation_id:
                self.correlation_id = correlation_id
            if trace_id:
                self.trace_id = trace_id

    # --- View Getters (read-only snapshots) ---

    def get_connection_view(self) -> Dict[str, Any]:
        with self._thread_lock:
            return {
                'state': self.connection.value,
                'details': dict(self.connection_details),
            }

    def get_processing_view(self) -> Dict[str, Any]:
        with self._thread_lock:
            elapsed = 0
            if self.operation_start:
                elapsed = round((time.time() - self.operation_start) * 1000)
            return {
                'state': self.processing.value,
                'operation': self.current_operation,
                'elapsed_ms': elapsed,
            }

    def get_conversation_view(self, limit: int = 50) -> List[Dict]:
        with self._thread_lock:
            msgs = list(self.messages)[-limit:]
        return [m if isinstance(m, dict) else m.to_dict() for m in msgs]

    def get_mission_view(self) -> Dict[str, Any]:
        with self._thread_lock:
            elapsed = 0
            if self.mission_start:
                elapsed = round(time.time() - self.mission_start)
            progress = 0
            if self.mission_total > 0:
                progress = round((self.mission_step / self.mission_total) * 100)
            return {
                'state': self.mission_state.value,
                'mission_id': self.mission_id,
                'objective': self.mission_objective,
                'step': self.mission_step,
                'total': self.mission_total,
                'progress': progress,
                'tool': self.mission_tool,
                'elapsed_s': elapsed,
            }

    def get_health_view(self) -> Dict[str, Any]:
        with self._thread_lock:
            return {
                'level': self.health_level.value,
                'details': dict(self.health_details),
            }

    def get_tts_view(self) -> Dict[str, Any]:
        with self._thread_lock:
            return {
                'state': self.tts_state.value,
                'text': self.tts_current_text,
            }

    def get_permission_view(self) -> Optional[Dict]:
        with self._thread_lock:
            return dict(self.pending_permission) if self.pending_permission else None

    def get_degraded_view(self) -> Dict[str, str]:
        with self._thread_lock:
            return dict(self.degraded_components)

    def get_full_view(self) -> Dict[str, Any]:
        """Snapshot completo do estado da interface."""
        return {
            'connection': self.get_connection_view(),
            'processing': self.get_processing_view(),
            'mission': self.get_mission_view(),
            'health': self.get_health_view(),
            'tts': self.get_tts_view(),
            'permission': self.get_permission_view(),
            'degraded': self.get_degraded_view(),
            'tool': self.current_tool,
            'recovery': {
                'active': self.recovery_active,
                'message': self.recovery_message,
            },
            'correlation_id': self.correlation_id,
            'trace_id': self.trace_id,
            'timestamp': datetime.now().isoformat(),
        }

    def reset(self):
        """Reseta estado para idle."""
        with self._thread_lock:
            self.connection = ConnectionState.DISCONNECTED
            self.processing = ProcessingState.IDLE
            self.current_operation = ""
            self.operation_start = None
            self.messages.clear()
            self._seen_ids.clear()
            self.conversation_id = ""
            self.mission_state = MissionState.IDLE
            self.mission_id = ""
            self.mission_objective = ""
            self.mission_step = 0
            self.mission_total = 0
            self.mission_tool = ""
            self.mission_start = None
            self.health_level = HealthLevel.HEALTHY
            self.tts_state = TTSState.READY
            self.pending_permission = None
            self.recovery_active = False
            self.recovery_message = ""
            self.degraded_components.clear()
            self.current_tool = ""
        self.bus.emit_any('reset')


# ============================================================================
# 5. PRESENTERS (Backend → UI format)
# ============================================================================

class Presenters:
    """Converte estados do backend em formato adequado para a UI."""

    @staticmethod
    def connection_state(ws_open: bool, serve_ok: bool = True) -> ConnectionState:
        if not ws_open:
            return ConnectionState.DISCONNECTED
        if not serve_ok:
            return ConnectionState.DEGRADED
        return ConnectionState.CONNECTED

    @staticmethod
    def processing_from_bridge(is_responding: bool) -> ProcessingState:
        if is_responding:
            return ProcessingState.PROCESSING
        return ProcessingState.IDLE

    @staticmethod
    def health_from_report(report: Dict) -> HealthLevel:
        level_str = report.get('global', 'healthy')
        try:
            return HealthLevel(level_str)
        except ValueError:
            return HealthLevel.HEALTHY

    @staticmethod
    def mission_from_result(result: Dict) -> Dict:
        status = result.get('status', 'unknown')
        state_map = {
            'completed': MissionState.COMPLETED,
            'failed': MissionState.FAILED,
            'running': MissionState.EXECUTING,
        }
        return {
            'state': state_map.get(status, MissionState.IDLE).value,
            'mission_id': result.get('mission_id', ''),
            'objective': result.get('objective', ''),
            'step': result.get('completed_steps', 0),
            'total': result.get('total_steps', 0),
            'progress': round(
                (result.get('completed_steps', 0) /
                 max(result.get('total_steps', 1), 1)) * 100),
            'elapsed_s': result.get('duration_s', 0),
        }

    @staticmethod
    def tts_state_from_files() -> TTSState:
        try:
            narr_path = os.path.join(BASE, 'runtime', 'narracao_estado.json')
            if os.path.exists(narr_path):
                narr = json.loads(open(narr_path, encoding='utf-8').read())
                if narr.get('ativo') and not narr.get('pausado'):
                    return TTSState.SPEAKING
            return TTSState.READY
        except Exception:
            return TTSState.READY

    @staticmethod
    def permission_for_ui(permission_data: Dict) -> Dict:
        """Formata dados de permissão para exibição na UI."""
        return {
            'action': permission_data.get('action', ''),
            'tool': permission_data.get('tool', ''),
            'risk': permission_data.get('risk_level', 'unknown'),
            'resources': permission_data.get('affected_resources', []),
            'reason': permission_data.get('reason', ''),
            'request_id': permission_data.get('request_id', ''),
        }

    @staticmethod
    def error_for_user(error: Exception) -> Dict:
        """Separa mensagem do usuário de detalhes técnicos."""
        error_type = type(error).__name__
        user_msg = str(error)
        if len(user_msg) > 200:
            user_msg = user_msg[:200] + '...'
        return {
            'user_message': user_msg,
            'error_type': error_type,
            'technical': {
                'type': error_type,
                'message': str(error),
            },
        }

    @staticmethod
    def degraded_for_user(components: Dict[str, str]) -> str:
        """Gera mensagem de degradação para o usuário."""
        if not components:
            return ""
        parts = []
        for comp, reason in components.items():
            parts.append(f"{comp}: {reason}")
        affected = ', '.join(parts)
        return f"Sistema degradado — {affected}. Operações principais continuam disponíveis."


# ============================================================================
# 6. MESSAGE DEDUPLICATION
# ============================================================================

class MessageDeduplicator:
    """Garante idempotência visual — mesma mensagem não aparece duas vezes."""

    def __init__(self, window_size: int = 1000):
        self._seen: Dict[str, float] = {}
        self._window = window_size
        self._lock = threading.Lock()

    def is_duplicate(self, message_id: str) -> bool:
        with self._lock:
            now = time.time()
            self._seen = {k: v for k, v in self._seen.items()
                         if now - v < 300}
            if message_id in self._seen:
                return True
            self._seen[message_id] = now
            if len(self._seen) > self._window:
                oldest = sorted(self._seen.items(), key=lambda x: x[1])
                for k, _ in oldest[:self._window // 2]:
                    del self._seen[k]
            return False


# ============================================================================
# 7. BRIDGE INTEGRATION
# ============================================================================

class BridgeIntegration:
    """Integração com jarvis_bridge.py (WebSocket port 8765)."""

    def __init__(self):
        self.state = UIState()
        self.dedup = MessageDeduplicator()
        self._last_snapshot: Dict = {}

    def process_ws_message(self, raw: str) -> Optional[Dict]:
        """Processa mensagem recebida do WebSocket bridge."""
        try:
            obj = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

        msg_type = obj.get('type', '')

        if msg_type == 'state':
            return self._handle_state(obj.get('payload', {}))
        elif msg_type == 'pong':
            return {'handled': 'pong'}
        elif msg_type == 'text':
            return self._handle_text(obj)
        elif msg_type == 'audio_chunk':
            return {'handled': 'audio_chunk'}
        elif msg_type == 'audio_done':
            self.state.set_tts(TTSState.READY)
            return {'handled': 'audio_done'}
        elif msg_type == 'error':
            return self._handle_error(obj)

        return {'handled': 'unknown', 'type': msg_type}

    def _handle_state(self, payload: Dict) -> Dict:
        """Processa snapshot de estado do ecossistema."""
        self._last_snapshot = payload

        mem = payload.get('memory', {})
        if mem.get('total', 0) > 0:
            pass  # Memory info available for display

        voice = payload.get('voice', {})
        if voice.get('tts_playing'):
            self.state.set_tts(TTSState.SPEAKING, voice.get('current_text', ''))
        else:
            self.state.set_tts(TTSState.READY)

        return {'handled': 'state', 'snapshot': payload}

    def _handle_text(self, obj: Dict) -> Dict:
        """Processa resposta de texto do Jarvis."""
        content = obj.get('text', '')
        if not content:
            return {'handled': 'empty'}

        import hashlib
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        if self.dedup.is_duplicate(f'text-{content_hash}'):
            return {'handled': 'duplicate'}

        msg = Message.jarvis(content,
                             correlation_id=obj.get('correlation_id', ''))
        self.state.add_message(msg)
        self.state.set_processing(ProcessingState.COMPLETED)
        return {'handled': 'text', 'message': msg.to_dict()}

    def _handle_error(self, obj: Dict) -> Dict:
        """Processa erro do bridge."""
        content = obj.get('message', obj.get('error', 'Unknown error'))
        msg = Message.error(content, error_type=obj.get('error_type', ''))
        self.state.add_message(msg)
        self.state.set_processing(ProcessingState.FAILED)
        return {'handled': 'error', 'message': msg.to_dict()}

    def build_user_message(self, text: str) -> Dict:
        """Constrói mensagem para envio ao bridge."""
        msg = Message.user(text,
                           correlation_id=self.state.correlation_id)
        self.state.add_message(msg)
        self.state.set_processing(ProcessingState.PROCESSING)
        return {
            'tipo': 'mensagem',
            'texto': text,
            'id': int(time.time() * 1000),
        }

    def get_snapshot(self) -> Dict:
        return dict(self._last_snapshot)


# ============================================================================
# 8. TERMINAL RENDERER (text-based UI)
# ============================================================================

class TerminalRenderer:
    """Renderizador de terminal para a interface do Jarvis."""

    ROLE_PREFIX = {
        MessageRole.USER: 'Voce',
        MessageRole.JARVIS: 'Jarvis',
        MessageRole.SYSTEM: '[SISTEMA]',
        MessageRole.ERROR: '[ERRO]',
        MessageRole.PERMISSION: '[PERMISSAO]',
    }

    def __init__(self):
        self.state = UIState()

    def render_message(self, msg: Dict) -> str:
        role = msg.get('role', 'system')
        content = msg.get('content', '')
        prefix = self.ROLE_PREFIX.get(MessageRole(role), role)
        ts = msg.get('timestamp', '')[:19]
        return f"[{ts}] {prefix}: {content}"

    def render_status(self) -> str:
        view = self.state.get_full_view()
        lines = []
        conn = view['connection']['state']
        health = view['health']['level']
        proc = view['processing']['state']
        lines.append(f"Conexao: {conn} | Saude: {health} | Status: {proc}")

        mission = view['mission']
        if mission['state'] != 'idle':
            lines.append(
                f"Missao: {mission['objective'][:60]} "
                f"[{mission['step']}/{mission['total']}] "
                f"{mission['progress']}%")

        tts = view['tts']
        if tts['state'] != 'ready':
            lines.append(f"TTS: {tts['state']} — {tts['text'][:40]}")

        perm = view['permission']
        if perm:
            lines.append(
                f"Permissao pendente: {perm.get('action', '')} "
                f"(risco: {perm.get('risk', '')})")

        if view['recovery']['active']:
            lines.append(f"Recuperacao: {view['recovery']['message']}")

        if view['degraded']:
            for comp, reason in view['degraded'].items():
                lines.append(f"Degrade: {comp} — {reason}")

        return '\n'.join(lines)

    def render_mission(self) -> str:
        m = self.state.get_mission_view()
        if m['state'] == 'idle':
            return "Nenhuma missao em andamento."
        progress_bar = ''
        if m['total'] > 0:
            filled = int(m['progress'] / 5)
            progress_bar = f"[{'#' * filled}{'.' * (20 - filled)}]"
        return (
            f"MISSAO: {m['objective']}\n"
            f"STATUS: {m['state'].upper()}\n"
            f"ETAPA: {m['step']}/{m['total']}\n"
            f"PROGRESSO: {m['progress']}% {progress_bar}\n"
            f"FERRAMENTA: {m['tool'] or 'N/A'}\n"
            f"DURACAO: {m['elapsed_s']}s"
        )

    def render_permission_request(self, perm: Dict) -> str:
        return (
            f"=== SOLICITACAO DE PERMISSAO ===\n"
            f"Acao: {perm.get('action', '')}\n"
            f"Ferramenta: {perm.get('tool', '')}\n"
            f"Risco: {perm.get('risk', '')}\n"
            f"Recursos: {', '.join(perm.get('resources', []))}\n"
            f"Motivo: {perm.get('reason', '')}\n"
            f"Comandos: permitir | negar | cancelar"
        )

    def render_error(self, error_data: Dict) -> str:
        user_msg = error_data.get('user_message', str(error_data))
        return f"[ERRO] {user_msg}"


# ============================================================================
# 9. OFFLINE / RECONNECTION HANDLER
# ============================================================================

class ReconnectionHandler:
    """Gerencia reconexão com o backend."""

    def __init__(self, max_attempts: int = 10, base_delay: float = 1.0,
                 max_delay: float = 30.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self._attempt = 0
        self._last_attempt: Optional[float] = None
        self.state = UIState()

    def on_disconnect(self):
        self.state.set_connection(ConnectionState.RECONNECTING)
        self._attempt = 0

    def should_reconnect(self) -> bool:
        return self._attempt < self.max_attempts

    def next_delay(self) -> float:
        delay = min(self.base_delay * (2 ** self._attempt), self.max_delay)
        self._attempt += 1
        self._last_attempt = time.time()
        return delay

    def on_connect(self):
        self._attempt = 0
        self._last_attempt = None
        self.state.set_connection(ConnectionState.CONNECTED)

    def on_failed(self, error: str):
        self._attempt += 1
        if self._attempt >= self.max_attempts:
            self.state.set_connection(ConnectionState.DISCONNECTED)
        else:
            self.state.set_connection(ConnectionState.RECONNECTING)


# ============================================================================
# 10. UI EVENT ROUTER
# ============================================================================

class UIRouter:
    """Roteador de eventos entre backend e UI."""

    def __init__(self):
        self.state = UIState()
        self.bridge = BridgeIntegration()
        self.reconnection = ReconnectionHandler()

    def on_backend_event(self, event_type: str, data: Dict):
        """Recebe eventos do backend e roteia para a UI."""
        if event_type == 'connection_change':
            ws_open = data.get('ws_open', False)
            serve_ok = data.get('serve_ok', True)
            conn_state = Presenters.connection_state(ws_open, serve_ok)
            self.state.set_connection(conn_state, data)

        elif event_type == 'mission_started':
            self.state.set_mission(
                MissionState.EXECUTING,
                mission_id=data.get('mission_id', ''),
                objective=data.get('objective', ''),
                total=data.get('total_steps', 0))

        elif event_type == 'mission_step':
            self.state.set_mission(
                MissionState.EXECUTING,
                step=data.get('step', 0),
                tool=data.get('tool', ''))

        elif event_type == 'mission_completed':
            self.state.set_mission(
                MissionState.COMPLETED,
                step=data.get('completed_steps', 0),
                total=data.get('total_steps', 0))

        elif event_type == 'mission_failed':
            self.state.set_mission(MissionState.FAILED)
            msg = Message.error(
                f"Missao falhou: {data.get('error', 'unknown')}")
            self.state.add_message(msg)

        elif event_type == 'tool_executing':
            self.state.set_tool(data.get('tool', ''))

        elif event_type == 'tool_completed':
            self.state.set_tool("")

        elif event_type == 'permission_request':
            self.state.request_permission(data)

        elif event_type == 'health_change':
            level = Presenters.health_from_report(data)
            self.state.set_health(level, data)

        elif event_type == 'recovery_started':
            self.state.set_recovery(True, data.get('message', ''))
            msg = Message.system(
                Presenters.degraded_for_user(data.get('components', {}))
                or "Recuperacao em andamento...")
            self.state.add_message(msg)

        elif event_type == 'recovery_completed':
            self.state.set_recovery(False)
            if data.get('success'):
                msg = Message.system("Recuperacao concluida com sucesso.")
            else:
                msg = Message.error("Recuperacao falhou.")
            self.state.add_message(msg)

        elif event_type == 'degraded':
            self.state.set_degraded(data.get('components', {}))
            user_msg = Presenters.degraded_for_user(data.get('components', {}))
            if user_msg:
                msg = Message.system(user_msg)
                self.state.add_message(msg)

        elif event_type == 'tts_state':
            tts_state = TTSState(data.get('state', 'ready'))
            self.state.set_tts(tts_state, data.get('text', ''))

        elif event_type == 'error':
            msg = Message.error(data.get('message', 'Unknown error'),
                                error_type=data.get('error_type', ''))
            self.state.add_message(msg)
            self.state.set_processing(ProcessingState.FAILED)


# ============================================================================
# 11. CLI
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Jarvis Interface CLI')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('state')
    sub.add_parser('conversation')
    sub.add_parser('mission')
    sub.add_parser('health')
    sub.add_parser('connection')
    p_render = sub.add_parser('render')
    p_render.add_argument('message', nargs='?', default='')

    args = parser.parse_args()
    state = UIState()

    if args.cmd == 'state':
        print(json.dumps(state.get_full_view(), indent=2, ensure_ascii=False))
    elif args.cmd == 'conversation':
        msgs = state.get_conversation_view()
        renderer = TerminalRenderer()
        for m in msgs:
            print(renderer.render_message(m))
    elif args.cmd == 'mission':
        renderer = TerminalRenderer()
        print(renderer.render_mission())
    elif args.cmd == 'health':
        print(json.dumps(state.get_health_view(), indent=2))
    elif args.cmd == 'connection':
        print(json.dumps(state.get_connection_view(), indent=2))
    elif args.cmd == 'render':
        renderer = TerminalRenderer()
        print(renderer.render_status())
    else:
        parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
