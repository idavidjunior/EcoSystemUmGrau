"""
OpenCode Bridge - Connects OpenCode with the Loop Engineering Agent.

Allows OpenCode to:
- Start the Loop Agent with a goal
- Query status
- Receive reports
- Execute delegated tasks
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime


class OpenCodeBridge:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.config_path = os.path.join(base_dir, "integrations", "opencode", "opencode_config.json")
        self.config = self._load_config()
        self.session = None

    def _load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def delegate_goal(self, goal_text):
        """Receive a goal from OpenCode and start the Loop Agent."""
        sys.path.insert(0, self.base_dir)
        from core.session import Session
        from core.checkpoint import init_checkpoint_dir
        from agent.orchestrator import Orchestrator

        init_checkpoint_dir(self.base_dir)
        session = Session(self.base_dir)
        self.session = session

        config_path = os.path.join(self.base_dir, "config", "config.json")
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        session.log("[OpenCode Bridge] Goal delegated from OpenCode")
        session.log(f"[OpenCode Bridge] Goal: {goal_text[:100]}")

        orchestrator = Orchestrator(session, config)
        result = orchestrator.run(goal_text)

        return result

    def get_status(self):
        """Return current status for OpenCode consumption."""
        if self.session is None:
            sys.path.insert(0, self.base_dir)
            from core.session import Session
            self.session = Session(self.base_dir)

        goal = self.session.get_goal()
        progress = self.session.load_progress()
        plan = self.session.get_plan()

        return {
            "status": "active" if goal else "idle",
            "goal": goal[:200] if goal else None,
            "plan_preview": plan[:500] if plan else None,
            "progress": {
                "total": len(progress.get("steps", [])),
                "completed": len(progress.get("completed_steps", [])),
                "failed": len(progress.get("failed_steps", [])),
                "current_step": progress.get("current_step", 0)
            },
            "timestamp": datetime.now().isoformat()
        }

    def execute_command(self, command):
        """Execute a shell command requested by OpenCode."""
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            return {
                "status": "completed",
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "exit_code": proc.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "error": "Command timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    def generate_report(self):
        """Generate a full execution report for OpenCode."""
        if self.session is None:
            sys.path.insert(0, self.base_dir)
            from core.session import Session
            self.session = Session(self.base_dir)

        from agent.final_auditor import FinalAuditor
        auditor = FinalAuditor(self.session, self.base_dir)
        report = auditor.generate_final_report()

        report_path = os.path.join(self.base_dir, "reports", "final_report.md")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        return report

    def run_opencode_agent(self, opencode_args=None):
        """Run an OpenCode agent task through the LEA bridge."""
        config = self.config.get("opencode_agent", {})
        agent_path = config.get("path", "opencode")
        args = opencode_args or config.get("default_args", [])

        cmd = [agent_path] + args
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            return {
                "status": "completed",
                "output": proc.stdout,
                "errors": proc.stderr,
                "exit_code": proc.returncode
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
