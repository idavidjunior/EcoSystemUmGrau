#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capability Provider Base + Circuit Breaker + Metrics.

Base class para todos os Conselheiros/Seams.
Inclui Circuit Breaker, métricas estruturadas e fallback síncrono.
"""

import time
import asyncio
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional, Callable, Awaitable
from datetime import datetime
import logging

from scripts.capability_seams.definition import CapabilityDefinition, CAPABILITY_REGISTRY

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Estados do Circuit Breaker."""
    CLOSED = "closed"      # Normal - requisições passam
    OPEN = "open"          # Aberto - falhas consecutivas, bloqueia
    HALF_OPEN = "half_open"  # Meio aberto - testa se recuperou


@dataclass
class CircuitBreakerStats:
    """Estatísticas do Circuit Breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    last_state_change: float = field(default_factory=time.time)
    consecutive_failures: int = 0
    consecutive_successes: int = 0


@dataclass
class SeamMetrics:
    """Métricas estruturadas por seam."""
    seam_name: str
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_latency_ms: float = 0.0
    latencies: list = field(default_factory=list)  # últimas 100 latências
    circuit_breaker_opens: int = 0
    last_call_time: Optional[float] = None
    last_error: Optional[str] = None
    
    def record_call(self, latency_ms: float, success: bool, error: Optional[str] = None):
        self.total_calls += 1
        self.last_call_time = time.time()
        self.latencies.append(latency_ms)
        if len(self.latencies) > 100:
            self.latencies.pop(0)
        self.total_latency_ms += latency_ms
        if success:
            self.successful_calls += 1
        else:
            self.failed_calls += 1
            self.last_error = error
    
    def get_p50_latency(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        return sorted_lat[len(sorted_lat) // 2]
    
    def get_p95_latency(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.95)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]
    
    def get_p99_latency(self) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * 0.99)
        return sorted_lat[min(idx, len(sorted_lat) - 1)]
    
    def get_avg_latency(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_latency_ms / self.total_calls
    
    def to_dict(self) -> dict:
        return {
            "seam_name": self.seam_name,
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "avg_latency_ms": round(self.get_avg_latency(), 2),
            "p50_latency_ms": round(self.get_p50_latency(), 2),
            "p95_latency_ms": round(self.get_p95_latency(), 2),
            "p99_latency_ms": round(self.get_p99_latency(), 2),
            "circuit_breaker_opens": self.circuit_breaker_opens,
            "last_call_time": self.last_call_time,
            "last_error": self.last_error,
        }


class CircuitBreaker:
    """Circuit Breaker com fallback automático.
    
    Configurável via RetryPolicy da Definition.
    """
    
    def __init__(self, seam_name: str, retry_policy, failure_threshold: int = 3, 
                 recovery_timeout: float = 30.0, half_open_max_calls: int = 3):
        self.seam_name = seam_name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.stats = CircuitBreakerStats()
        self._lock = threading.Lock()
        self._half_open_calls = 0
    
    @property
    def state(self) -> CircuitState:
        with self._lock:
            if self.stats.state == CircuitState.OPEN:
                # Verifica se tempo de recovery passou
                if self.stats.last_failure_time is not None and \
                   time.time() - self.stats.last_failure_time >= self.recovery_timeout:
                    self.stats.state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"Circuit breaker '{self.seam_name}' -> HALF_OPEN")
            return self.stats.state
    
    def can_execute(self) -> bool:
        """Verifica se pode executar (circuito fechado ou half-open com limite)."""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            with self._lock:
                return self._half_open_calls < self.half_open_max_calls
        return False  # OPEN
    
    def record_success(self):
        with self._lock:
            self.stats.success_count += 1
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = time.time()
            
            if self.stats.state == CircuitState.HALF_OPEN:
                self.stats.consecutive_successes += 1
                if self.stats.consecutive_successes >= 2:  # 2 sucessos consecutivos fecham
                    self.stats.state = CircuitState.CLOSED
                    self.stats.consecutive_failures = 0
                    self.stats.consecutive_successes = 0
                    logger.info(f"Circuit breaker '{self.seam_name}' -> CLOSED")
    
    def record_failure(self, error: str):
        with self._lock:
            self.stats.failure_count += 1
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            self.stats.last_failure_time = time.time()
            self.stats.last_state_change = time.time()
            
            if self.stats.state == CircuitState.HALF_OPEN:
                # Falha no half-open reabre o circuito
                self.stats.state = CircuitState.OPEN
                logger.warning(f"Circuit breaker '{self.seam_name}' -> OPEN (falha no half-open)")
            elif self.stats.state == CircuitState.CLOSED:
                if self.stats.consecutive_failures >= self.failure_threshold:
                    self.stats.state = CircuitState.OPEN
                    logger.warning(f"Circuit breaker '{self.seam_name}' -> OPEN ({self.stats.consecutive_failures} falhas consecutivas)")


class CapabilityProvider(ABC):
    """Base class para todos os Providers de Conselheiros/Seams.
    
    Inclui Circuit Breaker, métricas, logging estruturado e fallback síncrono.
    """
    
    def __init__(self, definition: 'CapabilityDefinition'):
        self.definition = definition
        self.name = definition.name
        self.metrics = SeamMetrics(seam_name=self.name)
        self.circuit_breaker = CircuitBreaker(
            seam_name=self.name,
            retry_policy=definition.retry_policy,
            failure_threshold=3,
            recovery_timeout=30.0,
        )
        self._fallback_fn: Optional[Callable] = None
    
    def set_fallback(self, fallback_fn: Callable):
        """Define função de fallback síncrono (usada quando circuit breaker aberto)."""
        self._fallback_fn = fallback_fn
    
    @abstractmethod
    def _execute_impl(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementação concreta do conselheiro.
        Deve ser implementada por cada Provider específico.
        """
        pass
    
    def execute(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa o seam com Circuit Breaker, métricas e fallback.
        
        Fluxo:
        1. Verifica circuit breaker
        2. Se OPEN -> executa fallback síncrono
        3. Se CLOSED/HALF_OPEN -> executa _execute_impl com timeout
        4. Registra métricas e atualiza circuit breaker
        5. Retorna resultado ou erro estruturado
        """
        start_time = time.time()
        mission_id = context.get('mission_id', 'unknown')
        seam_name = self.name
        
        # Log de entrada
        logger.info(f"SEAM_START seam={seam_name} mission_id={mission_id} request_keys={list(request.keys())}")
        
        # Verifica circuit breaker
        if not self.circuit_breaker.can_execute():
            logger.warning(f"SEAM_CIRCUIT_OPEN seam={seam_name} mission_id={mission_id} -> usando fallback")
            return self._execute_fallback(request, context, "circuit_breaker_open")
        
        # Executa com timeout
        try:
            # TODO: implementar timeout real (thread/asyncio)
            result = self._execute_with_timeout(request, context)
            latency_ms = (time.time() - start_time) * 1000
            
            # Valida saída
            ok, err = self.definition.validate_output(result)
            if not ok:
                raise ValueError(f"Saída inválida: {err}")
            
            self.metrics.record_call(latency_ms, True)
            self.circuit_breaker.record_success()
            
            logger.info(f"SEAM_SUCCESS seam={seam_name} mission_id={mission_id} latency_ms={latency_ms:.1f}")
            return result
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.metrics.record_call(latency_ms, False, str(e))
            self.circuit_breaker.record_failure(str(e))
            
            logger.error(f"SEAM_ERROR seam={seam_name} mission_id={mission_id} error={e} latency_ms={latency_ms:.1f}")
            
            # Tenta fallback
            return self._execute_fallback(request, context, str(e))
    
    def _execute_with_timeout(self, request: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Executa com timeout (placeholder - implementar com threading/asyncio)."""
        # TODO: implementar timeout real com threading.Thread + timeout
        return self._execute_impl(request, context)
    
    def _execute_fallback(self, request: Dict[str, Any], context: Dict[str, Any], error: str) -> Dict[str, Any]:
        """Executa fallback síncrono quando circuit breaker aberto ou erro.
        
        Fallback padrão: retorna erro estruturado.
        Override em subclasses para fallback customizado.
        """
        if self._fallback_fn:
            try:
                return self._fallback_fn(request, context)
            except Exception as fb_err:
                logger.error(f"Fallback também falhou: {fb_err}")
        
        # Fallback padrão: erro estruturado
        return {
            "error": True,
            "seam": self.name,
            "error_message": error,
            "fallback": True,
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas do seam."""
        return self.metrics.to_dict()
    
    def get_circuit_state(self) -> str:
        return self.circuit_breaker.state.value
    
    def health_check(self) -> Dict[str, Any]:
        """Health check do seam."""
        return {
            "seam": self.name,
            "circuit_state": self.circuit_breaker.state.value,
            "metrics": self.metrics.to_dict(),
            "definition_version": self.definition.version,
        }


# Registry global de métricas (para observabilidade)
SEAM_METRICS_REGISTRY: Dict[str, SeamMetrics] = {}

def get_seam_metrics(seam_name: str) -> Optional[SeamMetrics]:
    return SEAM_METRICS_REGISTRY.get(seam_name)

def get_all_seam_metrics() -> Dict[str, Dict]:
    return {name: m.to_dict() for name, m in SEAM_METRICS_REGISTRY.items()}


def register_seam_metrics(metrics: SeamMetrics):
    SEAM_METRICS_REGISTRY[metrics.seam_name] = metrics


def log_all_seam_metrics():
    """Log todas as métricas de seams (para observabilidade)."""
    for name, metrics in SEAM_METRICS_REGISTRY.items():
        logger.info(f"SEAM_METRICS {metrics.to_dict()}")