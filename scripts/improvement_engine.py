"""Improvement Engine — ETAPA 22

Candidatos a melhoria, fila prioritária, experimentos controlados,
A/B, shadow mode, feature flags, rollback, aprovação, regressão.

Princípio: melhoria precisa de evidência + validação + comparação + controle.
O Jarvis pode propor melhorias, mas nenhuma é válida porque ele "acredita que funciona".
"""

import sys
import os
import json
import time
import uuid
import copy
import threading
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict

BASE = str(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCRIPTS = os.path.join(BASE, 'scripts')
RUNTIME = os.path.join(BASE, 'runtime')
sys.path.insert(0, SCRIPTS)

# ──────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────

CANDIDATE_STATUSES = (
    "PROPOSED", "ANALYZING", "EXPERIMENTAL", "VALIDATING",
    "ACCEPTED", "REJECTED", "ROLLED_BACK", "DEFERRED",
)

QUEUE_STATUSES = (
    "NEW", "PRIORITIZED", "ANALYZING", "EXPERIMENTING",
    "VALIDATING", "ACCEPTED", "REJECTED", "DEFERRED",
)

RISK_LEVELS = ("LOW", "MEDIUM", "HIGH", "CRITICAL")

APPROVAL_POLICIES = {
    "LOW": "auto_adopt_if_validated",
    "MEDIUM": "additional_validation",
    "HIGH": "human_approval_required",
    "CRITICAL": "mandatory_human_review",
}

STOP_CONDITIONS = (
    "success_achieved", "budget_exceeded", "risk_threshold_exceeded",
    "regression_detected", "insufficient_evidence", "experiment_inconclusive",
)

ROLLBACK_TRIGGERS = (
    "error_rate_threshold", "security_event",
    "performance_degradation", "critical_regression",
)


# ──────────────────────────────────────────────────────────────────
# Improvement Candidate
# ──────────────────────────────────────────────────────────────────

class ImprovementCandidate:
    __slots__ = (
        'candidate_id', 'problem', 'evidence', 'hypothesis',
        'proposed_change', 'expected_benefit', 'expected_risk',
        'affected_components', 'baseline', 'experiment_plan',
        'validation_criteria', 'status', 'priority_score',
        'source', 'created_at', 'updated_at', 'decision_record',
        'risk_level', 'dependencies', 'related_candidates',
    )

    def __init__(self, problem: str, hypothesis: str,
                 proposed_change: str, source: str = "system"):
        self.candidate_id = f"imp_{str(uuid.uuid4())[:8]}"
        self.problem = problem
        self.evidence: List[Dict[str, Any]] = []
        self.hypothesis = hypothesis
        self.proposed_change = proposed_change
        self.expected_benefit = ""
        self.expected_risk = ""
        self.affected_components: List[str] = []
        self.baseline: Optional[Dict[str, float]] = None
        self.experiment_plan: Optional[Dict[str, Any]] = None
        self.validation_criteria: Dict[str, Any] = {}
        self.status = "PROPOSED"
        self.priority_score = 0.0
        self.source = source
        self.created_at = datetime.now().isoformat()
        self.updated_at = self.created_at
        self.decision_record: Optional[Dict[str, Any]] = None
        self.risk_level = "MEDIUM"
        self.dependencies: List[str] = []
        self.related_candidates: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ImprovementCandidate':
        c = cls(d.get('problem', ''), d.get('hypothesis', ''),
                d.get('proposed_change', ''), d.get('source', 'system'))
        for k in cls.__slots__:
            if k in d and k not in ('problem', 'hypothesis', 'proposed_change', 'source'):
                setattr(c, k, d[k])
        return c


# ──────────────────────────────────────────────────────────────────
# Experiment
# ──────────────────────────────────────────────────────────────────

class Experiment:
    __slots__ = (
        'experiment_id', 'candidate_id', 'baseline', 'candidate_config',
        'variables', 'controls', 'sample_size', 'duration_s',
        'success_criteria', 'risk_constraints', 'result',
        'status', 'started_at', 'completed_at', 'environment',
    )

    def __init__(self, candidate_id: str,
                 baseline: Optional[Dict[str, float]] = None,
                 candidate_config: Optional[Dict[str, Any]] = None):
        self.experiment_id = f"exp_{str(uuid.uuid4())[:8]}"
        self.candidate_id = candidate_id
        self.baseline = baseline or {}
        self.candidate_config = candidate_config or {}
        self.variables: Dict[str, Any] = {}
        self.controls: Dict[str, Any] = {}
        self.sample_size = 10
        self.duration_s = 300
        self.success_criteria: Dict[str, Any] = {}
        self.risk_constraints: Dict[str, Any] = {}
        self.result: Optional[Dict[str, Any]] = None
        self.status = "CREATED"
        self.started_at: Optional[str] = None
        self.completed_at: Optional[str] = None
        self.environment = "production"

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}


class ExperimentResult:
    __slots__ = (
        'experiment_id', 'baseline_metrics', 'candidate_metrics',
        'delta', 'confidence', 'regressions', 'security_result',
        'resource_cost', 'decision', 'evidence',
    )

    def __init__(self, experiment_id: str):
        self.experiment_id = experiment_id
        self.baseline_metrics: Dict[str, float] = {}
        self.candidate_metrics: Dict[str, float] = {}
        self.delta: Dict[str, float] = {}
        self.confidence = 0.0
        self.regressions: List[Dict[str, Any]] = []
        self.security_result = "PASS"
        self.resource_cost: Dict[str, Any] = {}
        self.decision = "INCONCLUSIVE"
        self.evidence: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}


# ──────────────────────────────────────────────────────────────────
# Decision Record
# ──────────────────────────────────────────────────────────────────

class DecisionRecord:
    __slots__ = (
        'decision_id', 'candidate_id', 'decision', 'reason',
        'evidence', 'baseline', 'result', 'risk',
        'rollback_plan', 'timestamp', 'actor',
    )

    def __init__(self, candidate_id: str, decision: str,
                 reason: str = "", actor: str = "system"):
        self.decision_id = f"dec_{str(uuid.uuid4())[:8]}"
        self.candidate_id = candidate_id
        self.decision = decision
        self.reason = reason
        self.evidence: List[Dict[str, Any]] = []
        self.baseline: Dict[str, float] = {}
        self.result: Dict[str, Any] = {}
        self.risk = "MEDIUM"
        self.rollback_plan = ""
        self.timestamp = datetime.now().isoformat()
        self.actor = actor

    def to_dict(self) -> Dict[str, Any]:
        return {k: getattr(self, k) for k in self.__slots__}


# ──────────────────────────────────────────────────────────────────
# Safety Gate
# ──────────────────────────────────────────────────────────────────

class SafetyGate:
    """Gate de segurança antes de adotar melhoria."""

    @staticmethod
    def evaluate(candidate: ImprovementCandidate,
                 experiment_result: Optional[ExperimentResult] = None,
                 improvement_level: int = 0) -> Dict[str, Any]:
        checks = []

        checks.append({
            'name': 'risk_assessment',
            'passed': candidate.risk_level in ('LOW', 'MEDIUM'),
            'detail': f"Risk level: {candidate.risk_level}",
        })

        if experiment_result:
            checks.append({
                'name': 'experiment_result',
                'passed': experiment_result.decision == 'SUCCESS',
                'detail': f"Decision: {experiment_result.decision}",
            })
            checks.append({
                'name': 'regression_check',
                'passed': len(experiment_result.regressions) == 0,
                'detail': f"Regressions: {len(experiment_result.regressions)}",
            })
            checks.append({
                'name': 'security_check',
                'passed': experiment_result.security_result == 'PASS',
                'detail': f"Security: {experiment_result.security_result}",
            })
            checks.append({
                'name': 'confidence_check',
                'passed': experiment_result.confidence >= 0.6,
                'detail': f"Confidence: {experiment_result.confidence:.2f}",
            })
        else:
            checks.append({
                'name': 'experiment_result',
                'passed': False,
                'detail': 'No experiment result available',
            })

        checks.append({
            'name': 'improvement_level',
            'passed': improvement_level >= 1,
            'detail': f"Level {improvement_level} (min: 1)",
        })

        if candidate.risk_level == 'CRITICAL':
            checks.append({
                'name': 'critical_requires_experiment',
                'passed': experiment_result is not None and experiment_result.decision == 'SUCCESS',
                'detail': 'Critical changes require proven experiment',
            })

        all_passed = all(c['passed'] for c in checks)
        policy = APPROVAL_POLICIES.get(candidate.risk_level, 'MEDIUM')

        return {
            'gate_result': 'PASS' if all_passed else 'BLOCK',
            'checks': checks,
            'approval_policy': policy,
            'requires_human': candidate.risk_level in ('HIGH', 'CRITICAL'),
        }


# ──────────────────────────────────────────────────────────────────
# Regression Detector
# ──────────────────────────────────────────────────────────────────

class RegressionDetector:
    """Detecta regressões causadas por melhorias."""

    @staticmethod
    def detect(baseline_metrics: Dict[str, float],
               current_metrics: Dict[str, float],
               regressions_config: Optional[Dict[str, float]] = None) -> List[Dict[str, Any]]:
        config = regressions_config or {
            'success_rate': -0.05,
            'failure_rate': 0.05,
            'avg_mission_duration': 0.30,
            'security_incidents': 0,
        }

        regressions = []
        for metric, threshold in config.items():
            if metric in baseline_metrics and metric in current_metrics:
                base = baseline_metrics[metric]
                curr = current_metrics[metric]

                if metric == 'success_rate' and curr - base < threshold:
                    regressions.append({
                        'metric': metric,
                        'baseline': round(base, 4),
                        'current': round(curr, 4),
                        'threshold': threshold,
                        'severity': 'CRITICAL' if (base - curr) > 0.15 else 'HIGH',
                        'detail': f"Success rate regressed: {base:.2%} → {curr:.2%}",
                    })
                elif metric == 'failure_rate' and curr - base > abs(threshold):
                    regressions.append({
                        'metric': metric,
                        'baseline': round(base, 4),
                        'current': round(curr, 4),
                        'threshold': threshold,
                        'severity': 'HIGH',
                        'detail': f"Failure rate increased: {base:.2%} → {curr:.2%}",
                    })
                elif metric == 'security_incidents' and curr > base:
                    regressions.append({
                        'metric': metric,
                        'baseline': base,
                        'current': curr,
                        'threshold': 0,
                        'severity': 'CRITICAL',
                        'detail': f"Security incidents: {base} → {curr}",
                    })

        return regressions


# ──────────────────────────────────────────────────────────────────
# ImprovementEngine — Núcleo
# ──────────────────────────────────────────────────────────────────

class ImprovementEngine:
    """Motor de melhoria controlada do ecossistema."""

    def __init__(self):
        self._lock = threading.Lock()
        self._candidates: Dict[str, ImprovementCandidate] = {}
        self._experiments: Dict[str, Experiment] = {}
        self._decision_records: List[Dict[str, Any]] = []
        self._improvement_journal: List[Dict[str, Any]] = []
        self._rejected_ids: set = set()
        self._accepted_ids: set = set()
        self._rollback_log: List[Dict[str, Any]] = []
        self._feature_flags: Dict[str, bool] = {}
        self._budget = {
            'max_experiments_per_day': 10,
            'max_duration_per_experiment_s': 600,
            'max_concurrent_experiments': 3,
            'max_changes_per_week': 5,
        }
        self._state_path = os.path.join(RUNTIME, 'improvement_state.json')

    # ---- Persistence ----

    def _save_state(self):
        os.makedirs(RUNTIME, exist_ok=True)
        state = {
            'candidates': {k: v.to_dict() for k, v in self._candidates.items()},
            'experiments': {k: v.to_dict() for k, v in self._experiments.items()},
            'decision_records': self._decision_records[-200:],
            'improvement_journal': self._improvement_journal[-200:],
            'rejected_ids': list(self._rejected_ids),
            'accepted_ids': list(self._accepted_ids),
            'rollback_log': self._rollback_log[-100:],
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
            self._candidates = {
                k: ImprovementCandidate.from_dict(v)
                for k, v in state.get('candidates', {}).items()
            }
            self._experiments = {}  # don't reload experiments
            self._decision_records = state.get('decision_records', [])
            self._improvement_journal = state.get('improvement_journal', [])
            self._rejected_ids = set(state.get('rejected_ids', []))
            self._accepted_ids = set(state.get('accepted_ids', []))
            self._rollback_log = state.get('rollback_log', [])
            self._feature_flags = state.get('feature_flags', {})
        except Exception:
            pass

    # ---- Feature Flags ----

    def set_feature_flag(self, flag: str, enabled: bool):
        self._feature_flags[flag] = enabled
        self._save_state()

    def get_feature_flag(self, flag: str, default: bool = False) -> bool:
        return self._feature_flags.get(flag, default)

    # ---- Candidates ----

    def propose(self, problem: str, hypothesis: str,
                proposed_change: str, source: str = "system",
                risk_level: str = "MEDIUM",
                expected_benefit: str = "",
                expected_risk: str = "",
                affected_components: Optional[List[str]] = None) -> ImprovementCandidate:
        c = ImprovementCandidate(problem, hypothesis, proposed_change, source)
        c.risk_level = risk_level
        c.expected_benefit = expected_benefit
        c.expected_risk = expected_risk
        c.affected_components = affected_components or []
        c.priority_score = self._compute_priority(c)

        with self._lock:
            self._candidates[c.candidate_id] = c
        self._journal("PROPOSED", c.candidate_id, problem=problem)
        self._save_state()
        return c

    def _compute_priority(self, c: ImprovementCandidate) -> float:
        score = 0.0
        severity_map = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        score += severity_map.get(c.risk_level, 2) * 0.3
        score += min(3.0, len(c.evidence)) * 0.2
        if 'security' in c.problem.lower():
            score += 2.0
        if 'failure' in c.problem.lower() or 'error' in c.problem.lower():
            score += 1.5
        if 'performance' in c.problem.lower() or 'latency' in c.problem.lower():
            score += 1.0
        return round(score, 2)

    def prioritize(self):
        with self._lock:
            for c in self._candidates.values():
                if c.status == 'PROPOSED':
                    c.priority_score = self._compute_priority(c)
                    c.status = 'PRIORITIZED'
        self._save_state()

    def get_candidates(self, status: Optional[str] = None,
                       min_priority: float = 0.0) -> List[ImprovementCandidate]:
        candidates = list(self._candidates.values())
        if status:
            candidates = [c for c in candidates if c.status == status]
        candidates = [c for c in candidates if c.priority_score >= min_priority]
        candidates.sort(key=lambda c: -c.priority_score)
        return candidates

    def update_status(self, candidate_id: str, new_status: str) -> bool:
        c = self._candidates.get(candidate_id)
        if not c:
            return False
        if new_status not in CANDIDATE_STATUSES:
            return False
        old = c.status
        c.status = new_status
        c.updated_at = datetime.now().isoformat()
        self._journal("STATUS_CHANGE", candidate_id,
                      old_status=old, new_status=new_status)
        if new_status == 'REJECTED':
            self._rejected_ids.add(candidate_id)
        elif new_status == 'ACCEPTED':
            self._accepted_ids.add(candidate_id)
        self._save_state()
        return True

    # ---- Duplicate Detection ----

    def find_duplicates(self, candidate: ImprovementCandidate,
                        threshold: float = 0.7) -> List[str]:
        duplicates = []
        cand_text = f"{candidate.problem} {candidate.hypothesis}".lower()
        for cid, c in self._candidates.items():
            if cid == candidate.candidate_id:
                continue
            existing_text = f"{c.problem} {c.hypothesis}".lower()
            common = sum(1 for w in cand_text.split() if w in existing_text)
            total = max(1, len(set(cand_text.split() + existing_text.split())))
            similarity = common / total
            if similarity >= threshold:
                duplicates.append(cid)
        return duplicates

    # ---- Conflicting Improvements ----

    def find_conflicts(self, candidate: ImprovementCandidate) -> List[Dict[str, Any]]:
        conflicts = []
        cand_components = set(candidate.affected_components)
        for cid, c in self._candidates.items():
            if cid == candidate.candidate_id:
                continue
            if c.status in ('REJECTED', 'ROLLED_BACK'):
                continue
            overlap = cand_components & set(c.affected_components)
            if overlap:
                conflicts.append({
                    'candidate_a': candidate.candidate_id,
                    'candidate_b': cid,
                    'shared_components': list(overlap),
                    'risk': 'may_interfere',
                })
        return conflicts

    # ---- Experiments ----

    def create_experiment(self, candidate_id: str,
                          baseline: Optional[Dict[str, float]] = None,
                          sample_size: int = 10,
                          duration_s: int = 300,
                          environment: str = "production") -> Optional[Experiment]:
        c = self._candidates.get(candidate_id)
        if not c:
            return None
        if c.status not in ('PRIORITIZED', 'ANALYZING'):
            return None

        exp = Experiment(candidate_id, baseline=baseline)
        exp.sample_size = sample_size
        exp.duration_s = duration_s
        exp.environment = environment
        exp.success_criteria = c.validation_criteria or {'min_improvement': 0.05}
        exp.status = "CREATED"

        with self._lock:
            self._experiments[exp.experiment_id] = exp
        c.experiment_plan = exp.to_dict()
        c.status = 'EXPERIMENTAL'
        self._journal("EXPERIMENT_CREATED", candidate_id,
                      experiment_id=exp.experiment_id)
        self._save_state()
        return exp

    def start_experiment(self, experiment_id: str) -> bool:
        exp = self._experiments.get(experiment_id)
        if not exp or exp.status != 'CREATED':
            return False
        exp.status = 'RUNNING'
        exp.started_at = datetime.now().isoformat()
        self._journal("EXPERIMENT_STARTED", exp.candidate_id,
                      experiment_id=experiment_id)
        self._save_state()
        return True

    def complete_experiment(self, experiment_id: str,
                            result: ExperimentResult) -> bool:
        exp = self._experiments.get(experiment_id)
        if not exp or exp.status != 'RUNNING':
            return False
        exp.result = result.to_dict()
        exp.status = 'COMPLETED'
        exp.completed_at = datetime.now().isoformat()

        c = self._candidates.get(exp.candidate_id)
        if c:
            c.status = 'VALIDATING'

        self._journal("EXPERIMENT_COMPLETED", exp.candidate_id,
                      experiment_id=experiment_id,
                      decision=result.decision)
        self._save_state()
        return True

    # ---- Shadow Mode ----

    def run_shadow(self, candidate_id: str,
                   production_output: Any,
                   candidate_output: Any) -> Dict[str, Any]:
        """Executa comparação shadow: production vs candidate sem afetar produção."""
        identical = production_output == candidate_output
        return {
            'mode': 'shadow',
            'candidate_id': candidate_id,
            'production_output': str(production_output)[:200],
            'candidate_output': str(candidate_output)[:200],
            'identical': identical,
            'candidate_controls_production': False,
            'note': 'Shadow mode: candidate does not control production',
        }

    # ---- Feature Flags for Improvements ----

    def enable_improvement(self, improvement_name: str) -> bool:
        self._feature_flags[f"improvement.{improvement_name}"] = True
        self._save_state()
        return True

    def disable_improvement(self, improvement_name: str) -> bool:
        self._feature_flags[f"improvement.{improvement_name}"] = False
        self._save_state()
        return True

    # ---- Safety Gate ----

    def evaluate_safety(self, candidate_id: str,
                        experiment_result: Optional[ExperimentResult] = None,
                        improvement_level: int = 0) -> Dict[str, Any]:
        c = self._candidates.get(candidate_id)
        if not c:
            return {'gate_result': 'BLOCK', 'reason': 'candidate_not_found'}
        return SafetyGate.evaluate(c, experiment_result, improvement_level)

    # ---- Adoption ----

    def accept(self, candidate_id: str, reason: str = "",
               actor: str = "system") -> bool:
        c = self._candidates.get(candidate_id)
        if not c:
            return False
        if c.status not in ('VALIDATING', 'ANALYZING'):
            return False

        gate = self.evaluate_safety(candidate_id, improvement_level=2)
        if gate['gate_result'] == 'BLOCK' and gate.get('requires_human'):
            return False

        c.status = 'ACCEPTED'
        self._accepted_ids.add(candidate_id)

        dr = DecisionRecord(candidate_id, 'ACCEPTED', reason, actor)
        dr.evidence = c.evidence
        dr.risk = c.risk_level
        dr.rollback_plan = f"Disable feature flag: improvement.{candidate_id}"

        with self._lock:
            self._decision_records.append(dr.to_dict())
        c.decision_record = dr.to_dict()

        self._journal("IMPROVEMENT_ACCEPTED", candidate_id,
                      reason=reason, risk=c.risk_level)
        self._save_state()
        return True

    def reject(self, candidate_id: str, reason: str = "",
               actor: str = "system") -> bool:
        c = self._candidates.get(candidate_id)
        if not c:
            return False

        c.status = 'REJECTED'
        self._rejected_ids.add(candidate_id)

        dr = DecisionRecord(candidate_id, 'REJECTED', reason, actor)
        with self._lock:
            self._decision_records.append(dr.to_dict())
        c.decision_record = dr.to_dict()

        self._journal("IMPROVEMENT_REJECTED", candidate_id,
                      reason=reason)
        self._save_state()
        return True

    # ---- Rollback ----

    def rollback(self, candidate_id: str, reason: str = "",
                 trigger: str = "manual") -> Dict[str, Any]:
        c = self._candidates.get(candidate_id)
        if not c:
            return {'success': False, 'reason': 'candidate_not_found'}

        flag_name = f"improvement.{candidate_id}"
        self._feature_flags[flag_name] = False

        c.status = 'ROLLED_BACK'

        entry = {
            'candidate_id': candidate_id,
            'reason': reason,
            'trigger': trigger,
            'timestamp': datetime.now().isoformat(),
            'previous_status': 'ACCEPTED',
        }
        with self._lock:
            self._rollback_log.append(entry)

        dr = DecisionRecord(candidate_id, 'ROLLED_BACK', reason)
        with self._lock:
            self._decision_records.append(dr.to_dict())

        self._journal("ROLLBACK", candidate_id, reason=reason, trigger=trigger)
        self._save_state()
        return {'success': True, 'flag_disabled': flag_name}

    # ---- Failure → Test ----

    def propose_regression_test(self, failure_event: Dict[str, Any],
                                root_cause: str,
                                test_description: str) -> Dict[str, Any]:
        """Propõe um teste de regressão a partir de uma falha."""
        return {
            'type': 'regression_test_proposal',
            'failure_event': failure_event,
            'root_cause': root_cause,
            'test_description': test_description,
            'status': 'PROPOSED',
            'note': 'Test should be implemented by ETAPA 22 or registered for ETAPA 23',
        }

    # ---- Journal ----

    def _journal(self, event: str, candidate_id: str, **kwargs):
        entry = {
            'event': event,
            'candidate_id': candidate_id,
            'timestamp': time.time(),
            **kwargs,
        }
        self._improvement_journal.append(entry)

    # ---- Report ----

    def generate_report(self) -> Dict[str, Any]:
        by_status = defaultdict(int)
        for c in self._candidates.values():
            by_status[c.status] += 1

        return {
            'total_candidates': len(self._candidates),
            'by_status': dict(by_status),
            'total_experiments': len(self._experiments),
            'accepted': len(self._accepted_ids),
            'rejected': len(self._rejected_ids),
            'rollbacks': len(self._rollback_log),
            'decision_records': len(self._decision_records),
            'journal_entries': len(self._improvement_journal),
            'feature_flags': {k: v for k, v in self._feature_flags.items()
                             if k.startswith('improvement.')},
        }


# ──────────────────────────────────────────────────────────────────
# Instância global
# ──────────────────────────────────────────────────────────────────

engine = ImprovementEngine()
engine._load_state()


# ──────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Improvement Engine (ETAPA 22)')
    sub = parser.add_subparsers(dest='cmd')

    p_propose = sub.add_parser('propose')
    p_propose.add_argument('problem')
    p_propose.add_argument('hypothesis')
    p_propose.add_argument('change')
    p_propose.add_argument('--risk', default='MEDIUM')
    p_propose.add_argument('--source', default='system')

    p_list = sub.add_parser('list')
    p_list.add_argument('--status', default=None)

    p_accept = sub.add_parser('accept')
    p_accept.add_argument('candidate_id')
    p_accept.add_argument('--reason', default='')

    p_reject = sub.add_parser('reject')
    p_reject.add_argument('candidate_id')
    p_reject.add_argument('--reason', default='')

    p_report = sub.add_parser('report')

    args = parser.parse_args()

    if args.cmd == 'propose':
        c = engine.propose(args.problem, args.hypothesis, args.change,
                          source=args.source, risk_level=args.risk)
        print(f'[OK] Candidate {c.candidate_id} proposed (priority={c.priority_score})')
    elif args.cmd == 'list':
        candidates = engine.get_candidates(status=args.status)
        print(f'{len(candidates)} candidates:')
        for c in candidates:
            print(f'  [{c.status}] {c.candidate_id} prio={c.priority_score} | {c.problem[:60]}')
    elif args.cmd == 'accept':
        ok = engine.accept(args.candidate_id, reason=args.reason)
        print(f'Accept {args.candidate_id}: {"OK" if ok else "FAILED"}')
    elif args.cmd == 'reject':
        ok = engine.reject(args.candidate_id, reason=args.reason)
        print(f'Reject {args.candidate_id}: {"OK" if ok else "FAILED"}')
    elif args.cmd == 'report':
        r = engine.generate_report()
        print(json.dumps(r, indent=2, ensure_ascii=False))
    else:
        parser.print_help()
