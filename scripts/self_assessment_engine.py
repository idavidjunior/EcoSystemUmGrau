"""Self-Assessment Engine — ETAPA 22

Sistema de autoavaliação, diagnóstico, medição e detecção de drift.
Coleta métricas do ecossistema, mantém baselines, detecta degradação
e alimenta o Improvement Engine com problemas diagnosticados.

Princípio: autoavaliação não é verdade — é medição objetiva com dados observáveis.
NÃO implementa experimentação/rollback/isso fica no improvement_engine.py.
"""

import sys
import os
import json
import time
import uuid
import math
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME = os.path.join(BASE, 'runtime')
sys.path.insert(0, SCRIPTS)

# ──────────────────────────────────────────────────────────────────
# Tipos de Métrica
# ──────────────────────────────────────────────────────────────────

METRIC_TYPES = (
    "MISSION_SUCCESS", "MISSION_FAILURE", "FALSE_SUCCESS",
    "RECOVERY_RATE", "REPLAN_SUCCESS", "TOOL_SUCCESS", "TOOL_FAILURE",
    "VALIDATION_SUCCESS", "HUMAN_INTERVENTION",
    "AVG_MISSION_DURATION", "AVG_STEP_DURATION",
    "AVG_TOOL_CALLS", "AVG_REPLANS", "AVG_RETRIES",
    "RESOURCE_USAGE", "MEMORY_RETRIEVAL_QUALITY",
    "PERMISSION_DENIALS", "SECURITY_BLOCKS",
    "TIMEOUT_RATE", "CRASH_RATE",
)

QUALITY_DIMENSIONS = (
    "correctness", "completeness", "relevance",
    "consistency", "factuality", "instruction_following",
)

RELIABILITY_METRICS = (
    "mtbf", "mttr", "failure_frequency",
    "recovery_success", "timeout_rate", "crash_rate",
)

EFFICIENCY_METRICS = (
    "time_to_completion", "tool_calls_per_mission",
    "replans_per_mission", "retries_per_mission",
)

SECURITY_EVENTS = (
    "permission_denials", "policy_denials", "security_blocks",
    "confirmation_requests", "prompt_injection_attempts",
    "secret_leak_attempts", "unauthorized_tool_attempts",
)

IMPROVEMENT_LEVELS = {
    0: "OBSERVE_ONLY",
    1: "PROPOSE_ONLY",
    2: "EXPERIMENT_SAFE",
    3: "REVERSIBLE_CHANGES",
    4: "AUTO_ADOPT_VALIDATED",
    5: "SUPERVISED_EVOLUTION",
}

RISK_CATEGORIES = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

ASSESSMENT_TRIGGERS = (
    "per_mission", "per_n_missions", "periodic",
    "after_major_failure", "after_major_improvement",
    "critical_failure", "repeated_failure",
    "performance_degradation", "security_event",
)


# ──────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────

class MetricValue:
    __slots__ = ('metric_type', 'value', 'timestamp', 'context',
                 'source', 'sample_size', 'confidence', 'label')

    def __init__(self, metric_type: str, value: float, timestamp: Optional[float] = None,
                 context: Optional[Dict] = None, source: str = "system",
                 sample_size: int = 1, confidence: float = 0.0,
                 label: str = ""):
        self.metric_type = metric_type
        self.value = value
        self.timestamp = timestamp or time.time()
        self.context = context or {}
        self.source = source
        self.sample_size = sample_size
        self.confidence = confidence
        self.label = label

    def to_dict(self) -> Dict[str, Any]:
        return {
            'metric_type': self.metric_type, 'value': self.value,
            'timestamp': self.timestamp, 'context': self.context,
            'source': self.source, 'sample_size': self.sample_size,
            'confidence': self.confidence, 'label': self.label,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'MetricValue':
        return cls(**{k: d[k] for k in d if k in cls.__slots__})


class Baseline:
    __slots__ = ('baseline_id', 'name', 'version', 'created_at',
                 'environment', 'metrics', 'description', 'active')

    def __init__(self, baseline_id: str, name: str, version: str = "1.0",
                 created_at: Optional[str] = None, environment: str = "production",
                 metrics: Optional[Dict[str, float]] = None,
                 description: str = "", active: bool = True):
        self.baseline_id = baseline_id
        self.name = name
        self.version = version
        self.created_at = created_at or datetime.now().isoformat()
        self.environment = environment
        self.metrics = metrics or {}
        self.description = description
        self.active = active

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}


class AssessmentResult:
    __slots__ = ('assessment_id', 'timestamp', 'scope', 'metrics',
                 'baseline_comparison', 'scorecard', 'problems',
                 'recommendations', 'trigger', 'duration_ms')

    def __init__(self, assessment_id: Optional[str] = None, timestamp: Optional[float] = None,
                 scope: str = "full", metrics: Optional[Dict[str, float]] = None,
                 baseline_comparison: Optional[Dict] = None,
                 scorecard: Optional[Dict] = None,
                 problems: Optional[List[Dict]] = None,
                 recommendations: Optional[List[str]] = None,
                 trigger: str = "periodic", duration_ms: float = 0.0):
        self.assessment_id = assessment_id or str(uuid.uuid4())[:8]
        self.timestamp = timestamp or time.time()
        self.scope = scope
        self.metrics = metrics or {}
        self.baseline_comparison = baseline_comparison or {}
        self.scorecard = scorecard or {}
        self.problems = problems or []
        self.recommendations = recommendations or []
        self.trigger = trigger
        self.duration_ms = duration_ms


# ──────────────────────────────────────────────────────────────────
# Root Cause Analysis
# ──────────────────────────────────────────────────────────────────

class RootCauseAnalysis:
    """Diagnóstico estruturado: 5 Whys, Failure Correlation, Pattern Analysis."""

    @staticmethod
    def five_whys(problem: str, events: List[Dict[str, Any]],
                  max_depth: int = 5) -> Dict[str, Any]:
        """Análise de 5 Whys baseada em eventos observados."""
        causes = []
        current_problem = problem

        for depth in range(max_depth):
            if not current_problem:
                break
            related = [e for e in events
                       if current_problem.lower() in str(e.get('error', e.get('detail', ''))).lower()
                       or current_problem.lower() in str(e.get('event', '')).lower()]
            if not related:
                break

            failure_cats = set()
            for e in related:
                cat = e.get('failure_category', e.get('suggested_action', ''))
                if cat:
                    failure_cats.add(cat)

            if failure_cats:
                cause = ', '.join(sorted(failure_cats)[:3])
                causes.append({
                    'why': depth + 1,
                    'problem': current_problem,
                    'cause': cause,
                    'evidence_count': len(related),
                })
                current_problem = cause
            else:
                break

        return {
            'root_causes': causes,
            'depth': len(causes),
            'confidence': min(0.9, 0.3 * len(causes)) if causes else 0.0,
        }

    @staticmethod
    def failure_correlation(failures: List[Dict[str, Any]],
                            successes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Detecta correlações entre falhas e contexto."""
        if not failures:
            return {'correlations': [], 'insight': 'no_failures'}

        fail_tools = defaultdict(int)
        fail_cats = defaultdict(int)
        fail_steps = defaultdict(int)

        for f in failures:
            tool = f.get('tool_id', 'unknown')
            fail_tools[tool] += 1
            cat = f.get('failure_category', 'unknown')
            fail_cats[cat] += 1
            step = f.get('step_idx', f.get('step', 'unknown'))
            fail_steps[str(step)] += 1

        correlations = []
        total_f = len(failures)

        for tool, count in fail_tools.items():
            if count >= 2:
                correlations.append({
                    'type': 'tool_concentration',
                    'factor': tool,
                    'count': count,
                    'percentage': round(count / total_f * 100, 1),
                    'insight': f"Tool '{tool}' responsible for {count}/{total_f} failures",
                })

        for cat, count in fail_cats.items():
            if count >= 2:
                correlations.append({
                    'type': 'category_pattern',
                    'factor': cat,
                    'count': count,
                    'percentage': round(count / total_f * 100, 1),
                    'insight': f"Failure category '{cat}' repeated {count} times",
                })

        return {'correlations': correlations, 'total_failures': total_f}

    @staticmethod
    def pattern_analysis(events: List[Dict[str, Any]],
                         window: int = 10) -> Dict[str, Any]:
        """Detecta padrões recorrentes em janela de eventos."""
        if len(events) < 3:
            return {'patterns': [], 'insight': 'insufficient_data'}

        patterns = []
        recent = events[-window:]

        error_events = [e for e in recent if e.get('event') in ('STEP_FAILED', 'MISSION_FAILED')]
        if len(error_events) >= 3:
            patterns.append({
                'type': 'recurring_failure',
                'count': len(error_events),
                'window_size': len(recent),
                'frequency': round(len(error_events) / len(recent), 2),
                'insight': f"High failure rate: {len(error_events)}/{len(recent)} events are failures",
            })

        replan_events = [e for e in recent if e.get('event') == 'REPLAN']
        if len(replan_events) >= 2:
            patterns.append({
                'type': 'excessive_replanning',
                'count': len(replan_events),
                'insight': f"Multiple replans ({len(replan_events)}) suggest planning issues",
            })

        timeout_events = [e for e in recent if 'timeout' in str(e.get('error', '')).lower()]
        if len(timeout_events) >= 2:
            patterns.append({
                'type': 'timeout_pattern',
                'count': len(timeout_events),
                'insight': f"Repeated timeouts ({len(timeout_events)}) suggest resource issues",
            })

        return {'patterns': patterns, 'window_size': len(recent)}


# ──────────────────────────────────────────────────────────────────
# Scorecard
# ──────────────────────────────────────────────────────────────────

class Scorecard:
    """Scorecard multidimensional — nunca reduzir a um único número."""

    WEIGHTS = {
        'correctness': 0.20,
        'reliability': 0.20,
        'efficiency': 0.15,
        'safety': 0.15,
        'adaptability': 0.10,
        'recovery': 0.10,
        'memory_quality': 0.05,
        'planning_quality': 0.05,
    }

    @staticmethod
    def compute(metrics: Dict[str, float]) -> Dict[str, Any]:
        scores = {}

        scores['correctness'] = metrics.get('success_rate', 0.5)
        scores['reliability'] = 1.0 - metrics.get('failure_rate', 0.1)
        scores['efficiency'] = max(0.0, 1.0 - metrics.get('avg_replans', 0) / 10.0)
        scores['safety'] = 1.0 - min(1.0, metrics.get('security_incidents', 0) / 5.0)
        scores['adaptability'] = metrics.get('recovery_rate', 0.5)
        scores['recovery'] = metrics.get('recovery_rate', 0.5)
        scores['memory_quality'] = metrics.get('memory_retrieval_quality', 0.5)
        scores['planning_quality'] = max(0.0, 1.0 - metrics.get('avg_replans', 0) / 5.0)

        weighted_sum = sum(
            scores.get(k, 0.5) * w
            for k, w in Scorecard.WEIGHTS.items()
        )

        return {
            'dimensions': {k: round(v, 3) for k, v in scores.items()},
            'global_score': round(weighted_sum, 3),
            'weights': Scorecard.WEIGHTS,
            'metric_observability': {
                k: ('OBSERVED' if k in metrics else 'UNOBSERVABLE')
                for k in Scorecard.WEIGHTS
            },
        }


# ──────────────────────────────────────────────────────────────────
# Drift Detection
# ──────────────────────────────────────────────────────────────────

class DriftDetector:
    """Detecta degradação ao longo do tempo."""

    @staticmethod
    def detect(history: List[Dict[str, Any]],
              metric_key: str,
              window: int = 5,
              threshold_pct: float = 10.0) -> Dict[str, Any]:
        """Compara primeira e segunda metade da janela."""
        if len(history) < window:
            return {'drifted': False, 'reason': 'insufficient_data', 'samples': len(history)}

        values = [h.get(metric_key, 0) for h in history[-window:] if metric_key in h]
        values = [v for v in values if isinstance(v, (int, float))]
        if len(values) < 3:
            return {'drifted': False, 'reason': 'insufficient_values', 'samples': len(values)}

        mid = len(values) // 2
        first_half = values[:mid] if mid > 0 else values[:1]
        second_half = values[mid:]

        avg_first = sum(first_half) / len(first_half) if first_half else 0
        avg_second = sum(second_half) / len(second_half) if second_half else 0

        if avg_first == 0:
            pct_change = 0.0
        else:
            pct_change = ((avg_second - avg_first) / abs(avg_first)) * 100

        drifted = abs(pct_change) >= threshold_pct

        return {
            'drifted': drifted,
            'metric': metric_key,
            'first_half_avg': round(avg_first, 4),
            'second_half_avg': round(avg_second, 4),
            'pct_change': round(pct_change, 2),
            'threshold_pct': threshold_pct,
            'direction': 'improvement' if pct_change > 0 else 'degradation',
            'samples': len(values),
        }

    @staticmethod
    def detect_all(baselines: Dict[str, float],
                   current: Dict[str, float],
                   threshold_pct: float = 10.0) -> List[Dict[str, Any]]:
        """Compara baseline vs current em todas as métricas."""
        drifts = []
        for key in baselines:
            if key in current:
                base_val = baselines[key]
                curr_val = current[key]
                if base_val == 0:
                    pct = 0.0
                else:
                    pct = ((curr_val - base_val) / abs(base_val)) * 100
                if abs(pct) >= threshold_pct:
                    drifts.append({
                        'metric': key,
                        'baseline': round(base_val, 4),
                        'current': round(curr_val, 4),
                        'pct_change': round(pct, 2),
                        'direction': 'improvement' if pct > 0 else 'degradation',
                    })
        return drifts


# ──────────────────────────────────────────────────────────────────
# Metric Gaming Detection
# ──────────────────────────────────────────────────────────────────

class MetricGamingDetector:
    """Detecta manipulação de métricas (reward hacking)."""

    @staticmethod
    def detect_gaming(history: List[Dict[str, Any]],
                      metric_key: str) -> Dict[str, Any]:
        """Detecta padrões suspeitos: melhoria rápida sem causa, oscilação artificial."""
        if len(history) < 5:
            return {'gaming_detected': False, 'reason': 'insufficient_data'}

        values = [h.get(metric_key, 0) for h in history[-10:] if metric_key in h]
        values = [v for v in values if isinstance(v, (int, float))]
        if len(values) < 4:
            return {'gaming_detected': False, 'reason': 'insufficient_values'}

        gaming_signals = []

        diffs = [values[i+1] - values[i] for i in range(len(values)-1)]
        sign_changes = sum(1 for i in range(len(diffs)-1)
                          if diffs[i] * diffs[i+1] < 0)
        if sign_changes >= len(diffs) * 0.6:
            gaming_signals.append({
                'type': 'oscillation',
                'detail': f'High sign-change rate: {sign_changes}/{len(diffs)}',
            })

        if len(values) >= 3:
            recent_jump = abs(values[-1] - values[-2])
            avg_movement = sum(abs(d) for d in diffs) / len(diffs) if diffs else 0
            if avg_movement > 0 and recent_jump > avg_movement * 3:
                gaming_signals.append({
                    'type': 'sudden_jump',
                    'detail': f'Recent jump {recent_jump:.3f} vs avg {avg_movement:.3f}',
                })

        total_change = values[-1] - values[0]
        if abs(total_change) > 0.3 and len(values) <= 3:
            gaming_signals.append({
                'type': 'too_good_to_be_true',
                'detail': f'Large change {total_change:.3f} in few samples',
            })

        return {
            'gaming_detected': len(gaming_signals) > 0,
            'signals': gaming_signals,
            'samples': len(values),
        }

    @staticmethod
    def check_metric_independence(candidate_metrics: Dict[str, float],
                                  system_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Verifica se candidato está manipulando critérios de avaliação."""
        warnings = []
        if candidate_metrics.get('success_rate', 0) > 0.99:
            warnings.append({
                'type': 'suspiciously_high_success',
                'detail': 'success_rate > 99% may indicate relaxed criteria',
            })
        if candidate_metrics.get('avg_tool_calls', 999) < 1:
            warnings.append({
                'type': 'tool_avoidance',
                'detail': 'avg_tool_calls < 1 may indicate avoiding necessary tool use',
            })
        if candidate_metrics.get('avg_duration', 999) < 0.1:
            warnings.append({
                'type': 'premature_termination',
                'detail': 'avg_duration < 0.1s may indicate declaring failure immediately',
            })
        return {'warnings': warnings, 'independent': len(warnings) == 0}


# ──────────────────────────────────────────────────────────────────
# SelfAssessmentEngine — Núcleo
# ──────────────────────────────────────────────────────────────────

class SelfAssessmentEngine:
    """Motor de autoavaliação do ecossistema."""

    def __init__(self):
        self._lock = threading.Lock()
        self._metrics: List[MetricValue] = []
        self._baselines: Dict[str, Baseline] = {}
        self._assessments: List[AssessmentResult] = []
        self._mission_history: List[Dict[str, Any]] = []
        self._improvement_level: int = 0
        self._max_improvement_level: int = 2
        self._assessment_budget = {
            'max_assessments_per_day': 50,
            'min_interval_seconds': 60,
            'max_metrics_per_assessment': 200,
        }
        self._last_assessment_time: float = 0.0
        self._feature_flags: Dict[str, bool] = {}
        self._state_path = os.path.join(RUNTIME, 'assessment_state.json')

    # ---- Persistence ----

    def _save_state(self):
        os.makedirs(RUNTIME, exist_ok=True)
        state = {
            'metrics': [m.to_dict() for m in self._metrics[-500:]],
            'baselines': {k: v.to_dict() for k, v in self._baselines.items()},
            'assessments': [
                {k: getattr(a, k) for k in a.__slots__}
                for a in self._assessments[-100:]
            ],
            'mission_history': self._mission_history[-200:],
            'improvement_level': self._improvement_level,
            'feature_flags': self._feature_flags,
            'saved_at': datetime.now().isoformat(),
        }
        tmp = self._state_path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)
        os.replace(tmp, self._state_path)

    def _load_state(self):
        if not os.path.exists(self._state_path):
            return
        try:
            with open(self._state_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            self._metrics = [MetricValue.from_dict(m) for m in state.get('metrics', [])]
            self._baselines = {
                k: Baseline(**v) for k, v in state.get('baselines', {}).items()
            }
            self._assessments = []  # don't reload full assessments
            self._mission_history = state.get('mission_history', [])
            self._improvement_level = state.get('improvement_level', 0)
            self._feature_flags = state.get('feature_flags', {})
        except Exception:
            pass

    # ---- Feature Flags ----

    def set_feature_flag(self, flag: str, enabled: bool):
        self._feature_flags[flag] = enabled
        self._save_state()

    def get_feature_flag(self, flag: str, default: bool = False) -> bool:
        return self._feature_flags.get(flag, default)

    # ---- Improvement Level ----

    def get_improvement_level(self) -> int:
        return self._improvement_level

    def set_improvement_level(self, level: int) -> bool:
        if level < 0 or level > 5:
            return False
        if level > self._max_improvement_level:
            return False
        self._improvement_level = level
        self._save_state()
        return True

    # ---- Metrics Collection ----

    def record_metric(self, metric_type: str, value: float,
                      context: Optional[Dict] = None,
                      source: str = "system", sample_size: int = 1,
                      confidence: float = 0.0, label: str = "") -> MetricValue:
        mv = MetricValue(metric_type, value, context=context, source=source,
                        sample_size=sample_size, confidence=confidence, label=label)
        with self._lock:
            self._metrics.append(mv)
        return mv

    def record_mission_result(self, result: Dict[str, Any]):
        """Registra resultado de missão para cálculo de métricas."""
        mission_data = {
            'mission_id': result.get('mission_id', str(uuid.uuid4())[:8]),
            'status': result.get('status', 'unknown'),
            'completed_steps': result.get('completed_steps', 0),
            'total_steps': result.get('total_steps', 0),
            'duration_s': result.get('duration_s', 0),
            'tool_calls': result.get('tool_calls', 0),
            'replans': result.get('replans', 0),
            'retries': result.get('retries', 0),
            'failure_categories': result.get('failure_categories', []),
            'timestamp': time.time(),
        }
        with self._lock:
            self._mission_history.append(mission_data)
        self._derive_metrics_from_mission(mission_data)
        self._save_state()

    def _derive_metrics_from_mission(self, m: Dict[str, Any]):
        """Deriva métricas automaticamente de uma missão."""
        status = m.get('status', 'unknown')
        if status == 'completed':
            self.record_metric('MISSION_SUCCESS', 1.0, source='mission_loop')
        elif status == 'failed':
            self.record_metric('MISSION_FAILURE', 1.0, source='mission_loop')
        elif status == 'blocked':
            self.record_metric('HUMAN_INTERVENTION', 1.0, source='mission_loop')

        duration = m.get('duration_s', 0)
        if duration > 0:
            self.record_metric('AVG_MISSION_DURATION', duration, source='mission_loop')

        tool_calls = m.get('tool_calls', 0)
        if tool_calls > 0:
            self.record_metric('AVG_TOOL_CALLS', tool_calls, source='mission_loop')

        replans = m.get('replans', 0)
        if replans > 0:
            self.record_metric('AVG_REPLANS', replans, source='mission_loop')

        retries = m.get('retries', 0)
        if retries > 0:
            self.record_metric('AVG_RETRIES', retries, source='mission_loop')

    # ---- Baseline Management ----

    def create_baseline(self, name: str, metrics: Dict[str, float],
                        description: str = "", version: str = "1.0") -> Baseline:
        bid = f"bl_{name}_{int(time.time())}"
        bl = Baseline(bid, name, version, metrics=metrics, description=description)
        with self._lock:
            self._baselines[bid] = bl
        self._save_state()
        return bl

    def get_active_baseline(self) -> Optional[Baseline]:
        actives = [b for b in self._baselines.values() if b.active]
        return actives[-1] if actives else None

    def deactivate_baseline(self, baseline_id: str) -> bool:
        bl = self._baselines.get(baseline_id)
        if not bl:
            return False
        bl.active = False
        self._save_state()
        return True

    # ---- Metric Aggregation ----

    def _aggregate_metrics(self, window_hours: float = 24.0) -> Dict[str, float]:
        """Agrega métricas na janela de tempo."""
        cutoff = time.time() - (window_hours * 3600)
        recent = [m for m in self._metrics if m.timestamp >= cutoff]

        agg = defaultdict(list)
        for m in recent:
            agg[m.metric_type].append(m.value)

        result = {}
        for metric_type, values in agg.items():
            if metric_type in ('MISSION_SUCCESS', 'MISSION_FAILURE', 'HUMAN_INTERVENTION'):
                result[metric_type.lower() + '_count'] = sum(values)
            else:
                result[metric_type.lower() + '_avg'] = sum(values) / len(values)

        total_success = sum(1 for m in recent if m.metric_type == 'MISSION_SUCCESS')
        total_failure = sum(1 for m in recent if m.metric_type == 'MISSION_FAILURE')
        total = total_success + total_failure
        if total > 0:
            result['success_rate'] = total_success / total
            result['failure_rate'] = total_failure / total

        mission_durations = [m.value for m in recent if m.metric_type == 'AVG_MISSION_DURATION']
        if mission_durations:
            result['avg_mission_duration'] = sum(mission_durations) / len(mission_durations)

        tool_calls = [m.value for m in recent if m.metric_type == 'AVG_TOOL_CALLS']
        if tool_calls:
            result['avg_tool_calls'] = sum(tool_calls) / len(tool_calls)

        replans = [m.value for m in recent if m.metric_type == 'AVG_REPLANS']
        if replans:
            result['avg_replans'] = sum(replans) / len(replans)

        security = sum(1 for m in recent if m.metric_type in SECURITY_EVENTS)
        result['security_incidents'] = security

        human = sum(1 for m in recent if m.metric_type == 'HUMAN_INTERVENTION')
        result['human_intervention_rate'] = human / total if total > 0 else 0.0

        result['memory_retrieval_quality'] = 0.7  # placeholder, ETAPA 21 fornece

        return result

    # ---- Assessment ----

    def run_assessment(self, scope: str = "full",
                       trigger: str = "periodic",
                       window_hours: float = 24.0) -> AssessmentResult:
        """Executa avaliação completa do sistema."""
        start = time.time()

        if time.time() - self._last_assessment_time < self._assessment_budget['min_interval_seconds']:
            return AssessmentResult(trigger=trigger, scope=scope,
                                   duration_ms=(time.time() - start) * 1000)

        metrics = self._aggregate_metrics(window_hours)
        baseline = self.get_active_baseline()

        baseline_comparison = {}
        if baseline and baseline.metrics:
            drifts = DriftDetector.detect_all(baseline.metrics, metrics)
            baseline_comparison = {
                'baseline_id': baseline.baseline_id,
                'baseline_name': baseline.name,
                'drifts': drifts,
                'drift_count': len(drifts),
            }

        scorecard = Scorecard.compute(metrics)

        problems = []
        if metrics.get('failure_rate', 0) > 0.2:
            problems.append({
                'type': 'high_failure_rate',
                'severity': 'HIGH',
                'metric': 'failure_rate',
                'value': metrics['failure_rate'],
                'threshold': 0.2,
            })
        if metrics.get('avg_replans', 0) > 3:
            problems.append({
                'type': 'excessive_replanning',
                'severity': 'MEDIUM',
                'metric': 'avg_replans',
                'value': metrics['avg_replans'],
                'threshold': 3.0,
            })
        if metrics.get('human_intervention_rate', 0) > 0.3:
            problems.append({
                'type': 'high_human_intervention',
                'severity': 'MEDIUM',
                'metric': 'human_intervention_rate',
                'value': metrics['human_intervention_rate'],
                'threshold': 0.3,
            })
        if metrics.get('security_incidents', 0) > 0:
            problems.append({
                'type': 'security_events_detected',
                'severity': 'CRITICAL',
                'metric': 'security_incidents',
                'value': metrics['security_incidents'],
                'threshold': 0,
            })

        recommendations = []
        if problems:
            for p in problems:
                if p['type'] == 'high_failure_rate':
                    recommendations.append('Investigate root causes of mission failures')
                elif p['type'] == 'excessive_replanning':
                    recommendations.append('Review planning heuristics and strategy selection')
                elif p['type'] == 'high_human_intervention':
                    recommendations.append('Improve autonomous decision-making capabilities')
                elif p['type'] == 'security_events_detected':
                    recommendations.append('URGENT: Investigate security events immediately')

        result = AssessmentResult(
            scope=scope, metrics=metrics,
            baseline_comparison=baseline_comparison,
            scorecard=scorecard, problems=problems,
            recommendations=recommendations,
            trigger=trigger,
            duration_ms=(time.time() - start) * 1000,
        )

        with self._lock:
            self._assessments.append(result)
            self._last_assessment_time = time.time()

        self._save_state()
        return result

    # ---- Root Cause Analysis ----

    def diagnose_failures(self, mission_result: Dict[str, Any]) -> Dict[str, Any]:
        """Executa diagnóstico em uma missão com falhas."""
        journal = mission_result.get('journal', [])
        failures = [e for e in journal if e.get('event') in ('STEP_FAILED', 'MISSION_FAILED')]
        successes = [e for e in journal if e.get('event') == 'STEP_COMPLETED']

        five_whys = RootCauseAnalysis.five_whys(
            mission_result.get('objective', ''), failures)
        correlation = RootCauseAnalysis.failure_correlation(failures, successes)
        patterns = RootCauseAnalysis.pattern_analysis(journal)

        return {
            'mission_id': mission_result.get('mission_id'),
            'five_whys': five_whys,
            'correlation': correlation,
            'patterns': patterns,
        }

    # ---- Drift Detection ----

    def check_drift(self, window: int = 10,
                    threshold_pct: float = 10.0) -> Dict[str, Any]:
        """Detecta drift de performance nas missões recentes."""
        if len(self._mission_history) < window:
            return {'drifted': False, 'reason': 'insufficient_data'}

        success_drift = DriftDetector.detect(
            self._mission_history, 'status', window, threshold_pct)

        durations = [{'avg_duration': m.get('duration_s', 0)}
                     for m in self._mission_history[-window:]]
        duration_drift = DriftDetector.detect(durations, 'avg_duration', window, threshold_pct)

        return {
            'success_drift': success_drift,
            'duration_drift': duration_drift,
            'overall_drifted': success_drift.get('drifted', False) or duration_drift.get('drifted', False),
        }

    # ---- Scorecard ----

    def get_scorecard(self) -> Dict[str, Any]:
        """Gera scorecard atual."""
        metrics = self._aggregate_metrics()
        return Scorecard.compute(metrics)

    # ---- Report ----

    def generate_report(self) -> Dict[str, Any]:
        """Gera relatório de autoavaliação."""
        metrics = self._aggregate_metrics()
        scorecard = Scorecard.compute(metrics)
        baseline = self.get_active_baseline()

        drift = self.check_drift()
        gaming_checks = []
        for key in ('success_rate', 'failure_rate', 'avg_mission_duration'):
            if key in metrics:
                gc = MetricGamingDetector.detect_gaming(
                    self._mission_history, key)
                gaming_checks.append({'metric': key, **gc})

        return {
            'timestamp': datetime.now().isoformat(),
            'metrics': {k: round(v, 4) if isinstance(v, float) else v
                       for k, v in metrics.items()},
            'scorecard': scorecard,
            'baseline': baseline.to_dict() if baseline else None,
            'drift': drift,
            'gaming_checks': gaming_checks,
            'total_missions': len(self._mission_history),
            'total_metrics': len(self._metrics),
            'total_assessments': len(self._assessments),
            'improvement_level': self._improvement_level,
            'feature_flags': dict(self._feature_flags),
        }

    # ---- Integration: consume Mission Loop (ETAPA 20) ----

    def consume_mission_result(self, mission_result: Dict[str, Any]) -> Dict[str, Any]:
        """Registra resultado de missão e gera diagnóstico se houver falhas."""
        self.record_mission_result(mission_result)
        result = {'recorded': True, 'diagnosis': None}

        status = mission_result.get('status', 'unknown')
        if status == 'failed':
            result['diagnosis'] = self.diagnose_failures(mission_result)

        return result

    # ---- Integration: consume Memory (ETAPA 21) ----

    def consume_memory_insights(self) -> Dict[str, Any]:
        """Lê insights da memória (ETAPA 21) para diagnóstico."""
        insights = {'failure_patterns': [], 'validated_procedures': []}
        try:
            from scripts.memory_consolidation import consolidation
            memories = consolidation.retrieve('failure error problem', limit=10)
            for m in memories:
                if m.get('kind') == 'erro':
                    insights['failure_patterns'].append({
                        'task': m.get('task', '')[:80],
                        'summary': m.get('summary', '')[:120],
                        'confidence': m.get('confidence', 0),
                    })
                elif m.get('metadata', {}).get('epistemic_status') == 'VALIDATED':
                    insights['validated_procedures'].append({
                        'task': m.get('task', '')[:80],
                        'confidence': m.get('confidence', 0),
                    })
        except Exception:
            pass
        return insights

    # ---- Integration: produce feedback for Cognitive Core (ETAPA 18) ----

    def get_cognitive_feedback(self) -> Dict[str, Any]:
        """Gera feedback para o Cognitive Core baseado em avaliação."""
        metrics = self._aggregate_metrics()
        scorecard = Scorecard.compute(metrics)
        return {
            'performance_insights': {
                'success_rate': metrics.get('success_rate', 0.5),
                'failure_rate': metrics.get('failure_rate', 0.1),
                'avg_replans': metrics.get('avg_replans', 0),
            },
            'known_failure_modes': [
                p.get('type', '') for p in self._last_problems()
            ],
            'planning_heuristics': {
                'replan_threshold': 2.0,
                'strategy_preference': 'conservative' if metrics.get('failure_rate', 0) > 0.2 else 'balanced',
            },
            'scorecard': scorecard,
        }

    def _last_problems(self) -> List[Dict]:
        if self._assessments:
            return self._assessments[-1].problems
        return []

    # ---- Integration: produce feedback for Mission Loop (ETAPA 20) ----

    def get_strategy_feedback(self) -> Dict[str, Any]:
        """Gera feedback de estratégia para o Mission Loop."""
        metrics = self._aggregate_metrics()
        return {
            'strategy_insights': {
                'preferred_approach': 'conservative' if metrics.get('failure_rate', 0) > 0.2 else 'mvp_first',
                'max_replans': 3 if metrics.get('avg_replans', 0) < 2 else 1,
                'timeout_multiplier': 1.5 if metrics.get('timeout_rate', 0) > 0.1 else 1.0,
            },
            'known_issues': [
                p.get('type') for p in self._last_problems()
            ],
        }

    # ---- Self-Critique ----

    def self_critique(self, mission_result: Dict[str, Any]) -> Dict[str, Any]:
        """Auto-crítica de uma missão (dados objetivos, não opinião)."""
        status = mission_result.get('status', 'unknown')
        steps = mission_result.get('total_steps', 0)
        completed = mission_result.get('completed_steps', 0)
        duration = mission_result.get('duration_s', 0)
        replans = mission_result.get('replans', 0)

        what_went_well = []
        what_failed = []
        what_uncertain = []

        if status == 'completed':
            what_went_well.append('Mission completed successfully')
        if completed and steps and completed == steps:
            what_went_well.append('All steps completed')
        if replans == 0:
            what_went_well.append('No replanning needed')
        if duration > 0 and completed and duration / completed < 10:
            what_went_well.append('Fast step execution')

        if status == 'failed':
            what_failed.append(f'Mission failed (status={status})')
        if replans > 2:
            what_failed.append(f'Excessive replanning: {replans}')
        if steps and completed and completed < steps * 0.8:
            what_failed.append(f'Low completion: {completed}/{steps}')

        if duration == 0:
            what_uncertain.append('Duration not recorded')
        if not mission_result.get('journal'):
            what_uncertain.append('No journal for detailed analysis')

        improvement_opportunities = []
        if replans > 1:
            improvement_opportunities.append('Planning heuristics may need tuning')
        if status == 'failed' and mission_result.get('failure_categories'):
            cats = mission_result['failure_categories']
            improvement_opportunities.append(
                f'Address failure categories: {", ".join(set(cats)[:3])}')

        return {
            'mission_id': mission_result.get('mission_id'),
            'what_went_well': what_went_well,
            'what_failed': what_failed,
            'what_uncertain': what_uncertain,
            'improvement_opportunities': improvement_opportunities,
            'objective_outcome': status,
            'note': 'Self-critique is OBSERVATION, not truth. Validate with data.',
        }


# ──────────────────────────────────────────────────────────────────
# Instância global
# ──────────────────────────────────────────────────────────────────

engine = SelfAssessmentEngine()
engine._load_state()


# ──────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Self-Assessment Engine (ETAPA 22)')
    sub = parser.add_subparsers(dest='cmd')

    p_report = sub.add_parser('report')
    p_assess = sub.add_parser('assess')
    p_assess.add_argument('--trigger', default='periodic')
    p_baseline = sub.add_parser('baseline')
    p_baseline.add_argument('name')
    p_baseline.add_argument('--desc', default='')
    p_score = sub.add_parser('scorecard')
    p_drift = sub.add_parser('drift')
    p_level = sub.add_parser('level')
    p_level.add_argument('value', type=int)
    p_flag = sub.add_parser('flag')
    p_flag.add_argument('name')
    p_flag.add_argument('enabled', type=lambda x: x.lower() == 'true')

    args = parser.parse_args()

    if args.cmd == 'report':
        r = engine.generate_report()
        print(json.dumps(r, indent=2, ensure_ascii=False, default=str))
    elif args.cmd == 'assess':
        r = engine.run_assessment(trigger=args.trigger)
        print(f'Assessment {r.assessment_id}: {len(r.problems)} problems, '
              f'{len(r.recommendations)} recommendations ({r.duration_ms:.0f}ms)')
        for p in r.problems:
            print(f'  [{p["severity"]}] {p["type"]}: {p["value"]}')
    elif args.cmd == 'baseline':
        m = engine._aggregate_metrics()
        bl = engine.create_baseline(args.name, m, description=args.desc)
        print(f'Baseline created: {bl.baseline_id} ({len(m)} metrics)')
    elif args.cmd == 'scorecard':
        sc = engine.get_scorecard()
        print(json.dumps(sc, indent=2, ensure_ascii=False))
    elif args.cmd == 'drift':
        d = engine.check_drift()
        print(json.dumps(d, indent=2, ensure_ascii=False))
    elif args.cmd == 'level':
        ok = engine.set_improvement_level(args.value)
        print(f'Level set to {args.value}: {"OK" if ok else "FAILED (exceeds max)"}')
    elif args.cmd == 'flag':
        engine.set_feature_flag(args.name, args.enabled)
        print(f'Flag {args.name} = {args.enabled}')
    else:
        parser.print_help()
