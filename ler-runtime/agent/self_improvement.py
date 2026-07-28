import json
import os
from datetime import datetime


class SelfImprovement:
    def __init__(self, session, base_dir):
        self.session = session
        self.base_dir = base_dir
        self.rules_file = os.path.join(base_dir, "memory", "learned_rules.json")
        self.config_file = os.path.join(base_dir, "config", "config.json")
        self.agent_rules_file = os.path.join(base_dir, "config", "agent_rules.json")

    def evaluate_mission(self, mission_result):
        self.session.log("[SelfImprovement] Evaluating mission for improvement opportunities...")
        findings = []

        bottlenecks = self._detect_bottlenecks(mission_result)
        findings.extend(bottlenecks)

        waste = self._detect_waste(mission_result)
        findings.extend(waste)

        rework = self._detect_rework(mission_result)
        findings.extend(rework)

        recurring = self._detect_recurring_failures()
        findings.extend(recurring)

        improvements = self._generate_suggestions(findings)

        report = {
            "mission_id": mission_result.get("mission_id"),
            "evaluated_at": datetime.now().isoformat(),
            "findings": findings,
            "improvement_suggestions": improvements,
            "metrics": {
                "iterations": mission_result.get("iterations", 0),
                "elapsed": mission_result.get("elapsed_seconds", 0),
                "steps_completed": mission_result.get("steps", {}).get("completed", 0),
                "steps_failed": mission_result.get("steps", {}).get("failed", 0),
            },
        }

        self._apply_improvements(improvements)
        self._save_report(report)

        return report

    def _detect_bottlenecks(self, result):
        bottlenecks = []
        elapsed = result.get("elapsed_seconds", 0)
        iterations = result.get("iterations", 1)
        steps_completed = result.get("steps", {}).get("completed", 0)

        avg_time_per_step = elapsed / max(iterations, 1)
        if avg_time_per_step > 30:
            bottlenecks.append({
                "type": "bottleneck",
                "description": f"Tempo medio por iteracao alto ({avg_time_per_step:.1f}s)",
                "severity": "medium",
                "suggestion": "Reduzir complexidade de cada iteracao ou paralelizar passos"
            })

        if iterations > 20 and steps_completed < iterations * 0.5:
            bottlenecks.append({
                "type": "bottleneck",
                "description": "Baixa taxa de conclusao por iteracao",
                "severity": "high",
                "suggestion": "Revisar planejamento de passos para serem mais granulares"
            })

        return bottlenecks

    def _detect_waste(self, result):
        waste = []
        iterations = result.get("iterations", 0)
        steps_completed = result.get("steps", {}).get("completed", 0)
        steps_total = result.get("steps", {}).get("total", 0)

        if steps_total > 0 and steps_completed < steps_total:
            waste_rate = (steps_total - steps_completed) / steps_total * 100
            if waste_rate > 30:
                waste.append({
                    "type": "waste",
                    "description": f"{waste_rate:.0f}% dos passos nao foram concluidos",
                    "severity": "high",
                    "suggestion": "Revisar escopo do plano e garantir factibilidade"
                })

        if iterations > steps_completed * 3 and steps_completed > 0:
            waste.append({
                "type": "waste",
                "description": "Iteracoes excessivas para passos concluidos",
                "severity": "medium",
                "suggestion": "Otimizar validacao e reduzir retries desnecessarios"
            })

        return waste

    def _detect_rework(self, result):
        rework = []
        failed = result.get("steps", {}).get("failed", 0)
        completed = result.get("steps", {}).get("completed", 0)

        if failed > 0 and completed > 0:
            rework_rate = failed / completed * 100
            if rework_rate > 20:
                rework.append({
                    "type": "rework",
                    "description": f"Taxa de retrabalho alta ({rework_rate:.0f}%)",
                    "severity": "high",
                    "suggestion": "Melhorar validacao pre-execucao para evitar erros"
                })

        return rework

    def _detect_recurring_failures(self):
        recurring = []
        if os.path.exists(self.rules_file):
            with open(self.rules_file, "r", encoding="utf-8") as f:
                rules = json.load(f)
            for rule in rules.get("rules", []):
                if rule.get("count", 0) >= 3 and not rule.get("applied_successfully", False):
                    recurring.append({
                        "type": "recurring_failure",
                        "description": f"Erro recorrente nao resolvido: {rule.get('error_key', '')} "
                                       f"({rule.get('count')}x)",
                        "severity": "high",
                        "suggestion": f"Aplicar correcao sugerida: {rule.get('suggested_fix', '')}"
                    })
        return recurring

    def _generate_suggestions(self, findings):
        suggestions = []
        for f in findings:
            suggestions.append(f["suggestion"])
        suggestions = list(set(suggestions))
        return suggestions[:5]

    def _apply_improvements(self, improvements):
        if not improvements:
            return
        self.session.record_decision(
            f"[SelfImprovement] {len(improvements)} improvement suggestions generated"
        )

    def _save_report(self, report):
        reports_dir = os.path.join(self.base_dir, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        path = os.path.join(reports_dir, f"self_improvement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        self.session.log(f"[SelfImprovement] Report saved: {path}")
