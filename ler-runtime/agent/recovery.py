import os
import json
import time
import traceback

class Recovery:
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.retry_counts = {}
        self.max_retries = config.get("loop", {}).get("max_retries_per_step", 3)

    def diagnose(self, step, execution_result, validation_result):
        self.session.log(f"Diagnosing failure in step {step['id']}")
        errors = []
        if execution_result.get("error"):
            errors.append({"source": "execution", "message": execution_result["error"]})
        if validation_result.get("errors"):
            for e in validation_result["errors"]:
                errors.append({"source": "validation", "message": e})

        diagnosis = {
            "step_id": step["id"],
            "action": step.get("action"),
            "errors": errors,
            "retry_count": self.retry_counts.get(step["id"], 0),
            "max_retries": self.max_retries,
        }

        self.session.record_decision(
            f"Diagnosis for step {step['id']} ({step.get('action')}): {len(errors)} error(s)"
        )
        return diagnosis

    def recover(self, step, diagnosis):
        step_id = step["id"]
        current_retries = self.retry_counts.get(step_id, 0)
        self.retry_counts[step_id] = current_retries + 1

        self.session.log(f"Recovery attempt {current_retries + 1}/{self.max_retries} for step {step_id}")

        if current_retries >= self.max_retries:
            self.session.log(f"Max retries reached for step {step_id}")
            return {"action": "replan", "reason": "max_retries_exceeded"}

        error_messages = [e.get("message", "") for e in diagnosis.get("errors", [])]
        combined = " ".join(error_messages).lower()

        if "timeout" in combined:
            return {
                "action": "retry",
                "modifications": {"timeout_multiplier": 2},
                "reason": "timeout"
            }
        elif "not found" in combined or "missing" in combined:
            return {
                "action": "retry",
                "pre_command": "echo 'Checking prerequisites...'",
                "reason": "missing_dependency"
            }
        elif "syntax" in combined or "compile" in combined or "error" in combined:
            return {
                "action": "retry",
                "modifications": {"fix_mode": True},
                "reason": "syntax_error"
            }
        elif "permission" in combined or "denied" in combined or "access" in combined:
            return {
                "action": "retry",
                "pre_command": "echo 'Checking permissions...'",
                "reason": "permission_denied"
            }
        else:
            return {
                "action": "retry",
                "reason": "unknown_error",
                "modifications": {"retry_clean": True}
            }

    def should_replan(self, step, diagnosis):
        step_id = step["id"]
        return self.retry_counts.get(step_id, 0) >= self.max_retries

    def reset_retries(self, step_id):
        if step_id in self.retry_counts:
            del self.retry_counts[step_id]
