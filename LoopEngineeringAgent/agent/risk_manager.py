import json
from datetime import datetime


class RiskManager:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def assess(self, goal_analysis, strategy=None):
        self.session.log("Assessing risks...")
        risks = []

        risks.extend(self._assess_environment_risks())
        risks.extend(self._assess_goal_risks(goal_analysis))
        risks.extend(self._assess_technical_risks(goal_analysis))
        risks.extend(self._assess_strategy_risks(strategy) if strategy else [])

        for risk in risks:
            risk["mitigation_plan"] = self._generate_mitigation(risk)

        critical = [r for r in risks if r.get("severity") == "critical"]
        high = [r for r in risks if r.get("severity") == "high"]

        assessment = {
            "risks": risks,
            "critical_count": len(critical),
            "high_count": len(high),
            "total_risks": len(risks),
            "can_proceed": len(critical) == 0,
            "assessed_at": datetime.now().isoformat(),
        }

        self.session.record_decision(
            f"Risk assessment: {len(critical)} critical, {len(high)} high, "
            f"{len(risks)} total. Can proceed: {assessment['can_proceed']}"
        )
        self.session.save_context({**self.session.load_context(), "risk_assessment": assessment})
        return assessment

    def _assess_environment_risks(self):
        return [
            {
                "id": "env_001",
                "category": "environment",
                "description": "Ferramentas necessarias podem nao estar instaladas",
                "severity": "high",
                "likelihood": "medium",
                "impact": "Bloqueia execucao",
                "affected_area": "setup"
            },
            {
                "id": "env_002",
                "category": "environment",
                "description": "Permissoes de arquivo insuficientes",
                "severity": "medium",
                "likelihood": "low",
                "impact": "Falha ao criar/modificar arquivos",
                "affected_area": "execution"
            },
        ]

    def _assess_goal_risks(self, analysis):
        risks = []
        complexity = analysis.get("complexity", 5)

        if complexity >= 8:
            risks.append({
                "id": "goal_001",
                "category": "complexity",
                "description": "Objetivo de alta complexidade requer multiplas iteracoes",
                "severity": "high",
                "likelihood": "high",
                "impact": "Tempo de execucao prolongado",
                "affected_area": "planning"
            })

        if not analysis.get("requirements"):
            risks.append({
                "id": "goal_002",
                "category": "ambiguity",
                "description": "Objetivo sem requisitos explicitos pode levar a resultado insatisfatorio",
                "severity": "medium",
                "likelihood": "high",
                "impact": "Escopo mal definido",
                "affected_area": "analysis"
            })

        if analysis.get("domain") == "android":
            risks.append({
                "id": "goal_003",
                "category": "technical",
                "description": "Ambiente Android requer SDK e build tools instalados",
                "severity": "high",
                "likelihood": "medium",
                "impact": "Falha na compilacao do APK",
                "affected_area": "execution"
            })

        return risks

    def _assess_technical_risks(self, analysis):
        return []

    def _assess_strategy_risks(self, strategy):
        risks = []
        if strategy:
            if strategy.get("risk_level") == "high":
                risks.append({
                    "id": "strat_001",
                    "category": "strategy",
                    "description": f"Estrategia '{strategy['name']}' possui alto risco",
                    "severity": "high",
                    "likelihood": "medium",
                    "impact": "Falha na execucao da estrategia",
                    "affected_area": "strategy"
                })
        return risks

    def _generate_mitigation(self, risk):
        category = risk.get("category", "")
        severity = risk.get("severity", "medium")

        mitigations = {
            "environment": "Verificar instalacao das ferramentas antes de executar. Usar fallback.",
            "complexity": "Dividir em etapas menores. Validar cada etapa antes de prosseguir.",
            "ambiguity": "Esclarecer requisitos com o usuario antes de iniciar.",
            "technical": "Verificar SDK e dependencias. Usar versoes compativeis.",
            "strategy": "Ter plano de fallback pronto. Reavaliar apos cada falha.",
        }

        mitigation = mitigations.get(category, "Monitorar e agir conforme necessario.")

        if severity in ("critical", "high"):
            mitigation += " [ACAO REQUERIDA ANTES DE PROSSEGUIR]"

        return mitigation
