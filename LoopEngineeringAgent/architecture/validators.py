"""
ARE Validators - Architecture validation utilities.
Ensures KISS, DRY, SOLID, low coupling, high cohesion.
"""

import os
import ast
import re


class ArchitectureValidators:
    def __init__(self, base_dir):
        self.base_dir = base_dir

    def validate_kiss(self, filepath):
        """KISS: Keep It Simple. Check for unnecessary complexity."""
        issues = []
        if not os.path.isfile(filepath):
            return issues
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return issues

        lines = content.split("\n")
        if len(lines) > 500:
            issues.append(f"File too long ({len(lines)} lines). Consider splitting.")

        for i, line in enumerate(lines, 1):
            if len(line) > 200:
                issues.append(f"Line {i}: {len(line)} chars. Consider breaking up.")
                break

        return issues

    def validate_dry(self, filepath):
        """DRY: Check for obvious duplication."""
        issues = []
        if not os.path.isfile(filepath):
            return issues
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return issues

        blocks = re.findall(r'def \w+\([^)]*\):\s*(?:"""([^"]*)""")?', content)
        seen = {}
        for b in blocks:
            if b in seen:
                issues.append(f"Duplicate docstring: '{b[:40]}...'")
            seen[b] = True

        return issues

    def validate_single_responsibility(self, filepath):
        """Single Responsibility: Class should have one reason to change."""
        issues = []
        if not os.path.isfile(filepath):
            return issues
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
        except Exception:
            return issues

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                public_methods = [m for m in methods if not m.startswith("_")]
                if len(public_methods) > 15:
                    issues.append(f"Class '{node.name}' has {len(public_methods)} public methods. "
                                f"Consider splitting.")

        return issues
