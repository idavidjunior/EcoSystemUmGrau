import json
import os
from datetime import datetime


class SuccessEvaluator:
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.SUCCESS_THRESHOLD = config.get("mission", {}).get("success_threshold", 95)

    def evaluate(self, goal_analysis, progress, test_results=None, execution_log=None,
                 evidence=None, audit_result=None):
        self.session.log("Evaluating overall success...")
        scores = {}

        scores["requirements_met"] = self._score_requirements(goal_analysis, progress)
        scores["code_functional"] = self._score_functionality(progress, execution_log)
        scores["tests_passed"] = self._score_tests(test_results)
        scores["execution_quality"] = self._score_execution_quality(progress)
        scores["evidence_quality"] = self._score_evidence(evidence)
        scores["audit_quality"] = self._score_audit(audit_result)
        scores["dod_satisfaction"] = self._score_dod(goal_analysis, progress)

        total = (
            scores["requirements_met"] * 0.30 +
            scores["dod_satisfaction"] * 0.10 +
            scores["code_functional"] * 0.30 +
            scores["tests_passed"] * 0.10 +
            scores["execution_quality"] * 0.05 +
            scores["evidence_quality"] * 0.05 +
            scores["audit_quality"] * 0.10
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

        for category, score in scores.items():
            label = category.replace("_", " ").title()
            if score < 80:
                evaluation["recommendations"].append(
                    f"Melhorar {label} (atual: {score}%, desejado: 80%+)"
                )

        self.session.record_decision(
            f"Success evaluation: {evaluation['total_score']}% "
            f"({'PASSED' if evaluation['passed'] else 'BELOW THRESHOLD'}) "
            f"(threshold: {self.SUCCESS_THRESHOLD}%)"
        )
        return evaluation

    def _score_requirements(self, analysis, progress):
        requirements = analysis.get("requirements", [])
        if not requirements:
            return 100
        completed = len(progress.get("completed_steps", []))
        total = max(len(progress.get("steps", [])), 1)
        ratio = completed / total
        acceptance = analysis.get("acceptance_criteria", [])
        criteria_bonus = min(10, len(acceptance) * 2) if acceptance else 0
        return min(100, ratio * 100 + criteria_bonus)

    def _score_functionality(self, progress, execution_log):
        completed = len(progress.get("completed_steps", []))
        failed = len(progress.get("failed_steps", []))
        total = max(len(progress.get("steps", [])), 1)
        if total == 0:
            return 0
        success_rate = completed / total
        penalty = failed * 10
        if execution_log:
            if "erro" in str(execution_log).lower() or "error" in str(execution_log).lower():
                penalty += 5
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
        if completed == total:
            base = 100
        elif completed > 0:
            base = 60 + (completed / total) * 40
        return max(0, min(100, base - penalty))

    def _score_evidence(self, evidence):
        if not evidence:
            return 0
        collected = evidence.get("collected", 0)
        total = max(evidence.get("total", 1), 1)
        return min(100, (collected / total) * 100)

    def _score_dod(self, analysis, progress):
        dod = analysis.get("definition_of_done", []) if analysis else []
        if not dod:
            return 100
        completed = len(progress.get("completed_steps", []))
        total = max(len(progress.get("steps", [])), 1)
        steps_ok = min(100, (completed / total) * 100)
        dod_lookup = " ".join(d.lower() for d in dod)
        git_ok = "versionado" in dod_lookup and any(
            s.get("action") == "git_commit" for s in progress.get("steps", [])
            if s.get("status") == "completed"
        )
        audit_ok = "auditoria" in dod_lookup
        bonus = 0
        if git_ok:
            bonus += 5
        if audit_ok:
            bonus += 5
        return min(100, steps_ok + bonus)

    def _score_audit(self, audit_result):
        if not audit_result:
            return 0
        checklist = audit_result.get("checklist", [])
        if not checklist:
            return 50
        checked = sum(1 for c in checklist if c.get("checked"))
        return min(100, (checked / len(checklist)) * 100)
