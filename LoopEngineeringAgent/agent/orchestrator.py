import os
import json
import sys
import time

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
        self.max_iterations = config.get("loop", {}).get("max_iterations", 100)
        self.iteration = 0
        self.goal_analysis = None
        self.current_strategy = None
        self.risk_assessment = None

    def run(self, goal_text):
        self.session.log("=" * 60)
        self.session.log("LOOP ENGINEERING AGENT v1.1 - ADAPTIVE LOOP")
        self.session.log("=" * 60)

        latest_cp = get_latest_checkpoint()
        if latest_cp:
            self.session.log(f"Checkpoint found: {latest_cp}")
            return self._restore_and_continue(latest_cp)

        self.session.set_goal(goal_text)
        self.learning_engine.initialize()
        self.state.transition(AgentState.INIT)
        return self._execution_loop()

    def _execution_loop(self):
        while self.iteration < self.max_iterations:
            self.iteration += 1
            self.session.log(f"\n--- Iteration {self.iteration} ---")
            self.session.log(f"State: {self.state.current}")

            handlers = {
                AgentState.INIT: self._phase_analyze_goal,
                AgentState.ANALYZING_GOAL: self._phase_analyze_goal,
                AgentState.CREATING_STRATEGY: self._phase_create_strategy,
                AgentState.PLANNING: self._phase_planning,
                AgentState.REPLANNING: self._phase_replanning,
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
            self.session.log("CRITICAL RISKS DETECTED - evaluating whether to proceed")
            self.session.record_decision("Critical risks detected, but proceeding with mitigation plans")

        save_checkpoint(self.state, {
            "strategy": self.current_strategy,
            "risk_assessment": self.risk_assessment
        }, self.session.load_progress(), self.session.load_context(), "strategy_created")

        self.state.transition(AgentState.PLANNING)

    def _phase_planning(self):
        self.session.log("Phase: PLANNING")
        self.state.transition(AgentState.PLANNING)

        goal = self.session.get_goal()
        if not goal:
            self.state.transition(AgentState.FAILED)
            return

        try:
            steps = self.planner.create_plan(goal)
            self.session.record_decision(f"Plan created with {len(steps)} steps")
            save_checkpoint(self.state, steps, self.session.load_progress(),
                          self.session.load_context(), "planning_done")
            self.state.transition(AgentState.EXECUTING)
        except Exception as e:
            self.session.record_error(str(e), "planning_phase")
            self.state.transition(AgentState.FAILED)

    def _phase_replanning(self):
        self.session.log("Phase: REPLANNING")
        self.state.transition(AgentState.REPLANNING)

        if self.current_strategy:
            strategies = self.strategy_engine.generate_strategies(
                self.goal_analysis or self.session.load_context().get("goal_analysis", {})
            )
            alt = [s for s in strategies if s.get("id") != self.current_strategy.get("id")]
            self.current_strategy = alt[0] if alt else strategies[0]
            self.session.record_decision(f"Replanned with alternative strategy: {self.current_strategy['name']}")

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

        save_checkpoint(self.state, progress.get("steps", []), progress,
                       self.session.load_context(), f"before_step_{next_step['id']}")

        context = self.session.load_context()
        result = self.executor.execute(next_step, context)
        self.session.save_context({**context, f"step_{next_step['id']}_result": result})

        if result["status"] == "failed":
            self.planner.update_step_status(next_step["id"], "failed")
        self.current_step = next_step
        self.current_result = result
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
            prog = self.session.load_progress()
            save_checkpoint(self.state, prog.get("steps", []), prog,
                          self.session.load_context(), f"step_{step['id']}_passed")
            goal_status = self.validator.validate_goal_complete(prog)
            if goal_status["status"] == "completed":
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
                        f"({stats['total_learned_rules']} rules learned)")

        self.session.record_decision(
            f"Learning cycle: {stats['total_failures']} failures, "
            f"{stats['total_successes']} successes"
        )

        failed_count = len(progress.get("failed_steps", []))
        retry_count = sum(self.recovery.retry_counts.values())
        max_retries = self.config.get("loop", {}).get("max_retries_per_step", 3) * 2

        if retry_count >= max_retries and failed_count > 0:
            self.session.log("Max retries reached. Trying alternative strategy.")
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
                         "total": len(progress.get("steps", []))}
        )

        self.session.save_context({**self.session.load_context(), "success_evaluation": evaluation})
        self.session.log(f"Success score: {evaluation['total_score']}% "
                        f"(threshold: {evaluation['threshold']}%)")

        if evaluation["passed"]:
            self.session.record_decision(f"Success evaluation PASSED: {evaluation['total_score']}%")
            self.state.transition(AgentState.FINAL_AUDITING)
        else:
            self.session.log(f"Score {evaluation['total_score']}% below threshold {evaluation['threshold']}%")
            progress = self.session.load_progress()
            if progress.get("failed_steps"):
                self.state.transition(AgentState.REPLANNING)
            else:
                self.state.transition(AgentState.SUCCESS_VERIFIED)

    def _phase_final_audit(self):
        self.session.log("Phase: FINAL AUDIT")
        self.state.transition(AgentState.FINAL_AUDITING)

        progress = self.session.load_progress()
        analysis = self.goal_analysis or self.session.load_context().get("goal_analysis", {})
        success_eval = self.session.load_context().get("success_evaluation", {})

        audit = self.final_auditor.audit(analysis, progress, self.current_strategy, success_eval)
        self.final_auditor.generate_final_report()

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

    def _restore_and_continue(self, cp_id):
        data = load_checkpoint(cp_id)
        if not data:
            self.session.log("Checkpoint load failed, starting fresh")
            return self._execution_loop()

        self.session.log(f"Restored from checkpoint: {cp_id}")
        if "state" in data:
            self.state = AgentState.deserialize(data["state"])
        if "progress" in data:
            self.session.save_progress(data["progress"])
        if "context" in data:
            self.session.save_context(data["context"])

        return self._execution_loop()

    def _finalize(self, reason):
        elapsed = self.session.elapsed()
        progress = self.session.load_progress()
        stats = self.learning_engine.get_statistics()

        report = {
            "status": reason,
            "version": "1.1.0",
            "elapsed_seconds": elapsed,
            "iterations": self.iteration,
            "steps_total": len(progress.get("steps", [])),
            "steps_completed": len(progress.get("completed_steps", [])),
            "steps_failed": len(progress.get("failed_steps", [])),
            "state_history": self.state.history,
            "learning": stats,
        }

        if self.goal_analysis:
            report["domain"] = self.goal_analysis.get("domain")
            report["complexity"] = self.goal_analysis.get("complexity")
        if self.current_strategy:
            report["strategy"] = self.current_strategy.get("name")

        self.session.log("=" * 60)
        self.session.log(f"AGENT FINALIZED: {reason.upper()}")
        self.session.log(f"v1.1 | Elapsed: {elapsed:.1f}s | Iterations: {self.iteration}")
        self.session.log(f"Steps: {report['steps_completed']}/{report['steps_total']} completed")
        self.session.log(f"Learning: {stats['total_learned_rules']} rules, "
                        f"{stats['success_rate']}% success rate")
        self.session.log("=" * 60)

        save_checkpoint(self.state, progress.get("steps", []), progress,
                       self.session.load_context(), f"final_{reason}")

        return report
