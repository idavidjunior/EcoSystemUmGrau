import os
import subprocess
import json
import time
import re

MAX_RESULTS = 50


class Executor:
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.results = {}
        self._test_cache = None
        self._test_cache_hash = None

    def execute(self, step, context=None):
        self.session.log(f"Executing step {step['id']}: {step['action']}")
        action = step.get("action", "")
        description = step.get("description", "")
        command = step.get("command")

        result = {
            "step_id": step["id"],
            "action": action,
            "status": "running",
            "output": "",
            "error": None,
            "start_time": time.time(),
        }

        try:
            if command:
                output = self._run_command(command)
                result["output"] = output
                result["status"] = "completed"
            else:
                output = self._execute_action(action, description, context)
                result["output"] = output
                result["status"] = "completed"
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self.session.record_error(str(e), f"Step {step['id']}: {action}")

        result["duration"] = time.time() - result["start_time"]
        self.results[step["id"]] = result
        if len(self.results) > MAX_RESULTS:
            oldest = min(self.results.keys())
            del self.results[oldest]
        self.session.log(f"Step {step['id']} {result['status']} ({result['duration']:.1f}s)")
        return result

    def _run_command(self, command):
        self.session.log(f"Running: {command}")
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = proc.stdout + "\n" + proc.stderr
            if proc.returncode != 0:
                raise RuntimeError(f"Command failed (exit={proc.returncode}): {proc.stderr[:500]}")
            return output
        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Command timed out: {command[:80]}")

    def _execute_action(self, action, description, context):
        handlers = {
            "analyze_environment": self._action_analyze_env,
            "initialize_project": self._action_init_project,
            "implement": self._action_implement,
            "diagnose": self._action_diagnose,
            "fix": self._action_fix,
            "refactor": self._action_refactor,
            "test": self._action_test,
            "run_tests": self._action_test,
            "git_commit": self._action_git_commit,
            "gather_information": self._action_gather_info,
            "analyze": self._action_analyze,
        }
        handler = handlers.get(action, self._action_generic)
        return handler(description)

    def _action_analyze_env(self, desc):
        info = {}
        info["os"] = os.name
        info["cwd"] = os.getcwd()
        info["python"] = self._which("python")
        info["git"] = self._which("git")
        info["node"] = self._which("node")
        info["shell"] = os.environ.get("SHELL", "powershell")
        return json.dumps(info, indent=2)

    def _action_init_project(self, desc):
        projects_dir = os.path.join(self.session.base_dir, "projects")
        os.makedirs(projects_dir, exist_ok=True)
        return f"Projects directory ready: {projects_dir}"

    def _action_implement(self, desc):
        return f"Implementation delegated to OpenCode: {desc}"

    def _action_diagnose(self, desc):
        return f"Diagnosis needed: {desc}"

    def _action_fix(self, desc):
        return f"Fix needed: {desc}"

    def _action_refactor(self, desc):
        return f"Refactoring needed: {desc}"

    def _action_test(self, desc):
        test_dir = os.path.join(self.session.base_dir, "tests")
        results = []
        if os.path.isdir(test_dir):
            current_hash = self._compute_test_hash(test_dir)
            if self._test_cache_hash == current_hash and self._test_cache is not None:
                self.session.log("Test cache hit — no changes detected")
                return json.dumps(self._test_cache, indent=2)
            for f in sorted(os.listdir(test_dir)):
                if f.endswith(".py"):
                    try:
                        proc = subprocess.run(
                            ["python", os.path.join(test_dir, f)],
                            capture_output=True, text=True, timeout=60
                        )
                        results.append({
                            "file": f,
                            "passed": proc.returncode == 0,
                            "output": proc.stdout[-200:] if proc.stdout else proc.stderr[-200:]
                        })
                    except Exception as e:
                        results.append({"file": f, "passed": False, "output": str(e)})
            self._test_cache = {"tests_run": len(results), "results": results}
            self._test_cache_hash = current_hash
        return json.dumps({"tests_run": len(results), "results": results}, indent=2)

    def _compute_test_hash(self, test_dir):
        import hashlib
        h = hashlib.md5()
        for f in sorted(os.listdir(test_dir)):
            if f.endswith(".py"):
                fpath = os.path.join(test_dir, f)
                try:
                    with open(fpath, "rb") as fh:
                        h.update(fh.read())
                except Exception:
                    pass
        return h.hexdigest()

    def _action_git_commit(self, desc):
        try:
            proc = subprocess.run(
                "git add -A && git commit -m \"[LEA] Automated commit\"",
                shell=True, capture_output=True, text=True, timeout=30
            )
            return proc.stdout + "\n" + proc.stderr
        except Exception as e:
            return f"Git commit skipped: {e}"

    def _action_gather_info(self, desc):
        return f"Research needed: {desc}"

    def _action_analyze(self, desc):
        return f"Analysis needed: {desc}"

    def _action_generic(self, desc):
        return f"Generic action: {desc}"

    def _which(self, cmd):
        try:
            proc = subprocess.run(f"where {cmd}", shell=True, capture_output=True, text=True, timeout=10)
            return proc.stdout.strip().split('\n')[0] if proc.returncode == 0 else None
        except:
            return None
