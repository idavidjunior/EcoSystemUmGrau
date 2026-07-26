#!/usr/bin/env python3
"""Continuous Learning Runner - Executes the full self-improvement pipeline.

This script orchestrates the complete learning and adaptation cycle:
1. Generates sample results (if needed)
2. Evaluates agent performance in reliability lab
3. Processes feedback loop to build learning profiles
4. Adapts agent prompts based on learned insights
5. Generates comprehensive reports

Run this script periodically to keep agents improving automatically.
"""

import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
LEARNING_REPO = ROOT / "learning-repository"
ADAPTED_AGENTS_DIR = ROOT / "adapted-agents"


def run_script(script_name: str, description: str) -> bool:
    """Run a Python script and report its status.
    
    Args:
        script_name: Name of the script to run.
        description: Human-readable description for logging.
        
    Returns:
        True if successful, False otherwise.
    """
    print(f"\n{'=' * 70}")
    print(f"📋 {description}")
    print(f"{'=' * 70}")
    
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=ROOT,
        capture_output=False,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ {description} completed successfully")
        return True
    else:
        print(f"❌ {description} failed with exit code {result.returncode}")
        return False


def check_prerequisites() -> dict:
    """Check if prerequisites exist for the learning pipeline.
    
    Returns:
        Dictionary with status of each prerequisite.
    """
    checks = {
        "scorecard_exists": (ROOT / "reliability-lab" / "reports" / "scorecard.json").exists(),
        "agent_profiles_exist": any(LEARNING_REPO.glob("agent-profiles/*.json")),
        "collaboration_patterns_exist": (LEARNING_REPO / "collaboration-patterns.json").exists(),
    }
    return checks


def generate_summary_report(results: dict) -> None:
    """Generate a summary report of the learning cycle.
    
    Args:
        results: Dictionary with results from each pipeline stage.
    """
    report_path = LEARNING_REPO / "learning-cycle-summary.md"
    
    timestamp = datetime.now(timezone.utc).isoformat()
    
    report_content = f"""# Learning Cycle Summary Report

**Generated at:** {timestamp}

## Pipeline Execution Results

| Stage | Status | Details |
|-------|--------|---------|
| Generate Results | {'✅ Success' if results.get('generate', False) else '⚠️ Skipped'} | Sample data generated |
| Evaluate Lab | {'✅ Success' if results.get('evaluate', False) else '❌ Failed'} | Performance evaluated |
| Feedback Loop | {'✅ Success' if results.get('feedback', False) else '❌ Failed'} | Learning profiles updated |
| Prompt Adaptation | {'✅ Success' if results.get('adapt', False) else '❌ Failed'} | Agent prompts adapted |

## Learning Repository Status

"""
    
    # Count agent profiles
    profile_count = len(list(LEARNING_REPO.glob("agent-profiles/*.json")))
    report_content += f"- **Agent Profiles:** {profile_count}\n"
    
    # Count adapted agents
    adapted_count = len(list(ADAPTED_AGENTS_DIR.glob("*.md")))
    report_content += f"- **Adapted Agents:** {adapted_count}\n"
    
    # Check collaboration patterns
    collab_file = LEARNING_REPO / "collaboration-patterns.json"
    if collab_file.exists():
        import json
        collab_data = json.loads(collab_file.read_text())
        top_collabs = collab_data.get("top_collaborations", [])
        report_content += f"- **Top Collaborations:** {len(top_collabs)}\n"
        
        if top_collabs:
            report_content += "\n### Top Collaboration Patterns\n\n"
            for collab in top_collabs[:5]:
                report_content += f"- `{collab['pair']}`: {collab['success_count']} successes\n"
    
    report_content += "\n## Adapted Agents\n\n"
    
    if adapted_count > 0:
        report_content += "| Agent | Adaptations | Skills Enhanced |\n"
        report_content += "|-------|-------------|----------------|\n"
        
        for adaptation_file in sorted(ADAPTED_AGENTS_DIR.glob("*.adaptation.json")):
            import json
            metadata = json.loads(adaptation_file.read_text())
            agent_id = metadata.get("agent_id", "unknown")
            adaptations = metadata.get("adaptations_count", 0)
            
            # Load profile to get skills
            profile_path = LEARNING_REPO / "agent-profiles" / f"{agent_id}.json"
            skills = []
            if profile_path.exists():
                profile = json.loads(profile_path.read_text())
                combos = profile.get("recommended_skill_combinations", [])
                if combos:
                    skills = list(set(s for combo in combos for s in combo))
            
            skills_str = ", ".join(skills[:3]) if skills else "N/A"
            report_content += f"| {agent_id} | {adaptations} | {skills_str} |\n"
    
    report_content += f"""
## Next Steps

1. Review adapted agents in `adapted-agents/` directory
2. Integrate adapted prompts into your AI assistant configuration
3. Run actual agent executions to validate improvements
4. Schedule this pipeline to run periodically (e.g., daily/weekly)

## Automated Scheduling

To run this pipeline automatically, add to your crontab:

```bash
# Run learning cycle daily at 2 AM
0 2 * * * cd {ROOT} && python scripts/run_continuous_learning.py >> learning-cycle.log 2>&1
```

---
*Report generated by Continuous Learning Runner*
"""
    
    report_path.write_text(report_content, encoding="utf-8")
    print(f"\n📄 Summary report saved to: {report_path}")


def main() -> None:
    """Main entry point for the continuous learning runner."""
    print("=" * 70)
    print("🚀 Continuous Learning Runner")
    print("   Executing Full Self-Improvement Pipeline")
    print("=" * 70)
    print(f"Started at: {datetime.now(timezone.utc).isoformat()}")
    
    results = {}
    
    # Step 1: Check prerequisites
    print("\n🔍 Checking prerequisites...")
    prereqs = check_prerequisites()
    
    needs_generation = not prereqs["scorecard_exists"]
    
    # Step 2: Generate sample results if needed
    if needs_generation:
        print("\n⚠️  No scorecard found. Generating sample results...")
        results["generate"] = run_script(
            "generate_sample_results.py",
            "Generating sample evaluation results"
        )
    else:
        print("✅ Scorecard already exists, skipping generation")
        results["generate"] = True  # Mark as OK since we have data
    
    # Step 3: Evaluate reliability lab
    results["evaluate"] = run_script(
        "evaluate_reliability_lab.py",
        "Evaluating agent performance in reliability lab"
    )
    
    if not results["evaluate"]:
        print("\n❌ Evaluation failed. Cannot proceed with learning cycle.")
        generate_summary_report(results)
        sys.exit(1)
    
    # Step 4: Process feedback loop
    results["feedback"] = run_script(
        "orchestrate_feedback_loop.py",
        "Processing feedback loop and building learning profiles"
    )
    
    if not results["feedback"]:
        print("\n❌ Feedback loop failed. Skipping prompt adaptation.")
        generate_summary_report(results)
        sys.exit(1)
    
    # Step 5: Adapt agent prompts
    results["adapt"] = run_script(
        "adapt_agent_prompts.py",
        "Adapting agent prompts based on learning profiles"
    )
    
    # Generate summary report
    generate_summary_report(results)
    
    # Final status
    print("\n" + "=" * 70)
    print("🎉 Learning Cycle Complete!")
    print("=" * 70)
    
    all_success = all(results.values())
    if all_success:
        print("✅ All stages completed successfully")
        print(f"\n📂 Outputs:")
        print(f"   - Reliability Lab Reports: {ROOT}/reliability-lab/reports/")
        print(f"   - Learning Profiles: {LEARNING_REPO}/agent-profiles/")
        print(f"   - Collaboration Patterns: {LEARNING_REPO}/collaboration-patterns.json")
        print(f"   - Adapted Agents: {ADAPTED_AGENTS_DIR}/")
        print(f"   - Summary Report: {LEARNING_REPO}/learning-cycle-summary.md")
    else:
        print("⚠️  Some stages encountered issues. Check logs above.")
        print(f"   Results: {results}")
    
    print(f"\nFinished at: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
