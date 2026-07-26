#!/usr/bin/env python3
"""Feedback Loop Orchestrator for Agent Learning and Collaboration.

This module implements a continuous improvement system where agents:
1. Learn from each other's performance in the reliability lab
2. Complement each other following the operating model
3. Adapt their specifications based on evaluation results
4. Share knowledge through a centralized learning repository
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class LearningEvent:
    """Represents a learning event from agent performance."""

    timestamp: str
    scenario_id: str
    agent_id: str
    score: float
    strengths: list[str]
    weaknesses: list[str]
    recommended_skills: list[str]
    collaboration_opportunities: list[str]


@dataclass
class AgentKnowledgeProfile:
    """Tracks an agent's accumulated knowledge and performance history."""

    agent_id: str
    total_scenarios: int = 0
    average_score: float = 0.0
    strength_patterns: dict[str, int] = field(default_factory=dict)
    weakness_patterns: dict[str, int] = field(default_factory=dict)
    successful_collaborations: list[str] = field(default_factory=list)
    recommended_skill_combinations: list[list[str]] = field(default_factory=list)
    last_updated: str = ""


# Configuration constants
ROOT = Path(__file__).resolve().parent.parent
RELIABILITY_LAB = ROOT / "reliability-lab"
LEARNING_REPO = ROOT / "learning-repository"
AGENT_PROFILES = LEARNING_REPO / "agent-profiles"
COLLABORATION_PATTERNS = LEARNING_REPO / "collaboration-patterns.json"
SKILL_COMBINATIONS = LEARNING_REPO / "skill-combinations.json"
FEEDBACK_LOG = LEARNING_REPO / "feedback-log.json"


def ensure_directories() -> None:
    """Create necessary directories for the learning repository."""
    LEARNING_REPO.mkdir(parents=True, exist_ok=True)
    AGENT_PROFILES.mkdir(parents=True, exist_ok=True)


def load_json(path: Path) -> Any:
    """Load JSON file with error handling.
    
    Args:
        path: Path to JSON file.
        
    Returns:
        Parsed JSON content or empty dict/list if file doesn't exist.
    """
    if not path.exists():
        return {} if path.suffix == ".json" else []
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Any) -> None:
    """Save data to JSON file.
    
    Args:
        path: Destination path.
        data: Data to serialize.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8"
    )


def load_scorecard() -> dict:
    """Load the latest reliability lab scorecard.
    
    Returns:
        Scorecard dictionary or empty dict if not found.
    """
    scorecard_path = RELIABILITY_LAB / "reports" / "scorecard.json"
    return load_json(scorecard_path)


def load_rubric() -> dict:
    """Load the evaluation rubric.
    
    Returns:
        Rubric dictionary.
    """
    return load_json(RELIABILITY_LAB / "rubric.json")


def load_scenarios() -> list[dict]:
    """Load all scenario definitions.
    
    Returns:
        List of scenario dictionaries.
    """
    scenarios_dir = RELIABILITY_LAB / "scenarios"
    scenarios = []
    for path in sorted(scenarios_dir.glob("*.json")):
        scenarios.append(load_json(path))
    return scenarios


def analyze_performance(row: dict, scenario: dict, rubric: dict) -> LearningEvent:
    """Analyze agent performance to extract learning insights.
    
    Args:
        row: Evaluation row from scorecard.
        scenario: Scenario definition.
        rubric: Evaluation rubric.
        
    Returns:
        LearningEvent with extracted insights.
    """
    strengths = []
    weaknesses = []
    
    # Analyze must_include compliance
    must_include = scenario.get("must_include", [])
    if must_include:
        compliant = sum(1 for term in must_include if term.lower() in row.get("details", []))
        if compliant == len(must_include):
            strengths.append("requirements_compliance")
        else:
            missing = [t for t in must_include if t.lower() not in str(row.get("details", []))]
            if missing:
                weaknesses.append(f"missing_requirements:{','.join(missing)}")
    
    # Analyze dimension performance
    for dim in rubric.get("dimensions", []):
        dim_id = dim["id"]
        required = dim.get("required_sections", [])
        details_str = str(row.get("details", [])).lower()
        
        hit_count = sum(1 for r in required if r.lower() in details_str)
        if hit_count == len(required):
            strengths.append(f"dimension_{dim_id}")
        elif hit_count < len(required) * 0.5:
            weaknesses.append(f"weak_{dim_id}")
    
    # Check for forbidden term violations
    forbidden = scenario.get("forbidden", [])
    if forbidden:
        violations = [t for t in forbidden if t.lower() in str(row.get("details", [])).lower()]
        if violations:
            weaknesses.append(f"forbidden_violations:{','.join(violations)}")
        else:
            strengths.append("avoided_forbidden_terms")
    
    # Determine recommended skills based on scenario type
    recommended_skills = determine_recommended_skills(scenario)
    
    # Identify collaboration opportunities from operating model
    collaboration_opportunities = identify_collaboration_opportunities(scenario, row["agent"])
    
    return LearningEvent(
        timestamp=datetime.now(timezone.utc).isoformat(),
        scenario_id=row["scenario"],
        agent_id=row["agent"],
        score=row["score"],
        strengths=strengths,
        weaknesses=weaknesses,
        recommended_skills=recommended_skills,
        collaboration_opportunities=collaboration_opportunities
    )


def determine_recommended_skills(scenario: dict) -> list[str]:
    """Determine which skills would help based on scenario characteristics.
    
    Args:
        scenario: Scenario definition.
        
    Returns:
        List of recommended skill IDs.
    """
    title_lower = scenario.get("title", "").lower()
    prompt_lower = scenario.get("prompt", "").lower()
    combined = f"{title_lower} {prompt_lower}"
    
    skill_mapping = {
        "incident": ["observability-stack", "resilience-engineering"],
        "debug": ["observability-stack", "error-message-design"],
        "migration": ["migration-playbooks", "database-migrations"],
        "security": ["security-review", "authz-authn-matrix"],
        "performance": ["cache-strategy-selector", "concurrent-computation-patterns"],
        "api": ["api-design", "contract-test-broker"],
        "review": ["tdd-workflow", "search-first"],
        "dependency": ["security-review", "dependency-auditor"],
    }
    
    for keyword, skills in skill_mapping.items():
        if keyword in combined:
            return skills
    
    return ["search-first"]


def identify_collaboration_opportunities(scenario: dict, primary_agent: str) -> list[str]:
    """Identify which other agents could collaborate based on operating model.
    
    Args:
        scenario: Scenario definition.
        primary_agent: ID of the primary agent.
        
    Returns:
        List of collaborating agent IDs.
    """
    # Operating model routing patterns
    routing_map = {
        "debug-forensic": ["incident-postmortem", "sentinel"],
        "incident-simulator": ["incident-postmortem", "doctor"],
        "legacy-modernizer": ["schema-evolution-planner", "monorepo-architect"],
        "performance-profiler": ["performance-profiler", "cache-strategy-selector"],
        "api-integration-specialist": ["contract-test-broker", "vulnerability-hunter"],
        "ai-code-verifier": ["code-reviewer", "prompt-optimizer"],
        "sentinel": ["vulnerability-hunter", "dependency-auditor"],
    }
    
    collaborators = routing_map.get(primary_agent, [])
    return [c for c in collaborators if c != primary_agent]


def update_agent_profile(event: LearningEvent) -> AgentKnowledgeProfile:
    """Update an agent's knowledge profile with new learning event.
    
    Args:
        event: Learning event to process.
        
    Returns:
        Updated AgentKnowledgeProfile.
    """
    profile_path = AGENT_PROFILES / f"{event.agent_id}.json"
    profile_data = load_json(profile_path)
    
    # Initialize or load existing profile
    if profile_data:
        profile = AgentKnowledgeProfile(**profile_data)
    else:
        profile = AgentKnowledgeProfile(agent_id=event.agent_id)
    
    # Update statistics
    old_total = profile.total_scenarios
    old_avg = profile.average_score
    
    profile.total_scenarios += 1
    profile.average_score = ((old_avg * old_total) + event.score) / profile.total_scenarios
    profile.last_updated = event.timestamp
    
    # Track strength patterns
    for strength in event.strengths:
        profile.strength_patterns[strength] = profile.strength_patterns.get(strength, 0) + 1
    
    # Track weakness patterns
    for weakness in event.weaknesses:
        # Extract base pattern (before colon if present)
        base_pattern = weakness.split(":")[0]
        profile.weakness_patterns[base_pattern] = profile.weakness_patterns.get(base_pattern, 0) + 1
    
    # Track successful collaborations (score > 70)
    if event.score >= 70 and event.collaboration_opportunities:
        for collaborator in event.collaboration_opportunities:
            collab_key = f"{event.agent_id}+{collaborator}"
            if collab_key not in profile.successful_collaborations:
                profile.successful_collaborations.append(collab_key)
    
    # Update recommended skill combinations
    if event.recommended_skills and event.score >= 60:
        skill_combo = sorted(event.recommended_skills)
        if skill_combo not in profile.recommended_skill_combinations:
            profile.recommended_skill_combinations.append(skill_combo)
    
    # Save updated profile
    save_json(profile_path, asdict(profile))
    
    return profile


def generate_collaboration_insights() -> dict:
    """Generate insights about effective agent collaborations.
    
    Returns:
        Dictionary with collaboration patterns and recommendations.
    """
    # Load all agent profiles
    profiles = []
    for profile_path in AGENT_PROFILES.glob("*.json"):
        profiles.append(load_json(profile_path))
    
    # Aggregate collaboration data
    collaboration_counts = {}
    skill_combo_counts = {}
    
    for profile in profiles:
        for collab in profile.get("successful_collaborations", []):
            collaboration_counts[collab] = collaboration_counts.get(collab, 0) + 1
        
        for combo in profile.get("recommended_skill_combinations", []):
            combo_key = "+".join(combo)
            skill_combo_counts[combo_key] = skill_combo_counts.get(combo_key, 0) + 1
    
    insights = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "top_collaborations": sorted(
            [{"pair": k, "success_count": v} for k, v in collaboration_counts.items()],
            key=lambda x: x["success_count"],
            reverse=True
        )[:10],
        "effective_skill_combinations": sorted(
            [{"skills": k.split("+"), "usage_count": v} for k, v in skill_combo_counts.items()],
            key=lambda x: x["usage_count"],
            reverse=True
        )[:10],
        "agent_summaries": [
            {
                "agent_id": p["agent_id"],
                "avg_score": round(p["average_score"], 2),
                "top_strengths": sorted(p.get("strength_patterns", {}).items(), key=lambda x: x[1], reverse=True)[:3],
                "areas_for_improvement": sorted(p.get("weakness_patterns", {}).items(), key=lambda x: x[1], reverse=True)[:3]
            }
            for p in profiles
        ]
    }
    
    save_json(COLLABORATION_PATTERNS, insights)
    return insights


def generate_skill_recommendations() -> dict:
    """Generate global skill combination recommendations.
    
    Returns:
        Dictionary with skill combination insights.
    """
    profiles = []
    for profile_path in AGENT_PROFILES.glob("*.json"):
        profiles.append(load_json(profile_path))
    
    # Aggregate all skill combinations
    all_combos = {}
    for profile in profiles:
        for combo in profile.get("recommended_skill_combinations", []):
            combo_key = "+".join(sorted(combo))
            if combo_key not in all_combos:
                all_combos[combo_key] = {"skills": combo, "agents_using": [], "avg_score": 0}
            all_combos[combo_key]["agents_using"].append(profile["agent_id"])
    
    # Calculate average scores for each combination
    for combo_key, combo_data in all_combos.items():
        scores = []
        for agent_id in combo_data["agents_using"]:
            agent_profile = load_json(AGENT_PROFILES / f"{agent_id}.json")
            if agent_profile:
                scores.append(agent_profile.get("average_score", 0))
        combo_data["avg_score"] = round(sum(scores) / max(len(scores), 1), 2)
    
    recommendations = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill_combinations": sorted(
            all_combos.values(),
            key=lambda x: (x["avg_score"], len(x["agents_using"])),
            reverse=True
        ),
        "usage_statistics": {
            "total_combinations": len(all_combos),
            "most_used_skills": get_most_used_skills(all_combos)
        }
    }
    
    save_json(SKILL_COMBINATIONS, recommendations)
    return recommendations


def get_most_used_skills(combos: dict) -> list[dict]:
    """Get the most frequently used skills across combinations.
    
    Args:
        combos: Dictionary of skill combinations.
        
    Returns:
        List of skills with usage counts.
    """
    skill_counts = {}
    for combo_data in combos.values():
        for skill in combo_data["skills"]:
            skill_counts[skill] = skill_counts.get(skill, 0) + 1
    
    return sorted(
        [{"skill": k, "usage_count": v} for k, v in skill_counts.items()],
        key=lambda x: x["usage_count"],
        reverse=True
    )[:10]


def log_feedback_event(event: LearningEvent, profile: AgentKnowledgeProfile) -> None:
    """Log a feedback event to the feedback log.
    
    Args:
        event: Learning event.
        profile: Updated agent profile.
    """
    feedback_log = load_json(FEEDBACK_LOG)
    if not isinstance(feedback_log, list):
        feedback_log = []
    
    feedback_log.append({
        "event": asdict(event),
        "profile_snapshot": asdict(profile),
        "learning_summary": {
            "score_trend": "improving" if profile.average_score > 70 else "needs_attention",
            "key_strengths": list(profile.strength_patterns.keys())[:3],
            "priority_improvements": list(profile.weakness_patterns.keys())[:3]
        }
    })
    
    # Keep only last 1000 events
    if len(feedback_log) > 1000:
        feedback_log = feedback_log[-1000:]
    
    save_json(FEEDBACK_LOG, feedback_log)


def process_learning_cycle() -> dict:
    """Process a complete learning cycle from scorecard to insights.
    
    Returns:
        Summary dictionary of the learning cycle.
    """
    ensure_directories()
    
    scorecard = load_scorecard()
    if not scorecard:
        return {"error": "No scorecard found. Run evaluate_reliability_lab.py first."}
    
    rubric = load_rubric()
    scenarios = {s["id"]: s for s in load_scenarios()}
    
    processed_events = []
    updated_profiles = []
    
    for row in scorecard.get("rows", []):
        if row["status"] != "ok":
            continue
        
        scenario = scenarios.get(row["scenario"])
        if not scenario:
            continue
        
        # Analyze performance
        event = analyze_performance(row, scenario, rubric)
        processed_events.append(event)
        
        # Update agent profile
        profile = update_agent_profile(event)
        updated_profiles.append(profile)
        
        # Log feedback
        log_feedback_event(event, profile)
    
    # Generate insights
    collaboration_insights = generate_collaboration_insights()
    skill_recommendations = generate_skill_recommendations()
    
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "events_processed": len(processed_events),
        "profiles_updated": len(updated_profiles),
        "overall_score": scorecard.get("overall_score", 0),
        "top_performers": sorted(
            [{"agent_id": p.agent_id, "avg_score": round(p.average_score, 2)} 
             for p in updated_profiles],
            key=lambda x: x["avg_score"],
            reverse=True
        )[:5],
        "insights_generated": {
            "collaboration_patterns": str(COLLABORATION_PATTERNS),
            "skill_combinations": str(SKILL_COMBINATIONS)
        }
    }
    
    return summary


def main() -> None:
    """Main entry point for the feedback loop orchestrator."""
    print("Starting Feedback Loop Orchestrator...")
    print("=" * 60)
    
    summary = process_learning_cycle()
    
    if "error" in summary:
        print(f"Error: {summary['error']}")
        return
    
    print(f"Processed {summary['events_processed']} learning events")
    print(f"Updated {summary['profiles_updated']} agent profiles")
    print(f"Overall reliability score: {summary['overall_score']}")
    print("\nTop performers:")
    for performer in summary["top_performers"]:
        print(f"  - {performer['agent_id']}: {performer['avg_score']}")
    
    print("\nInsights generated:")
    print(f"  - Collaboration patterns: {summary['insights_generated']['collaboration_patterns']}")
    print(f"  - Skill combinations: {summary['insights_generated']['skill_combinations']}")
    
    print("\n" + "=" * 60)
    print("Feedback loop completed successfully!")


if __name__ == "__main__":
    main()
