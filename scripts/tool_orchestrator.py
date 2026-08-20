"""Tool Orchestrator - Camada centralizada de execução de ferramentas.

Todas as chamadas de ferramentas passam por aqui. Fornece:
- Logging estruturado e métricas
- Retry com backoff exponencial
- Circuit breaker
- Timeout configurável
- Rastreabilidade de execução (auditoria)
- Checkpoint automático em operações longas
"""

import os
import sys
import time
import json
import uuid
import threading
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import traceback

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
sys.path.insert(0, SCRIPTS)

try:
    from runtime_state import load_state, save_state
except ImportError:
    def load_state():
        return {}
    def save_state(state):
        pass


class ToolStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CIRCUIT_OPEN = "circuit_open"


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class ToolCall:
    id: str
    tool_name: str
    args: Dict[str, Any]
    status: ToolStatus = ToolStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0


class CircuitBreaker:
    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
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
                   time.time() - self.last_failure_time >= self.config.timeout_seconds:
                    self.state = CircuitState.HALF_OPEN
                    return True
                return False
            return True

    def record_success(self):
        with self._lock:
            if self.state == CircuitState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                self.failure_count = 0

    def record_failure(self):
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = time.time()
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.OPEN
                self.success_count = 0
            elif self.state == CircuitState.CLOSED:
                if self.failure_count >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'success_count': self.success_count,
            }


class ToolOrchestrator:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.call_history: List[ToolCall] = []
        self.max_history = 1000
        self.default_timeout = 120.0
        self.default_max_retries = 3
        self.default_backoff_base = 1.0
        self._lock = threading.Lock()
        self.metrics = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'retries': 0,
            'timeouts': 0,
            'circuit_opens': 0,
        }

    def get_circuit_breaker(self, tool_name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        with self._lock:
            if tool_name not in self.circuit_breakers:
                self.circuit_breakers[tool_name] = CircuitBreaker(tool_name, config)
            return self.circuit_breakers[tool_name]

    def execute(
        self,
        tool_name: str,
        fn: Callable,
        args: Dict[str, Any],
        timeout: float = None,
        max_retries: int = None,
        backoff_base: float = None,
        retry_on: Tuple[type, ...] = (Exception,),
        metadata: Dict[str, Any] = None,
    ) -> Any:
        call_id = str(uuid.uuid4())[:8]
        timeout = timeout or self.default_timeout
        max_retries = max_retries if max_retries is not None else self.default_max_retries
        backoff_base = backoff_base or self.default_backoff_base

        cb = self.get_circuit_breaker(tool_name)

        if not cb.can_execute():
            self.metrics['circuit_opens'] += 1
            raise RuntimeError(f"Circuit breaker OPEN for {tool_name}")

        call = ToolCall(
            id=call_id,
            tool_name=tool_name,
            args=args,
            metadata=metadata or {},
        )

        self._record_call(call)

        last_error = None
        for attempt in range(max_retries + 1):
            call.retry_count = attempt
            call.status = ToolStatus.RUNNING
            call.start_time = time.time()
            self._update_call(call)

            try:
                result = self._execute_with_timeout(fn, args, timeout)
                call.end_time = time.time()
                call.duration_ms = (call.end_time - call.start_time) * 1000
                call.status = ToolStatus.SUCCESS
                call.result = result
                cb.record_success()
                self.metrics['successful_calls'] += 1
                self._update_call(call)
                self._maybe_checkpoint(call)
                return result

            except retry_on as e:
                last_error = e
                call.error = f"{type(e).__name__}: {str(e)}"
                cb.record_failure()
                self.metrics['failed_calls'] += 1

                if attempt < max_retries:
                    self.metrics['retries'] += 1
                    wait = backoff_base * (2 ** attempt)
                    time.sleep(wait)
                    continue

                call.end_time = time.time()
                call.duration_ms = (call.end_time - call.start_time) * 1000 if call.start_time else 0
                call.status = ToolStatus.FAILED
                self._update_call(call)
                raise

            except TimeoutError:
                last_error = TimeoutError(f"Timeout after {timeout}s")
                call.error = str(last_error)
                call.end_time = time.time()
                call.duration_ms = (call.end_time - call.start_time) * 1000 if call.start_time else 0
                call.status = ToolStatus.TIMEOUT
                cb.record_failure()
                self.metrics['timeouts'] += 1
                self.metrics['failed_calls'] += 1
                self._update_call(call)
                raise

            except Exception as e:
                last_error = e
                call.error = f"{type(e).__name__}: {str(e)}"
                call.end_time = time.time()
                call.duration_ms = (call.end_time - call.start_time) * 1000 if call.start_time else 0
                call.status = ToolStatus.FAILED
                cb.record_failure()
                self.metrics['failed_calls'] += 1
                self._update_call(call)
                raise

        raise last_error or RuntimeError("Unknown failure")

    def _execute_with_timeout(self, fn: Callable, args: Dict[str, Any], timeout: float) -> Any:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            if 'args' in args and 'kwargs' in args:
                future = executor.submit(fn, *args['args'], **args['kwargs'])
            elif 'args' in args:
                future = executor.submit(fn, *args['args'])
            else:
                future = executor.submit(fn, **args)
            try:
                return future.result(timeout=timeout)
            except concurrent.futures.TimeoutError:
                future.cancel()
                raise TimeoutError(f"Tool execution exceeded {timeout}s")

    def _record_call(self, call: ToolCall):
        with self._lock:
            self.call_history.append(call)
            if len(self.call_history) > self.max_history:
                self.call_history = self.call_history[-self.max_history:]
            self.metrics['total_calls'] += 1

    def _update_call(self, call: ToolCall):
        with self._lock:
            for i, c in enumerate(self.call_history):
                if c.id == call.id:
                    self.call_history[i] = call
                    break

    def _maybe_checkpoint(self, call: ToolCall):
        if call.duration_ms and call.duration_ms > 5000:
            try:
                state = load_state()
                state.setdefault('tool_checkpoints', []).append({
                    'call_id': call.id,
                    'tool': call.tool_name,
                    'duration_ms': call.duration_ms,
                    'timestamp': datetime.now().isoformat(),
                })
                if len(state['tool_checkpoints']) > 50:
                    state['tool_checkpoints'] = state['tool_checkpoints'][-50:]
                save_state(state)
            except Exception:
                pass

    def get_history(self, limit: int = 50, tool_name: str = None) -> List[Dict[str, Any]]:
        with self._lock:
            history = list(self.call_history)
        if tool_name:
            history = [c for c in history if c.tool_name == tool_name]
        return [asdict(c) for c in history[-limit:]]

    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.metrics)

    def get_circuit_status(self) -> Dict[str, Any]:
        return {name: cb.get_status() for name, cb in self.circuit_breakers.items()}

    def reset_circuit(self, tool_name: str):
        with self._lock:
            if tool_name in self.circuit_breakers:
                self.circuit_breakers[tool_name] = CircuitBreaker(tool_name)

    def clear_history(self):
        with self._lock:
            self.call_history.clear()


orchestrator = ToolOrchestrator()


def orchestrated(
    tool_name: str = None,
    timeout: float = None,
    max_retries: int = None,
    backoff_base: float = None,
    retry_on: Tuple[type, ...] = (Exception,),
    metadata: Dict[str, Any] = None,
):
    def decorator(fn: Callable):
        name = tool_name or fn.__name__

        @wraps(fn)
        def wrapper(*args, **kwargs):
            return orchestrator.execute(
                tool_name=name,
                fn=fn,
                args={'args': args, 'kwargs': kwargs} if args else kwargs,
                timeout=timeout,
                max_retries=max_retries,
                backoff_base=backoff_base,
                retry_on=retry_on,
                metadata=metadata,
            )
        return wrapper
    return decorator


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Tool Orchestrator CLI')
    sub = parser.add_subparsers(dest='cmd')

    sub.add_parser('metrics')
    sub.add_parser('history')
    p_hist = sub.add_parser('history-tool')
    p_hist.add_argument('tool')
    p_hist.add_argument('--limit', type=int, default=20)
    sub.add_parser('circuits')
    p_reset = sub.add_parser('reset-circuit')
    p_reset.add_argument('tool')
    sub.add_parser('clear-history')

    args = parser.parse_args()

    if args.cmd == 'metrics':
        print(json.dumps(orchestrator.get_metrics(), indent=2, ensure_ascii=False))
    elif args.cmd == 'history':
        print(json.dumps(orchestrator.get_history(limit=50), indent=2, ensure_ascii=False))
    elif args.cmd == 'history-tool':
        print(json.dumps(orchestrator.get_history(limit=args.limit, tool_name=args.tool), indent=2, ensure_ascii=False))
    elif args.cmd == 'circuits':
        print(json.dumps(orchestrator.get_circuit_status(), indent=2, ensure_ascii=False))
    elif args.cmd == 'reset-circuit':
        orchestrator.reset_circuit(args.tool)
        print(f"Circuit reset for {args.tool}")
    elif args.cmd == 'clear-history':
        orchestrator.clear_history()
        print("History cleared")
    else:
        parser.print_help()
    return 0


if __name__ == '__main__':
    sys.exit(main())