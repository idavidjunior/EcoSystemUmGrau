import json
import os
from datetime import datetime


class SuccessEvaluator:
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.SUCCESS_THRESHOLD = 95

    def evaluate(self, goal_analysis, progress, test_results=None, execution_log=None):
        self.session.log("Evaluating overall success...")
        scores = {}

        scores["requirements_met"] = self._score_requirements(goal_analysis, progress)
        scores["code_functional"] = self._score_functionality(progress, execution_log)
        scores["tests_passed"] = self._score_tests(test_results)
        scores["execution_quality"] = self._score_execution_quality(progress)

        total = (
            scores["requirements_met"] * 0.40 +
            scores["code_functional"] * 0.30 +
            scores["tests_passed"] * 0.20 +
            scores["execution_quality"] * 0.10
        )

        evaluation = {
            "total_score": round(total, 1),
            "threshold": self.SUCCESS_THRESHOLD,
            "passed": total >= self.SUCCESS_THRESHOLD,
            "breakdown": scores,
            "missing_requirements": [],
            "recommendations": [],
            "evaluated_at": datetime.now().isoformat(),
        }

        if scores["requirements_met"] < 80:
            evaluation["recommendations"].append("Revisar requisitos nao atendidos")
        if scores["tests_passed"] < 70:
            evaluation["recommendations"].append("Aumentar cobertura de testes")
        if scores["code_functional"] < 70:
            evaluation["recommendations"].append("Corrigir problemas de funcionalidade")

        self.session.record_decision(
            f"Success evaluation: {evaluation['total_score']}% "
            f"({'PASSED' if evaluation['passed'] else 'BELOW THRESHOLD'})"
        )
        return evaluation

    def _score_requirements(self, analysis, progress):
        requirements = analysis.get("requirements", [])
        if not requirements:
            return 100

        completed = len(progress.get("completed_steps", []))
        total = max(len(progress.get("steps", [])), 1)
        ratio = completed / total
        return min(100, ratio * 100)

    def _score_functionality(self, progress, execution_log):
        completed = len(progress.get("completed_steps", []))
        failed = len(progress.get("failed_steps", []))
        total = max(len(progress.get("steps", [])), 1)

        if total == 0:
            return 0

        success_rate = completed / total
        penalty = failed * 10
        return max(0, min(100, success_rate * 100 - penalty))

    def _score_tests(self, test_results):
        if not test_results:
            return 50

        passed = test_results.get("passed", 0)
        total = test_results.get("total", 1)
        if total == 0:
            return 50
        return min(100, (passed / total) * 100)

    def _score_execution_quality(self, progress):
        failed = len(progress.get("failed_steps", []))
        completed = len(progress.get("completed_steps", []))
        total = max(len(progress.get("steps", [])), 1)

        base = 80
        penalty = failed * 15

        if completed == 0 and failed == 0:
            return 0

        if completed == total:
            base = 100
        elif completed > 0:
            base = 60 + (completed / total) * 40

        return max(0, min(100, base - penalty))
