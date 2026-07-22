import os
import json
import subprocess

class Validator:
    def __init__(self, session, config):
        self.session = session
        self.config = config

    def validate(self, step, execution_result):
        self.session.log(f"Validating step {step['id']}: {step.get('validation', 'check_output')}")
        validation_type = step.get("validation", "check_output")
        method = getattr(self, f"_validate_{validation_type}", self._validate_check_output)
        result = method(step, execution_result)
        self.session.log(f"Validation: {result['status']}")
        return result

    def _validate_check_env(self, step, result):
        errors = []
        for tool in ["git", "python"]:
            try:
                subprocess.run(f"where {tool}", shell=True, capture_output=True, timeout=10, check=True)
            except:
                errors.append(f"{tool} not found")
        if errors:
            return {"status": "failed", "errors": errors, "step_id": step["id"]}
        return {"status": "passed", "step_id": step["id"]}

    def _validate_check_structure(self, step, result):
        base = self.session.base_dir
        required_dirs = ["agent", "core", "memory", "config", "logs", "checkpoints", "projects"]
        missing = [d for d in required_dirs if not os.path.isdir(os.path.join(base, d))]
        if missing:
            return {"status": "failed", "errors": [f"Missing directories: {missing}"], "step_id": step["id"]}
        return {"status": "passed", "step_id": step["id"]}

    def _validate_check_output(self, step, result):
        if result.get("status") == "failed":
            return {"status": "failed", "errors": [result.get("error", "Execution failed")], "step_id": step["id"]}
        if not result.get("output"):
            return {"status": "warning", "errors": ["No output produced"], "step_id": step["id"]}
        return {"status": "passed", "step_id": step["id"]}

    def _validate_check_research(self, step, result):
        return self._validate_check_output(step, result)

    def _validate_test_pass(self, step, result):
        if result.get("status") == "failed":
            return {"status": "failed", "errors": [result.get("error", "Test execution failed")], "step_id": step["id"]}
        output = result.get("output", "")
        try:
            data = json.loads(output)
            if data.get("tests_run", 0) == 0:
                return {"status": "warning", "errors": ["No tests found"], "step_id": step["id"]}
            failed = [t for t in data.get("results", []) if not t.get("passed")]
            if failed:
                return {"status": "failed", "errors": [f"{len(failed)} tests failed"], "details": failed, "step_id": step["id"]}
            return {"status": "passed", "step_id": step["id"], "tests_run": data.get("tests_run")}
        except (json.JSONDecodeError, TypeError):
            pass
        return {"status": "passed", "step_id": step["id"]}

    def _validate_check_git(self, step, result):
        try:
            proc = subprocess.run("git status --porcelain", shell=True, capture_output=True, text=True, timeout=15)
            if proc.stdout.strip():
                return {"status": "warning", "errors": ["Uncommitted changes remain"], "step_id": step["id"]}
            return {"status": "passed", "step_id": step["id"]}
        except Exception as e:
            return {"status": "failed", "errors": [str(e)], "step_id": step["id"]}

    def validate_goal_complete(self, progress):
        total = len(progress.get("steps", []))
        completed = len(progress.get("completed_steps", []))
        failed = len(progress.get("failed_steps", []))
        if total > 0 and completed >= total:
            return {"status": "completed", "total": total, "completed": completed, "failed": failed}
        return {"status": "in_progress", "total": total, "completed": completed, "failed": failed}
