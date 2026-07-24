import json
import os
import hashlib
from datetime import datetime


class EvidenceCollector:
    def __init__(self, session, base_dir):
        self.session = session
        self.base_dir = base_dir
        self.report_dir = os.path.join(base_dir, "reports")
        self._hash_cache = {}
        self.evidence = {
            "mission_id": None,
            "collected_at": datetime.now().isoformat(),
            "logs": [],
            "files": [],
            "hashes": [],
            "tests": [],
            "artifacts": [],
            "timing": {},
            "decisions": [],
        }

    def start_mission(self, mission_id):
        self.evidence["mission_id"] = mission_id
        self.evidence["collected_at"] = datetime.now().isoformat()
        self.evidence["timing"]["started_at"] = datetime.now().isoformat()

    def collect_log(self, log_file):
        if not os.path.exists(log_file):
            return
        with open(log_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.evidence["logs"].append({
            "file": log_file,
            "size": len(content),
            "lines": len(content.split("\n")),
        })

    def collect_file(self, file_path, category="artifact"):
        if not os.path.exists(file_path):
            return
        real = os.path.realpath(file_path)
        mtime = os.path.getmtime(real)
        cache_key = (real, mtime)
        if cache_key in self._hash_cache:
            file_hash = self._hash_cache[cache_key]
            content = b""
        else:
            with open(real, "rb") as f:
                content = f.read()
            file_hash = hashlib.sha256(content).hexdigest()
            self._hash_cache[cache_key] = file_hash
        entry = {
            "path": file_path,
            "size": len(content),
            "hash": file_hash,
            "category": category,
            "collected_at": datetime.now().isoformat(),
        }
        self.evidence["hashes"].append({"path": file_path, "sha256": file_hash})
        self.evidence["files"].append(entry)
        if category == "artifact":
            self.evidence["artifacts"].append(entry)

    def collect_test_result(self, test_file, passed, output=""):
        self.evidence["tests"].append({
            "file": test_file,
            "passed": passed,
            "output": output[:500],
            "timestamp": datetime.now().isoformat(),
        })

    def collect_decisions(self, decisions_file):
        if not os.path.exists(decisions_file):
            return
        with open(decisions_file, "r", encoding="utf-8") as f:
            content = f.read()
        self.evidence["decisions"].append({
            "file": decisions_file,
            "content": content[:2000],
        })

    def finish_mission(self):
        self.evidence["timing"]["finished_at"] = datetime.now().isoformat()
        if "started_at" in self.evidence["timing"]:
            start = datetime.fromisoformat(self.evidence["timing"]["started_at"])
            finish = datetime.fromisoformat(self.evidence["timing"]["finished_at"])
            self.evidence["timing"]["elapsed_seconds"] = (finish - start).total_seconds()
        self.evidence["collected"] = self._count_collected()
        self.evidence["total"] = max(1, self.evidence["collected"])

    def generate_report(self):
        os.makedirs(self.report_dir, exist_ok=True)
        ev_json_path = os.path.join(self.report_dir, "evidence.json")
        with open(ev_json_path, "w", encoding="utf-8") as f:
            json.dump(self.evidence, f, indent=2, ensure_ascii=False)
        ev_md_path = os.path.join(self.report_dir, "evidence.md")
        md_lines = []
        md_lines.append("# Evidence Report\n")
        md_lines.append(f"**Mission:** {self.evidence.get('mission_id', 'N/A')}\n")
        md_lines.append(f"**Generated:** {datetime.now().isoformat()}\n")
        md_lines.append("---\n")
        md_lines.append(f"\n## Logs ({len(self.evidence['logs'])})\n")
        for log in self.evidence["logs"]:
            md_lines.append(f"- {log['file']} ({log['size']} bytes, {log['lines']} lines)\n")
        md_lines.append(f"\n## Files ({len(self.evidence['files'])})\n")
        for f_entry in self.evidence["files"]:
            md_lines.append(f"- {f_entry['path']} ({f_entry['size']} bytes, SHA256: {f_entry['hash'][:16]}...)\n")
        md_lines.append(f"\n## Hashes ({len(self.evidence['hashes'])})\n")
        for h in self.evidence["hashes"]:
            md_lines.append(f"- `{h['path']}` → `{h['sha256']}`\n")
        md_lines.append(f"\n## Tests ({len(self.evidence['tests'])})\n")
        for t in self.evidence["tests"]:
            status = "PASS" if t["passed"] else "FAIL"
            md_lines.append(f"- [{status}] {t['file']}\n")
        md_lines.append(f"\n## Artifacts ({len(self.evidence['artifacts'])})\n")
        for a in self.evidence["artifacts"]:
            md_lines.append(f"- {a['path']}\n")
        md_lines.append(f"\n## Timing\n")
        md_lines.append(f"- Started: {self.evidence['timing'].get('started_at', 'N/A')}\n")
        md_lines.append(f"- Finished: {self.evidence['timing'].get('finished_at', 'N/A')}\n")
        md_lines.append(f"- Elapsed: {self.evidence['timing'].get('elapsed_seconds', 0):.1f}s\n")
        md_lines.append("---\n")
        md_lines.append("*Evidence collected by LER v2.0 EvidenceCollector*\n")
        with open(ev_md_path, "w", encoding="utf-8") as f:
            f.writelines(md_lines)
        return self.evidence

    def _count_collected(self):
        return (len(self.evidence["logs"]) + len(self.evidence["files"]) +
                len(self.evidence["tests"]) + len(self.evidence["artifacts"]) +
                len(self.evidence["decisions"]))

    def get_summary(self):
        return {
            "collected": self._count_collected(),
            "logs": len(self.evidence["logs"]),
            "files": len(self.evidence["files"]),
            "hashes": len(self.evidence["hashes"]),
            "tests": len(self.evidence["tests"]),
            "artifacts": len(self.evidence["artifacts"]),
            "decisions": len(self.evidence["decisions"]),
        }
