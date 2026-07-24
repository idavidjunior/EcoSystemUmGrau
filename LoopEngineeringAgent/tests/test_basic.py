#!/usr/bin/env python3
"""Unit tests for Loop Engineering Agent v1.1 components."""

import os
import sys
import json
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

class TestState(unittest.TestCase):
    def test_new_states_exist(self):
        from core.state import AgentState
        self.assertTrue(hasattr(AgentState, 'ANALYZING_GOAL'))
        self.assertTrue(hasattr(AgentState, 'CREATING_STRATEGY'))
        self.assertTrue(hasattr(AgentState, 'LEARNING'))
        self.assertTrue(hasattr(AgentState, 'REPLANNING'))
        self.assertTrue(hasattr(AgentState, 'SUCCESS_EVALUATING'))
        self.assertTrue(hasattr(AgentState, 'FINAL_AUDITING'))
        self.assertTrue(hasattr(AgentState, 'SUCCESS_VERIFIED'))

    def test_adaptive_transitions(self):
        from core.state import AgentState
        s = AgentState()
        self.assertTrue(s.transition(AgentState.INIT))
        self.assertTrue(s.transition(AgentState.ANALYZING_GOAL))
        self.assertTrue(s.transition(AgentState.CREATING_STRATEGY))
        self.assertTrue(s.transition(AgentState.PLANNING))
        self.assertTrue(s.transition(AgentState.EXECUTING))
        self.assertTrue(s.transition(AgentState.VALIDATING))
        self.assertTrue(s.transition(AgentState.SUCCESS_EVALUATING))
        self.assertTrue(s.transition(AgentState.FINAL_AUDITING))
        self.assertTrue(s.transition(AgentState.SUCCESS_VERIFIED))
        self.assertTrue(s.transition(AgentState.COMPLETED))
        self.assertTrue(s.transition(AgentState.IDLE))

    def test_state_history(self):
        from core.state import AgentState
        s = AgentState()
        for st in [AgentState.INIT, AgentState.ANALYZING_GOAL, AgentState.CREATING_STRATEGY]:
            self.assertTrue(s.transition(st))
        self.assertEqual(len(s.history), 3)

class TestGoalAnalyzer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_analyze_creation(self):
        from agent.goal_analyzer import GoalAnalyzer
        ga = GoalAnalyzer(self.session, {})
        a = ga.analyze("Create an Android Bible app with PDF import")
        self.assertEqual(a["task_type"], "creation")
        self.assertIn("android", a["domain"])
        self.assertIn("android", a["technologies"])
        self.assertGreater(a["complexity"], 3)
        self.assertTrue(len(a["success_criteria"]) > 0)

    def test_analyze_fix(self):
        from agent.goal_analyzer import GoalAnalyzer
        ga = GoalAnalyzer(self.session, {})
        a = ga.analyze("Fix the login bug in the authentication module")
        self.assertEqual(a["task_type"], "fix")

    def test_analyze_extracts_requirements(self):
        from agent.goal_analyzer import GoalAnalyzer
        ga = GoalAnalyzer(self.session, {})
        a = ga.analyze("Need a calculator with:\n- Addition\n- Subtraction\n- Multiplication")
        self.assertTrue(len(a["requirements"]) > 0)

class TestStrategyEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generates_multiple_strategies(self):
        from agent.strategy_engine import StrategyEngine
        se = StrategyEngine(self.session, {})
        analysis = {"task_type": "creation", "domain": "android", "complexity": 5,
                    "technologies": ["android"]}
        strategies = se.generate_strategies(analysis)
        self.assertGreaterEqual(len(strategies), 2)

    def test_selects_best(self):
        from agent.strategy_engine import StrategyEngine
        se = StrategyEngine(self.session, {})
        analysis = {"task_type": "creation", "domain": "general", "complexity": 3,
                    "technologies": ["python"]}
        strategies = se.generate_strategies(analysis)
        best = se.select_best(analysis)
        self.assertIsNotNone(best)
        self.assertEqual(best["rank"], 1)

class TestLearningEngine(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_learn_from_error(self):
        from agent.learning_engine import LearningEngine
        le = LearningEngine(None, self.tmpdir)
        le.initialize()
        le.learn_from_error("File not found", "Reading config", {"action": "load"})
        rules_file = os.path.join(self.tmpdir, "memory", "learned_rules.json")
        self.assertTrue(os.path.exists(rules_file))
        with open(rules_file) as f:
            data = json.load(f)
        self.assertEqual(len(data["rules"]), 1)

    def test_learn_from_success(self):
        from agent.learning_engine import LearningEngine
        le = LearningEngine(None, self.tmpdir)
        le.initialize()
        le.learn_from_success({"action": "test", "description": "Running tests"}, {"duration": 1.5})
        success_file = os.path.join(self.tmpdir, "memory", "successful_patterns.json")
        self.assertTrue(os.path.exists(success_file))

    def test_get_statistics(self):
        from agent.learning_engine import LearningEngine
        le = LearningEngine(None, self.tmpdir)
        le.initialize()
        stats = le.get_statistics()
        self.assertIn("total_learned_rules", stats)
        self.assertIn("success_rate", stats)

class TestRiskManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_assess_risks(self):
        from agent.risk_manager import RiskManager
        rm = RiskManager(self.session, {})
        analysis = {"task_type": "creation", "domain": "android", "complexity": 8,
                    "technologies": ["android"], "requirements": ["Import PDF"]}
        assessment = rm.assess(analysis)
        self.assertIn("risks", assessment)
        self.assertIn("can_proceed", assessment)
        self.assertGreater(assessment["total_risks"], 0)

class TestSuccessEvaluator(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_evaluate_success(self):
        from agent.success_evaluator import SuccessEvaluator
        se = SuccessEvaluator(self.session, {})
        analysis = {"domain": "python", "task_type": "creation", "complexity": 3,
                    "technologies": ["python"], "requirements": ["Create file"]}
        progress = {"steps": [{"id": 1}, {"id": 2}], "completed_steps": [1, 2],
                    "failed_steps": [], "current_step": 2}
        eval_result = se.evaluate(analysis, progress)
        self.assertIn("total_score", eval_result)
        self.assertIn("passed", eval_result)
        self.assertIn("breakdown", eval_result)

class TestFinalAuditor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_audit_checklist(self):
        from agent.final_auditor import FinalAuditor
        fa = FinalAuditor(self.session, self.tmpdir)
        analysis = {"domain": "python", "task_type": "creation",
                    "requirements": ["Test"], "technologies": ["python"],
                    "success_criteria": ["Works"]}
        progress = {"steps": [{"id": 1, "action": "test"}], "completed_steps": [1],
                    "failed_steps": [], "current_step": 1}
        audit = fa.audit(analysis, progress)
        self.assertIn("checklist", audit)
        self.assertIn("all_checked", audit)

    def test_generate_report(self):
        from agent.final_auditor import FinalAuditor
        fa = FinalAuditor(self.session, self.tmpdir)
        report = fa.generate_final_report()
        self.assertTrue("Loop Engineering" in report or "Loop Engineering Runtime" in report)

class TestOpenCodeBridge(unittest.TestCase):
    def test_bridge_imports(self):
        try:
            from integrations.opencode.opencode_bridge import OpenCodeBridge
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Bridge import failed: {e}")

def run_all():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for tc in [TestState, TestGoalAnalyzer, TestStrategyEngine,
               TestLearningEngine, TestRiskManager, TestSuccessEvaluator,
               TestFinalAuditor, TestOpenCodeBridge]:
        suite.addTests(loader.loadTestsFromTestCase(tc))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
