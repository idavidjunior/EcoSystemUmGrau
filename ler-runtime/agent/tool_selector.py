import json
import os
from datetime import datetime


class ToolSelector:
    def __init__(self, session, base_dir):
        self.session = session
        self.base_dir = base_dir
        self.stats_file = os.path.join(base_dir, "memory", "tool_statistics.json")

    def select_tool(self, task_type, context=None):
        task_type = task_type.lower()
        tools = self._get_available_tools()

        tool_map = {
            "programming": "opencode",
            "implementation": "opencode",
            "coding": "opencode",
            "llm": "nvidia",
            "analysis": "nvidia",
            "research": "opencode",
            "reasoning": "nvidia",
            "terminal": "shell",
            "command": "shell",
            "shell": "shell",
            "git": "git",
            "versioning": "git",
            "commit": "git",
            "python": "python",
            "script": "python",
            "testing": "python",
            "test": "python",
            "file": "shell",
            "filesystem": "shell",
            "read": "shell",
            "write": "shell",
        }

        preferred = tool_map.get(task_type, "opencode")

        stats = self._load_stats()
        tool_stats = stats.get("tools", {})

        if preferred in tools:
            pref_stats = tool_stats.get(preferred, {})
            success_rate = pref_stats.get("success_rate", 100)
            if success_rate < 50:
                alternatives = [t for t in tools if t != preferred]
                if alternatives:
                    self.session.log(
                        f"[ToolSelector] {preferred} has low success rate ({success_rate}%). "
                        f"Falling back to {alternatives[0]}"
                    )
                    preferred = alternatives[0]

        selection = {
            "tool": preferred,
            "task_type": task_type,
            "available_tools": tools,
            "stats": tool_stats.get(preferred, {}),
            "selected_at": datetime.now().isoformat(),
        }

        self.session.log(f"[ToolSelector] Selected '{preferred}' for '{task_type}'")
        return selection

    def record_result(self, tool_name, success, duration, cost=0):
        stats = self._load_stats()
        stats.setdefault("tools", {})
        if tool_name not in stats["tools"]:
            stats["tools"][tool_name] = {
                "total_calls": 0, "successes": 0, "failures": 0,
                "total_duration": 0.0, "total_cost": 0.0,
                "avg_duration": 0.0, "avg_cost": 0.0,
                "success_rate": 0.0, "latency_samples": [],
            }
        t = stats["tools"][tool_name]
        t["total_calls"] += 1
        if success:
            t["successes"] += 1
        else:
            t["failures"] += 1
        t["total_duration"] += duration
        t["total_cost"] += cost
        t["avg_duration"] = round(t["total_duration"] / t["total_calls"], 3)
        t["avg_cost"] = round(t["total_cost"] / t["total_calls"], 3)
        t["success_rate"] = round((t["successes"] / t["total_calls"]) * 100, 1)
        t["latency_samples"].append(round(duration, 3))
        if len(t["latency_samples"]) > 100:
            t["latency_samples"] = t["latency_samples"][-100:]
        self._save_stats(stats)

    def get_tool_report(self):
        stats = self._load_stats()
        tools = stats.get("tools", {})
        report = {}
        for name, t in sorted(tools.items(), key=lambda x: x[1].get("total_calls", 0), reverse=True):
            report[name] = {
                "total_calls": t["total_calls"],
                "success_rate": t["success_rate"],
                "avg_duration": t["avg_duration"],
                "avg_cost": t["avg_cost"],
            }
        return report

    def _get_available_tools(self):
        return ["opencode", "nvidia", "shell", "git", "python"]

    def _load_stats(self):
        if os.path.exists(self.stats_file):
            with open(self.stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"tools": {}}

    def _save_stats(self, data):
        os.makedirs(os.path.dirname(self.stats_file), exist_ok=True)
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
