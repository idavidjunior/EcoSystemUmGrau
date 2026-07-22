import json
import os
from datetime import datetime


class StrategyEngine:
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.strategies = {}

    def generate_strategies(self, goal_analysis):
        self.session.log("Generating execution strategies...")
        strategies = []

        task_type = goal_analysis.get("task_type", "creation")
        domain = goal_analysis.get("domain", "general")
        complexity = goal_analysis.get("complexity", 5)

        strategy_generators = {
            "creation": self._strategy_for_creation,
            "fix": self._strategy_for_fix,
            "improvement": self._strategy_for_improvement,
            "validation": self._strategy_for_validation,
            "learning": self._strategy_for_learning,
        }

        generator = strategy_generators.get(task_type, self._strategy_for_creation)
        primary = generator(goal_analysis, "A")
        self._score_strategy(primary, goal_analysis)
        strategies.append(primary)

        alternative = self._generate_alternative(primary, goal_analysis)
        strategies.append(alternative)

        if complexity >= 6:
            conservative = self._generate_conservative(primary, goal_analysis)
            strategies.append(conservative)

        strategies.sort(key=lambda s: s.get("score", 0), reverse=True)
        for i, s in enumerate(strategies):
            s["rank"] = i + 1

        self.strategies = {s["id"]: s for s in strategies}
        self.session.record_decision(
            f"Generated {len(strategies)} strategies. "
            f"Top: {strategies[0]['name']} (score: {strategies[0].get('score', 0)})"
        )
        self.session.save_context({**self.session.load_context(), "strategies": strategies})
        return strategies

    def _strategy_for_creation(self, analysis, label):
        techs = analysis.get("technologies", ["unknown"])
        return {
            "id": f"strat_{label}",
            "name": f"Direct Implementation ({label})",
            "approach": "Objetivo direto com implementacao guiada por requisitos",
            "phases": [
                "Setup environment",
                "Implement core structure",
                "Implement features incrementalmente",
                "Test each feature",
                "Integrate and validate",
            ],
            "risk_level": "medium",
            "estimated_effort": f"{analysis.get('complexity', 5) * 2} iterations",
            "technologies": techs,
            "parallel_execution": False,
            "fallback_plan": "Replan with simpler scope if stuck",
        }

    def _strategy_for_fix(self, analysis, label):
        return {
            "id": f"strat_{label}",
            "name": f"Diagnostic-Fix-Validate ({label})",
            "approach": "Diagnosticar raiz, aplicar correcao, validar funcionamento",
            "phases": [
                "Reproduce the issue",
                "Diagnose root cause",
                "Research solution",
                "Apply fix",
                "Test fix",
                "Verify no regressions",
            ],
            "risk_level": "low",
            "estimated_effort": "3-5 iterations",
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": False,
            "fallback_plan": "Rollback and try alternative fix",
        }

    def _strategy_for_improvement(self, analysis, label):
        return {
            "id": f"strat_{label}",
            "name": f"Incremental Improvement ({label})",
            "approach": "Melhorias incrementais com validacao continua",
            "phases": [
                "Analyze current state",
                "Identify improvement areas",
                "Implement changes one by one",
                "Test after each change",
                "Benchmark results",
            ],
            "risk_level": "low",
            "estimated_effort": "4-6 iterations",
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": False,
            "fallback_plan": "Revert changes and simplify scope",
        }

    def _strategy_for_validation(self, analysis, label):
        return {
            "id": f"strat_{label}",
            "name": f"Test Coverage ({label})",
            "approach": "Cobertura de testes e validacao de requisitos",
            "phases": [
                "Identify test cases",
                "Write unit tests",
                "Write integration tests",
                "Run full test suite",
                "Report coverage",
            ],
            "risk_level": "low",
            "estimated_effort": "2-4 iterations",
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": True,
            "fallback_plan": "Priorize critical path tests",
        }

    def _strategy_for_learning(self, analysis, label):
        return {
            "id": f"strat_{label}",
            "name": f"Exploratory Learning ({label})",
            "approach": "Aprendizado exploratorio com experimentos praticos",
            "phases": [
                "Research topic",
                "Create minimal example",
                "Experiment with variations",
                "Document findings",
                "Create reference implementation",
            ],
            "risk_level": "low",
            "estimated_effort": "3-5 iterations",
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": False,
            "fallback_plan": "Focus on core concepts only",
        }

    def _generate_alternative(self, primary, analysis):
        techs = analysis.get("technologies", ["unknown"])
        return {
            "id": "strat_B",
            "name": "Alternative Approach (B)",
            "approach": "Abordagem alternativa com escopo reduzido",
            "phases": [
                "Quick prototype",
                "Validate core concept",
                "Expand incrementally",
                "Test and refine",
            ],
            "risk_level": "low" if primary.get("risk_level") == "high" else "medium",
            "estimated_effort": "60% of primary effort",
            "technologies": techs,
            "parallel_execution": False,
            "fallback_plan": "Consolidate and simplify",
        }

    def _generate_conservative(self, primary, analysis):
        return {
            "id": "strat_C",
            "name": "Conservative (C)",
            "approach": "Abordagem conservadora com maxima seguranca",
            "phases": [
                "Thorough analysis",
                "Design documentation",
                "Implement with extensive validation",
                "Full test suite",
                "Security review",
            ],
            "risk_level": "very low",
            "estimated_effort": "150% of primary effort",
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": False,
            "fallback_plan": "Fall back to strategy B",
        }

    def _score_strategy(self, strategy, analysis):
        score = 5
        risk_map = {"very low": 3, "low": 2, "medium": 0, "high": -3, "very high": -5}
        score += risk_map.get(strategy.get("risk_level", "medium"), 0)
        score += analysis.get("complexity", 5) * 0.5
        strategy["score"] = max(1, min(10, score))

    def select_best(self, goal_analysis):
        if not self.strategies:
            self.generate_strategies(goal_analysis)
        ranked = sorted(self.strategies.values(), key=lambda s: s.get("score", 0), reverse=True)
        best = ranked[0] if ranked else None
        if best:
            self.session.record_decision(
                f"Selected strategy: {best['name']} (score: {best.get('score', 0)})"
            )
        return best
