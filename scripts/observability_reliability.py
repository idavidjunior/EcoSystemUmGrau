"""ETAPA 23 — Observabilidade + Reliability Unificada.

Camada única que fornece:
- Logs estruturados com redação de segredos
- Métricas centralizadas com percentis
- Trace/correlação cross-module
- Health checks (liveness + readiness)
- Circuit breaker generalizado
- Retry com backoff + jitter + budget
- Timeout com cascata
- Watchdog com heartbeat
- Crash-loop detection
- Degraded mode
- Recovery pipeline (detect→classify→diagnose→retry→fallback→recover→validate)
- Incident recording
- Security event recording
- Integração com ETAPA 21 (Memory) e ETAPA 22 (Self-Assessment)
"""

import os
import re
import sys
import json
import time
import uuid
import math
import random
import logging
import threading
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_DIR = os.path.join(BASE, 'runtime')
os.makedirs(RUNTIME_DIR, exist_ok=True)


# ============================================================================
# 1. ENUMS
# ============================================================================

class HealthLevel(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    OFFLINE = "offline"


class Severity(Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class IncidentStatus(Enum):
    OPEN = "open"
    DIAGNOSED = "diagnosed"
    RECOVERING = "recovering"
    RECOVERED = "recovered"
    DEGRADED = "degraded"
    ESCALATED = "escalated"


class RecoveryAction(Enum):
    RETRY = "retry"
    FALLBACK = "fallback"
    RESTART = "restart"
    DEGRADE = "degrade"
    ESCALATE = "escalate"
    NONE = "none"


# ============================================================================
# 2. SECRETS REDACTION
# ============================================================================

_SECRET_PATTERNS = [
    (re.compile(r'sk-[A-Za-z0-9]{20,}'), 'sk-***REDACTED***'),
    (re.compile(r'ghp_[A-Za-z0-9]{36}'), 'ghp_***REDACTED***'),
    (re.compile(r'gho_[A-Za-z0-9]{36}'), 'gho_***REDACTED***'),
    (re.compile(r'(?i)(password|passwd|pwd)\s*[:=]\s*\S+'), r'\1=***REDACTED***'),
    (re.compile(r'(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*', re.IGNORECASE), 'Bearer ***REDACTED***'),
    (re.compile(r'eyJ[A-Za-z0-9\-._]+\.eyJ[A-Za-z0-9\-._]+\.[A-Za-z0-9\-._]+'), 'JWT.***REDACTED***'),
    (re.compile(r'AKIA[0-9A-Z]{16}'), 'AKIA***REDACTED***'),
    (re.compile(r'-----BEGIN (?:RSA )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA )?PRIVATE KEY-----'), '***PRIVATE_KEY_REDACTED***'),
    (re.compile(r'nvidia-[A-Za-z0-9]{20,}'), 'nvidia-***REDACTED***'),
    (re.compile(r'(?i)(api[_-]?key|token|secret)\s*[:=]\s*\S+'), r'\1=***REDACTED***'),
]


def redact_secrets(text: str) -> str:
    """Remove segredos de texto. Chamado em TODOS os outputs de log."""
    if not text:
        return text
    for pattern, replacement in _SECRET_PATTERNS:
        text = pattern.sub(replacement, str(text))
    return text


# ============================================================================
# 3. STRUCTURED LOGGER
# ============================================================================

class StructuredLogger:
    """Logger centralizado com formato JSON, correlation_id e redação de segredos."""

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

        self._log_file = os.path.join(RUNTIME_DIR, 'observability.jsonl')
        self._events: deque = deque(maxlen=10000)
        self._thread_lock = threading.Lock()

        self._py_logger = logging.getLogger('ecosystem_observability')
        self._py_logger.setLevel(logging.DEBUG)
        if not self._py_logger.handlers:
            fh = logging.FileHandler(
                os.path.join(RUNTIME_DIR, 'ecosystem.log'),
                encoding='utf-8'
            )
            fh.setFormatter(logging.Formatter(
                '%(asctime)s [%(levelname)s] %(message)s'
            ))
            self._py_logger.addHandler(fh)

    def emit(
        self,
        level: Severity,
        component: str,
        operation: str,
        message: str,
        correlation_id: str = None,
        mission_id: str = None,
        trace_id: str = None,
        duration_ms: float = None,
        error: str = None,
        result: str = None,
        extra: Dict[str, Any] = None,
    ):
        """Emite evento de log estruturado."""
        event = {
            'ts': datetime.now().isoformat(),
            'level': level.value,
            'component': component,
            'operation': operation,
            'message': redact_secrets(message),
        }
        if correlation_id:
            event['correlation_id'] = correlation_id
        if mission_id:
            event['mission_id'] = mission_id
        if trace_id:
            event['trace_id'] = trace_id
        if duration_ms is not None:
            event['duration_ms'] = round(duration_ms, 2)
        if error:
            event['error'] = redact_secrets(error)
        if result:
            event['result'] = result
        if extra:
            event['extra'] = {k: redact_secrets(str(v)) for k, v in extra.items()}

        with self._thread_lock:
            self._events.append(event)

        py_level = {
            Severity.DEBUG: logging.DEBUG,
            Severity.INFO: logging.INFO,
            Severity.WARNING: logging.WARNING,
            Severity.ERROR: logging.ERROR,
            Severity.CRITICAL: logging.CRITICAL,
        }.get(level, logging.INFO)

        self._py_logger.log(py_level, json.dumps(event, ensure_ascii=False))

    def debug(self, component: str, operation: str, message: str, **kw):
        self.emit(Severity.DEBUG, component, operation, message, **kw)

    def info(self, component: str, operation: str, message: str, **kw):
        self.emit(Severity.INFO, component, operation, message, **kw)

    def warning(self, component: str, operation: str, message: str, **kw):
        self.emit(Severity.WARNING, component, operation, message, **kw)

    def error(self, component: str, operation: str, message: str, **kw):
        self.emit(Severity.ERROR, component, operation, message, **kw)

    def critical(self, component: str, operation: str, message: str, **kw):
        self.emit(Severity.CRITICAL, component, operation, message, **kw)

    def get_recent(self, limit: int = 100, level: Severity = None) -> List[Dict]:
        with self._thread_lock:
            events = list(self._events)
        if level:
            events = [e for e in events if e.get('level') == level.value]
        return events[-limit:]

    def flush_jsonl(self):
        """Escreve eventos para disco."""
        with self._thread_lock:
            events = list(self._events)
        path = self._log_file
        tmp = path + '.tmp'
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                for e in events:
                    f.write(json.dumps(e, ensure_ascii=False) + '\n')
            if os.path.exists(path):
                os.remove(path)
            os.replace(tmp, path)
        except Exception:
            pass


log = StructuredLogger()


# ============================================================================
# 4. TRACE CONTEXT
# ============================================================================

class TraceContext:
    """Propaga correlation_id, mission_id, trace_id, tool_execution_id."""

    _local = threading.local()

    @classmethod
    def current(cls) -> Dict[str, str]:
        ctx = getattr(cls._local, 'ctx', {})
        return dict(ctx)

    @classmethod
    def start(
        cls,
        mission_id: str = None,
        correlation_id: str = None,
        trace_id: str = None,
    ) -> Dict[str, str]:
        ctx = {
            'correlation_id': correlation_id or str(uuid.uuid4())[:12],
            'mission_id': mission_id or '',
            'trace_id': trace_id or str(uuid.uuid4())[:8],
            'tool_execution_id': '',
        }
        cls._local.ctx = ctx
        return dict(ctx)

    @classmethod
    def set_tool(cls, tool_execution_id: str):
        ctx = getattr(cls._local, 'ctx', {})
        ctx['tool_execution_id'] = tool_execution_id
        cls._local.ctx = ctx

    @classmethod
    def child(cls) -> Dict[str, str]:
        """Cria child context herdando parent."""
        parent = cls.current()
        child_id = str(uuid.uuid4())[:8]
        return {
            'correlation_id': parent.get('correlation_id', child_id),
            'mission_id': parent.get('mission_id', ''),
            'trace_id': parent.get('trace_id', child_id),
            'tool_execution_id': '',
        }


# ============================================================================
# 5. METRICS COLLECTOR
# ============================================================================

class MetricsCollector:
    """Métricas centralizadas com contadores, timers e percentis."""

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
        self._counters: Dict[str, int] = {}
        self._timers: Dict[str, List[float]] = {}
        self._gauges: Dict[str, float] = {}
        self._thread_lock = threading.Lock()
        self._max_samples = 10000

    def inc(self, name: str, value: int = 1):
        with self._thread_lock:
            self._counters[name] = self._counters.get(name, 0) + value

    def set_gauge(self, name: str, value: float):
        with self._thread_lock:
            self._gauges[name] = value

    def timer_start(self, name: str) -> float:
        return time.time()

    def timer_end(self, name: str, start: float):
        elapsed_ms = (time.time() - start) * 1000
        with self._thread_lock:
            if name not in self._timers:
                self._timers[name] = []
            self._timers[name].append(elapsed_ms)
            if len(self._timers[name]) > self._max_samples:
                self._timers[name] = self._timers[name][-self._max_samples:]

    def _percentile(self, data: List[float], p: float) -> float:
        if not data:
            return 0.0
        sorted_data = sorted(data)
        idx = int(len(sorted_data) * p / 100)
        idx = min(idx, len(sorted_data) - 1)
        return round(sorted_data[idx], 2)

    def snapshot(self) -> Dict[str, Any]:
        with self._thread_lock:
            counters = dict(self._counters)
            gauges = dict(self._gauges)
            timers = dict(self._timers)

        result = {
            'counters': counters,
            'gauges': gauges,
            'timers': {},
            'snapshot_ts': datetime.now().isoformat(),
        }
        for name, samples in timers.items():
            if samples:
                result['timers'][name] = {
                    'count': len(samples),
                    'p50': self._percentile(samples, 50),
                    'p95': self._percentile(samples, 95),
                    'p99': self._percentile(samples, 99),
                    'avg': round(sum(samples) / len(samples), 2),
                    'min': round(min(samples), 2),
                    'max': round(max(samples), 2),
                }
        return result

    def reset(self):
        with self._thread_lock:
            self._counters.clear()
            self._timers.clear()
            self._gauges.clear()


metrics = MetricsCollector()


# ============================================================================
# 6. HEALTH SYSTEM
# ============================================================================

@dataclass
class HealthProbe:
    name: str
    healthy: bool
    message: str = ""
    latency_ms: float = 0
    component: str = ""


@dataclass
class ComponentHealth:
    name: str
    level: HealthLevel
    liveness: bool = True
    readiness: bool = True
    probes: List[HealthProbe] = field(default_factory=list)
    last_check: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


class HealthAggregator:
    """Agrega saúde de múltiplos componentes em status global."""

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
        self._components: Dict[str, ComponentHealth] = {}
        self._dependencies: Dict[str, Callable] = {}
        self._thread_lock = threading.Lock()

    def register_component(self, name: str, level: HealthLevel = HealthLevel.HEALTHY):
        with self._thread_lock:
            self._components[name] = ComponentHealth(
                name=name, level=level,
                last_check=datetime.now().isoformat()
            )

    def update_component(
        self, name: str, level: HealthLevel,
        liveness: bool = None, readiness: bool = None,
        probes: List[HealthProbe] = None,
        details: Dict[str, Any] = None,
    ):
        with self._thread_lock:
            if name not in self._components:
                self._components[name] = ComponentHealth(name=name, level=level)
            ch = self._components[name]
            ch.level = level
            ch.last_check = datetime.now().isoformat()
            if liveness is not None:
                ch.liveness = liveness
            if readiness is not None:
                ch.readiness = readiness
            if probes is not None:
                ch.probes = probes
            if details is not None:
                ch.details = details

    def register_dependency(self, name: str, check_fn: Callable):
        """Registra dependência com health check callable."""
        with self._thread_lock:
            self._dependencies[name] = check_fn

    def check_dependencies(self) -> Dict[str, HealthProbe]:
        """Executa checks de dependências."""
        results = {}
        for name, check_fn in self._dependencies.items():
            start = time.time()
            try:
                healthy = check_fn()
                lat = (time.time() - start) * 1000
                results[name] = HealthProbe(
                    name=name, healthy=healthy,
                    latency_ms=round(lat, 2), component='dependency'
                )
            except Exception as e:
                lat = (time.time() - start) * 1000
                results[name] = HealthProbe(
                    name=name, healthy=False,
                    message=str(e), latency_ms=round(lat, 2),
                    component='dependency'
                )
        return results

    def get_liveness(self) -> bool:
        """Liveness: pelo menos um componente está respondendo."""
        with self._thread_lock:
            comps = list(self._components.values())
        if not comps:
            return True
        return any(c.liveness for c in comps)

    def get_readiness(self) -> bool:
        """Readiness: todos os componentes registrados estão prontos."""
        with self._thread_lock:
            comps = list(self._components.values())
        return all(c.readiness for c in comps)

    def get_global_health(self) -> HealthLevel:
        """Determina nível global de saúde."""
        with self._thread_lock:
            comps = list(self._components.values())
        if not comps:
            return HealthLevel.HEALTHY

        levels = [c.level for c in comps]
        if HealthLevel.CRITICAL in levels:
            return HealthLevel.CRITICAL
        if HealthLevel.OFFLINE in levels:
            return HealthLevel.OFFLINE
        if levels.count(HealthLevel.UNHEALTHY) >= 2:
            return HealthLevel.CRITICAL
        if HealthLevel.UNHEALTHY in levels:
            return HealthLevel.UNHEALTHY
        if HealthLevel.DEGRADED in levels:
            return HealthLevel.DEGRADED
        return HealthLevel.HEALTHY

    def get_report(self) -> Dict[str, Any]:
        with self._thread_lock:
            comps = {n: {
                'level': c.level.value,
                'liveness': c.liveness,
                'readiness': c.readiness,
                'last_check': c.last_check,
                'probes': len(c.probes),
                'details': c.details,
            } for n, c in self._components.items()}

        dep_probes = self.check_dependencies()
        deps = {n: {
            'healthy': p.healthy,
            'latency_ms': p.latency_ms,
            'message': p.message,
        } for n, p in dep_probes.items()}

        return {
            'global': self.get_global_health().value,
            'liveness': self.get_liveness(),
            'readiness': self.get_readiness(),
            'components': comps,
            'dependencies': deps,
            'timestamp': datetime.now().isoformat(),
        }


health = HealthAggregator()


# ============================================================================
# 7. CIRCUIT BREAKER
# ============================================================================

class CircuitBreaker:
    """Circuit breaker generalizado com thread safety."""

    def __init__(
        self, name: str,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: float = 30.0,
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self._lock = threading.Lock()

    def can_execute(self) -> bool:
        with self._lock:
            if self.state == CircuitState.CLOSED:
                return True
            if self.state == CircuitState.OPEN:
                if self.last_failure_time and \
                   time.time() - self.last_failure_time >= self.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    log.info('circuit_breaker', f'{self.name}',
                             f'Circuit half-open after {self.timeout_seconds}s')
                    return True
                return False
            return True

    def record_success(self):
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    log.info('circuit_breaker', f'{self.name}',
                             'Circuit closed (recovered)')
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.success_count = 0
                log.warning('circuit_breaker', f'{self.name}',
                            'Circuit reopened from half-open')
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    log.warning('circuit_breaker', f'{self.name}',
                                f'Circuit OPEN after {self.failure_count} failures')

    def reset(self):
        with self._lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
            }


# Global circuit breakers registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}
_cb_lock = threading.Lock()


def get_circuit_breaker(name: str, **kwargs) -> CircuitBreaker:
    with _cb_lock:
        if name not in _circuit_breakers:
            _circuit_breakers[name] = CircuitBreaker(name, **kwargs)
        return _circuit_breakers[name]


def reset_circuit_breaker(name: str):
    with _cb_lock:
        if name in _circuit_breakers:
            _circuit_breakers[name].reset()


# ============================================================================
# 8. RETRY POLICY
# ============================================================================

class RetryPolicy:
    """Retry com backoff exponencial + jitter + budget."""

    def __init__(
        self,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        backoff_max: float = 60.0,
        jitter: bool = True,
        retry_budget_per_minute: int = 10,
        retry_on: Tuple[type, ...] = (Exception,),
    ):
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self.backoff_max = backoff_max
        self.jitter = jitter
        self.retry_budget_per_minute = retry_budget_per_minute
        self.retry_on = retry_on
        self._retry_times: deque = deque(maxlen=1000)
        self._lock = threading.Lock()

    def _budget_remaining(self) -> int:
        with self._lock:
            now = time.time()
            cutoff = now - 60
            self._retry_times = deque(
                (t for t in self._retry_times if t > cutoff),
                maxlen=1000
            )
            return max(0, self.retry_budget_per_minute - len(self._retry_times))

    def _record_retry(self):
        with self._lock:
            self._retry_times.append(time.time())

    def wait_time(self, attempt: int) -> float:
        wait = min(self.backoff_base * (2 ** attempt), self.backoff_max)
        if self.jitter:
            wait = wait * (0.5 + random.random() * 0.5)
        return wait

    def execute(self, fn: Callable, *args, **kwargs) -> Any:
        """Executa fn com retry, backoff e jitter."""
        last_error = None
        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                if self._budget_remaining() <= 0:
                    log.warning('retry', 'budget',
                                'Retry budget exhausted, failing fast')
                    break
                wait = self.wait_time(attempt - 1)
                log.info('retry', 'wait',
                         f'Attempt {attempt}/{self.max_retries}, '
                         f'waiting {wait:.1f}s')
                time.sleep(wait)
                self._record_retry()

            try:
                result = fn(*args, **kwargs)
                if attempt > 0:
                    log.info('retry', 'success',
                             f'Succeeded on attempt {attempt + 1}')
                return result
            except self.retry_on as e:
                last_error = e
                if attempt < self.max_retries:
                    metrics.inc('retry.attempts')
                    log.warning('retry', 'attempt',
                                f'Attempt {attempt + 1} failed: {type(e).__name__}: {e}')
                continue
            except Exception as e:
                if not issubclass(type(e), self.retry_on):
                    raise
                last_error = e
                if attempt < self.max_retries:
                    metrics.inc('retry.attempts')
                    log.warning('retry', 'attempt',
                                f'Attempt {attempt + 1} failed: {type(e).__name__}: {e}')
                continue

        metrics.inc('retry.exhausted')
        raise last_error or RuntimeError("Retry exhausted")


# ============================================================================
# 9. TIMEOUT MANAGER
# ============================================================================

class TimeoutManager:
    """Executa callable com timeout using threads."""

    @staticmethod
    def execute(
        fn: Callable,
        timeout: float = 30.0,
        *args, **kwargs
    ) -> Any:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(fn, *args, **kwargs)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                future.cancel()
                raise TimeoutError(f"Operation exceeded {timeout}s timeout")

    @staticmethod
    def wrap_fn(fn: Callable, timeout: float = 30.0) -> Callable:
        """Envolve função com timeout."""
        def wrapped(*args, **kwargs):
            return TimeoutManager.execute(fn, timeout, *args, **kwargs)
        return wrapped


# ============================================================================
# 10. WATCHDOG
# ============================================================================

class Watchdog:
    """Monitor de heartbeat. Detecta componentes travados."""

    def __init__(self, check_interval: float = 10.0):
        self._heartbeats: Dict[str, float] = {}
        self._thresholds: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def register(self, name: str, max_silence_s: float = 60.0):
        with self._lock:
            self._heartbeats[name] = time.time()
            self._thresholds[name] = max_silence_s

    def beat(self, name: str):
        with self._lock:
            self._heartbeats[name] = time.time()

    def is_alive(self, name: str) -> bool:
        with self._lock:
            last = self._heartbeats.get(name, 0)
            threshold = self._thresholds.get(name, 60)
        return (time.time() - last) < threshold

    def get_stale(self) -> List[str]:
        stale = []
        with self._lock:
            for name, last in self._heartbeats.items():
                threshold = self._thresholds.get(name, 60)
                if (time.time() - last) >= threshold:
                    stale.append(name)
        return stale

    def start_monitoring(self, on_stale: Callable = None):
        """Inicia thread de monitoramento."""
        if self._running:
            return
        self._running = True

        def _loop():
            while self._running:
                stale = self.get_stale()
                for name in stale:
                    log.warning('watchdog', 'stale',
                                f'Component {name} missed heartbeat')
                    if on_stale:
                        on_stale(name)
                time.sleep(self._check_interval)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        self._running = False


watchdog = Watchdog()


# ============================================================================
# 11. CRASH-LOOP DETECTOR
# ============================================================================

class CrashLoopDetector:
    """Detecta crash/restart loops."""

    def __init__(self, window_seconds: float = 300.0, threshold: int = 5):
        self.window_seconds = window_seconds
        self.threshold = threshold
        self._events: Dict[str, deque] = {}
        self._lock = threading.Lock()

    def record_event(self, component: str, event_type: str = "crash"):
        with self._lock:
            if component not in self._events:
                self._events[component] = deque(maxlen=100)
            self._events[component].append({
                'ts': time.time(),
                'type': event_type,
            })

    def is_crash_loop(self, component: str) -> bool:
        with self._lock:
            events = self._events.get(component, deque())
            now = time.time()
            recent = [e for e in events
                      if now - e['ts'] < self.window_seconds]
        return len(recent) >= self.threshold

    def get_crash_counts(self) -> Dict[str, int]:
        with self._lock:
            now = time.time()
            return {
                name: len([e for e in events
                           if now - e['ts'] < self.window_seconds])
                for name, events in self._events.items()
            }


crash_detector = CrashLoopDetector()


# ============================================================================
# 12. DEGRADED MODE
# ============================================================================

class DegradedMode:
    """Gerencia modo degradado do sistema."""

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
        self._is_degraded = False
        self._degraded_components: Dict[str, str] = {}
        self._degraded_since: Optional[float] = None
        self._restrictions: List[str] = []
        self._thread_lock = threading.Lock()

    def enter_degraded(self, component: str, reason: str, restrictions: List[str] = None):
        with self._thread_lock:
            self._is_degraded = True
            self._degraded_components[component] = reason
            if self._degraded_since is None:
                self._degraded_since = time.time()
            if restrictions:
                self._restrictions.extend(restrictions)
            log.warning('degraded_mode', 'enter',
                        f'Entering degraded mode: {component} — {reason}',
                        extra={'restrictions': restrictions or []})

    def exit_degraded(self, component: str):
        with self._thread_lock:
            self._degraded_components.pop(component, None)
            if not self._degraded_components:
                self._is_degraded = False
                self._degraded_since = None
                self._restrictions.clear()
                log.info('degraded_mode', 'exit', 'System restored to normal')
            else:
                log.info('degraded_mode', 'component_restored',
                         f'Component {component} restored')

    def is_degraded(self) -> bool:
        with self._thread_lock:
            return self._is_degraded

    def get_status(self) -> Dict[str, Any]:
        with self._thread_lock:
            return {
                'degraded': self._is_degraded,
                'components': dict(self._degraded_components),
                'since': self._degraded_since,
                'duration_s': round(time.time() - self._degraded_since, 1)
                             if self._degraded_since else 0,
                'restrictions': list(self._restrictions),
            }

    def is_action_allowed(self, action: str) -> bool:
        """Verifica se ação é permitida no modo degradado."""
        with self._thread_lock:
            if not self._is_degraded:
                return True
            for r in self._restrictions:
                if action.startswith(r):
                    return False
            return True


degraded = DegradedMode()


# ============================================================================
# 13. INCIDENT RECORDER
# ============================================================================

@dataclass
class Incident:
    id: str
    component: str
    timestamp: str
    severity: str
    symptom: str
    probable_cause: str = ""
    actions_taken: List[str] = field(default_factory=list)
    result: str = ""
    recovery: str = ""
    final_state: str = "open"
    correlation_id: str = ""
    mission_id: str = ""
    resolved_at: str = ""


class IncidentRecorder:
    """Registra incidentes de forma estruturada."""

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
        self._incidents: List[Incident] = []
        self._thread_lock = threading.Lock()

    def create(
        self,
        component: str,
        severity: str,
        symptom: str,
        probable_cause: str = "",
        correlation_id: str = "",
        mission_id: str = "",
    ) -> Incident:
        inc = Incident(
            id=str(uuid.uuid4())[:8],
            component=component,
            timestamp=datetime.now().isoformat(),
            severity=severity,
            symptom=symptom,
            probable_cause=probable_cause,
            correlation_id=correlation_id,
            mission_id=mission_id,
        )
        with self._thread_lock:
            self._incidents.append(inc)

        metrics.inc('incidents.total')
        metrics.inc(f'incidents.{severity}')
        log.error('incidents', 'create',
                  f'Incident {inc.id}: [{severity}] {component} — {symptom}',
                  correlation_id=correlation_id, mission_id=mission_id)
        return inc

    def add_action(self, incident_id: str, action: str):
        with self._thread_lock:
            for inc in self._incidents:
                if inc.id == incident_id:
                    inc.actions_taken.append(action)
                    break

    def resolve(
        self,
        incident_id: str,
        result: str,
        recovery: str = "",
        final_state: str = "recovered",
    ):
        with self._thread_lock:
            for inc in self._incidents:
                if inc.id == incident_id:
                    inc.result = result
                    inc.recovery = recovery
                    inc.final_state = final_state
                    inc.resolved_at = datetime.now().isoformat()
                    break

        log.info('incidents', 'resolve',
                 f'Incident {incident_id}: {final_state} — {result}')

    def get_recent(self, limit: int = 20) -> List[Dict]:
        with self._thread_lock:
            incidents = self._incidents[-limit:]
        return [asdict(i) for i in incidents]

    def get_open(self) -> List[Dict]:
        with self._thread_lock:
            open_inc = [i for i in self._incidents
                        if i.final_state == 'open']
        return [asdict(i) for i in open_inc]

    def get_stats(self) -> Dict[str, Any]:
        with self._thread_lock:
            total = len(self._incidents)
            open_count = sum(1 for i in self._incidents
                            if i.final_state == 'open')
            recovered = sum(1 for i in self._incidents
                           if i.final_state == 'recovered')
            degraded_count = sum(1 for i in self._incidents
                                if i.final_state == 'degraded')
            escalated = sum(1 for i in self._incidents
                           if i.final_state == 'escalated')
        return {
            'total': total, 'open': open_count,
            'recovered': recovered, 'degraded': degraded_count,
            'escalated': escalated,
        }


incidents = IncidentRecorder()


# ============================================================================
# 14. SECURITY EVENT RECORDER
# ============================================================================

@dataclass
class SecurityEventRecord:
    id: str
    timestamp: str
    event_type: str
    threat_level: str
    component: str
    description: str
    source: str = ""
    blocked: bool = False
    correlation_id: str = ""


class SecurityEventRecorder:
    """Registra eventos de segurança."""

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
        self._events: List[SecurityEventRecord] = []
        self._thread_lock = threading.Lock()

    def record(
        self,
        event_type: str,
        threat_level: str,
        component: str,
        description: str,
        source: str = "",
        blocked: bool = False,
        correlation_id: str = "",
    ) -> SecurityEventRecord:
        evt = SecurityEventRecord(
            id=str(uuid.uuid4())[:8],
            timestamp=datetime.now().isoformat(),
            event_type=event_type,
            threat_level=threat_level,
            component=component,
            description=redact_secrets(description),
            source=source,
            blocked=blocked,
            correlation_id=correlation_id,
        )
        with self._thread_lock:
            self._events.append(evt)

        metrics.inc('security.events')
        metrics.inc(f'security.{event_type}')
        log.warning('security', event_type,
                    f'[{threat_level}] {component}: {redact_secrets(description)}',
                    correlation_id=correlation_id)
        return evt

    def permission_denied(self, component: str, action: str, **kw):
        return self.record('permission_denied', 'HIGH', component,
                           f'Permission denied: {action}', blocked=True, **kw)

    def tool_blocked(self, component: str, tool: str, reason: str, **kw):
        return self.record('tool_blocked', 'MEDIUM', component,
                           f'Tool {tool} blocked: {reason}', blocked=True, **kw)

    def unauthorized_attempt(self, component: str, details: str, **kw):
        return self.record('unauthorized', 'HIGH', component,
                           f'Unauthorized attempt: {details}', **kw)

    def sandbox_violation(self, component: str, violation: str, **kw):
        return self.record('sandbox_violation', 'CRITICAL', component,
                           f'Sandbox violation: {violation}', blocked=True, **kw)

    def secret_exposure(self, component: str, details: str, **kw):
        return self.record('secret_exposure', 'CRITICAL', component,
                           f'Secret exposure: {details}', **kw)

    def suspicious_behavior(self, component: str, details: str, **kw):
        return self.record('suspicious', 'MEDIUM', component,
                           f'Suspicious: {details}', **kw)

    def get_recent(self, limit: int = 20) -> List[Dict]:
        with self._thread_lock:
            return [asdict(e) for e in self._events[-limit:]]

    def get_by_level(self, level: str) -> List[Dict]:
        with self._thread_lock:
            return [asdict(e) for e in self._events
                    if e.threat_level == level]


security_events = SecurityEventRecorder()


# ============================================================================
# 15. RECOVERY PIPELINE
# ============================================================================

@dataclass
class RecoveryStep:
    name: str
    status: str
    result: str = ""
    timestamp: str = ""
    duration_ms: float = 0


class RecoveryPipeline:
    """Pipeline: DETECT → CLASSIFY → DIAGNOSE → RETRY → FALLBACK → RECOVER → VALIDATE."""

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
        self._recovery_history: List[Dict] = []

    def detect(self, component: str, error: Exception,
               context: Dict = None) -> Dict[str, Any]:
        """Detecta e classifica falha."""
        error_type = type(error).__name__
        error_msg = str(error)

        classification = self._classify_error(error_type, error_msg)

        result = {
            'component': component,
            'error_type': error_type,
            'error_message': error_msg,
            'classification': classification,
            'recoverable': classification.get('recoverable', False),
            'suggested_action': classification.get('action', RecoveryAction.NONE),
            'timestamp': datetime.now().isoformat(),
            'context': context or {},
        }

        log.error('recovery', 'detect',
                  f'Failure detected in {component}: {error_type}: {error_msg}',
                  extra={'classification': classification})

        return result

    def _classify_error(self, error_type: str, message: str) -> Dict[str, Any]:
        """Classifica erro em categorias de recovery."""
        msg_lower = message.lower()

        if error_type in ('TimeoutError', 'timeout') or 'timeout' in msg_lower:
            return {'category': 'timeout', 'recoverable': True,
                    'action': RecoveryAction.RETRY, 'retryable': True}
        if error_type in ('ConnectionError', 'ConnectionRefusedError',
                          'ConnectionResetError') or 'connection' in msg_lower:
            return {'category': 'dependency', 'recoverable': True,
                    'action': RecoveryAction.RETRY, 'retryable': True}
        if 'permission' in msg_lower or 'denied' in msg_lower:
            return {'category': 'authorization', 'recoverable': False,
                    'action': RecoveryAction.ESCALATE, 'retryable': False}
        if 'not found' in msg_lower or 'no such file' in msg_lower:
            return {'category': 'resource', 'recoverable': True,
                    'action': RecoveryAction.FALLBACK, 'retryable': False}
        if 'memory' in msg_lower or 'out of' in msg_lower:
            return {'category': 'resource_exhaustion', 'recoverable': False,
                    'action': RecoveryAction.DEGRADE, 'retryable': False}
        if error_type == 'ImportError' or 'module' in msg_lower:
            return {'category': 'dependency_missing', 'recoverable': False,
                    'action': RecoveryAction.ESCALATE, 'retryable': False}
        if 'rate limit' in msg_lower or '429' in msg_lower:
            return {'category': 'rate_limit', 'recoverable': True,
                    'action': RecoveryAction.RETRY, 'retryable': True}
        if error_type in ('FileNotFoundError', 'FileExistsError'):
            return {'category': 'filesystem', 'recoverable': True,
                    'action': RecoveryAction.RETRY, 'retryable': True}

        return {'category': 'unknown', 'recoverable': True,
                'action': RecoveryAction.RETRY, 'retryable': True}

    def execute_recovery(
        self,
        component: str,
        detection: Dict[str, Any],
        retry_fn: Callable = None,
        fallback_fn: Callable = None,
        validate_fn: Callable = None,
    ) -> Dict[str, Any]:
        """Executa pipeline de recovery completo."""
        ctx = TraceContext.current()
        start = time.time()

        inc = incidents.create(
            component=component,
            severity='HIGH' if not detection['recoverable'] else 'MEDIUM',
            symptom=f"{detection['error_type']}: {detection['error_message']}",
            correlation_id=ctx.get('correlation_id', ''),
            mission_id=ctx.get('mission_id', ''),
        )

        steps: List[RecoveryStep] = []
        final_result = {'success': False, 'incident_id': inc.id}

        # RETRY
        if detection['suggested_action'] == RecoveryAction.RETRY and retry_fn:
            step_start = time.time()
            try:
                result = retry_fn()
                elapsed = (time.time() - step_start) * 1000
                steps.append(RecoveryStep(
                    name='retry', status='success',
                    result=str(result)[:200],
                    timestamp=datetime.now().isoformat(),
                    duration_ms=round(elapsed, 2)))
                incidents.add_action(inc.id, 'retry_succeeded')
                final_result['success'] = True
                final_result['result'] = result
            except Exception as e:
                elapsed = (time.time() - step_start) * 1000
                steps.append(RecoveryStep(
                    name='retry', status='failed',
                    result=str(e)[:200],
                    timestamp=datetime.now().isoformat(),
                    duration_ms=round(elapsed, 2)))
                incidents.add_action(inc.id, f'retry_failed: {e}')

        # FALLBACK
        if not final_result['success'] and fallback_fn:
            step_start = time.time()
            try:
                result = fallback_fn()
                elapsed = (time.time() - step_start) * 1000
                steps.append(RecoveryStep(
                    name='fallback', status='success',
                    result=str(result)[:200],
                    timestamp=datetime.now().isoformat(),
                    duration_ms=round(elapsed, 2)))
                incidents.add_action(inc.id, 'fallback_succeeded')
                final_result['success'] = True
                final_result['result'] = result
                final_result['used_fallback'] = True
            except Exception as e:
                elapsed = (time.time() - step_start) * 1000
                steps.append(RecoveryStep(
                    name='fallback', status='failed',
                    result=str(e)[:200],
                    timestamp=datetime.now().isoformat(),
                    duration_ms=round(elapsed, 2)))
                incidents.add_action(inc.id, f'fallback_failed: {e}')

        # VALIDATE
        if final_result['success'] and validate_fn:
            step_start = time.time()
            try:
                valid = validate_fn(final_result.get('result'))
                elapsed = (time.time() - step_start) * 1000
                steps.append(RecoveryStep(
                    name='validate', status='success' if valid else 'failed',
                    result='validation passed' if valid else 'validation failed',
                    timestamp=datetime.now().isoformat(),
                    duration_ms=round(elapsed, 2)))
                if not valid:
                    final_result['success'] = False
                    incidents.add_action(inc.id, 'validation_failed')
            except Exception as e:
                elapsed = (time.time() - step_start) * 1000
                steps.append(RecoveryStep(
                    name='validate', status='error',
                    result=str(e)[:200],
                    timestamp=datetime.now().isoformat(),
                    duration_ms=round(elapsed, 2)))

        # ESCALATE / DEGRADE
        if not final_result['success']:
            if detection['suggested_action'] == RecoveryAction.ESCALATE:
                incidents.resolve(inc.id, 'escalated',
                                  'Requires human intervention',
                                  final_state='escalated')
                degraded.enter_degraded(component,
                    f'Recovery failed, escalated: {detection["error_type"]}')
                final_result['escalated'] = True
            elif detection['suggested_action'] == RecoveryAction.DEGRADE:
                degraded.enter_degraded(component,
                    f'Entering degraded mode: {detection["error_type"]}')
                incidents.resolve(inc.id, 'degraded',
                                  'Operating in degraded mode',
                                  final_state='degraded')
                final_result['degraded'] = True
            else:
                incidents.resolve(inc.id, 'failed',
                                  'Recovery unsuccessful',
                                  final_state='open')
        else:
            incidents.resolve(inc.id, 'recovered',
                              'Automatic recovery successful',
                              final_state='recovered')

        elapsed = (time.time() - start) * 1000
        final_result['steps'] = [asdict(s) for s in steps]
        final_result['duration_ms'] = round(elapsed, 2)

        with self._lock:
            self._recovery_history.append(final_result)
            if len(self._recovery_history) > 500:
                self._recovery_history = self._recovery_history[-500:]

        log.info('recovery', 'complete',
                 f'Recovery {"succeeded" if final_result["success"] else "failed"} '
                 f'for {component} in {elapsed:.0f}ms',
                 correlation_id=ctx.get('correlation_id', ''),
                 extra={'steps': len(steps)})

        return final_result

    def get_history(self, limit: int = 20) -> List[Dict]:
        with self._lock:
            return self._recovery_history[-limit:]


recovery = RecoveryPipeline()


# ============================================================================
# 16. INTEGRATION WITH ETAPA 21 + 22
# ============================================================================

def consume_for_memory(
    component: str,
    error: Exception,
    context: Dict = None,
) -> Optional[Dict]:
    """Registra falha para consolidação de memória (ETAPA 21)."""
    try:
        from scripts.memory_consolidation import consolidation
        detection = recovery.detect(component, error, context)
        consolidation.store(
            task=f"Failure in {component}: {type(error).__name__}",
            summary=f"Error: {str(error)[:200]}. "
                    f"Category: {detection['classification'].get('category', 'unknown')}. "
                    f"Recoverable: {detection['recoverable']}",
            kind='erro',
            importance=0.8 if not detection['recoverable'] else 0.5,
            evidence=[{
                'type': 'failure_observation',
                'component': component,
                'error_type': type(error).__name__,
                'category': detection['classification'].get('category'),
            }],
        )
        log.info('integration', 'memory',
                 f'Failure recorded for memory consolidation: {component}')
        return detection
    except Exception as e:
        log.warning('integration', 'memory',
                    f'Failed to record to memory: {e}')
        return None


def consume_for_self_assessment(
    component: str,
    operation: str,
    success: bool,
    duration_ms: float = 0,
    error: str = None,
):
    """Alimenta Self-Assessment Engine (ETAPA 22)."""
    try:
        from scripts.self_assessment_engine import SelfAssessmentEngine
        sae = SelfAssessmentEngine()
        sae.record_metric(
            f'{component}.success_rate', 1.0 if success else 0.0)
        sae.record_metric(
            f'{component}.latency_ms', duration_ms)
        if error:
            sae.record_metric(f'{component}.error_count', 1.0)
        log.info('integration', 'self_assessment',
                 f'Metrics recorded for {component}/{operation}')
    except Exception as e:
        log.warning('integration', 'self_assessment',
                    f'Failed to record metrics: {e}')


# ============================================================================
# 17. HEALTH CHECK HELPERS
# ============================================================================

def check_filesystem_writable(path: str = None) -> bool:
    """Verifica se diretório é gravável."""
    path = path or RUNTIME_DIR
    try:
        test_file = os.path.join(path, '.health_check')
        with open(test_file, 'w', encoding="utf-8") as f:
            f.write('ok')
        os.remove(test_file)
        return True
    except Exception:
        return False


def check_memory_available(min_mb: float = 50) -> bool:
    """Verifica se há memória disponível."""
    try:
        import psutil
        mem = psutil.virtual_memory()
        return mem.available / (1024 * 1024) >= min_mb
    except ImportError:
        return True


def check_disk_space(path: str = None, min_mb: float = 100) -> bool:
    """Verifica espaço em disco."""
    path = path or BASE
    try:
        usage = os.statvfs(path)
        free_mb = (usage.f_bavail * usage.f_frsize) / (1024 * 1024)
        return free_mb >= min_mb
    except Exception:
        return True


# ============================================================================
# 18. DECORATOR: @observable
# ============================================================================

def observable(
    component: str,
    operation: str = None,
    timeout: float = None,
    max_retries: int = 0,
    retry_backoff: float = 1.0,
    health_check: bool = True,
):
    """Decorator que adiciona observabilidade automática a uma função."""
    def decorator(fn: Callable):
        op_name = operation or fn.__name__

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            ctx = TraceContext.current()
            start = metrics.timer_start(f'{component}.{op_name}.latency')
            metrics.inc(f'{component}.{op_name}.total')

            try:
                if timeout:
                    result = TimeoutManager.execute(fn, timeout, *args, **kwargs)
                else:
                    result = fn(*args, **kwargs)

                elapsed = metrics.timer_end(f'{component}.{op_name}.latency', start)
                metrics.inc(f'{component}.{op_name}.success')

                if health_check:
                    health.update_component(component, HealthLevel.HEALTHY)

                log.debug(component, op_name, 'OK',
                          duration_ms=elapsed,
                          correlation_id=ctx.get('correlation_id'),
                          mission_id=ctx.get('mission_id'))
                return result

            except Exception as e:
                elapsed = metrics.timer_end(f'{component}.{op_name}.latency', start)
                metrics.inc(f'{component}.{op_name}.failure')

                log.error(component, op_name,
                          f'Failed: {type(e).__name__}: {e}',
                          duration_ms=elapsed,
                          error=str(e),
                          correlation_id=ctx.get('correlation_id'))

                if max_retries > 0:
                    policy = RetryPolicy(
                        max_retries=max_retries,
                        backoff_base=retry_backoff)
                    return policy.execute(fn, *args, **kwargs)

                raise

        return wrapper
    return decorator


# Need functools for @observable
import functools


# ============================================================================
# 19. PERSISTENCE
# ============================================================================

def save_state():
    """Salva estado observável em disco."""
    state = {
        'ts': datetime.now().isoformat(),
        'health': health.get_report(),
        'metrics': metrics.snapshot(),
        'incidents': incidents.get_stats(),
        'security': security_events.get_recent(limit=10),
        'degraded': degraded.get_status(),
        'crash_loops': crash_detector.get_crash_counts(),
        'circuits': {n: cb.get_status()
                     for n, cb in _circuit_breakers.items()},
        'recovery_history': recovery.get_history(limit=10),
    }
    path = os.path.join(RUNTIME_DIR, 'observability_state.json')
    tmp = path + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)
        if os.path.exists(path):
            os.remove(path)
        os.replace(tmp, path)
    except Exception as e:
        log.error('persistence', 'save', f'Failed to save state: {e}')


# ============================================================================
# 20. CLI
# ============================================================================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Observability + Reliability CLI')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('health')
    sub.add_parser('metrics')
    sub.add_parser('incidents')
    sub.add_parser('security')
    sub.add_parser('circuits')
    sub.add_parser('degraded')
    sub.add_parser('crashes')
    sub.add_parser('recovery')
    p_log = sub.add_parser('logs')
    p_log.add_argument('--limit', type=int, default=20)
    p_save = sub.add_parser('save')

    args = parser.parse_args()

    if args.cmd == 'health':
        print(json.dumps(health.get_report(), indent=2, ensure_ascii=False))
    elif args.cmd == 'metrics':
        print(json.dumps(metrics.snapshot(), indent=2, ensure_ascii=False))
    elif args.cmd == 'incidents':
        print(json.dumps(incidents.get_recent(), indent=2, ensure_ascii=False))
    elif args.cmd == 'security':
        print(json.dumps(security_events.get_recent(), indent=2, ensure_ascii=False))
    elif args.cmd == 'circuits':
        data = {n: cb.get_status() for n, cb in _circuit_breakers.items()}
        print(json.dumps(data, indent=2, ensure_ascii=False))
    elif args.cmd == 'degraded':
        print(json.dumps(degraded.get_status(), indent=2, ensure_ascii=False))
    elif args.cmd == 'crashes':
        print(json.dumps(crash_detector.get_crash_counts(), indent=2))
    elif args.cmd == 'recovery':
        print(json.dumps(recovery.get_history(), indent=2, ensure_ascii=False))
    elif args.cmd == 'logs':
        print(json.dumps(log.get_recent(args.limit), indent=2, ensure_ascii=False))
    elif args.cmd == 'save':
        save_state()
        print("State saved")
    else:
        parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())
