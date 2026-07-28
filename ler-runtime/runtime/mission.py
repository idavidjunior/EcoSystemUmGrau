"""
Mission Runtime - Core execution loop for LER.
Controls mission lifecycle: receive -> understand -> plan -> execute -> validate -> persist.
Mission only ends when goal is PROVABLY achieved (Principio da Missao).
"""

import os
import sys
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


class MissionRuntime:
    def __init__(self, session, config, persistence, security):
        self.session = session
        self.config = config
        self.persistence = persistence
        self.security = security
        self.mission_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.iteration = 0
        self.max_iterations = config.get("loop", {}).get("max_iterations", 100)

    def execute(self, goal_text):
        self.session.log("=" * 60)
        self.session.log(f"LER v2.0 - MISSION RUNTIME STARTED")
        self.session.log(f"Mission ID: {self.mission_id}")
        self.session.log("=" * 60)

        self.session.set_goal(goal_text)
        self.persistence.save_mission_state(self.mission_id, {
            "status": "active",
            "goal": goal_text[:200],
            "started_at": datetime.now().isoformat()
        })

        from governance.agent_governance import AgentGovernance
        from architecture.review_engine import ArchitectureReviewEngine

        governance = AgentGovernance(self.session, BASE_DIR)
        architecture = ArchitectureReviewEngine(self.session, self.config)

        gov_result = governance.initialize()
        if not gov_result.get("ready"):
            self.session.log("Governance system not ready")
            return self._finalize("governance_blocked")

        arch_result = architecture.validate_current()
        if not arch_result.get("valid"):
            self.session.log(f"Architecture issues: {arch_result.get('issues', [])}")

        from agent.orchestrator import Orchestrator
        orchestrator = Orchestrator(self.session, self.config)

        while self.iteration < self.max_iterations:
            self.iteration += 1
            self.session.log(f"\n--- Mission Iteration {self.iteration} ---")

            self.persistence.save_checkpoint(f"iter_{self.iteration}", {
                "mission_id": self.mission_id,
                "iteration": self.iteration,
                "state": self._capture_state()
            })

            result = orchestrator.run_iteration()

            if result.get("action") == "complete":
                return self._finalize("completed", orchestrator)
            elif result.get("action") == "failed":
                if self._can_continue(result):
                    self.session.log("Failure is recoverable. Continuing mission.")
                    continue
                return self._finalize("failed", orchestrator)

            self.security.backup_before_modify(
                os.path.join(BASE_DIR, "memory", "progress.json")
            )

        return self._finalize("max_iterations", orchestrator)

    def _can_continue(self, result):
        reason = result.get("reason", "")
        permanent_blockers = ["security_violation", "permanent_technical_block"]
        return reason not in permanent_blockers

    def _capture_state(self):
        progress = self.session.load_progress()
        return {
            "session_id": self.session.session_id,
            "iteration": self.iteration,
            "completed": len(progress.get("completed_steps", [])),
            "failed": len(progress.get("failed_steps", [])),
            "total": len(progress.get("steps", [])),
        }

    def _finalize(self, status, orchestrator=None):
        elapsed = self.session.elapsed()
        progress = self.session.load_progress()
        context = self.session.load_context()

        report = {
            "status": status,
            "mission_id": self.mission_id,
            "version": "2.0",
            "elapsed_seconds": elapsed,
            "iterations": self.iteration,
            "steps": {
                "total": len(progress.get("steps", [])),
                "completed": len(progress.get("completed_steps", [])),
                "failed": len(progress.get("failed_steps", [])),
            },
        }

        if orchestrator:
            learning = getattr(orchestrator, 'learning_engine', None)
            if learning:
                report["learning"] = learning.get_statistics()
            analysis = context.get("goal_analysis", {})
            if analysis:
                report["domain"] = analysis.get("domain")
                report["complexity"] = analysis.get("complexity")

        security_report = self.security.get_report()
        report["security"] = security_report

        self.session.log("=" * 60)
        self.session.log(f"MISSION {status.upper()}")
        self.session.log(f"v2.0 | Elapsed: {elapsed:.1f}s | Iterations: {self.iteration}")
        self.session.log(f"Steps: {report['steps']['completed']}/{report['steps']['total']}")
        self.session.log(f"Security: {'CLEAN' if security_report['safe'] else 'VIOLATIONS'}")
        self.session.log("=" * 60)

        self.persistence.save_checkpoint(f"final_{status}", report)
        self.persistence.save_mission_state(self.mission_id, {
            "status": status,
            "completed_at": datetime.now().isoformat(),
            "report": report
        })

        from architecture.review_engine import ArchitectureReviewEngine
        arch = ArchitectureReviewEngine(self.session, self.config)
        arch.log_mission_result(report)

        return report
