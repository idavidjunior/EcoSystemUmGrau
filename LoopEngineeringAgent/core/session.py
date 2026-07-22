import json
import os
import time
from datetime import datetime


class Session:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.start_time = time.time()
        self.memory_dir = os.path.join(base_dir, "memory")
        self.log_dir = os.path.join(base_dir, "logs")
        self.goal_file = os.path.join(self.memory_dir, "goal.md")
        self.plan_file = os.path.join(self.memory_dir, "plan.md")
        self.progress_file = os.path.join(self.memory_dir, "progress.json")
        self.context_file = os.path.join(self.memory_dir, "context.json")
        self.decisions_file = os.path.join(self.memory_dir, "decisions.md")
        self.errors_file = os.path.join(self.memory_dir, "errors.log")
        os.makedirs(self.memory_dir, exist_ok=True)
        os.makedirs(self.log_dir, exist_ok=True)
        self._init_long_term_memory()

    def _init_long_term_memory(self):
        lt_dirs = ["projects", "knowledge", "user_preferences", "technical_history", "successful_architectures"]
        for d in lt_dirs:
            os.makedirs(os.path.join(self.memory_dir, d), exist_ok=True)

    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{timestamp}] [{level}] {message}"
        log_file = os.path.join(self.log_dir, f"session_{self.session_id}.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(line)

    def set_goal(self, goal):
        with open(self.goal_file, "w", encoding="utf-8") as f:
            f.write(f"# Goal\n\n{goal}\n\n---\nSet: {datetime.now().isoformat()}\n")
        self.log(f"Goal set: {goal[:80]}...")

    def get_goal(self):
        if not os.path.exists(self.goal_file):
            return None
        with open(self.goal_file, "r", encoding="utf-8") as f:
            return f.read()

    def set_plan(self, plan_text):
        with open(self.plan_file, "w", encoding="utf-8") as f:
            f.write(plan_text)
        self.log("Plan updated")

    def get_plan(self):
        if not os.path.exists(self.plan_file):
            return None
        with open(self.plan_file, "r", encoding="utf-8") as f:
            return f.read()

    def save_progress(self, data):
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        self._archive_progress(data)

    def load_progress(self):
        if not os.path.exists(self.progress_file):
            return {"steps": [], "current_step": 0, "completed_steps": [], "failed_steps": [],
                    "strategy_used": None, "analysis": None}
        with open(self.progress_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save_context(self, data):
        with open(self.context_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_context(self):
        if not os.path.exists(self.context_file):
            return {}
        with open(self.context_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def record_decision(self, decision):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.decisions_file, "a", encoding="utf-8") as f:
            f.write(f"\n## [{timestamp}] {decision}\n\n")

    def record_error(self, error, context=""):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.errors_file, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] ERROR: {error} | Context: {context}\n")
        self.log(f"ERROR: {error}", level="ERROR")

    def elapsed(self):
        return time.time() - self.start_time

    def save_long_term(self, category, key, data):
        base = os.path.join(self.memory_dir, category)
        os.makedirs(base, exist_ok=True)
        path = os.path.join(base, f"{key}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_long_term(self, category, key):
        path = os.path.join(self.memory_dir, category, f"{key}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def list_long_term(self, category):
        base = os.path.join(self.memory_dir, category)
        if not os.path.isdir(base):
            return []
        return [f.replace(".json", "") for f in os.listdir(base) if f.endswith(".json")]

    def _archive_progress(self, progress):
        if progress.get("completed_steps") or progress.get("failed_steps"):
            archive_dir = os.path.join(self.memory_dir, "technical_history")
            os.makedirs(archive_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%H%M%S")
            path = os.path.join(archive_dir, f"progress_{timestamp}.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump(progress, f, indent=2, ensure_ascii=False)
