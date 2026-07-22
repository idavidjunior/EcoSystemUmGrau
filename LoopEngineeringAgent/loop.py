#!/usr/bin/env python3
"""
LOOP ENGINEERING AGENT v1.1
Adaptive autonomous engineering agent with:
- Goal analysis & strategy generation
- Risk assessment
- Multi-strategy execution
- Learning from failures
- Success evaluation with scoring
- Final audit before delivery
- OpenCode integration
"""

import os
import sys
import json
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)


def load_config():
    config_path = os.path.join(BASE_DIR, "config", "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def init():
    from core.checkpoint import init_checkpoint_dir
    from core.session import Session

    config = load_config()
    init_checkpoint_dir(BASE_DIR)
    session = Session(BASE_DIR)

    memory_dir = os.path.join(BASE_DIR, "memory")
    os.makedirs(memory_dir, exist_ok=True)

    mem_files = [
        "goal.md", "plan.md", "progress.json", "context.json",
        "decisions.md", "errors.log",
        "learned_rules.json", "successful_patterns.json", "failed_patterns.json",
    ]
    defaults = {
        "progress.json": '{"steps": [], "current_step": 0, "completed_steps": [], "failed_steps": []}',
        "context.json": "{}",
        "goal.md": "# Goal\n\nNo goal set yet.\n",
        "plan.md": "# Plan\n\nNo plan created yet.\n",
        "decisions.md": "# Decisions Log\n\n",
        "errors.log": "# Errors Log\n\n",
        "learned_rules.json": '{"rules": []}',
        "successful_patterns.json": '{"patterns": []}',
        "failed_patterns.json": '{"patterns": []}',
    }
    for fname in mem_files:
        fpath = os.path.join(memory_dir, fname)
        if not os.path.exists(fpath) and fname in defaults:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(defaults[fname])

    lt_dirs = ["projects", "knowledge", "user_preferences", "technical_history", "successful_architectures"]
    for d in lt_dirs:
        os.makedirs(os.path.join(memory_dir, d), exist_ok=True)

    session.log(f"LoopEngineeringAgent v{config['version']} initialized")
    session.log(f"Base directory: {BASE_DIR}")
    return session, config


def main():
    parser = argparse.ArgumentParser(description="Loop Engineering Agent v1.1")
    parser.add_argument("goal", nargs="?", help="The goal to achieve")
    parser.add_argument("--resume", "-r", action="store_true", help="Resume from last checkpoint")
    parser.add_argument("--status", "-s", action="store_true", help="Show current status and exit")
    parser.add_argument("--version", "-v", action="store_true", help="Show version and exit")
    parser.add_argument("--reset", action="store_true", help="Reset all state and start fresh")
    parser.add_argument("--report", action="store_true", help="Generate final report from current state")
    parser.add_argument("--bridge", action="store_true", help="Run in OpenCode bridge mode")

    args = parser.parse_args()

    if args.version:
        config = load_config()
        print(f"Loop Engineering Agent v{config['version']}")
        print("Adaptive Autonomous Engineering System")
        print("Modules: GoalAnalyzer, StrategyEngine, RiskManager, LearningEngine, SuccessEvaluator, FinalAuditor")
        return

    session, config = init()

    if args.status:
        _show_status(session)
        return

    if args.reset:
        _reset_state(session)
        print("State reset. Ready for new goal.")
        return

    if args.report:
        from agent.final_auditor import FinalAuditor
        auditor = FinalAuditor(session, BASE_DIR)
        report = auditor.generate_final_report()
        print(report[:2000])
        return

    if args.bridge:
        from integrations.opencode.opencode_bridge import OpenCodeBridge
        bridge = OpenCodeBridge(BASE_DIR)
        goal = args.goal or input("\nEnter goal from OpenCode: ").strip()
        if goal:
            result = bridge.delegate_goal(goal)
            print(json.dumps(result, indent=2, default=str))
        return

    from agent.orchestrator import Orchestrator
    orchestrator = Orchestrator(session, config)

    if args.resume:
        print("Resuming from last checkpoint...")
    elif args.goal:
        goal = args.goal
    else:
        goal = input("\nEnter your goal: ").strip()
        if not goal:
            print("No goal provided. Use: python loop.py \"your goal\"")
            return

    if args.goal:
        print(f"\nGoal: {args.goal}\n")

    result = orchestrator.run(args.goal if args.goal else goal)

    print(f"\n{'='*60}")
    print(f"RESULT: {result.get('status', 'unknown').upper()}")
    print(f"v1.1 | Elapsed: {result.get('elapsed_seconds', 0):.1f}s")
    print(f"Iterations: {result.get('iterations', 0)}")
    print(f"Steps: {result.get('steps_completed', 0)}/{result.get('steps_total', 0)}")
    print(f"Strategy: {result.get('strategy', 'N/A')}")
    print(f"Learning: {result.get('learning', {}).get('total_learned_rules', 0)} rules")
    print(f"{'='*60}")

    if result.get("status") == "completed":
        print("\n[OK] GOAL ACHIEVED - All validations passed")
    else:
        print(f"\n[FAIL] Status: {result.get('status', 'unknown')}")

    return 0 if result.get("status") == "completed" else 1


def _show_status(session):
    goal = session.get_goal()
    plan = session.get_plan()
    progress = session.load_progress()
    context = session.load_context()

    print(f"\n{'='*60}")
    print("LOOP ENGINEERING AGENT v1.1 - STATUS")
    print(f"{'='*60}")
    if goal:
        print(f"\nGoal: {goal[:200]}")
    print(f"\nProgress: {len(progress.get('completed_steps', []))}/{len(progress.get('steps', []))} steps")
    print(f"Completed: {progress.get('completed_steps', [])}")
    print(f"Failed: {progress.get('failed_steps', [])}")
    print(f"Current step: {progress.get('current_step', 0)}")

    analysis = context.get("goal_analysis")
    if analysis:
        print(f"\nDomain: {analysis.get('domain', 'N/A')}")
        print(f"Type: {analysis.get('task_type', 'N/A')}")
        print(f"Complexity: {analysis.get('complexity', 'N/A')}/10")
        print(f"Technologies: {', '.join(analysis.get('technologies', ['N/A']))}")

    strategies = context.get("strategies")
    if strategies:
        print(f"\nStrategies available: {len(strategies)}")
        for s in strategies[:3]:
            print(f"  #{s.get('rank', '?')}: {s.get('name', 'N/A')} (score: {s.get('score', 0)})")

    success_eval = context.get("success_evaluation")
    if success_eval:
        print(f"\nSuccess score: {success_eval.get('total_score', 0)}%")

    cp_dir = os.path.join(BASE_DIR, "checkpoints")
    if os.path.isdir(cp_dir):
        cps = [d for d in os.listdir(cp_dir) if os.path.isdir(os.path.join(cp_dir, d))]
        print(f"\nCheckpoints: {len(cps)}")

    report_dir = os.path.join(BASE_DIR, "reports")
    if os.path.isdir(report_dir):
        reports = [f for f in os.listdir(report_dir) if f.endswith(".md")]
        if reports:
            print(f"Reports: {len(reports)}")


def _reset_state(session):
    import shutil
    memory_dir = os.path.join(BASE_DIR, "memory")
    cp_dir = os.path.join(BASE_DIR, "checkpoints")
    for d in [memory_dir, cp_dir]:
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d, exist_ok=True)

    mem_files = {
        "goal.md": "# Goal\n\nNo goal set yet.\n",
        "plan.md": "# Plan\n\nNo plan created yet.\n",
        "progress.json": '{"steps": [], "current_step": 0, "completed_steps": [], "failed_steps": []}',
        "context.json": "{}",
        "decisions.md": "# Decisions Log\n\n",
        "errors.log": "# Errors Log\n\n",
        "learned_rules.json": '{"rules": []}',
        "successful_patterns.json": '{"patterns": []}',
        "failed_patterns.json": '{"patterns": []}',
    }
    for fname, content in mem_files.items():
        with open(os.path.join(memory_dir, fname), "w", encoding="utf-8") as f:
            f.write(content)

    session.log("State reset complete")


if __name__ == "__main__":
    sys.exit(main())
