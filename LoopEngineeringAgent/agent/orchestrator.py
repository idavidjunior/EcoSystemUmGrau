import os
import json
import sys
import time
from datetime import datetime

from core.state import AgentState
from core.checkpoint import save_checkpoint, load_checkpoint, get_latest_checkpoint
from agent.planner import Planner
from agent.executor import Executor
from agent.validator import Validator
from agent.recovery import Recovery
from agent.goal_analyzer import GoalAnalyzer
from agent.strategy_engine import StrategyEngine
from agent.risk_manager import RiskManager
from agent.learning_engine import LearningEngine
from agent.success_evaluator import SuccessEvaluator
from agent.final_auditor import FinalAuditor
from agent.evidence_collector import EvidenceCollector
from agent.tool_selector import ToolSelector
from agent.self_improvement import SelfImprovement
from agent.supervisor import Supervisor


class Orchestrator:
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.state = AgentState()
        self.planner = Planner(session, config)
        self.executor = Executor(session, config)
        self.validator = Validator(session, config)
        self.recovery = Recovery(session, config)
        self.goal_analyzer = GoalAnalyzer(session, config)
        self.strategy_engine = StrategyEngine(session, config)
        self.risk_manager = RiskManager(session, config)
        self.learning_engine = LearningEngine(session, session.base_dir)
        self.success_evaluator = SuccessEvaluator(session, config)
        self.final_auditor = FinalAuditor(session, session.base_dir)
        self.evidence_collector = EvidenceCollector(session, session.base_dir)
        self.tool_selector = ToolSelector(session, session.base_dir)
        self.self_improvement = SelfImprovement(session, session.base_dir)
        self.supervisor = Supervisor(session, config)
        self.max_iterations = config.get("loop", {}).get("max_iterations", 100)
        self.iteration = 0
        self.goal_analysis = None
        self.current_strategy = None
        self.risk_assessment = None
        self.current_step = None
        self.current_result = None
        self._loop_done = False
        self._replan_count = 0
        self._last_strategies_tried = []
        self._cycle_detector = {}
        self._recovery_loop_count = 0

        self.supervisor.register_module("planner", self.planner)
        self.supervisor.register_module("executor", self.executor)
        self.supervisor.register_module("validator", self.validator)
        self.supervisor.register_module("recovery", self.recovery)
        self.supervisor.register_module("goal_analyzer", self.goal_analyzer)
        self.supervisor.register_module("strategy_engine", self.strategy_engine)
        self.supervisor.register_module("risk_manager", self.risk_manager)
        self.supervisor.register_module("learning_engine", self.learning_engine)
        self.supervisor.register_module("success_evaluator", self.success_evaluator)
        self.supervisor.register_module("final_auditor", self.final_auditor)

    def run(self, goal_text):
        self.session.log("=" * 60)
        self.session.log("LOOP ENGINEERING AGENT v2.0 - GOAL ORIENTED LOOP")
        self.session.log("=" * 60)

        self.session.set_goal(goal_text)
        self.learning_engine.initialize()
        self.evidence_collector.start_mission(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        self.state.transition(AgentState.INIT)
        return self._execution_loop()

    def _execution_loop(self):
        while self.iteration < self.max_iterations:
            self.iteration += 1
            self.session.log(f"\n--- Iteration {self.iteration} ---")
            self.session.log(f"State: {self.state.current}")

            recent = self.state.history[-6:]
            state_seq = tuple(
                (h["from"], h["to"]) if isinstance(h, dict) else h
                for h in recent
            )
            self._cycle_detector[state_seq] = self._cycle_detector.get(state_seq, 0) + 1
            if self._cycle_detector[state_seq] >= 4:
                self.session.log(f"[CYCLE] Same state sequence detected 4+ times. Forcing autonomous replan.")
                self._cycle_detector.clear()
                self._recovery_loop_count = 0
                self.state.transition(AgentState.REPLANNING)
                continue

            if self.state.current in (AgentState.VALIDATION_FAILED, AgentState.RECOVERING, AgentState.LEARNING):
                self._recovery_loop_count += 1
            else:
                self._recovery_loop_count = 0
            if self._recovery_loop_count >= 8:
                self.session.log(f"[CYCLE] Recovery loop exceeded 8 iterations. Forcing replan.")
                self._recovery_loop_count = 0
                self.state.transition(AgentState.REPLANNING)
                continue

            supervisor_check = self.supervisor.monitor_all()
            unhealthy = self.supervisor.get_unhealthy_modules()
            for name in unhealthy:
                self.session.log(f"[Supervisor] Module '{name}' is unhealthy. Attempting recovery.")
                self.supervisor.recover_module(name)

            handlers = {
                AgentState.INIT: self._phase_analyze_goal,
                AgentState.ANALYZING_GOAL: self._phase_analyze_goal,
                AgentState.CREATING_STRATEGY: self._phase_create_strategy,
                AgentState.PLANNING: self._phase_planning,
                AgentState.REPLANNING: self._phase_autonomous_replanning,
                AgentState.EXECUTING: self._phase_executing,
                AgentState.VALIDATING: self._phase_validating,
                AgentState.VALIDATION_FAILED: self._phase_recovering,
                AgentState.RECOVERING: self._phase_recovering,
                AgentState.LEARNING: self._phase_learning,
                AgentState.SUCCESS_EVALUATING: self._phase_success_eval,
                AgentState.FINAL_AUDITING: self._phase_final_audit,
                AgentState.SUCCESS_VERIFIED: self._phase_success_verified,
                AgentState.COMPLETED: lambda: self._finalize("completed"),
                AgentState.FAILED: lambda: self._finalize("failed"),
            }

            handler = handlers.get(self.state.current)
            if handler:
                result = handler()
                if result:
                    return result
            else:
                self.session.log(f"No handler for state: {self.state.current}")
                break

        return self._finalize("max_iterations")

    def _phase_analyze_goal(self):
        self.session.log("Phase: ANALYZING GOAL")
        self.state.transition(AgentState.ANALYZING_GOAL)
        goal = self.session.get_goal()
        if not goal:
            self.state.transition(AgentState.FAILED)
            return
        self.goal_analysis = self.goal_analyzer.analyze(goal)
        dod = self.goal_analysis.get("definition_of_done", [])
        ac = self.goal_analysis.get("acceptance_criteria", [])
        self.session.log(f"DoD: {len(dod)} items, Acceptance: {len(ac)} criteria")
        save_checkpoint(self.state, self.goal_analysis, self.session.load_progress(),
                       self.session.load_context(), "goal_analyzed")
        self.state.transition(AgentState.CREATING_STRATEGY)

    def _phase_create_strategy(self):
        self.session.log("Phase: CREATING STRATEGY")
        self.state.transition(AgentState.CREATING_STRATEGY)
        if not self.goal_analysis:
            self.goal_analysis = self.session.load_context().get("goal_analysis", {})
            if not self.goal_analysis:
                self.state.transition(AgentState.ANALYZING_GOAL)
                return
        strategies = self.strategy_engine.generate_strategies(self.goal_analysis)
        self.current_strategy = self.strategy_engine.select_best(self.goal_analysis)
        self.risk_assessment = self.risk_manager.assess(self.goal_analysis, self.current_strategy)
        if not self.risk_assessment.get("can_proceed", True):
            self.session.log("CRITICAL RISKS DETECTED - proceeding with mitigation plans")
            for risk in self.risk_assessment.get("risks", []):
                if risk.get("severity") == "critical":
                    self.session.log(f"  Mitigation: {risk.get('mitigation_plan', 'N/A')}")
        save_checkpoint(self.state, {"strategy": self.current_strategy,
                                      "risk_assessment": self.risk_assessment},
                       self.session.load_progress(), self.session.load_context(), "strategy_created")
        self.state.transition(AgentState.PLANNING)

    def _phase_planning(self):
        self.session.log("Phase: PLANNING")
        self.state.transition(AgentState.PLANNING)
        goal = self.session.get_goal()
        if not goal:
            self.state.transition(AgentState.FAILED)
            return
        analysis = self.goal_analysis or self.session.load_context().get("goal_analysis", {})
        try:
            steps = self.planner.create_plan(goal, analysis)
            dod = self.goal_analysis.get("definition_of_done", []) if self.goal_analysis else []
            for item in dod:
                self.session.log(f"  DoD: {item}")
            self.session.record_decision(f"Plan created with {len(steps)} steps, {len(dod)} DoD items")
            save_checkpoint(self.state, steps, self.session.load_progress(),
                           self.session.load_context(), "planning_done")
            self.state.transition(AgentState.EXECUTING)
        except Exception as e:
            self.session.record_error(str(e), "planning_phase")
            self.state.transition(AgentState.FAILED)

    def _phase_autonomous_replanning(self):
        self.session.log("Phase: AUTONOMOUS REPLANNING")
        self.state.transition(AgentState.REPLANNING)
        self._replan_count += 1

        progress = self.session.load_progress()
        failed = progress.get("failed_steps", [])
        self.session.log(f"Analyzing {len(failed)} failed steps...")

        self._last_strategies_tried.append(
            self.current_strategy.get("id") if self.current_strategy else "unknown"
        )

        self.strategy_engine.mark_failed(
            self.current_strategy.get("id") if self.current_strategy else ""
        )

        prev_missions = self.learning_engine.get_knowledge_for_domain(
            self.goal_analysis.get("domain", "") if self.goal_analysis else ""
        )
        if prev_missions:
            self.session.log(f"Consulted memory: {len(prev_missions)} similar past missions found")

        new_strategy = self.strategy_engine.select_next_best(
            self.goal_analysis or self.session.load_context().get("goal_analysis", {})
        )
        if new_strategy:
            self.current_strategy = new_strategy
            self.session.log(f"New strategy: {new_strategy['name']}")
        else:
            self.session.log("No alternative strategies available. Re-planning with same approach.")

        self.risk_assessment = self.risk_manager.assess(
            self.goal_analysis or {}, self.current_strategy
        )

        self.state.transition(AgentState.PLANNING)

    def _phase_executing(self):
        self.session.log("Phase: EXECUTING")
        self.state.transition(AgentState.EXECUTING)
        progress = self.session.load_progress()
        next_step = self._get_next_step(progress)
        if next_step is None:
            self.state.transition(AgentState.SUCCESS_EVALUATING)
            return
        self.session.log(f"Executing step {next_step['id']}: {next_step['action']} - {next_step['description']}")
        tool_selection = self.tool_selector.select_tool(next_step.get("action", "general"))
        save_checkpoint(self.state, progress.get("steps", []), progress,
                       self.session.load_context(), f"before_step_{next_step['id']}")
        context = self.session.load_context()
        t_start = time.time()
        result = self.executor.execute(next_step, context)
        t_elapsed = time.time() - t_start
        self.tool_selector.record_result(tool_selection["tool"], result["status"] == "completed", t_elapsed)
        self.session.save_context({**context, f"step_{next_step['id']}_result": result})
        if result["status"] == "failed":
            self.planner.update_step_status(next_step["id"], "failed")
        self.current_step = next_step
        self.current_result = result
        self.evidence_collector.collect_file(
            os.path.join(self.session.base_dir, "memory", "progress.json"),
            category="execution"
        )
        self.state.transition(AgentState.VALIDATING)

    def _phase_validating(self):
        self.session.log("Phase: VALIDATING")
        self.state.transition(AgentState.VALIDATING)
        step = getattr(self, 'current_step', None)
        if step is None:
            progress = self.session.load_progress()
            step = self._get_last_executed_step(progress)
        if step is None:
            self.state.transition(AgentState.SUCCESS_EVALUATING)
            return
        result = getattr(self, 'current_result', None) or self.executor.results.get(step["id"], {})
        validation = self.validator.validate(step, result)
        if validation["status"] in ("passed", "warning"):
            pass_type = "PASSED" if validation["status"] == "passed" else "PASSED (warning)"
            self.session.log(f"Step {step['id']} {pass_type} validation")
            self.planner.update_step_status(step["id"], "completed")
            self.session.record_decision(f"Step {step['id']} completed successfully")
            self.learning_engine.learn_from_success(step, result)
            self.evidence_collector.collect_test_result(
                f"step_{step['id']}", True, result.get("output", "")
            )
            prog = self.session.load_progress()
            save_checkpoint(self.state, prog.get("steps", []), prog,
                           self.session.load_context(), f"step_{step['id']}_passed")
            dod = self.goal_analysis.get("definition_of_done", []) if self.goal_analysis else []
            ac = self.goal_analysis.get("acceptance_criteria", []) if self.goal_analysis else []
            steps_done = len(prog.get("completed_steps", []))
            steps_total = len(prog.get("steps", []))
            if steps_done >= steps_total:
                self.session.log(f"All {steps_total} steps completed. Checking DoD ({len(dod)} items) and AC ({len(ac)} criteria)")
                self.state.transition(AgentState.SUCCESS_EVALUATING)
            else:
                self.state.transition(AgentState.EXECUTING)
        else:
            self.session.log(f"Step {step['id']} FAILED validation: {validation.get('errors', [])}")
            self.planner.update_step_status(step["id"], "failed")
            self.learning_engine.learn_from_error(
                str(validation.get('errors', [])),
                f"Step {step['id']}: {step.get('action', '')}",
                step
            )
            self.evidence_collector.collect_test_result(
                f"step_{step['id']}", False, str(validation.get('errors', []))
            )
            self.state.transition(AgentState.VALIDATION_FAILED)

    def _phase_recovering(self):
        self.session.log("Phase: RECOVERING")
        self.state.transition(AgentState.RECOVERING)
        progress = self.session.load_progress()
        step = self._find_failed_step(progress)
        if step is None:
            self.state.transition(AgentState.PLANNING)
            return
        result = self.executor.results.get(step["id"], {})
        validation = self.validator.validate(step, result)
        diagnosis = self.recovery.diagnose(step, result, validation)
        rules = self.learning_engine.get_relevant_rules(str(diagnosis.get("errors", "")))
        if rules:
            self.session.log(f"Applying learned rule: {rules[0].get('suggested_fix', '')[:80]}")
            self.learning_engine.mark_rule_applied(rules[0].get("error_key", ""))
        recovery_plan = self.recovery.recover(step, diagnosis)
        if recovery_plan["action"] == "retry":
            self.session.log(f"Retrying step {step['id']}")
            self.state.transition(AgentState.EXECUTING)
        elif recovery_plan["action"] == "replan":
            self.session.log("Replanning required")
            self.recovery.reset_retries(step["id"])
            self.state.transition(AgentState.LEARNING)
        else:
            self.session.log(f"Recovery action: {recovery_plan['action']}")
            self.state.transition(AgentState.LEARNING)

    def _phase_learning(self):
        self.session.log("Phase: LEARNING")
        self.state.transition(AgentState.LEARNING)
        progress = self.session.load_progress()
        stats = self.learning_engine.get_statistics()
        self.session.log(f"Learning stats: {stats['success_rate']}% success rate "
                        f"({stats['total_learned_rules']} rules, "
                        f"{stats['total_prev_missions']} past missions, "
                        f"{stats['total_tools_tracked']} tools tracked)")
        self.session.record_decision(
            f"Learning cycle: {stats['total_failures']} failures, "
            f"{stats['total_successes']} successes, "
            f"{stats['total_arch_patterns']} arch patterns"
        )
        failed_count = len(progress.get("failed_steps", []))
        retry_count = sum(self.recovery.retry_counts.values())
        max_retries = self.config.get("loop", {}).get("max_retries_per_step", 3) * 2
        if retry_count >= max_retries and failed_count > 0:
            self.session.log("Max retries reached. Entering autonomous replanning.")
            self.state.transition(AgentState.REPLANNING)
        elif failed_count > 0:
            self.state.transition(AgentState.EXECUTING)
        else:
            self.state.transition(AgentState.SUCCESS_EVALUATING)

    def _phase_success_eval(self):
        self.session.log("Phase: SUCCESS EVALUATION")
        self.state.transition(AgentState.SUCCESS_EVALUATING)
        progress = self.session.load_progress()
        analysis = self.goal_analysis or self.session.load_context().get("goal_analysis", {})
        evaluation = self.success_evaluator.evaluate(
            analysis, progress,
            test_results={"passed": len(progress.get("completed_steps", [])),
                         "total": len(progress.get("steps", []))},
            evidence=self.evidence_collector.get_summary(),
        )
        self.session.save_context({**self.session.load_context(), "success_evaluation": evaluation})
        self.session.log(f"Success score: {evaluation['total_score']}% "
                        f"(threshold: {evaluation['threshold']}%)")
        self.session.log(f"Breakdown: {evaluation['breakdown']}")
        if evaluation["passed"]:
            self.session.record_decision(
                f"Success evaluation PASSED: {evaluation['total_score']}% >= {evaluation['threshold']}%"
            )
            self.state.transition(AgentState.FINAL_AUDITING)
        else:
            self.session.log(f"Score {evaluation['total_score']}% below threshold {evaluation['threshold']}%")
            missing = []
            for category, score in evaluation.get("breakdown", {}).items():
                if score < 80:
                    missing.append(f"{category}: {score}%")
            self.session.log(f"Low scores: {', '.join(missing)}")
            progress_data = self.session.load_progress()
            if progress_data.get("failed_steps"):
                self.state.transition(AgentState.REPLANNING)
            else:
                self.state.transition(AgentState.SUCCESS_VERIFIED)

    def _phase_final_audit(self):
        self.session.log("Phase: FINAL AUDIT")
        self.state.transition(AgentState.FINAL_AUDITING)
        progress = self.session.load_progress()
        analysis = self.goal_analysis or self.session.load_context().get("goal_analysis", {})
        success_eval = self.session.load_context().get("success_evaluation", {})
        audit = self.final_auditor.audit(analysis, progress, self.current_strategy, success_eval,
                                        evidence=self.evidence_collector.get_summary())
        dod = analysis.get("definition_of_done", []) if analysis else []
        ac = analysis.get("acceptance_criteria", []) if analysis else []
        dod_checked = sum(1 for item in dod if item in [
            s.get("description", "") for s in progress.get("steps", [])
        ]) if dod else 0
        self.session.log(f"DoD: {dod_checked}/{len(dod)} satisfied, "
                        f"AC: {len(ac)} defined")
        self.final_auditor.generate_final_report(
            goal_analysis=analysis,
            progress=progress,
            strategy=self.current_strategy,
            success_evaluation=success_eval,
            audit_result=audit,
            evidence=self.evidence_collector.get_summary(),
            risk_assessment=self.risk_assessment,
        )
        if audit.get("all_checked"):
            self.session.log("FINAL AUDIT PASSED")
            self.state.transition(AgentState.SUCCESS_VERIFIED)
        else:
            self.session.log(f"FINAL AUDIT: {audit.get('all_checked')} - needs improvement")
            unchecked = [i["item"] for i in audit.get("checklist", []) if not i.get("checked")]
            self.session.record_decision(f"Audit failed. Unchecked: {unchecked}")
            if progress.get("failed_steps"):
                self.state.transition(AgentState.REPLANNING)
            else:
                self.state.transition(AgentState.SUCCESS_VERIFIED)

    def _phase_success_verified(self):
        self.session.log("Phase: SUCCESS VERIFIED")
        self.state.transition(AgentState.SUCCESS_VERIFIED)
        self.session.log("=" * 60)
        self.session.log("GOAL ACHIEVED - ALL VALIDATIONS PASSED")
        self.session.log("=" * 60)
        dod = self.goal_analysis.get("definition_of_done", []) if self.goal_analysis else []
        ac = self.goal_analysis.get("acceptance_criteria", []) if self.goal_analysis else []
        self.session.log(f"Criterio absoluto: DoD ({len(dod)} items), AC ({len(ac)} criteria)")
        self.state.transition(AgentState.COMPLETED)

    def _get_next_step(self, progress):
        for step in progress.get("steps", []):
            if step.get("status") == "pending":
                return step
        return None

    def _get_last_executed_step(self, progress):
        current = progress.get("current_step", 0)
        for step in progress.get("steps", []):
            if step["id"] == current:
                return step
        if progress.get("steps"):
            return progress["steps"][-1]
        return None

    def _find_failed_step(self, progress):
        step_id = progress.get("current_step", 0)
        for s in progress.get("steps", []):
            if s["id"] == step_id and s["status"] == "failed":
                return s
        for s in reversed(progress.get("steps", [])):
            if s["status"] == "failed":
                return s
        return None

    def _finalize(self, reason):
        elapsed = self.session.elapsed()
        progress = self.session.load_progress()
        stats = self.learning_engine.get_statistics()
        dod = self.goal_analysis.get("definition_of_done", []) if self.goal_analysis else []
        ac = self.goal_analysis.get("acceptance_criteria", []) if self.goal_analysis else []
        report = {
            "status": reason,
            "version": "2.0.0",
            "elapsed_seconds": elapsed,
            "iterations": self.iteration,
            "steps_total": len(progress.get("steps", [])),
            "steps_completed": len(progress.get("completed_steps", [])),
            "steps_failed": len(progress.get("failed_steps", [])),
            "state_history": self.state.history,
            "learning": stats,
            "evidence": self.evidence_collector.get_summary(),
            "tool_stats": self.tool_selector.get_tool_report(),
            "definition_of_done": dod,
            "acceptance_criteria": ac,
            "definition_of_done_satisfied": len(progress.get("completed_steps", [])) >= len(progress.get("steps", [])),
        }
        if self.goal_analysis:
            report["domain"] = self.goal_analysis.get("domain")
            report["complexity"] = self.goal_analysis.get("complexity")
            report["goal_objective"] = self.goal_analysis.get("objective")
        if self.current_strategy:
            report["strategy"] = self.current_strategy.get("name")
        if self.risk_assessment:
            report["risks"] = {
                "total": self.risk_assessment.get("total_risks", 0),
                "critical": self.risk_assessment.get("critical_count", 0),
                "high": self.risk_assessment.get("high_count", 0),
            }
        self.evidence_collector.finish_mission()
        self.evidence_collector.generate_report()
        self.learning_engine.learn_from_mission(report)
        self.self_improvement.evaluate_mission(report)
        health_report = self.supervisor.get_health_report()
        report["supervisor"] = health_report
        self.session.log("=" * 60)
        self.session.log(f"AGENT FINALIZED: {reason.upper()}")
        self.session.log(f"v2.0 | Elapsed: {elapsed:.1f}s | Iterations: {self.iteration}")
        self.session.log(f"Steps: {report['steps_completed']}/{report['steps_total']} completed")
        self.session.log(f"DoD: {len(dod)} items, AC: {len(ac)} criteria")
        self.session.log(f"Learning: {stats['total_learned_rules']} rules, "
                        f"{stats['success_rate']}% success rate")
        self.session.log(f"Tools: {len(report.get('tool_stats', {}))} tracked")
        self.session.log(f"Supervisor: {health_report['healthy']}/{health_report['total_modules']} modules healthy")
        self.session.log("=" * 60)
        save_checkpoint(self.state, progress.get("steps", []), progress,
                       self.session.load_context(), f"final_{reason}")
        return report

    def run_iteration(self):
        if self._loop_done:
            return {"action": "complete", "reason": "already_completed"}
        if self.state.current == AgentState.IDLE:
            self.state.transition(AgentState.INIT)
        self.iteration += 1
        self.session.log(f"\n--- LER Iteration {self.iteration} ---")
        self.session.log(f"State: {self.state.current}")
        handlers = {
            AgentState.INIT: lambda: self._phase_analyze_goal(),
            AgentState.ANALYZING_GOAL: lambda: self._phase_analyze_goal(),
            AgentState.CREATING_STRATEGY: lambda: self._phase_create_strategy(),
            AgentState.PLANNING: lambda: self._phase_planning(),
            AgentState.REPLANNING: lambda: self._phase_autonomous_replanning(),
            AgentState.EXECUTING: lambda: self._phase_executing(),
            AgentState.VALIDATING: lambda: self._phase_validating(),
            AgentState.VALIDATION_FAILED: lambda: self._phase_recovering(),
            AgentState.RECOVERING: lambda: self._phase_recovering(),
            AgentState.LEARNING: lambda: self._phase_learning(),
            AgentState.SUCCESS_EVALUATING: lambda: self._phase_success_eval(),
            AgentState.FINAL_AUDITING: lambda: self._phase_final_audit(),
            AgentState.SUCCESS_VERIFIED: lambda: self._phase_success_verified(),
            AgentState.COMPLETED: lambda: self._handle_complete(),
            AgentState.FAILED: lambda: self._handle_failed(),
        }
        handler = handlers.get(self.state.current)
        if handler:
            result = handler()
            if result:
                return result
        return {"action": "continue", "reason": "iteration_complete"}

    def _handle_complete(self):
        self._loop_done = True
        return {"action": "complete", "reason": "goal_achieved"}

    def _handle_failed(self):
        self._loop_done = True
        return {"action": "failed", "reason": "permanent_failure"}
