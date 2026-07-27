#!/usr/bin/env python3
"""Validate core specification files and generated build artifacts.

This script ensures that the core-spec manifest exists and all required
platform distribution files have been generated.
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = ROOT / "core-spec" / "manifest.json"
REQUIRED_PATHS = [
    ROOT / "dist" / "claude-code" / "manifest.json",
    ROOT / "dist" / "ollama" / "README.md",
    ROOT / "dist" / "openwebui" / "agents",
    ROOT / "dist" / "continue" / "prompts",
]


def load_manifest(path: Path) -> dict:
    """Load and parse JSON manifest file.

    Args:
        path: Path to the manifest file.

    Returns:
        Parsed manifest dictionary.

    Raises:
        SystemExit: If manifest file is missing.
    """
    if not path.exists():
        raise SystemExit(f"Missing {path}. Run build_core_and_targets.py first.")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_required_paths(paths: list[Path]) -> None:
    """Validate that all required paths exist.

    Args:
        paths: List of paths to validate.

    Raises:
        SystemExit: If any required path is missing.
    """
    for path in paths:
        if not path.exists():
            raise SystemExit(f"Missing generated target: {path}")


def main() -> None:
    """Main entry point for validation script."""
    manifest = load_manifest(MANIFEST_PATH)
    validate_required_paths(REQUIRED_PATHS)

    agent_count = manifest["counts"]["agents"]
    skill_count = manifest["counts"]["skills"]
    print(f"Core spec validated: {agent_count} agents, {skill_count} skills.")


if __name__ == "__main__":
    main()
