"""Testes da ETAPA 22 — Self-Assessment / Self-Improvement."""
import sys, os, json
sys.path.insert(0, r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')
os.chdir(r'C:\Users\David Jr\Documents\Default Project\EcoSystemUmGrau')

from scripts.self_assessment_engine import (
    SelfAssessmentEngine, MetricValue, Baseline, AssessmentResult,
    RootCauseAnalysis, DriftDetector, MetricGamingDetector, Scorecard
)
from scripts.improvement_engine import (
    ImprovementEngine, ImprovementCandidate, Experiment, ExperimentResult,
    DecisionRecord, SafetyGate, RegressionDetector
)

passed = 0
failed = 0

def check(name, cond, detail=''):
    global passed, failed
    if cond:
        passed += 1
        print(f'  [PASS] {name}')
    else:
        failed += 1
        print(f'  [FAIL] {name} {detail}')

# ======================================================================
print('=== 1. Metrics Collection ===')
sae = SelfAssessmentEngine()
sae.record_metric('MISSION_SUCCESS', 1.0, source='test')
sae.record_metric('MISSION_SUCCESS', 1.0, source='test')
sae.record_metric('MISSION_FAILURE', 1.0, source='test')
sae.record_metric('AVG_MISSION_DURATION', 45.0, source='test')
sae.record_metric('AVG_TOOL_CALLS', 8.0, source='test')
sae.record_metric('AVG_REPLANS', 2.0, source='test')
check('metrics recorded', len(sae._metrics) >= 6)
agg = sae._aggregate_metrics(window_hours=1.0)
check('success_rate computed', 'success_rate' in agg, f'keys={list(agg.keys())}')
check('success_rate = 2/3', abs(agg.get('success_rate', 0) - 2/3) < 0.01,
      f"val={agg.get('success_rate')}")

# ======================================================================
print('\n=== 2. Mission Result Recording ===')
sae2 = SelfAssessmentEngine()
r1 = {'mission_id': 'm1', 'status': 'completed', 'completed_steps': 5,
      'total_steps': 5, 'duration_s': 30, 'tool_calls': 10, 'replans': 0}
r2 = {'mission_id': 'm2', 'status': 'failed', 'completed_steps': 2,
      'total_steps': 5, 'duration_s': 60, 'tool_calls': 15, 'replans': 3,
      'failure_categories': ['DEPENDENCY', 'DEPENDENCY']}
sae2.record_mission_result(r1)
sae2.record_mission_result(r2)
check('mission history', len(sae2._mission_history) == 2)
check('metrics derived', len(sae2._metrics) >= 6)

# ======================================================================
print('\n=== 3. Baseline ===')
bl = sae2.create_baseline('test_baseline', {'success_rate': 0.8, 'failure_rate': 0.2},
                          description='Test baseline')
check('baseline created', bl.baseline_id.startswith('bl_'))
check('baseline active', bl.active)
active = sae2.get_active_baseline()
check('get_active_baseline', active is not None and active.baseline_id == bl.baseline_id)
ok = sae2.deactivate_baseline(bl.baseline_id)
check('deactivate_baseline', ok)
active2 = sae2.get_active_baseline()
check('no active after deactivate', active2 is None)

# ======================================================================
print('\n=== 4. Assessment ===')
sae3 = SelfAssessmentEngine()
for i in range(5):
    sae3.record_mission_result({'mission_id': f'a{i}', 'status': 'completed',
                                'completed_steps': 3, 'total_steps': 3,
                                'duration_s': 20, 'tool_calls': 5, 'replans': 0})
for i in range(2):
    sae3.record_mission_result({'mission_id': f'f{i}', 'status': 'failed',
                                'completed_steps': 1, 'total_steps': 3,
                                'duration_s': 40, 'tool_calls': 8, 'replans': 2})
asmt = sae3.run_assessment(trigger='test')
check('assessment created', isinstance(asmt, AssessmentResult))
check('assessment has metrics', len(asmt.metrics) > 0)
check('assessment has scorecard', 'dimensions' in asmt.scorecard)
check('assessment has problems or none', isinstance(asmt.problems, list))

# ======================================================================
print('\n=== 5. Scorecard ===')
sc = Scorecard.compute({'success_rate': 0.9, 'failure_rate': 0.1, 'avg_replans': 1.0,
                        'security_incidents': 0, 'recovery_rate': 0.8,
                        'memory_retrieval_quality': 0.7})
check('scorecard global_score', 0 <= sc['global_score'] <= 1, f"score={sc['global_score']}")
check('scorecard dimensions', len(sc['dimensions']) == 8)
check('scorecard weights sum ~1', abs(sum(sc['weights'].values()) - 1.0) < 0.01)

# ======================================================================
print('\n=== 6. Root Cause Analysis ===')
events = [
    {'event': 'STEP_FAILED', 'error': 'filesystem not found', 'failure_category': 'DEPENDENCY'},
    {'event': 'STEP_FAILED', 'error': 'filesystem not found', 'failure_category': 'DEPENDENCY'},
    {'event': 'STEP_FAILED', 'error': 'timeout on network', 'failure_category': 'RESOURCE'},
    {'event': 'STEP_COMPLETED', 'step': '1'},
]
rca = RootCauseAnalysis.five_whys('filesystem not found', events)
check('5 whys has causes', len(rca['root_causes']) >= 1, f"causes={rca['root_causes']}")
corr = RootCauseAnalysis.failure_correlation(events, [events[-1]])
check('correlation found', len(corr['correlations']) >= 1)
pat = RootCauseAnalysis.pattern_analysis(events + events, window=6)
check('patterns found', len(pat['patterns']) >= 1)

# ======================================================================
print('\n=== 7. Drift Detection ===')
history = [{'success_rate': 0.9}] * 8 + [{'success_rate': 0.6}] * 4
drift = DriftDetector.detect(history, 'success_rate', window=10, threshold_pct=20)
check('drift detected', drift.get('drifted', False), f"drift={drift}")
baseline_m = {'success_rate': 0.9, 'failure_rate': 0.1}
current_m = {'success_rate': 0.7, 'failure_rate': 0.3}
drifts = DriftDetector.detect_all(baseline_m, current_m, threshold_pct=5)
check('detect_all finds drifts', len(drifts) >= 1)

# ======================================================================
print('\n=== 8. Metric Gaming Detection ===')
normal = [{'val': 0.5 + i*0.01} for i in range(10)]
gaming = MetricGamingDetector.detect_gaming(normal, 'val')
check('normal data not gaming', not gaming['gaming_detected'])
oscillating = [{'val': 0.5 if i%2==0 else 0.9} for i in range(10)]
gaming2 = MetricGamingDetector.detect_gaming(oscillating, 'val')
check('oscillation detected', gaming2['gaming_detected'], f"signals={gaming2.get('signals')}")
dep = MetricGamingDetector.check_metric_independence(
    {'success_rate': 1.0, 'avg_tool_calls': 0.5}, {})
check('tool avoidance detected', not dep['independent'])

# ======================================================================
print('\n=== 9. Improvement Candidates ===')
ie = ImprovementEngine()
c1 = ie.propose('High failure rate in file missions',
                'Planner lacks filesystem precondition check',
                'Add filesystem existence check before file operations',
                source='mission_loop', risk_level='MEDIUM',
                affected_components=['mission_planner'])
check('candidate proposed', c1.candidate_id.startswith('imp_'))
check('priority computed', c1.priority_score > 0, f"prio={c1.priority_score}")
c2 = ie.propose('High failure rate in file missions',
                'Planner lacks filesystem precondition check',
                'Add filesystem existence check before file operations',
                source='mission_loop', risk_level='MEDIUM',
                affected_components=['mission_planner'])
dupes = ie.find_duplicates(c2)
check('duplicate detected', len(dupes) >= 1, f"dupes={dupes}")

# ======================================================================
print('\n=== 10. Improvement Queue (Prioritization) ===')
c3 = ie.propose('Security prompt injection detected',
                'Input sanitization insufficient',
                'Add prompt injection filter',
                source='security', risk_level='HIGH',
                affected_components=['security_engine'])
ie.prioritize()
candidates = ie.get_candidates(status='PRIORITIZED')
check('prioritized', len(candidates) >= 1)
check('security first', any('Security' in c.problem for c in candidates))

# ======================================================================
print('\n=== 11. Experiment Lifecycle ===')
exp = ie.create_experiment(c1.candidate_id, baseline={'success_rate': 0.7},
                           sample_size=5, duration_s=60)
check('experiment created', exp is not None and exp.status == 'CREATED')
ok = ie.start_experiment(exp.experiment_id)
check('experiment started', ok)
result = ExperimentResult(exp.experiment_id)
result.baseline_metrics = {'success_rate': 0.7, 'failure_rate': 0.3}
result.candidate_metrics = {'success_rate': 0.85, 'failure_rate': 0.15}
result.delta = {'success_rate': 0.15, 'failure_rate': -0.15}
result.confidence = 0.8
result.decision = 'SUCCESS'
result.regressions = []
result.security_result = 'PASS'
ok2 = ie.complete_experiment(exp.experiment_id, result)
check('experiment completed', ok2)
check('candidate moved to VALIDATING', ie._candidates[c1.candidate_id].status == 'VALIDATING')

# ======================================================================
print('\n=== 12. Safety Gate ===')
gate = ie.evaluate_safety(c1.candidate_id, result, improvement_level=2)
check('safety gate PASS', gate['gate_result'] == 'PASS', f"gate={gate['gate_result']}")
check('checks all passed', all(c['passed'] for c in gate['checks']))

# ======================================================================
print('\n=== 13. Accept / Reject ===')
ok = ie.accept(c1.candidate_id, reason='Experiment succeeded')
check('accept OK', ok)
check('status ACCEPTED', ie._candidates[c1.candidate_id].status == 'ACCEPTED')
ok2 = ie.reject(c2.candidate_id, reason='Duplicate of c1')
check('reject OK', ok2)

# ======================================================================
print('\n=== 14. Rollback ===')
rb = ie.rollback(c1.candidate_id, reason='Regression detected', trigger='automatic')
check('rollback success', rb['success'])
check('status ROLLED_BACK', ie._candidates[c1.candidate_id].status == 'ROLLED_BACK')
check('flag disabled', ie.get_feature_flag(f"improvement.{c1.candidate_id}") == False)

# ======================================================================
print('\n=== 15. Feature Flags ===')
ie.enable_improvement('test_feature')
check('flag enabled', ie.get_feature_flag('improvement.test_feature') == True)
ie.disable_improvement('test_feature')
check('flag disabled', ie.get_feature_flag('improvement.test_feature') == False)

# ======================================================================
print('\n=== 16. Shadow Mode ===')
shadow = ie.run_shadow('test_cand', 'output_A', 'output_B')
check('shadow runs', shadow['mode'] == 'shadow')
check('shadow does not control production', not shadow['candidate_controls_production'])

# ======================================================================
print('\n=== 17. Regression Detection ===')
regressions = RegressionDetector.detect(
    {'success_rate': 0.9, 'failure_rate': 0.1},
    {'success_rate': 0.7, 'failure_rate': 0.3})
check('regression detected', len(regressions) >= 1)
check('severity HIGH or CRITICAL', regressions[0]['severity'] in ('HIGH', 'CRITICAL'))

# ======================================================================
print('\n=== 18. Failure → Test ===')
proposal = ie.propose_regression_test(
    {'error': 'filesystem not found', 'step': '2'},
    root_cause='DEPENDENCY',
    test_description='Verify filesystem existence before file operations')
check('regression test proposed', proposal['status'] == 'PROPOSED')

# ======================================================================
print('\n=== 19. Decision Records ===')
check('decision records exist', len(ie._decision_records) >= 3)
last_dec = ie._decision_records[-1]
check('decision has fields', 'decision' in last_dec and 'reason' in last_dec)

# ======================================================================
print('\n=== 20. Journal ===')
check('journal entries', len(ie._improvement_journal) >= 5)
events = [j['event'] for j in ie._improvement_journal]
check('journal has PROPOSED', 'PROPOSED' in events)
check('journal has ROLLBACK', 'ROLLBACK' in events)

# ======================================================================
print('\n=== 21. Reports ===')
sae_report = sae3.generate_report()
check('assessment report has metrics', 'metrics' in sae_report)
check('assessment report has scorecard', 'scorecard' in sae_report)
ie_report = ie.generate_report()
check('improvement report has candidates', 'total_candidates' in ie_report)
check('improvement report has journal', 'journal_entries' in ie_report)

# ======================================================================
print('\n=== 22. Self-Critique ===')
critique = sae3.self_critique(r1)
check('critique has what_went_well', len(critique['what_went_well']) > 0)
check('critique has note', 'note' in critique)

# ======================================================================
print('\n=== 23. Improvement Level ===')
sae4 = SelfAssessmentEngine()
ok = sae4.set_improvement_level(2)
check('level set', ok)
check('level stored', sae4.get_improvement_level() == 2)
ok2 = sae4.set_improvement_level(10)
check('level 10 rejected', not ok2)

# ======================================================================
print('\n=== 24. Conflicting Improvements ===')
c4 = ie.propose('Increase cache size',
                'More caching improves performance',
                'Increase cache from 100 to 1000 entries',
                affected_components=['cache'])
c5 = ie.propose('Reduce memory usage',
                'Smaller cache reduces memory',
                'Decrease cache from 100 to 50 entries',
                affected_components=['cache'])
conflicts = ie.find_conflicts(c4)
check('conflict found', len(conflicts) >= 1, f"conflicts={conflicts}")

# ======================================================================
print('\n=== 25. Metric Gaming Protection (adversarial) ===')
# Simulate: candidate tries to inflate success_rate by reducing total missions
dep2 = MetricGamingDetector.check_metric_independence(
    {'success_rate': 1.0, 'avg_tool_calls': 0.3, 'avg_duration': 0.05},
    {})
check('gaming signals detected', len(dep2['warnings']) >= 1)

# ======================================================================
print('\n=== 26. Metric Gaming Detection (oscillation) ===')
osc = [{'val': 0.5 + (0.4 if i%2 else -0.4)} for i in range(8)]
g = MetricGamingDetector.detect_gaming(osc, 'val')
check('oscillation detected as gaming', g['gaming_detected'])

# ======================================================================
print('\n=== 27. Stop Conditions (incomplete experiment) ===')
exp2 = ie.create_experiment(c3.candidate_id, baseline={}, sample_size=2, duration_s=10)
check('incomplete experiment created', exp2 is not None)
result_inconclusive = ExperimentResult(exp2.experiment_id)
result_inconclusive.decision = 'INCONCLUSIVE'
result_inconclusive.confidence = 0.3
result_inconclusive.regressions = []
result_inconclusive.security_result = 'PASS'
ie.complete_experiment(exp2.experiment_id, result_inconclusive)
gate2 = ie.evaluate_safety(c3.candidate_id, result_inconclusive, improvement_level=2)
check('inconclusive → BLOCK', gate2['gate_result'] == 'BLOCK')

# ======================================================================
print('\n=== 28. Mission Loop Integration ===')
sae_m = SelfAssessmentEngine()
# Simulate real mission results
for i in range(3):
    sae_m.record_mission_result({
        'mission_id': f'ml_{i}', 'status': 'completed',
        'completed_steps': 4, 'total_steps': 4,
        'duration_s': 25 + i*5, 'tool_calls': 8, 'replans': 0
    })
asmt_m = sae_m.run_assessment(trigger='per_mission')
check('mission integration: assessment works', asmt_m.assessment_id is not None)
check('mission integration: has success_rate', 'success_rate' in asmt_m.metrics)

# ======================================================================
print(f'\n==== RESULTADO: {passed} passaram, {failed} falharam ====')
sys.exit(1 if failed else 0)
