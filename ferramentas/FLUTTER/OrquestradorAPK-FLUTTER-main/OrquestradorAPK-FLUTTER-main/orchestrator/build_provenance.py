# -*- coding: utf-8 -*-
"""
Build Provenance — coleta de evidencias de build.
Padrao: LER EvidenceCollector + Android Pure SDK APK verification.
"""
import os
import json
import hashlib
import subprocess
from datetime import datetime
from typing import Dict, Optional, List


class BuildProvenance:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.evidence = {
            "build_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "steps": [],
            "artifacts": [],
            "decisions": [],
            "errors": [],
            "summary": {},
        }

    def record_step(self, name: str, status: str, duration: float,
                    output: str = "", error: Optional[str] = None):
        self.evidence["steps"].append({
            "step": name,
            "status": status,
            "duration_seconds": round(duration, 2),
            "output_preview": output[:500] if output else "",
            "error": error,
            "timestamp": datetime.now().isoformat(),
        })

    def record_decision(self, decision: str, rationale: str = ""):
        self.evidence["decisions"].append({
            "decision": decision,
            "rationale": rationale,
            "timestamp": datetime.now().isoformat(),
        })

    def record_artifact(self, path: str, label: str = ""):
        sha256 = self._hash_file(path)
        size = os.path.getsize(path) if os.path.exists(path) else 0
        entry = {
            "path": path,
            "label": label or os.path.basename(path),
            "sha256": sha256,
            "size_bytes": size,
            "size_mb": round(size / (1024 * 1024), 2) if size > 0 else 0,
        }
        self.evidence["artifacts"].append(entry)
        return entry

    def record_error(self, error: str, context: str = ""):
        self.evidence["errors"].append({
            "error": error[:500],
            "context": context[:500],
            "timestamp": datetime.now().isoformat(),
        })

    def verify_apk(self, apk_path: str) -> Dict:
        result = {"path": apk_path, "valid": False, "checks": []}
        if not os.path.exists(apk_path):
            result["error"] = "APK not found"
            return result
        sha256 = self._hash_file(apk_path)
        size = os.path.getsize(apk_path)
        result["sha256"] = sha256
        result["size_mb"] = round(size / (1024 * 1024), 2)
        result["checks"].append({"name": "sha256", "value": sha256, "passed": True})
        result["checks"].append({"name": "non_zero_size", "value": size > 0, "passed": size > 0})
        try:
            proc = subprocess.run(
                f"apksigner verify --print-certs \"{apk_path}\"",
                shell=True, capture_output=True, text=True, timeout=30
            )
            apksigner_ok = proc.returncode == 0
            result["checks"].append({
                "name": "apksigner_verify",
                "value": proc.stdout.strip()[:500],
                "passed": apksigner_ok,
            })
        except Exception:
            result["checks"].append({
                "name": "apksigner_verify",
                "value": "apksigner not available",
                "passed": None,
            })
        result["all_passed"] = all(
            c["passed"] for c in result["checks"] if c["passed"] is not None
        )
        result["valid"] = result["all_passed"]
        self.evidence["apk_verification"] = result
        return result

    def _hash_file(self, path: str) -> Optional[str]:
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return None

    def finalize(self) -> Dict:
        steps_ok = sum(1 for s in self.evidence["steps"] if s["status"] == "completed")
        steps_total = len(self.evidence["steps"])
        self.evidence["summary"] = {
            "steps_passed": steps_ok,
            "steps_total": steps_total,
            "steps_passed_pct": round(steps_ok / steps_total * 100, 1) if steps_total else 0,
            "artifacts_count": len(self.evidence["artifacts"]),
            "errors_count": len(self.evidence["errors"]),
            "decisions_count": len(self.evidence["decisions"]),
            "build_successful": steps_ok == steps_total and steps_total > 0,
        }
        return self.evidence["summary"]

    def save_json(self, path: Optional[str] = None) -> str:
        if path is None:
            os.makedirs(self.output_dir, exist_ok=True)
            path = os.path.join(self.output_dir,
                                f"evidence_{self.evidence['build_id']}.json")
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.evidence, f, indent=2, ensure_ascii=False)
            os.replace(tmp, path)
        except Exception as e:
            print(f"[BuildProvenance] Erro ao salvar evidencias: {e}")
        return path

    def save_markdown(self, path: Optional[str] = None) -> str:
        if path is None:
            os.makedirs(self.output_dir, exist_ok=True)
            path = os.path.join(self.output_dir,
                                f"evidence_{self.evidence['build_id']}.md")
        lines = []
        lines.append("# Build Evidence Report\n")
        lines.append(f"**Build ID:** {self.evidence['build_id']}")
        lines.append(f"**Timestamp:** {self.evidence['timestamp']}\n")
        lines.append("## Steps\n")
        lines.append("| Step | Status | Duration | Error |")
        lines.append("|------|--------|----------|-------|")
        for s in self.evidence["steps"]:
            err = s.get("error", "") or ""
            lines.append(f"| {s['step']} | {s['status']} | {s['duration_seconds']}s | {err[:50]} |")
        lines.append("\n## Artifacts\n")
        lines.append("| File | SHA256 | Size |")
        lines.append("|------|--------|------|")
        for a in self.evidence["artifacts"]:
            lines.append(f"| {a['label']} | `{a['sha256'] or 'N/A'}` | {a['size_mb']}MB |")
        if self.evidence.get("apk_verification"):
            lines.append("\n## APK Verification\n")
            for c in self.evidence["apk_verification"].get("checks", []):
                status = "PASS" if c["passed"] else "FAIL" if c["passed"] is False else "SKIP"
                lines.append(f"- **{c['name']}**: {status} — {c.get('value', '')[:100]}")
        if self.evidence["decisions"]:
            lines.append("\n## Decisions\n")
            for d in self.evidence["decisions"]:
                lines.append(f"- {d['decision']} ({d.get('rationale', '')[:100]})")
        if self.evidence["errors"]:
            lines.append("\n## Errors\n")
            for e in self.evidence["errors"]:
                lines.append(f"- {e['error'][:200]}")
        lines.append("\n## Summary\n")
        s = self.evidence.get("summary", {})
        lines.append(f"- Steps: {s.get('steps_passed', 0)}/{s.get('steps_total', 0)} passed")
        lines.append(f"- Artifacts: {s.get('artifacts_count', 0)}")
        lines.append(f"- Build successful: {'YES' if s.get('build_successful') else 'NO'}")
        content = "\n".join(lines)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            print(f"[BuildProvenance] Erro ao salvar markdown: {e}")
        return path
