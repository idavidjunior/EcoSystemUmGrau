import json
import os
from datetime import datetime


class StrategyEngine:
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.strategies = {}
        self.failed_strategies = set()

    def mark_failed(self, strategy_id):
        self.failed_strategies.add(strategy_id)
        self.session.record_decision(f"Strategy {strategy_id} marked as failed")

    def generate_strategies(self, goal_analysis):
        self.session.log("Generating execution strategies...")
        strategies = []

        task_type = goal_analysis.get("task_type", "creation")
        domain = goal_analysis.get("domain", "general")
        complexity = goal_analysis.get("complexity", 5)
        requirements = goal_analysis.get("requirements", [])

        strategy_generators = {
            "creation": self._strategy_for_creation,
            "fix": self._strategy_for_fix,
            "improvement": self._strategy_for_improvement,
            "validation": self._strategy_for_validation,
            "learning": self._strategy_for_learning,
        }

        generator = strategy_generators.get(task_type, self._strategy_for_creation)

        primary = generator(goal_analysis, "A", "Directa", "Objetivo direto com implementacao guiada por requisitos")
        self._score_strategy(primary, goal_analysis)
        strategies.append(primary)

        alternative = self._generate_alternative(primary, goal_analysis)
        strategies.append(alternative)

        conservative = self._generate_conservative(primary, goal_analysis)
        strategies.append(conservative)

        if complexity >= 5:
            incremental = self._generate_incremental(goal_analysis)
            strategies.append(incremental)

        if requirements:
            parallel = self._generate_parallel(goal_analysis)
            strategies.append(parallel)

        active_ids = {s["id"] for s in strategies}
        strategies = [s for s in strategies if s["id"] not in self.failed_strategies]

        if not strategies:
            self.session.log("All known strategies have failed. Generating fresh set.")
            self.failed_strategies.clear()
            strategies = [primary, alternative, conservative]

        strategies.sort(key=lambda s: s.get("score", 0), reverse=True)
        for i, s in enumerate(strategies):
            s["rank"] = i + 1

        self.strategies = {s["id"]: s for s in strategies}
        best = strategies[0] if strategies else None
        self.session.record_decision(
            f"Generated {len(strategies)} strategies. "
            f"Top: {best['name'] if best else 'N/A'} "
            f"(score: {best.get('score', 0) if best else 0}, "
            f"cost: {best.get('cost', 'N/A') if best else 'N/A'}, "
            f"success_prob: {best.get('success_probability', 0) if best else 0}%)"
        )
        self.session.save_context({**self.session.load_context(), "strategies": strategies})
        return strategies

    def _strategy_for_creation(self, analysis, label, name_suffix="Directa", approach=None):
        techs = analysis.get("technologies", ["unknown"])
        complexity = analysis.get("complexity", 5)
        if approach is None:
            approach = "Objetivo direto com implementacao guiada por requisitos"
        return {
            "id": f"strat_{label}",
            "name": f"Implementacao {name_suffix} ({label})",
            "approach": approach,
            "cost": self._estimate_cost(complexity, "medium"),
            "risk": "medium",
            "estimated_time": f"{max(3, complexity * 2)} iteracoes",
            "complexity": complexity,
            "success_probability": max(50, 90 - complexity * 3),
            "phases": [
                "Setup environment",
                "Implement core structure",
                "Implement features incrementalmente",
                "Test each feature",
                "Integrate and validate",
            ],
            "technologies": techs,
            "parallel_execution": False,
            "fallback_plan": "Replan with simpler scope if stuck",
            "dependencies": analysis.get("dependencies", []),
        }

    def _strategy_for_fix(self, analysis, label, name_suffix="Diagnostico", approach=None):
        if approach is None:
            approach = "Diagnosticar raiz, aplicar correcao, validar funcionamento"
        return {
            "id": f"strat_{label}",
            "name": f"Diagnostico e Correcao {name_suffix} ({label})",
            "approach": approach,
            "cost": self._estimate_cost(analysis.get("complexity", 5), "low"),
            "risk": "low",
            "estimated_time": "3-5 iteracoes",
            "complexity": analysis.get("complexity", 5),
            "success_probability": 80,
            "phases": [
                "Reproduce the issue",
                "Diagnose root cause",
                "Research solution",
                "Apply fix",
                "Test fix",
                "Verify no regressions",
            ],
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": False,
            "fallback_plan": "Rollback and try alternative fix",
            "dependencies": analysis.get("dependencies", []),
        }

    def _strategy_for_improvement(self, analysis, label, name_suffix="Iterativo", approach=None):
        if approach is None:
            approach = "Melhorias incrementais com validacao continua"
        return {
            "id": f"strat_{label}",
            "name": f"Melhoria {name_suffix} ({label})",
            "approach": approach,
            "cost": self._estimate_cost(analysis.get("complexity", 5), "low"),
            "risk": "low",
            "estimated_time": "4-6 iteracoes",
            "complexity": analysis.get("complexity", 5),
            "success_probability": 85,
            "phases": [
                "Analyze current state",
                "Identify improvement areas",
                "Implement changes one by one",
                "Test after each change",
                "Benchmark results",
            ],
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": False,
            "fallback_plan": "Revert changes and simplify scope",
            "dependencies": analysis.get("dependencies", []),
        }

    def _strategy_for_validation(self, analysis, label, name_suffix="Cobertura", approach=None):
        if approach is None:
            approach = "Cobertura de testes e validacao de requisitos"
        return {
            "id": f"strat_{label}",
            "name": f"Testes {name_suffix} ({label})",
            "approach": approach,
            "cost": self._estimate_cost(analysis.get("complexity", 5), "low"),
            "risk": "low",
            "estimated_time": "2-4 iteracoes",
            "complexity": analysis.get("complexity", 5),
            "success_probability": 90,
            "phases": [
                "Identify test cases",
                "Write unit tests",
                "Write integration tests",
                "Run full test suite",
                "Report coverage",
            ],
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": True,
            "fallback_plan": "Priorize critical path tests",
            "dependencies": analysis.get("dependencies", []),
        }

    def _strategy_for_learning(self, analysis, label, name_suffix="Exploratorio", approach=None):
        if approach is None:
            approach = "Aprendizado exploratorio com experimentos praticos"
        return {
            "id": f"strat_{label}",
            "name": f"Aprendizado {name_suffix} ({label})",
            "approach": approach,
            "cost": self._estimate_cost(analysis.get("complexity", 5), "low"),
            "risk": "low",
            "estimated_time": "3-5 iteracoes",
            "complexity": analysis.get("complexity", 5),
            "success_probability": 75,
            "phases": [
                "Research topic",
                "Create minimal example",
                "Experiment with variations",
                "Document findings",
                "Create reference implementation",
            ],
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": False,
            "fallback_plan": "Focus on core concepts only",
            "dependencies": analysis.get("dependencies", []),
        }

    def _generate_alternative(self, primary, analysis):
        return {
            "id": "strat_B",
            "name": "Abordagem Alternativa (B)",
            "approach": "Abordagem alternativa com escopo reduzido e validacao rapida",
            "cost": self._estimate_cost(analysis.get("complexity", 5), "low"),
            "risk": "low" if primary.get("risk") == "high" else "medium",
            "estimated_time": "60% do tempo da estrategia primaria",
            "complexity": max(1, analysis.get("complexity", 5) - 2),
            "success_probability": 70,
            "phases": [
                "Quick prototype",
                "Validate core concept",
                "Expand incrementally",
                "Test and refine",
            ],
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": False,
            "fallback_plan": "Consolidate and simplify",
            "dependencies": analysis.get("dependencies", []),
        }

    def _generate_conservative(self, primary, analysis):
        return {
            "id": "strat_C",
            "name": "Abordagem Conservadora (C)",
            "approach": "Abordagem conservadora com maxima seguranca e validacao por etapa",
            "cost": self._estimate_cost(analysis.get("complexity", 5), "high"),
            "risk": "very low",
            "estimated_time": "150% do tempo da estrategia primaria",
            "complexity": analysis.get("complexity", 5),
            "success_probability": 95,
            "phases": [
                "Thorough analysis",
                "Design documentation",
                "Implement with extensive validation",
                "Full test suite",
                "Security review",
            ],
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": False,
            "fallback_plan": "Fall back to strategy B",
            "dependencies": analysis.get("dependencies", []),
        }

    def _generate_incremental(self, analysis):
        return {
            "id": "strat_D",
            "name": "Incremental (D)",
            "approach": "Implementacao incremental com entregas parciais e feedback continuo",
            "cost": self._estimate_cost(analysis.get("complexity", 5), "medium"),
            "risk": "low",
            "estimated_time": "Iteracoes curtas com entregas parciais",
            "complexity": analysis.get("complexity", 5),
            "success_probability": 85,
            "phases": [
                "Implementar funcionalidade minima viavel",
                "Validar com usuario",
                "Adicionar funcionalidades incrementais",
                "Testar integracao",
                "Refinar com feedback",
            ],
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": False,
            "fallback_plan": "Consolidar funcionalidades basicas apenas",
            "dependencies": analysis.get("dependencies", []),
        }

    def _generate_parallel(self, analysis):
        return {
            "id": "strat_E",
            "name": "Execucao Paralela (E)",
            "approach": "Execucao paralela de modulos independentes para reducao de tempo total",
            "cost": self._estimate_cost(analysis.get("complexity", 5), "very high"),
            "risk": "high",
            "estimated_time": "40% do tempo da estrategia primaria",
            "complexity": analysis.get("complexity", 5) + 2,
            "success_probability": 60,
            "phases": [
                "Identificar modulos independentes",
                "Executar modulos em paralelo",
                "Integrar resultados",
                "Testar integracao",
                "Validar sistema completo",
            ],
            "technologies": analysis.get("technologies", ["unknown"]),
            "parallel_execution": True,
            "fallback_plan": "Serializar execucao e reduzir escopo",
            "dependencies": analysis.get("dependencies", []),
        }

    def _estimate_cost(self, complexity, risk_level):
        cost_map = {
            "very low": max(1, complexity // 3),
            "low": max(2, complexity // 2),
            "medium": complexity,
            "high": complexity * 2,
            "very high": complexity * 3,
        }
        return cost_map.get(risk_level, complexity)

    def _score_strategy(self, strategy, analysis):
        score = 50
        cost = strategy.get("cost", 5)
        risk = strategy.get("risk", "medium")
        success_prob = strategy.get("success_probability", 50)

        risk_scores = {"very low": 20, "low": 15, "medium": 10, "high": 0, "very high": -10}
        score += risk_scores.get(risk, 10)
        score += success_prob * 0.3
        score -= cost * 2

        strategy["score"] = max(1, min(100, round(score)))
        return strategy["score"]

    def select_best(self, goal_analysis):
        if not self.strategies:
            self.generate_strategies(goal_analysis)
        available = {k: v for k, v in self.strategies.items() if k not in self.failed_strategies}
        if not available:
            available = self.strategies
        ranked = sorted(available.values(), key=lambda s: s.get("score", 0), reverse=True)
        best = ranked[0] if ranked else None
        if best:
            self.session.record_decision(
                f"Selected strategy: {best['name']} "
                f"(score: {best.get('score', 0)}, "
                f"success: {best.get('success_probability', 0)}%, "
                f"cost: {best.get('cost', 'N/A')})"
            )
        return best

    def select_next_best(self, goal_analysis):
        if not self.strategies:
            self.generate_strategies(goal_analysis)
        available = {k: v for k, v in self.strategies.items() if k not in self.failed_strategies}
        ranked = sorted(available.values(), key=lambda s: s.get("score", 0), reverse=True)
        next_best = ranked[0] if ranked else None
        if next_best:
            self.session.record_decision(
                f"Next best strategy: {next_best['name']} "
                f"(score: {next_best.get('score', 0)}, "
                f"success: {next_best.get('success_probability', 0)}%)"
            )
        return next_best
