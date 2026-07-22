import json
import os
import re
from datetime import datetime

class Planner:
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.max_steps = 50

    def create_plan(self, goal_text):
        self.session.log("Creating plan from goal...")
        goal_text = self._clean_goal(goal_text)
        steps = self._generate_steps(goal_text)
        plan = self._build_plan_document(goal_text, steps)
        self.session.set_plan(plan)
        progress = {
            "steps": steps,
            "current_step": 0,
            "completed_steps": [],
            "failed_steps": [],
            "total_steps": len(steps),
            "created": datetime.now().isoformat(),
        }
        self.session.save_progress(progress)
        self.session.log(f"Plan created with {len(steps)} steps")
        return steps

    def _clean_goal(self, goal):
        goal = re.sub(r'^["\']|["\']$', '', goal.strip())
        return goal

    def _generate_steps(self, goal):
        analysis = self._analyze_goal(goal)
        steps = []
        step_num = 1

        # Phase 1: Setup
        steps.append({
            "id": step_num,
            "phase": "setup",
            "action": "analyze_environment",
            "description": f"Analyze environment for: {analysis['task_type']}",
            "command": None,
            "validation": "check_env",
            "status": "pending"
        })
        step_num += 1

        steps.append({
            "id": step_num,
            "phase": "setup",
            "action": "initialize_project",
            "description": f"Initialize project structure for: {goal[:60]}",
            "command": None,
            "validation": "check_structure",
            "status": "pending"
        })
        step_num += 1

        # Phase 2: Research
        if analysis["needs_research"]:
            steps.append({
                "id": step_num,
                "phase": "research",
                "action": "gather_information",
                "description": f"Research requirements for: {goal[:60]}",
                "command": None,
                "validation": "check_research",
                "status": "pending"
            })
            step_num += 1

        # Phase 3: Implementation steps
        for i, impl_step in enumerate(analysis["implementation_steps"]):
            steps.append({
                "id": step_num,
                "phase": "implementation",
                "action": impl_step["action"],
                "description": impl_step["description"],
                "command": impl_step.get("command"),
                "validation": impl_step.get("validation", "check_output"),
                "status": "pending"
            })
            step_num += 1

        # Phase 4: Verification
        steps.append({
            "id": step_num,
            "phase": "verification",
            "action": "run_tests",
            "description": "Run tests to validate implementation",
            "command": None,
            "validation": "test_pass",
            "status": "pending"
        })
        step_num += 1

        if analysis["needs_git"]:
            steps.append({
                "id": step_num,
                "phase": "verification",
                "action": "git_commit",
                "description": "Commit changes to git",
                "command": None,
                "validation": "check_git",
                "status": "pending"
            })
            step_num += 1

        return steps

    def _analyze_goal(self, goal):
        g = goal.lower()
        task_type = "general"
        needs_research = False
        needs_git = True
        implementation_steps = []

        if any(w in g for w in ["create", "build", "make", "develop", "write"]):
            task_type = "creation"
            implementation_steps.append({
                "action": "implement",
                "description": f"Implement core functionality: {goal[:60]}",
                "validation": "check_output"
            })
        elif any(w in g for w in ["fix", "repair", "bug", "error", "issue"]):
            task_type = "fix"
            implementation_steps.append({
                "action": "diagnose",
                "description": f"Diagnose issue: {goal[:60]}",
                "validation": "check_output"
            })
            implementation_steps.append({
                "action": "fix",
                "description": f"Apply fix for: {goal[:60]}",
                "validation": "test_pass"
            })
        elif any(w in g for w in ["test", "verify", "validate", "check"]):
            task_type = "validation"
            implementation_steps.append({
                "action": "test",
                "description": f"Run validation: {goal[:60]}",
                "validation": "test_pass"
            })
        elif any(w in g for w in ["refactor", "improve", "optimize", "clean"]):
            task_type = "improvement"
            implementation_steps.append({
                "action": "analyze",
                "description": f"Analyze codebase for: {goal[:60]}",
                "validation": "check_output"
            })
            implementation_steps.append({
                "action": "refactor",
                "description": f"Apply improvements for: {goal[:60]}",
                "validation": "test_pass"
            })
        else:
            implementation_steps.append({
                "action": "implement",
                "description": f"Implement: {goal[:60]}",
                "validation": "check_output"
            })

        return {
            "task_type": task_type,
            "needs_research": needs_research,
            "needs_git": needs_git,
            "implementation_steps": implementation_steps
        }

    def _build_plan_document(self, goal, steps):
        lines = []
        lines.append(f"# Execution Plan\n")
        lines.append(f"**Goal:** {goal}\n")
        lines.append(f"**Created:** {datetime.now().isoformat()}\n")
        lines.append(f"**Total Steps:** {len(steps)}\n")
        lines.append("---\n")
        for s in steps:
            lines.append(f"### Step {s['id']}: {s['phase'].upper()} - {s['action']}")
            lines.append(f"**Description:** {s['description']}")
            lines.append(f"**Validation:** {s['validation']}")
            lines.append(f"**Status:** {s['status']}")
            lines.append("")
        lines.append("---\n")
        lines.append("## Completion Criteria\n")
        lines.append("- [ ] All steps completed successfully\n")
        lines.append("- [ ] All validations passed\n")
        lines.append("- [ ] Goal achieved\n")
        return "\n".join(lines)

    def update_step_status(self, step_id, status):
        progress = self.session.load_progress()
        for step in progress["steps"]:
            if step["id"] == step_id:
                step["status"] = status
                break
        if status == "completed":
            if step_id not in progress["completed_steps"]:
                progress["completed_steps"].append(step_id)
        elif status == "failed":
            if step_id not in progress["failed_steps"]:
                progress["failed_steps"].append(step_id)
        progress["current_step"] = step_id
        self.session.save_progress(progress)
