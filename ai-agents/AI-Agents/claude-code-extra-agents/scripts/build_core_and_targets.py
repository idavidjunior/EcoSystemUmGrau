#!/usr/bin/env python3
"""Build core specifications and generate platform-specific exports.

This module processes agent and skill markdown files, extracts metadata,
and generates platform-specific configurations for Claude Code, Ollama,
OpenWebUI, and Continue.
"""

import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class SpecDocument:
    """Represents a parsed agent or skill document."""

    id: str
    kind: str
    version: str
    source: str
    title: str
    description: str
    allowed_tools: list[str]
    platforms: list[str]


# Configuration constants
ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
SKILLS_DIR = ROOT / "skills"
CORE_AGENTS = ROOT / "core-spec" / "agents"
CORE_SKILLS = ROOT / "core-spec" / "skills"
DIST = ROOT / "dist"
SUPPORTED_PLATFORMS = ["claude-code", "ollama", "openwebui", "continue"]
DEFAULT_VERSION = "1.0.0"
ENCODING_FALLBACKS = ("utf-8", "cp1252", "latin-1")


def read_text(path: Path) -> str:
    """Read text from file with encoding fallbacks.

    Args:
        path: Path to the file to read.

    Returns:
        File content as string.
    """
    for enc in ENCODING_FALLBACKS:
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    """Write text to file, creating directories if needed.

    Args:
        path: Destination file path.
        content: Text content to write.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def parse_frontmatter(md: str) -> tuple[dict[str, Any], str]:
    """Parse YAML-like frontmatter from markdown content.

    Args:
        md: Markdown content with optional frontmatter.

    Returns:
        Tuple of (parsed metadata dict, body content without frontmatter).
    """
    if not md.startswith("---"):
        return {}, md

    end = md.find("\n---", 3)
    if end == -1:
        return {}, md

    raw = md[3:end].strip("\n")
    body = md[end + 4 :].lstrip("\n")

    data: dict[str, Any] = {}
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue

        key, val = line.split(":", 1)
        key = key.strip()
        val = val.rstrip()

        if val.strip() == "|":
            i += 1
            block = []
            while i < len(lines):
                nxt = lines[i]
                if nxt.startswith("  "):
                    block.append(nxt[2:])
                    i += 1
                elif not nxt.strip():
                    block.append("")
                    i += 1
                else:
                    break
            data[key] = "\n".join(block).strip()
            continue

        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            parts = [p.strip() for p in val[1:-1].split(",") if p.strip()]
            data[key] = [p.strip('"\'') for p in parts]
        else:
            data[key] = val.strip('"\'')
        i += 1

    return data, body


def first_heading(body: str, fallback: str) -> str:
    """Extract the first heading from markdown body.

    Args:
        body: Markdown body content.
        fallback: Default value if no heading found.

    Returns:
        First heading text or fallback value.
    """
    for line in body.splitlines():
        if line.strip().startswith("#"):
            return line.strip().lstrip("#").strip()
    return fallback


def as_yaml_scalar(value: Any) -> str:
    """Convert a Python value to YAML scalar representation.

    Args:
        value: Python value to convert.

    Returns:
        YAML-formatted string representation.
    """
    if isinstance(value, list):
        return "[" + ", ".join(value) + "]"
    if isinstance(value, str):
        if any(ch in value for ch in [":", "#", "[", "]", "{", "}", "\n"]):
            return json.dumps(value, ensure_ascii=False)
        return value
    return str(value)


def dump_yaml(doc: dict[str, Any]) -> str:
    """Dump a dictionary to simple YAML format.

    Args:
        doc: Dictionary to serialize.

    Returns:
        YAML-formatted string.
    """
    lines = []
    for key, value in doc.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for sk, sv in value.items():
                lines.append(f"  {sk}: {as_yaml_scalar(sv)}")
        else:
            lines.append(f"{key}: {as_yaml_scalar(value)}")
    return "\n".join(lines) + "\n"


def normalize_name(name: str) -> str:
    """Normalize a name to a slug format.

    Args:
        name: Original name string.

    Returns:
        Normalized slug with lowercase letters, numbers, and hyphens.
    """
    return re.sub(r"[^a-z0-9\-]+", "-", name.lower()).strip("-")


def build_core_specs() -> tuple[list[SpecDocument], list[SpecDocument]]:
    """Build core specification files from agent and skill markdown sources.

    Returns:
        Tuple of (list of agent specs, list of skill specs).
    """
    agents: list[SpecDocument] = []
    skills: list[SpecDocument] = []

    for path in sorted(AGENTS_DIR.glob("*.md")):
        raw = read_text(path)
        fm, body = parse_frontmatter(raw)
        name = normalize_name(fm.get("name", path.stem))
        description = fm.get("description", "").strip() or first_heading(body, name)
        version = str(fm.get("version", DEFAULT_VERSION))
        allowed = fm.get("allowed-tools", [])
        if isinstance(allowed, str):
            allowed = [x.strip() for x in allowed.split(",") if x.strip()]

        agent_doc = SpecDocument(
            id=name,
            kind="agent",
            version=version,
            source=str(path.relative_to(ROOT)).replace("\\", "/"),
            title=first_heading(body, name),
            description=description,
            allowed_tools=allowed,
            platforms=SUPPORTED_PLATFORMS.copy(),
        )
        write_text(CORE_AGENTS / f"{name}.agent.yaml", dump_yaml(asdict(agent_doc)))
        agents.append(agent_doc)

    for path in sorted(SKILLS_DIR.glob("*/skill.md")):
        raw = read_text(path)
        fm, body = parse_frontmatter(raw)
        name = normalize_name(fm.get("name", path.parent.name))
        description = fm.get("description", "").strip() or first_heading(body, name)
        version = str(fm.get("version", DEFAULT_VERSION))
        allowed = fm.get("allowed-tools", [])
        if isinstance(allowed, str):
            allowed = [x.strip() for x in allowed.split(",") if x.strip()]

        skill_doc = SpecDocument(
            id=name,
            kind="skill",
            version=version,
            source=str(path.relative_to(ROOT)).replace("\\", "/"),
            title=first_heading(body, name),
            description=description,
            allowed_tools=allowed,
            platforms=SUPPORTED_PLATFORMS.copy(),
        )
        write_text(CORE_SKILLS / f"{name}.skill.yaml", dump_yaml(asdict(skill_doc)))
        skills.append(skill_doc)

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {"agents": len(agents), "skills": len(skills)},
        "agents": [a.id for a in agents],
        "skills": [s.id for s in skills],
    }
    write_text(ROOT / "core-spec" / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")

    return agents, skills


def generate_claude_code(agents: list[SpecDocument], skills: list[SpecDocument]) -> None:
    """Generate Claude Code platform manifest.

    Args:
        agents: List of agent specifications.
        skills: List of skill specifications.
    """
    payload = {
        "platform": "claude-code",
        "agents": [a.id for a in agents],
        "skills": [s.id for s in skills],
        "notes": "Uses native markdown agent/skill files from source folders.",
    }
    write_text(DIST / "claude-code" / "manifest.json", json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def generate_ollama(agents: list[SpecDocument]) -> None:
    """Generate Ollama Modelfiles for each agent.

    Args:
        agents: List of agent specifications.
    """
    out = DIST / "ollama" / "modelfiles"
    for a in agents:
        modelfile = (
            "FROM llama3\n"
            f"SYSTEM You are the '{a.id}' specialist from claude-code-extra-agents. "
            f"Purpose: {a.description}\n"
            "PARAMETER temperature 0.2\n"
        )
        write_text(out / f"{a.id}.Modelfile", modelfile)

    readme = """# Ollama Export

Generated Modelfiles for each agent.

## Build example
```bash
ollama create agent-debug-forensic -f dist/ollama/modelfiles/debug-forensic.Modelfile
```
"""
    write_text(DIST / "ollama" / "README.md", readme)


def generate_openwebui(agents: list[SpecDocument]) -> None:
    """Generate OpenWebUI agent configurations.

    Args:
        agents: List of agent specifications.
    """
    out = DIST / "openwebui" / "agents"
    for a in agents:
        obj = {
            "id": a.id,
            "name": a.title,
            "description": a.description,
            "system_prompt": f"You are {a.id}. Focus on: {a.description}",
            "source": a.source,
        }
        write_text(out / f"{a.id}.json", json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def generate_continue(agents: list[SpecDocument]) -> None:
    """Generate Continue/Cline prompt presets.

    Args:
        agents: List of agent specifications.
    """
    out = DIST / "continue" / "prompts"
    for a in agents:
        prompt = (
            f"# {a.id}\n\n"
            f"Purpose: {a.description}\n\n"
            "Use this prompt in Continue/Cline as a role preset.\n"
        )
        write_text(out / f"{a.id}.prompt.md", prompt)


def main() -> None:
    """Main entry point for the build script."""
    agents, skills = build_core_specs()
    generate_claude_code(agents, skills)
    generate_ollama(agents)
    generate_openwebui(agents)
    generate_continue(agents)
    print(f"Generated core spec and exports: {len(agents)} agents, {len(skills)} skills.")


if __name__ == "__main__":
    main()

