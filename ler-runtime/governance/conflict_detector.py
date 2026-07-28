"""
AGS Conflict Detector - Prevents responsibility overlap before execution.
Every responsibility must have exactly one owner.
"""

import json
import os


class ConflictDetector:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.map_file = os.path.join(base_dir, "governance", "responsibility_map.json")

    def detect_all(self):
        map_data = self._load_map()
        conflicts = []
        warnings = []

        ownership = {}
        for agent in map_data.get("agents", []):
            name = agent["name"]
            for resp in agent.get("ownership", []):
                if resp in ownership:
                    conflicts.append({
                        "type": "duplicate_responsibility",
                        "responsibility": resp,
                        "owners": [ownership[resp], name],
                        "severity": "high"
                    })
                ownership[resp] = name

        all_responsibilities = set(ownership.keys())
        orphans = self._find_orphan_dependencies(all_responsibilities, map_data)
        for o in orphans:
            warnings.append({
                "type": "unowned_dependency",
                "dependency": o,
                "severity": "medium"
            })

        return {"conflicts": conflicts, "warnings": warnings, "safe": len(conflicts) == 0}

    def _load_map(self):
        if os.path.exists(self.map_file):
            with open(self.map_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"agents": []}

    def _find_orphan_dependencies(self, owned, map_data):
        orphans = []
        for agent in map_data.get("agents", []):
            for dep in agent.get("depends_on", []):
                if dep not in owned:
                    orphans.append(dep)
        return orphans
