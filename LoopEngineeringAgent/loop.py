#!/usr/bin/env python3
"""
LOOP ENGINEERING AGENT v1.0
Main entry point: receives a goal and runs the autonomous engineering loop.
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

    # Init memory files
    memory_dir = os.path.join(BASE_DIR, "memory")
    os.makedirs(memory_dir, exist_ok=True)

    mem_files = [
        "goal.md",
        "plan.md",
        "progress.json",
        "context.json",
        "decisions.md",
        "errors.log",
    ]
    for fname in mem_files:
        fpath = os.path.join(memory_dir, fname)
        if not os.path.exists(fpath):
            with open(fpath, "w", encoding="utf-8") as f:
                if fname == "progress.json":
                    f.write('{"steps": [], "current_step": 0, "completed_steps": [], "failed_steps": []}')
                elif fname == "context.json":
                    f.write("{}")
                elif fname == "goal.md":
                    f.write("# Goal\n\nNo goal set yet.\n")
                elif fname == "plan.md":
                    f.write("# Plan\n\nNo plan created yet.\n")
                elif fname == "decisions.md":
                    f.write("# Decisions Log\n\n")
                elif fname == "errors.log":
                    f.write("# Errors Log\n\n")

    session.log(f"LoopEngineeringAgent v{config['version']} initialized")
    session.log(f"Base directory: {BASE_DIR}")
    return session, config


def main():
    parser = argparse.ArgumentParser(description="Loop Engineering Agent v1.0")
    parser.add_argument("goal", nargs="?", help="The goal to achieve")
    parser.add_argument("--resume", "-r", action="store_true",
                       help="Resume from last checkpoint")
    parser.add_argument("--status", "-s", action="store_true",
                       help="Show current status and exit")
    parser.add_argument("--version", "-v", action="store_true",
                       help="Show version and exit")
    parser.add_argument("--reset", action="store_true",
                       help="Reset all state and start fresh")

    args = parser.parse_args()

    if args.version:
        config = load_config()
        print(f"Loop Engineering Agent v{config['version']}")
        return

    session, config = init()

    if args.status:
        _show_status(session)
        return

    if args.reset:
        _reset_state(session)
        print("State reset. Ready for new goal.")
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
    print(f"Elapsed: {result.get('elapsed_seconds', 0):.1f}s")
    print(f"Iterations: {result.get('iterations', 0)}")
    print(f"Steps: {result.get('steps_completed', 0)}/{result.get('steps_total', 0)}")
    print(f"{'='*60}")

    if result.get("status") == "completed":
        print("\n✓ GOAL ACHIEVED")
    else:
        print(f"\n✗ Status: {result.get('status', 'unknown')}")

    return 0 if result.get("status") == "completed" else 1


def _show_status(session):
    goal = session.get_goal()
    plan = session.get_plan()
    progress = session.load_progress()

    print(f"\n{'='*60}")
    print(f"LOOP ENGINEERING AGENT - STATUS")
    print(f"{'='*60}")
    if goal:
        print(f"\nGoal: {goal[:200]}")
    print(f"\nProgress: {len(progress.get('completed_steps', []))}/{len(progress.get('steps', []))} steps")
    print(f"Completed: {progress.get('completed_steps', [])}")
    print(f"Failed: {progress.get('failed_steps', [])}")
    print(f"Current step: {progress.get('current_step', 0)}")

    import glob
    cp_dir = os.path.join(BASE_DIR, "checkpoints")
    if os.path.isdir(cp_dir):
        cps = [d for d in os.listdir(cp_dir) if os.path.isdir(os.path.join(cp_dir, d))]
        print(f"\nCheckpoints available: {len(cps)}")
        for cp in sorted(cps)[-5:]:
            print(f"  - {cp}")


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
    }
    for fname, content in mem_files.items():
        with open(os.path.join(memory_dir, fname), "w", encoding="utf-8") as f:
            f.write(content)

    session.log("State reset complete")


if __name__ == "__main__":
    sys.exit(main())
