"""
LER Security Module (Principio da Seguranca)
Enforces: no credential leaks, no destructive ops, backups before changes.
"""

import os
import re
import json


class SecurityEnforcer:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.violations = []

    SENSITIVE_PATTERNS = [
        r'api[_-]?key\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}',
        r'token\s*[=:]\s*["\']?[A-Za-z0-9_\-.]{16,}',
        r'password\s*[=:]\s*["\'][^"\']+["\']',
        r'secret\s*[=:]\s*["\'][^"\']+["\']',
        r'-----BEGIN\s+(RSA|EC|PRIVATE|OPENSSH)\s+KEY-----',
    ]

    def check_file_before_commit(self, filepath):
        if not os.path.isfile(filepath):
            return True
        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return True
        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                self.violations.append(f"Sensitive data in {filepath}: matched {pattern[:40]}")
                return False
        return True

    def check_directory_before_commit(self, directory):
        clean = True
        for root, dirs, files in os.walk(directory):
            for f in files:
                if f.endswith(('.py', '.json', '.md', '.ps1', '.txt', '.yml', '.yaml', '.toml')):
                    fpath = os.path.join(root, f)
                    if not self.check_file_before_commit(fpath):
                        clean = False
        return clean

    def verify_no_destructive_op(self, command):
        dangerous = [
            'rm -rf /', 'rm -rf ~', 'del /f /s', 'rd /s /q',
            'format ', 'diskpart', 'clean all',
            '> /dev/sda', '> /dev/sdb',
        ]
        for d in dangerous:
            if d.lower() in command.lower():
                self.violations.append(f"Destructive command blocked: {command[:80]}")
                return False
        return True

    def backup_before_modify(self, filepath):
        if not os.path.isfile(filepath):
            return True
        backup_dir = os.path.join(self.base_dir, "checkpoints", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        rel = filepath.replace(self.base_dir, "").lstrip("\\/").replace("\\", "_").replace("/", "_")
        backup_path = os.path.join(backup_dir, f"{rel}.bak")
        if not os.path.exists(backup_path):
            import shutil
            shutil.copy2(filepath, backup_path)
        return backup_path

    def get_report(self):
        return {
            "violations": self.violations,
            "total_violations": len(self.violations),
            "safe": len(self.violations) == 0
        }
