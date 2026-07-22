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

class Orchestrator:
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.state = AgentState()
        self.planner = Planner(session, config)
        self.executor = Executor(session, config)
        self.validator = Validator(session, config)
        self.recovery = Recovery(session, config)
        self.max_iterations = config.get("loop", {}).get("max_iterations", 100)
        self.iteration = 0

    def run(self, goal_text):
        self.session.log("=" * 60)
        self.session.log(f"LOOP ENGINEERING AGENT v1.0 STARTED")
        self.session.log("=" * 60)

        latest_cp = get_latest_checkpoint()
        if latest_cp:
            self.session.log(f"Checkpoint found: {latest_cp}")
            should_restore = input(f"Restore from checkpoint {latest_cp}? (y/n): ").strip().lower() == 'y'
            if should_restore:
                return self._restore_and_continue(latest_cp)

        self.session.set_goal(goal_text)
        self.state.transition(AgentState.INIT)
        return self._execution_loop()

    def _execution_loop(self):
        while self.iteration < self.max_iterations:
            self.iteration += 1
            self.session.log(f"\n--- Iteration {self.iteration} ---")

            if self.state.current == AgentState.INIT:
                self._phase_planning()
            elif self.state.current == AgentState.PLANNING:
                self._phase_planning()
            elif self.state.current == AgentState.EXECUTING:
                self._phase_executing()
            elif self.state.current == AgentState.VALIDATING:
                self._phase_validating()
            elif self.state.current == AgentState.VALIDATION_FAILED:
                self._phase_recovering()
            elif self.state.current == AgentState.RECOVERING:
                self._phase_recovering()
            elif self.state.current == AgentState.COMPLETED:
                return self._finalize("completed")
            elif self.state.current == AgentState.FAILED:
                return self._finalize("failed")
            else:
                self.session.log(f"Unknown state: {self.state.current}")
                break

        return self._finalize("max_iterations")

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

    def _phase_executing(self):
        self.session.log("Phase: EXECUTING")
        self.state.transition(AgentState.EXECUTING)

        progress = self.session.load_progress()
        next_step = self._get_next_step(progress)

        if next_step is None:
            self.state.transition(AgentState.COMPLETED)
            return

        self.session.log(f"Executing step {next_step['id']}: {next_step['action']} - {next_step['description']}")

        save_checkpoint(self.state, progress.get("steps", []), progress,
                       self.session.load_context(), f"before_step_{next_step['id']}")

        context = self.session.load_context()
        result = self.executor.execute(next_step, context)

        self.session.save_context({**context, f"step_{next_step['id']}_result": result})

        if result["status"] == "failed":
            self.planner.update_step_status(next_step["id"], "failed")
            self.state.transition(AgentState.VALIDATING)
        else:
            self.state.transition(AgentState.VALIDATING)

        self.current_step = next_step

    def _phase_validating(self):
        self.session.log("Phase: VALIDATING")
        self.state.transition(AgentState.VALIDATING)

        step = getattr(self, 'current_step', None)
        if step is None:
            progress = self.session.load_progress()
            step = self._get_last_executed_step(progress)

        if step is None:
            self.state.transition(AgentState.COMPLETED)
            return

        result = self.executor.results.get(step["id"], {})
        validation = self.validator.validate(step, result)

        if validation["status"] in ("passed", "warning"):
            pass_type = "PASSED" if validation["status"] == "passed" else "PASSED (warning)"
            self.session.log(f"Step {step['id']} {pass_type} validation")
            self.planner.update_step_status(step["id"], "completed")
            self.session.record_decision(f"Step {step['id']} completed successfully")
            prog = self.session.load_progress()
            save_checkpoint(self.state, prog.get("steps", []), prog,
                          self.session.load_context(), f"step_{step['id']}_passed")

            goal_status = self.validator.validate_goal_complete(prog)
            if goal_status["status"] == "completed":
                self.state.transition(AgentState.COMPLETED)
            else:
                self.state.transition(AgentState.EXECUTING)
        else:
            self.session.log(f"Step {step['id']} FAILED validation: {validation.get('errors', [])}")
            self.planner.update_step_status(step["id"], "failed")
            self.state.transition(AgentState.VALIDATION_FAILED)

    def _phase_recovering(self):
        self.session.log("Phase: RECOVERING")
        self.state.transition(AgentState.RECOVERING)

        progress = self.session.load_progress()
        step_id = progress.get("current_step", 0)
        step = None
        for s in progress.get("steps", []):
            if s["id"] == step_id and s["status"] == "failed":
                step = s
                break
        if step is None:
            for s in reversed(progress.get("steps", [])):
                if s["status"] == "failed":
                    step = s
                    break

        if step is None:
            self.session.log("No failed step found for recovery")
            self.state.transition(AgentState.PLANNING)
            return

        result = self.executor.results.get(step["id"], {})
        validation = self.validator.validate(step, result)
        diagnosis = self.recovery.diagnose(step, result, validation)

        recovery_plan = self.recovery.recover(step, diagnosis)

        if recovery_plan["action"] == "retry":
            self.session.log(f"Retrying step {step['id']} ({recovery_plan.get('reason', 'unknown')})")
            self.state.transition(AgentState.EXECUTING)
        elif recovery_plan["action"] == "replan":
            self.session.log("Replanning required")
            self.recovery.reset_retries(step["id"])
            self.state.transition(AgentState.PLANNING)
        else:
            self.session.log(f"Unknown recovery action: {recovery_plan['action']}")
            self.state.transition(AgentState.FAILED)

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

        report = {
            "status": reason,
            "elapsed_seconds": elapsed,
            "iterations": self.iteration,
            "steps_total": len(progress.get("steps", [])),
            "steps_completed": len(progress.get("completed_steps", [])),
            "steps_failed": len(progress.get("failed_steps", [])),
            "state_history": self.state.history,
        }

        self.session.log("=" * 60)
        self.session.log(f"AGENT FINALIZED: {reason.upper()}")
        self.session.log(f"Elapsed: {elapsed:.1f}s | Iterations: {self.iteration}")
        self.session.log(f"Steps: {report['steps_completed']}/{report['steps_total']} completed")
        self.session.log("=" * 60)

        save_checkpoint(self.state, progress.get("steps", []), progress,
                       self.session.load_context(), f"final_{reason}")

        return report
