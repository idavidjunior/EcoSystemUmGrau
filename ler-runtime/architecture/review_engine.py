"""
Architecture Review Engine (ARE) - Camada 2
Controls all architecture decisions.
Validates module structure, ownership, layering, and evolution.
"""

import json
import os
from datetime import datetime


class ArchitectureReviewEngine:
    def __init__(self, session, config):
        self.session = session
        self.config = config
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.issues = []

    ARCHITECTURE_RULES = [
        "Camada 1: Governanca (governance/)",
        "Camada 2: Arquitetura (architecture/)",
        "Camada 3: Planejamento (agent/planner, strategy_engine)",
        "Camada 4: Execucao (agent/executor, runtime/mission)",
        "Camada 5: Validacao (agent/validator)",
        "Camada 6: Recuperacao (agent/recovery)",
        "Camada 7: Persistencia (runtime/persistence)",
        "Camada 8: Versionamento (git integration)",
        "Camada 9: Auditoria (agent/final_auditor)",
    ]

    def validate_current(self):
        self.session.log("[ARE] Validating current architecture...")
        self.issues = []
        checks = []

        checks.append(self._check_layer_separation())
        checks.append(self._check_module_boundaries())
        checks.append(self._check_single_responsibility())

        for c in checks:
            if not c.get("passed"):
                self.issues.append(c)

        result = {
            "valid": len(self.issues) == 0,
            "issues": self.issues,
            "checks_performed": len(checks),
            "checks_passed": sum(1 for c in checks if c.get("passed")),
        }

        if result["valid"]:
            self.session.log("[ARE] Architecture validation PASSED")
        else:
            for issue in self.issues:
                self.session.log(f"[ARE] Issue: {issue.get('message', 'Unknown')}", level="WARNING")

        return result

    def _check_layer_separation(self):
        layers = ["governance", "architecture", "agent", "core", "runtime", "omni_route", "integrations"]
        missing = []
        for layer in layers:
            path = os.path.join(self.base_dir, layer)
            if not os.path.isdir(path):
                missing.append(layer)
        return {
            "check": "layer_separation",
            "passed": len(missing) == 0,
            "message": f"Missing layers: {missing}" if missing else "All layers present"
        }

    def _check_module_boundaries(self):
        issues = []
        agent_dir = os.path.join(self.base_dir, "agent")
        if os.path.isdir(agent_dir):
            for f in os.listdir(agent_dir):
                if f.endswith(".py") and f != "__init__.py":
                    module_path = os.path.join(agent_dir, f)
                    with open(module_path, "r", encoding="utf-8") as fh:
                        content = fh.read()
                    if "from runtime" in content or "from governance" in content or "from architecture" in content:
                        issues.append(f"{f} crosses layer boundary")
        return {
            "check": "module_boundaries",
            "passed": len(issues) == 0,
            "message": f"Boundary issues: {issues}" if issues else "Module boundaries clean"
        }

    def _check_single_responsibility(self):
        gov_file = os.path.join(self.base_dir, "governance", "responsibility_map.json")
        if not os.path.exists(gov_file):
            return {"check": "single_responsibility", "passed": False, "message": "No responsibility map"}
        with open(gov_file, "r", encoding="utf-8") as f:
            map_data = json.load(f)
        ownership = {}
        conflicts = []
        for agent in map_data.get("agents", []):
            for resp in agent.get("ownership", []):
                if resp in ownership:
                    conflicts.append(f"{resp} owned by {ownership[resp]} and {agent['name']}")
                ownership[resp] = agent["name"]
        return {
            "check": "single_responsibility",
            "passed": len(conflicts) == 0,
            "message": f"Conflicts: {conflicts}" if conflicts else "No responsibility conflicts"
        }

    def log_mission_result(self, report):
        history_dir = os.path.join(self.base_dir, "memory", "technical_history")
        os.makedirs(history_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(history_dir, f"mission_{timestamp}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def get_architecture_report(self):
        return {
            "architecture_rules": self.ARCHITECTURE_RULES,
            "module_count": self._count_modules(),
            "layers": ["governance", "architecture", "agent", "runtime", "core", "omni_route", "integrations"]
        }

    def _count_modules(self):
        count = 0
        for layer in ["governance", "architecture", "agent", "core", "runtime", "omni_route", "integrations"]:
            path = os.path.join(self.base_dir, layer)
            if os.path.isdir(path):
                for f in os.listdir(path):
                    if f.endswith(".py") and f != "__init__.py":
                        count += 1
        return count
