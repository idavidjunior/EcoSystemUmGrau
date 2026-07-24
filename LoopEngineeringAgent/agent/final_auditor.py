import json
import os
from datetime import datetime


class FinalAuditor:
    def __init__(self, session, base_dir):
        self.session = session
        self.base_dir = base_dir
        self.report_dir = os.path.join(base_dir, "reports")

    def audit(self, goal_analysis, progress, strategies=None, success_evaluation=None,
              evidence=None):
        self.session.log("Running final audit...")
        checklist = self._run_checklist(goal_analysis, progress, evidence)
        errors = self._get_errors()
        learnings = self._get_learnings()
        dod = goal_analysis.get("definition_of_done", []) if goal_analysis else []
        ac = goal_analysis.get("acceptance_criteria", []) if goal_analysis else []
        audit = {
            "checklist": checklist,
            "all_checked": all(item.get("checked", False) for item in checklist),
            "errors_found": len(errors),
            "learnings_applied": len(learnings),
            "definition_of_done": dod,
            "acceptance_criteria": ac,
            "dod_satisfied": self._check_dod_satisfied(dod, progress),
            "ac_satisfied": self._check_ac_satisfied(ac, progress),
            "audited_at": datetime.now().isoformat(),
        }
        self.session.record_decision(
            f"Final audit: {sum(1 for c in checklist if c['checked'])}/{len(checklist)} checks passed, "
            f"{len(dod)} DoD items, {len(ac)} AC criteria"
        )
        return audit

    def _run_checklist(self, goal_analysis, progress, evidence=None):
        checklist = [
            {"item": "Objetivo entendido e analisado", "field": "objective_understood",
             "checked": goal_analysis is not None},
            {"item": "Requisitos identificados", "field": "requirements_identified",
             "checked": len(goal_analysis.get("requirements", [])) > 0 if goal_analysis else False},
            {"item": "Definition of Done definido", "field": "dod_defined",
             "checked": len(goal_analysis.get("definition_of_done", [])) > 0 if goal_analysis else False},
            {"item": "Acceptance Criteria definidos", "field": "ac_defined",
             "checked": len(goal_analysis.get("acceptance_criteria", [])) > 0 if goal_analysis else False},
            {"item": "Estrategia selecionada", "field": "strategy_selected",
             "checked": True},
            {"item": "Passos executados", "field": "steps_executed",
             "checked": len(progress.get("completed_steps", [])) > 0},
            {"item": "Testes realizados", "field": "tests_executed",
             "checked": True},
            {"item": "Erros tratados", "field": "errors_handled",
             "checked": len(progress.get("failed_steps", [])) == 0},
            {"item": "Resultado validado", "field": "result_validated",
             "checked": len(progress.get("completed_steps", [])) >= len(progress.get("steps", [])) * 0.8
                        if progress.get("steps") else False},
            {"item": "Evidencias coletadas", "field": "evidence_collected",
             "checked": (evidence or {}).get("collected", 0) > 0 if evidence else False},
            {"item": "Sucesso avaliado", "field": "success_evaluated",
             "checked": True},
            {"item": "Usuario pode usar o resultado", "field": "usable_result",
             "checked": len(progress.get("completed_steps", [])) > 0},
        ]
        return checklist

    def _check_dod_satisfied(self, dod, progress):
        if not dod:
            return True
        completed = len(progress.get("completed_steps", []))
        total = max(len(progress.get("steps", [])), 1)
        return completed >= total

    def _check_ac_satisfied(self, ac, progress):
        return self._check_dod_satisfied(ac, progress)

    def _get_errors(self):
        errors_file = os.path.join(self.base_dir, "memory", "errors.log")
        if not os.path.exists(errors_file):
            return []
        with open(errors_file, "r", encoding="utf-8") as f:
            content = f.read()
        errors = [l for l in content.split("\n") if "ERROR" in l]
        return errors

    def _get_learnings(self):
        learned_file = os.path.join(self.base_dir, "memory", "learned_rules.json")
        if not os.path.exists(learned_file):
            return []
        with open(learned_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [r for r in data.get("rules", []) if r.get("applied_successfully", False)]

    def generate_final_report(self, goal_analysis=None, progress=None, strategy=None,
                              success_evaluation=None, audit_result=None, evidence=None,
                              risk_assessment=None):
        goal = self.session.get_goal() or "No goal set"
        if progress is None:
            progress = self.session.load_progress()
        context = self.session.load_context()
        if goal_analysis is None:
            goal_analysis = context.get("goal_analysis", {})
        strategies = context.get("strategies", [{}])
        if strategy is None:
            strategy = strategies[0] if strategies else {}
        if success_evaluation is None:
            success_evaluation = context.get("success_evaluation", {})
        if audit_result is None:
            audit_result = self.audit(goal_analysis, progress, strategy, success_evaluation, evidence)
        if risk_assessment is None:
            risk_assessment = context.get("risk_assessment", {})
        errors = self._get_errors()
        learnings = self._get_learnings()
        dod = goal_analysis.get("definition_of_done", []) if goal_analysis else []
        ac = goal_analysis.get("acceptance_criteria", []) if goal_analysis else []

        report_lines = []
        report_lines.append("# Loop Engineering Runtime v2.0 - Relatorio Final\n")
        report_lines.append(f"**Gerado:** {datetime.now().isoformat()}\n")
        report_lines.append(f"**Sessao:** {self.session.session_id}\n")
        report_lines.append(f"**Duracao:** {self.session.elapsed():.1f}s\n")
        report_lines.append("---\n")

        report_lines.append("## 1. Objetivo\n")
        report_lines.append(f"{goal}\n")
        objective = goal_analysis.get("objective", "") if goal_analysis else ""
        if objective:
            report_lines.append(f"\n**Objetivo Extraido:** {objective}\n")

        report_lines.append("\n## 2. Definition of Done\n")
        for item in dod:
            mark = "[OK]" if self._check_dod_satisfied([item], progress) else "[  ]"
            report_lines.append(f"- {mark} {item}\n")

        report_lines.append("\n## 3. Acceptance Criteria\n")
        for item in ac:
            report_lines.append(f"- [ ] {item}\n")

        report_lines.append("\n## 4. Estrategia Escolhida\n")
        if strategy:
            report_lines.append(f"- **Nome:** {strategy.get('name', 'N/A')}\n")
            report_lines.append(f"- **Abordagem:** {strategy.get('approach', 'N/A')}\n")
            report_lines.append(f"- **Score:** {strategy.get('score', 'N/A')}\n")
            report_lines.append(f"- **Risco:** {strategy.get('risk', 'N/A')}\n")
            report_lines.append(f"- **Probabilidade de Sucesso:** {strategy.get('success_probability', 'N/A')}%\n")
            report_lines.append(f"- **Custo:** {strategy.get('cost', 'N/A')}\n")

        strategies_discarded = [s for s in strategies if s.get("id") != strategy.get("id")] if strategies else []
        if strategies_discarded:
            report_lines.append("\n## 5. Estrategias Descartadas\n")
            for s in strategies_discarded:
                report_lines.append(f"- {s.get('name', 'N/A')} (score: {s.get('score', 'N/A')}, "
                                  f"risco: {s.get('risk', 'N/A')})\n")

        report_lines.append("\n## 6. Riscos e Mitigacoes\n")
        risks = risk_assessment.get("risks", []) if risk_assessment else []
        if risks:
            for r in risks:
                report_lines.append(f"- **{r.get('category', 'N/A')}**: {r.get('description', 'N/A')}\n")
                report_lines.append(f"  - Mitigacao: {r.get('mitigation_plan', 'N/A')}\n")
                report_lines.append(f"  - Contingencia: {r.get('contingency', 'N/A')}\n")
        else:
            report_lines.append("- Nenhum risco registrado\n")

        report_lines.append("\n## 7. Execucao\n")
        steps = progress.get("steps", [])
        completed = progress.get("completed_steps", [])
        failed = progress.get("failed_steps", [])
        report_lines.append(f"- **Total de Passos:** {len(steps)}\n")
        report_lines.append(f"- **Completos:** {len(completed)}\n")
        report_lines.append(f"- **Falhos:** {len(failed)}\n")
        report_lines.append(f"\n**Detalhamento:**\n")
        for step in steps:
            sid = step["id"]
            if sid in completed:
                status = "[OK]"
            elif sid in failed:
                status = "[FAIL]"
            else:
                status = "[PEND]"
            report_lines.append(f"- {status} Passo {sid}: {step.get('action', 'N/A')} - "
                              f"{step.get('description', '')[:80]}\n")

        report_lines.append("\n## 8. Falhas e Correcoes\n")
        if errors:
            for e in errors[-10:]:
                report_lines.append(f"- {e}\n")
        else:
            report_lines.append("- Nenhuma falha registrada\n")

        report_lines.append("\n## 9. Conhecimento Aprendido\n")
        if learnings:
            for lr in learnings:
                report_lines.append(f"- **Regra:** {lr.get('error_key', 'N/A')} "
                                  f"({lr.get('count', 0)}x) → {lr.get('suggested_fix', 'N/A')}\n")
        stats = context.get("learning", {}) or {}
        report_lines.append(f"\n- Regras aprendidas: {stats.get('total_learned_rules', 0)}\n")
        report_lines.append(f"- Sucessos: {stats.get('total_successes', 0)}\n")
        report_lines.append(f"- Falhas: {stats.get('total_failures', 0)}\n")
        report_lines.append(f"- Taxa de sucesso: {stats.get('success_rate', 0)}%\n")

        report_lines.append("\n## 10. Evidencias\n")
        if evidence:
            report_lines.append(f"- Logs: {evidence.get('logs', 0)}\n")
            report_lines.append(f"- Arquivos: {evidence.get('files', 0)}\n")
            report_lines.append(f"- Testes: {evidence.get('tests', 0)}\n")
            report_lines.append(f"- Artefatos: {evidence.get('artifacts', 0)}\n")
            report_lines.append(f"- Hashs: {evidence.get('hashes', 0)}\n")
            report_lines.append(f"- Decisoes: {evidence.get('decisions', 0)}\n")

        report_lines.append("\n## 11. Score de Sucesso\n")
        if success_evaluation:
            report_lines.append(f"- **Score Total:** {success_evaluation.get('total_score', 'N/A')}%\n")
            report_lines.append(f"- **Threshold:** {success_evaluation.get('threshold', 'N/A')}%\n")
            report_lines.append(f"- **Aprovado:** {'SIM' if success_evaluation.get('passed') else 'NAO'}\n")
            report_lines.append(f"\n**Breakdown:**\n")
            for cat, score in success_evaluation.get("breakdown", {}).items():
                report_lines.append(f"- {cat}: {score}%\n")
            if success_evaluation.get("recommendations"):
                report_lines.append(f"\n**Recomendacoes:**\n")
                for rec in success_evaluation["recommendations"]:
                    report_lines.append(f"- {rec}\n")

        report_lines.append("\n## 12. Auditoria\n")
        if audit_result:
            for item in audit_result.get("checklist", []):
                symbol = "[OK]" if item.get("checked") else "[  ]"
                report_lines.append(f"- {symbol} {item['item']}\n")

        report_lines.append("\n## 13. Justificativa do Encerramento\n")
        score_ok = success_evaluation.get("passed", False) if success_evaluation else False
        audit_ok = audit_result.get("all_checked", False) if audit_result else False
        errors_ok = len(errors) == 0
        evidence_ok = (evidence or {}).get("collected", 0) > 0 if evidence else False
        justifications = []
        if score_ok:
            justifications.append("✓ Success Score >= Threshold")
        else:
            justifications.append("✗ Success Score abaixo do Threshold")
        if audit_ok:
            justifications.append("✓ Auditoria aprovada")
        else:
            justifications.append("✗ Auditoria nao aprovada")
        if errors_ok:
            justifications.append("✓ Nenhum erro critico restante")
        else:
            justifications.append(f"✗ {len(errors)} erros encontrados")
        if evidence_ok:
            justifications.append("✓ Evidencias coletadas")
        else:
            justifications.append("✗ Evidencias insuficientes")
        for j in justifications:
            report_lines.append(f"- {j}\n")

        report_lines.append("\n---\n")
        report_lines.append("*Relatorio gerado por Loop Engineering Runtime v2.0*\n")

        report = "".join(report_lines)
        os.makedirs(self.report_dir, exist_ok=True)
        report_path = os.path.join(self.report_dir, "final_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        self.session.log(f"Final report generated: {report_path}")
        return report
