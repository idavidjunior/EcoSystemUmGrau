"""
LER Analyzer - Static code analysis for multiple languages.
Scans the current project and reports issues using available tools.
"""

import os
import re
import sys
import json
import subprocess
import difflib
import tempfile
from datetime import datetime


class Analyzer:
    LANGUAGES = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".c": "c",
        ".cpp": "cpp",
        ".cs": "csharp",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
    }

    def __init__(self, project_dir, session=None):
        self.project_dir = os.path.abspath(project_dir)
        self.session = session
        self.issues = []
        self.fixed = []

    def log(self, msg):
        if self.session:
            self.session.log(msg)
        else:
            print(msg)

    def scan(self, fix=False):
        self.log(f"[Analyzer] Scanning {self.project_dir}")
        self.issues = []
        self.fixed = []

        project_type = self._detect_project_type()
        self.log(f"[Analyzer] Project type: {project_type}")

        if project_type == "python":
            self._scan_python(fix)
        elif project_type in ("javascript", "typescript"):
            self._scan_javascript(fix)
        elif project_type == "go":
            self._scan_go(fix)
        elif project_type == "kotlin":
            self._scan_kotlin(fix)
        else:
            self._scan_generic()

        report = self._generate_report(project_type)
        return report

    def _detect_project_type(self):
        files = os.listdir(self.project_dir)
        if "setup.py" in files or "pyproject.toml" in files or "requirements.txt" in files:
            return "python"
        if "package.json" in files:
            return "javascript"
        if "go.mod" in files:
            return "go"
        if "Cargo.toml" in files:
            return "rust"
        if "build.gradle" in files or "build.gradle.kts" in files or "gradlew" in files:
            return "kotlin"
        py_files = self._find_files(".py")
        js_files = self._find_files(".js")
        go_files = self._find_files(".go")
        kt_files = self._find_files(".kt")
        java_files = self._find_files(".java")
        if kt_files or java_files:
            return "kotlin"
        if py_files:
            return "python"
        if js_files:
            return "javascript"
        if go_files:
            return "go"
        return "generic"

    def _find_files(self, ext):
        matches = []
        for root, dirs, files in os.walk(self.project_dir):
            dirs[:] = [d for d in dirs if not d.startswith((".", "node_modules", "venv", "__pycache__", "build", "dist"))]
            for f in files:
                if f.endswith(ext):
                    matches.append(os.path.join(root, f))
        return matches

    def _scan_python(self, fix):
        self._check_syntax(fix)
        self._check_flake8()
        self._check_imports()
        self._check_common_patterns()

    def _scan_javascript(self, fix):
        self._check_syntax(fix)
        if fix:
            self._run_node_lint_fix()

    def _scan_go(self, fix):
        self._run_go_vet()

    def _scan_kotlin(self, fix):
        self._check_gradle_lint()

    def _check_gradle_lint(self):
        kt_files = self._find_files(".kt")
        java_files = self._find_files(".java")
        self.log(f"[Analyzer] {len(kt_files)} .kt files, {len(java_files)} .java files")
        if not kt_files and not java_files:
            return
        gradlew = os.path.join(self.project_dir, "gradlew.bat")
        if os.path.exists(gradlew) or os.path.exists(os.path.join(self.project_dir, "gradlew")):
            self.log("[Analyzer] gradlew found. Run 'gradlew lint' manually for full Android lint.")
            self._add_issue("info", "project", 0,
                           "gradlew found. Run 'gradlew lint' for Android Lint results.")
        else:
            self._add_issue("info", "project", 0,
                           "No lint tool available. Install ktlint or detekt for Kotlin checks.")

    def _scan_generic(self):
        py = self._find_files(".py")
        js = self._find_files(".js")
        kt = self._find_files(".kt")
        java = self._find_files(".java")
        if py:
            self._scan_python(False)
        if js:
            self._scan_javascript(False)
        if kt or java:
            self.log(f"[Analyzer] {len(kt)} .kt, {len(java)} .java files found — use gradle wrapper for full lint")

    def _check_syntax(self, fix):
        sources = self._find_files(".py")
        for path in sources:
            try:
                compile(open(path, "r", encoding="utf-8").read(), path, "exec")
            except SyntaxError as e:
                self._add_issue("syntax", path, e.lineno or 0, str(e))

    def _check_flake8(self):
        sources = self._find_files(".py")
        if not sources:
            return
        try:
            proc = subprocess.run(
                ["flake8"] + sources,
                capture_output=True, text=True, timeout=60
            )
            for line in proc.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                m = re.match(r"^(.+):(\d+):(\d+):\s*(\S+)\s+(.+)$", line)
                if m:
                    fpath = m.group(1)
                    lineno = int(m.group(2))
                    code = m.group(4)
                    msg = f"{m.group(5)} [{code}]"
                    self._add_issue("style", fpath, lineno, msg, code=code)
        except FileNotFoundError:
            self.log("[Analyzer] flake8 not installed. Install with: pip install flake8")
        except subprocess.TimeoutExpired:
            self.log("[Analyzer] flake8 timed out")

    def _check_imports(self):
        sources = self._find_files(".py")
        for path in sources:
            with open(path, "r", encoding="utf-8") as f:
                try:
                    lines = f.readlines()
                except Exception:
                    continue
            imports = []
            for i, line in enumerate(lines):
                m = re.match(r"^(?:from|import)\s+(\S+)", line)
                if m:
                    imports.append((i + 1, m.group(1)))
            for lineno, mod in imports:
                if mod == "os" and "print(" not in "".join(lines):
                    continue

    def _check_common_patterns(self):
        sources = self._find_files(".py")
        for path in sources:
            with open(path, "r", encoding="utf-8") as f:
                try:
                    content = f.read()
                    lines = content.split("\n")
                except Exception:
                    continue
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                if "import *" in stripped:
                    self._add_issue("warning", path, i, "wildcard import (import *)")
                if "except:" in stripped and stripped != "except: pass":
                    self._add_issue("warning", path, i, "bare except clause")
                if "# TODO" in stripped or "# todo" in stripped.lower():
                    self._add_issue("info", path, i, "TODO comment")
                if "# FIXME" in stripped or "# fixme" in stripped.lower():
                    self._add_issue("info", path, i, "FIXME comment")
                if "sys.exit" in stripped and "__name__" not in content:
                    self._add_issue("warning", path, i, "sys.exit() in library code")

    def _run_go_vet(self):
        src_dir = self.project_dir
        if self._find_files(".go"):
            try:
                proc = subprocess.run(
                    ["go", "vet", "./..."],
                    capture_output=True, text=True, timeout=120, cwd=src_dir
                )
                for line in proc.stderr.strip().split("\n"):
                    if not line.strip():
                        continue
                    parts = line.split(":", 2)
                    if len(parts) >= 2:
                        fpath = parts[0].strip()
                        lineno = parts[1] if parts[1].isdigit() else 0
                        msg = parts[2] if len(parts) > 2 else line
                        self._add_issue("go_vet", fpath, int(lineno) if str(lineno).isdigit() else 0, msg)
            except FileNotFoundError:
                self.log("[Analyzer] go not found on PATH")
            except subprocess.TimeoutExpired:
                self.log("[Analyzer] go vet timed out")

    def _run_node_lint_fix(self):
        try:
            subprocess.run(["node", "--check"] + self._find_files(".js") + self._find_files(".jsx"),
                          capture_output=True, text=True, timeout=60)
        except FileNotFoundError:
            pass

    def _add_issue(self, category, filepath, lineno, message, code=None):
        try:
            rel = os.path.relpath(filepath, self.project_dir)
        except ValueError:
            rel = filepath
        issue = {
            "category": category,
            "file": rel,
            "line": lineno,
            "message": message,
            "code": code,
        }
        self.issues.append(issue)

    def _generate_report(self, project_type):
        by_category = {}
        for issue in self.issues:
            by_category.setdefault(issue["category"], []).append(issue)

        report = {
            "project": self.project_dir,
            "type": project_type,
            "scanned_at": datetime.now().isoformat(),
            "total_issues": len(self.issues),
            "by_category": {k: len(v) for k, v in by_category.items()},
            "issues": self.issues[:100],
            "issues_truncated": len(self.issues) > 100,
            "files_scanned": len(self._find_files(".py")) + len(self._find_files(".js")) + len(self._find_files(".go")),
        }

        return report


def audit(project_dir, fix=False, session=None, output_dir=None):
    a = Analyzer(project_dir, session)
    report = a.scan(fix=fix)

    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(output_dir, exist_ok=True)

    path = os.path.join(output_dir, f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    return report, path
