#!/usr/bin/env python3
"""Tests for LER v2.0: GoalSpecification, Strategy Ranking, Risk, Learning,
Evidence, ToolSelector, SelfImprovement, Supervisor, Goal Oriented Loop."""

import os
import sys
import json
import tempfile
import unittest
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


class TestGoalAnalyzerV2(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_goal_spec_has_all_fields(self):
        from agent.goal_analyzer import GoalAnalyzer
        ga = GoalAnalyzer(self.session, {})
        analysis = ga.analyze("Create an Android app")
        spec = analysis.get("goal_spec", {})
        self.assertIn("objective", spec)
        self.assertIn("requirements", spec)
        self.assertIn("constraints", spec)
        self.assertIn("dependencies", spec)
        self.assertIn("assumptions", spec)
        self.assertIn("acceptance_criteria", spec)
        self.assertIn("definition_of_done", spec)
        self.assertIn("risks", spec)

    def test_definition_of_done_generated(self):
        from agent.goal_analyzer import GoalAnalyzer
        ga = GoalAnalyzer(self.session, {})
        analysis = ga.analyze("Fix login bug")
        dod = analysis.get("definition_of_done", [])
        self.assertGreater(len(dod), 3)

    def test_acceptance_criteria_generated(self):
        from agent.goal_analyzer import GoalAnalyzer
        ga = GoalAnalyzer(self.session, {})
        analysis = ga.analyze("Create a test file")
        ac = analysis.get("acceptance_criteria", [])
        self.assertGreater(len(ac), 1)

    def test_risks_identified(self):
        from agent.goal_analyzer import GoalAnalyzer
        ga = GoalAnalyzer(self.session, {})
        analysis = ga.analyze("Create Android app with API integration")
        risks = analysis.get("risks", [])
        self.assertGreater(len(risks), 0)

    def test_assumptions_extracted(self):
        from agent.goal_analyzer import GoalAnalyzer
        ga = GoalAnalyzer(self.session, {})
        analysis = ga.analyze("Create Python script")
        assumptions = analysis.get("assumptions", [])
        self.assertGreater(len(assumptions), 0)

    def test_constraints_detected(self):
        from agent.goal_analyzer import GoalAnalyzer
        ga = GoalAnalyzer(self.session, {})
        analysis = ga.analyze("Create Windows app with no git")
        constraints = analysis.get("constraints", [])
        self.assertTrue(any("Windows" in c for c in constraints))


class TestStrategyEngineV2(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generates_three_or_more_strategies(self):
        from agent.strategy_engine import StrategyEngine
        se = StrategyEngine(self.session, {})
        strategies = se.generate_strategies({
            "task_type": "creation", "domain": "python",
            "complexity": 5, "technologies": ["python"],
            "requirements": ["req1"], "dependencies": ["dep1"],
        })
        self.assertGreaterEqual(len(strategies), 3)

    def test_strategies_have_cost_risk_time_complexity(self):
        from agent.strategy_engine import StrategyEngine
        se = StrategyEngine(self.session, {})
        strategies = se.generate_strategies({
            "task_type": "creation", "domain": "general",
            "complexity": 5, "technologies": ["unknown"],
            "requirements": [], "dependencies": [],
        })
        for s in strategies:
            self.assertIn("cost", s)
            self.assertIn("risk", s)
            self.assertIn("estimated_time", s)
            self.assertIn("complexity", s)
            self.assertIn("success_probability", s)

    def test_ranking_selects_best(self):
        from agent.strategy_engine import StrategyEngine
        se = StrategyEngine(self.session, {})
        analysis = {"task_type": "creation", "domain": "general",
                    "complexity": 3, "technologies": ["python"],
                    "requirements": [], "dependencies": []}
        se.generate_strategies(analysis)
        best = se.select_best(analysis)
        self.assertIsNotNone(best)
        self.assertIn("score", best)

    def test_failed_strategies_not_repeated(self):
        from agent.strategy_engine import StrategyEngine
        se = StrategyEngine(self.session, {})
        analysis = {"task_type": "creation", "domain": "general",
                    "complexity": 3, "technologies": ["python"],
                    "requirements": [], "dependencies": []}
        se.generate_strategies(analysis)
        best = se.select_best(analysis)
        se.mark_failed(best["id"])
        next_best = se.select_next_best(analysis)
        self.assertIsNotNone(next_best)
        self.assertNotEqual(next_best["id"], best["id"])


class TestRiskManagerV2(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_technical_external_api_permission_risks(self):
        from agent.risk_manager import RiskManager
        rm = RiskManager(self.session, {})
        assessment = rm.assess({
            "raw": "Create app with API",
            "complexity": 5, "domain": "web",
            "technologies": ["python", "javascript"],
            "requirements": [], "dependencies": ["Node.js"],
        })
        categories = {r["category"] for r in assessment["risks"]}
        self.assertIn("api", categories)
        self.assertIn("dependency", categories)
        self.assertIn("permission", categories)

    def test_mitigation_plan_for_each_risk(self):
        from agent.risk_manager import RiskManager
        rm = RiskManager(self.session, {})
        assessment = rm.assess({
            "raw": "Create app",
            "complexity": 3, "domain": "general",
            "technologies": ["unknown"],
            "requirements": [], "dependencies": [],
        })
        for risk in assessment["risks"]:
            self.assertIn("mitigation_plan", risk)
            self.assertIn("contingency", risk)

    def test_contingency_plans_present(self):
        from agent.risk_manager import RiskManager
        rm = RiskManager(self.session, {})
        assessment = rm.assess({
            "raw": "Create app",
            "complexity": 3, "domain": "general",
            "technologies": ["unknown"],
            "requirements": [], "dependencies": [],
        })
        for risk in assessment["risks"]:
            self.assertIn("contingency", risk)


class TestLearningEngineV2(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_tool_statistics_tracked(self):
        from agent.tool_selector import ToolSelector
        ts = ToolSelector(self.session, self.tmpdir)
        ts.record_result("python", True, 1.5, 0)
        ts.record_result("python", True, 2.0, 0)
        ts.record_result("git", False, 3.0, 0)
        report = ts.get_tool_report()
        self.assertIn("python", report)
        self.assertIn("git", report)
        self.assertEqual(report["python"]["total_calls"], 2)
        self.assertEqual(report["git"]["total_calls"], 1)
        self.assertLess(report["git"]["success_rate"], 100)

    def test_learn_from_mission(self):
        from agent.learning_engine import LearningEngine
        le = LearningEngine(self.session, self.tmpdir)
        le.initialize()
        le.learn_from_mission({
            "status": "completed", "iterations": 10,
            "steps": {"completed": 5, "total": 5},
            "elapsed_seconds": 30, "domain": "python", "complexity": 5,
        })
        knowledge = le.get_knowledge_for_domain("python")
        self.assertEqual(len(knowledge), 1)

    def test_architecture_patterns(self):
        from agent.learning_engine import LearningEngine
        le = LearningEngine(self.session, self.tmpdir)
        le.initialize()
        le.learn_architecture_pattern("mvp", "Model-View-Presenter", {"layers": 3})
        stats = le.get_statistics()
        self.assertGreaterEqual(stats["total_arch_patterns"], 1)

    def test_get_statistics_includes_tools_and_arch(self):
        from agent.learning_engine import LearningEngine
        le = LearningEngine(self.session, self.tmpdir)
        le.initialize()
        stats = le.get_statistics()
        self.assertIn("total_tools_tracked", stats)
        self.assertIn("total_arch_patterns", stats)
        self.assertIn("total_prev_missions", stats)


class TestSuccessEvaluatorV2(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_weighted_scoring_six_categories(self):
        from agent.success_evaluator import SuccessEvaluator
        se = SuccessEvaluator(self.session, {"mission": {"success_threshold": 95}})
        eval_result = se.evaluate(
            {"requirements": ["req1"], "acceptance_criteria": ["crit1"]},
            {"steps": [{"id": 1}], "completed_steps": [1], "failed_steps": []},
            test_results={"passed": 5, "total": 5},
            evidence={"collected": 3, "total": 3},
            audit_result={"checklist": [{"checked": True}, {"checked": True}]},
        )
        self.assertIn("total_score", eval_result)
        self.assertIn("breakdown", eval_result)
        breakdown = eval_result["breakdown"]
        self.assertIn("requirements_met", breakdown)
        self.assertIn("code_functional", breakdown)
        self.assertIn("tests_passed", breakdown)
        self.assertIn("execution_quality", breakdown)
        self.assertIn("evidence_quality", breakdown)
        self.assertIn("audit_quality", breakdown)

    def test_high_score_passes_with_all_categories(self):
        from agent.success_evaluator import SuccessEvaluator
        se = SuccessEvaluator(self.session, {"mission": {"success_threshold": 50}})
        eval_result = se.evaluate(
            {"requirements": ["req1"], "acceptance_criteria": ["crit1"]},
            {"steps": [{"id": 1}], "completed_steps": [1], "failed_steps": []},
            test_results={"passed": 5, "total": 5},
            evidence={"collected": 5, "total": 5},
            audit_result={"checklist": [{"checked": True}] * 5},
        )
        self.assertTrue(eval_result["passed"])


class TestEvidenceCollector(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_collect_log_and_file(self):
        from agent.evidence_collector import EvidenceCollector
        from core.session import Session
        ec = EvidenceCollector(Session(self.tmpdir), self.tmpdir)
        ec.start_mission("test_001")
        test_file = os.path.join(self.tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        ec.collect_file(test_file, "artifact")
        ec.collect_test_result("test_1.py", True, "OK")
        ec.finish_mission()
        summary = ec.get_summary()
        self.assertGreaterEqual(summary["files"], 1)
        self.assertGreaterEqual(summary["tests"], 1)
        self.assertGreaterEqual(summary["hashes"], 1)

    def test_generates_json_and_md(self):
        from agent.evidence_collector import EvidenceCollector
        from core.session import Session
        ec = EvidenceCollector(Session(self.tmpdir), self.tmpdir)
        ec.start_mission("test_002")
        test_file = os.path.join(self.tmpdir, "data.txt")
        with open(test_file, "w") as f:
            f.write("data")
        ec.collect_file(test_file, "artifact")
        ec.finish_mission()
        ec.generate_report()
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "reports", "evidence.json")))
        self.assertTrue(os.path.exists(os.path.join(self.tmpdir, "reports", "evidence.md")))


class TestToolSelector(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_selects_correct_tool_for_task(self):
        from agent.tool_selector import ToolSelector
        ts = ToolSelector(self.session, self.tmpdir)
        sel = ts.select_tool("git")
        self.assertEqual(sel["tool"], "git")
        sel = ts.select_tool("testing")
        self.assertEqual(sel["tool"], "python")
        sel = ts.select_tool("programming")
        self.assertEqual(sel["tool"], "opencode")

    def test_records_and_reports_stats(self):
        from agent.tool_selector import ToolSelector
        ts = ToolSelector(self.session, self.tmpdir)
        ts.record_result("python", True, 1.5, 0)
        ts.record_result("python", False, 2.0, 0)
        ts.record_result("git", True, 3.0, 0)
        report = ts.get_tool_report()
        self.assertIn("python", report)
        self.assertIn("git", report)

    def test_selects_alternative_on_low_success_rate(self):
        from agent.tool_selector import ToolSelector
        ts = ToolSelector(self.session, self.tmpdir)
        for _ in range(10):
            ts.record_result("nvidia", False, 5.0, 0)
        sel = ts.select_tool("llm")
        self.assertNotEqual(sel["tool"], "nvidia")


class TestSelfImprovement(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_detects_bottlenecks(self):
        from agent.self_improvement import SelfImprovement
        si = SelfImprovement(self.session, self.tmpdir)
        report = si.evaluate_mission({
            "mission_id": "test_001",
            "status": "completed",
            "iterations": 30,
            "elapsed_seconds": 200,
            "steps": {"completed": 5, "failed": 3, "total": 8},
        })
        self.assertIn("findings", report)
        self.assertIn("improvement_suggestions", report)

    def test_detects_recurring_failures(self):
        from agent.self_improvement import SelfImprovement
        si = SelfImprovement(self.session, self.tmpdir)
        os.makedirs(os.path.join(self.tmpdir, "memory"), exist_ok=True)
        with open(os.path.join(self.tmpdir, "memory", "learned_rules.json"), "w") as f:
            json.dump({
                "rules": [
                    {"error_key": "timeout", "count": 5, "applied_successfully": False,
                     "suggested_fix": "Increase timeout"}
                ]
            }, f)
        report = si.evaluate_mission({
            "mission_id": "test_002",
            "iterations": 10,
            "elapsed_seconds": 50,
            "steps": {"completed": 5, "failed": 1, "total": 6},
        })
        types = [f["type"] for f in report["findings"]]
        self.assertIn("recurring_failure", types)


class TestSupervisor(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_register_and_monitor(self):
        from agent.supervisor import Supervisor
        sv = Supervisor(self.session, {})
        mock = type('MockModule', (), {'get_statistics': lambda self: {"ok": True}})()
        sv.register_module("test", mock)
        results = sv.monitor_all()
        self.assertIn("test", results)
        self.assertEqual(results["test"]["status"], "healthy")

    def test_health_report(self):
        from agent.supervisor import Supervisor
        sv = Supervisor(self.session, {})
        mock = type('MockModule', (), {'get_statistics': lambda self: {"ok": True}})()
        sv.register_module("test", mock)
        sv.monitor_all()
        report = sv.get_health_report()
        self.assertEqual(report["total_modules"], 1)
        self.assertEqual(report["healthy"], 1)


class TestPlannerWithDoD(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_creates_plan_with_steps(self):
        from agent.planner import Planner
        p = Planner(self.session, {})
        steps = p.create_plan("Create a test file")
        self.assertGreater(len(steps), 0)
        for s in steps:
            self.assertIn("id", s)
            self.assertIn("action", s)
            self.assertIn("status", s)


class TestFinalAuditorV2(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_audit_with_dod_and_ac(self):
        from agent.final_auditor import FinalAuditor
        fa = FinalAuditor(self.session, self.tmpdir)
        audit = fa.audit(
            {"requirements": ["req1"], "definition_of_done": ["item1", "item2"],
             "acceptance_criteria": ["crit1"]},
            {"steps": [{"id": 1}], "completed_steps": [1], "failed_steps": []},
            evidence={"collected": 1, "total": 1},
        )
        self.assertIn("definition_of_done", audit)
        self.assertIn("acceptance_criteria", audit)
        self.assertIn("dod_satisfied", audit)

    def test_generate_final_report_expanded(self):
        from agent.final_auditor import FinalAuditor
        fa = FinalAuditor(self.session, self.tmpdir)
        report = fa.generate_final_report(
            goal_analysis={"objective": "Test", "definition_of_done": ["d1"],
                          "acceptance_criteria": ["a1"], "requirements": ["r1"]},
            progress={"steps": [{"id": 1, "action": "test", "description": "test step"}],
                     "completed_steps": [1], "failed_steps": []},
            strategy={"name": "Direct", "score": 90, "risk": "low", "success_probability": 95,
                     "cost": "medium", "approach": "Direct approach"},
            success_evaluation={"total_score": 95, "threshold": 95, "passed": True,
                              "breakdown": {"requirements_met": 100, "code_functional": 100},
                              "recommendations": []},
            audit_result={"all_checked": True, "checklist": [{"item": "Test", "checked": True}]},
            evidence={"collected": 5, "logs": 2, "files": 1, "tests": 1, "artifacts": 1,
                     "hashes": 1, "decisions": 1},
            risk_assessment={"risks": [{"category": "technical", "description": "Test risk",
                                       "mitigation_plan": "Mitigate", "contingency": "Fallback"}]},
        )
        self.assertIn("v2.0", report)
        self.assertIn("Definition of Done", report)
        self.assertIn("Acceptance Criteria", report)
        self.assertIn("Score de Sucesso", report)
        self.assertIn("Justificativa do Encerramento", report)


def run_all():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for tc in [TestGoalAnalyzerV2, TestStrategyEngineV2, TestRiskManagerV2,
               TestLearningEngineV2, TestSuccessEvaluatorV2, TestEvidenceCollector,
               TestToolSelector, TestSelfImprovement, TestSupervisor,
               TestPlannerWithDoD, TestFinalAuditorV2]:
        suite.addTests(loader.loadTestsFromTestCase(tc))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
