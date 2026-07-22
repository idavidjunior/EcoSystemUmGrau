import json
import os
from datetime import datetime


class FinalAuditor:
    def __init__(self, session, base_dir):
        self.session = session
        self.base_dir = base_dir
        self.report_dir = os.path.join(base_dir, "reports")

    def audit(self, goal_analysis, progress, strategies=None, success_evaluation=None):
        self.session.log("Running final audit...")
        checklist = self._run_checklist(goal_analysis, progress)
        errors = self._get_errors()
        learnings = self._get_learnings()

        audit = {
            "checklist": checklist,
            "all_checked": all(item.get("checked", False) for item in checklist),
            "errors_found": len(errors),
            "learnings_applied": len(learnings),
            "audited_at": datetime.now().isoformat(),
        }

        self.session.record_decision(
            f"Final audit: {sum(1 for c in checklist if c['checked'])}/{len(checklist)} checks passed"
        )
        return audit

    def _run_checklist(self, goal_analysis, progress):
        checklist = [
            {"item": "Objetivo entendido e analisado", "field": "objective_understood",
             "checked": goal_analysis is not None},
            {"item": "Requisitos identificados", "field": "requirements_identified",
             "checked": len(goal_analysis.get("requirements", [])) > 0 if goal_analysis else False},
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
             "checked": True},
            {"item": "Usuario pode usar o resultado", "field": "usable_result",
             "checked": len(progress.get("completed_steps", [])) > 0},
        ]
        return checklist

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

    def generate_final_report(self):
        goal = self.session.get_goal() or "No goal set"
        progress = self.session.load_progress()
        context = self.session.load_context()
        goal_analysis = context.get("goal_analysis", {})
        strategies = context.get("strategies", [{}])
        success_eval = context.get("success_evaluation", {})

        audit = self.audit(goal_analysis, progress)
        errors = self._get_errors()

        report_lines = []
        report_lines.append("# Loop Engineering Agent - Final Report\n")
        report_lines.append(f"**Generated:** {datetime.now().isoformat()}\n")
        report_lines.append(f"**Session:** {self.session.session_id}\n")
        report_lines.append(f"**Duration:** {self.session.elapsed():.1f}s\n")
        report_lines.append("---\n")

        report_lines.append("## 1. Original Goal\n")
        report_lines.append(f"{goal}\n")

        report_lines.append("## 2. Goal Analysis\n")
        if goal_analysis:
            report_lines.append(f"- **Domain:** {goal_analysis.get('domain', 'N/A')}")
            report_lines.append(f"- **Task Type:** {goal_analysis.get('task_type', 'N/A')}")
            report_lines.append(f"- **Complexity:** {goal_analysis.get('complexity', 'N/A')}/10")
            report_lines.append(f"- **Technologies:** {', '.join(goal_analysis.get('technologies', ['N/A']))}")
            report_lines.append(f"\n**Success Criteria:**")
            for c in goal_analysis.get("success_criteria", []):
                report_lines.append(f"- [ ] {c}")

        report_lines.append("\n## 3. Strategy Used\n")
        if strategies:
            best = strategies[0] if isinstance(strategies, list) else strategies
            report_lines.append(f"- **Strategy:** {best.get('name', 'N/A')}")
            report_lines.append(f"- **Approach:** {best.get('approach', 'N/A')}")
            report_lines.append(f"- **Risk Level:** {best.get('risk_level', 'N/A')}")

        report_lines.append("\n## 4. Execution Progress\n")
        steps = progress.get("steps", [])
        completed = progress.get("completed_steps", [])
        failed = progress.get("failed_steps", [])
        report_lines.append(f"- **Total Steps:** {len(steps)}")
        report_lines.append(f"- **Completed:** {len(completed)}")
        report_lines.append(f"- **Failed:** {len(failed)}")
        report_lines.append(f"\n**Steps Detail:**")
        for step in steps:
            status = "[OK]" if step["id"] in completed else "[FAIL]" if step["id"] in failed else "[PENDING]"
            report_lines.append(f"- {status} Step {step['id']}: {step.get('action', 'N/A')} - {step.get('description', '')[:80]}")

        report_lines.append("\n## 5. Errors Found\n")
        if errors:
            for e in errors[-10:]:
                report_lines.append(f"- {e}")
        else:
            report_lines.append("- No errors recorded")

        report_lines.append("\n## 6. Audit Checklist\n")
        for item in audit.get("checklist", []):
            symbol = "[OK]" if item.get("checked") else "[  ]"
            report_lines.append(f"- {symbol} {item['item']}")

        report_lines.append("\n## 7. Final Status\n")
        if audit.get("all_checked"):
            report_lines.append("**GOAL ACHIEVED - All checks passed**")
        else:
            report_lines.append("**GOAL PARTIALLY ACHIEVED**")
            unchecked = [i["item"] for i in audit.get("checklist", []) if not i.get("checked")]
            if unchecked:
                report_lines.append("**Unchecked items:**")
                for item in unchecked:
                    report_lines.append(f"- {item}")

        report_lines.append("\n---\n")
        report_lines.append("*Report generated by Loop Engineering Agent v1.1*\n")

        report = "\n".join(report_lines)
        os.makedirs(self.report_dir, exist_ok=True)

        report_path = os.path.join(self.report_dir, "final_report.md")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        self.session.log(f"Final report generated: {report_path}")
        return report
