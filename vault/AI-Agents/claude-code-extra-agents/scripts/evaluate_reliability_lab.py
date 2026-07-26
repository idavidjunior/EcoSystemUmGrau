#!/usr/bin/env python3
"""Evaluate reliability lab scenarios and generate scorecards.

This script evaluates agent performance against defined scenarios,
computes scores based on rubric dimensions, and generates reports.
"""

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Configuration constants
ROOT = Path(__file__).resolve().parent.parent
LAB = ROOT / "reliability-lab"
SCENARIOS = LAB / "scenarios"
RESULTS = LAB / "results"
REPORTS = LAB / "reports"
RUBRIC = LAB / "rubric.json"
PLUGIN_PATH = ROOT / ".claude-plugin" / "plugin.json"

# Scoring weights
MUST_INCLUDE_WEIGHT = 0.6
DIMENSION_WEIGHT = 0.4
FORBIDDEN_PENALTY = 10.0


@dataclass
class EvaluationRow:
    """Represents a single scenario evaluation result."""

    scenario: str
    agent: str
    status: str
    score: float
    details: list[str]


def read_json(path: Path) -> Any:
    """Read and parse JSON file.

    Args:
        path: Path to JSON file.

    Returns:
        Parsed JSON content.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def contains_any(text: str, terms: list[str]) -> bool:
    """Check if text contains any of the given terms (case-insensitive).

    Args:
        text: Text to search in.
        terms: List of terms to search for.

    Returns:
        True if any term is found, False otherwise.
    """
    t = text.lower()
    return any(term.lower() in t for term in terms)


def evaluate_scenario(scenario: dict, rubric: dict) -> EvaluationRow:
    """Evaluate a single scenario against its requirements.

    Args:
        scenario: Scenario specification dictionary.
        rubric: Rubric with dimensions and weights.

    Returns:
        EvaluationRow with scoring results.
    """
    out_file = RESULTS / f"{scenario['id']}.md"
    if not out_file.exists():
        return EvaluationRow(
            scenario=scenario["id"],
            agent=scenario["agent"],
            status="missing_result",
            score=0.0,
            details=["missing output file"],
        )

    text = out_file.read_text(encoding="utf-8").lower()
    details: list[str] = []

    # Check must_include requirements
    must_ok = sum(
        1 for term in scenario.get("must_include", []) if term.lower() in text
    )
    must_ratio = must_ok / max(len(scenario.get("must_include", [])), 1)

    for term in scenario.get("must_include", []):
        if term.lower() not in text:
            details.append(f"missing must_include: {term}")

    # Check forbidden terms
    forbidden_hits = sum(
        1 for term in scenario.get("forbidden", []) if term.lower() in text
    )
    for term in scenario.get("forbidden", []):
        if term.lower() in text:
            details.append(f"forbidden found: {term}")

    # Evaluate dimensions
    dim_score = 0.0
    for dim in rubric["dimensions"]:
        reqs = dim.get("required_sections", [])
        hit = sum(1 for r in reqs if r.lower() in text)
        for r in reqs:
            if r.lower() not in text:
                details.append(f"missing section marker ({dim['id']}): {r}")
        ratio = hit / max(len(reqs), 1)
        dim_score += ratio * float(dim["weight"])

    # Calculate final score
    score = (MUST_INCLUDE_WEIGHT * must_ratio + DIMENSION_WEIGHT * dim_score) * 100.0
    score -= forbidden_hits * FORBIDDEN_PENALTY
    score = max(0.0, min(100.0, score))

    return EvaluationRow(
        scenario=scenario["id"],
        agent=scenario["agent"],
        status="ok",
        score=round(score, 2),
        details=details,
    )


def get_version() -> str:
    """Get version from plugin manifest if available.

    Returns:
        Version string or 'dev' if not found.
    """
    if PLUGIN_PATH.exists():
        try:
            return read_json(PLUGIN_PATH).get("version", "dev")
        except Exception:
            pass
    return "dev"


def deduplicate_leaderboard(entries: list[dict]) -> list[dict]:
    """Remove duplicate leaderboard entries by (version, generated_at).

    Args:
        entries: List of leaderboard entries.

    Returns:
        Deduplicated list keeping latest unique entries.
    """
    seen: set[tuple[str | None, str | None]] = set()
    compact = []
    for item in reversed(entries):
        key = (item.get("version"), item.get("generated_at"))
        if key not in seen:
            seen.add(key)
            compact.append(item)
    return list(reversed(compact))


def evaluate() -> None:
    """Main evaluation function that processes all scenarios."""
    rubric = read_json(RUBRIC)
    scenarios = [read_json(p) for p in sorted(SCENARIOS.glob("*.json"))]

    rows = [evaluate_scenario(sc, rubric) for sc in scenarios]

    valid_scores = [r.score for r in rows if r.status == "ok"]
    overall = round(sum(valid_scores) / max(len(valid_scores), 1), 2)

    scorecard = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenarios_total": len(rows),
        "scenarios_with_results": len(valid_scores),
        "overall_score": overall,
        "rows": [asdict(r) for r in rows],
    }

    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "scorecard.json").write_text(
        json.dumps(scorecard, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Generate markdown report
    md_lines = [
        "# Reliability Scorecard",
        "",
        f"- Generated at: {scorecard['generated_at']}",
        f"- Scenarios total: {scorecard['scenarios_total']}",
        f"- Scenarios with results: {scorecard['scenarios_with_results']}",
        f"- Overall score: {scorecard['overall_score']}",
        "",
        "| Scenario | Agent | Status | Score |",
        "|---|---|---|---:|",
    ]
    for r in rows:
        md_lines.append(f"| {r.scenario} | {r.agent} | {r.status} | {r.score} |")

    (REPORTS / "scorecard.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # Update leaderboard
    lb_path = REPORTS / "leaderboard.json"
    leaderboard = []
    if lb_path.exists():
        leaderboard = read_json(lb_path)

    leaderboard.append({
        "version": get_version(),
        "generated_at": scorecard["generated_at"],
        "overall_score": overall,
        "scenarios_with_results": scorecard["scenarios_with_results"],
    })

    leaderboard = deduplicate_leaderboard(leaderboard)
    lb_path.write_text(
        json.dumps(leaderboard, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Reliability lab evaluated. Overall score: {overall}")


def asdict(obj: Any) -> dict:
    """Convert dataclass to dictionary.

    Args:
        obj: Dataclass instance.

    Returns:
        Dictionary representation.
    """
    if hasattr(obj, "__dataclass_fields__"):
        return {k: getattr(obj, k) for k in obj.__dataclass_fields__}
    return obj


if __name__ == "__main__":
    evaluate()
