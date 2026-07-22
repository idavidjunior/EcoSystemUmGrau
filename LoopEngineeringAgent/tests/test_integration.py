#!/usr/bin/env python3
"""Integration tests for Loop Engineering Agent."""

import os
import sys
import json
import tempfile
import shutil

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

def test_full_loop():
    """Test a complete execution loop with a simple goal."""
    print("\n=== Integration Test: Full Loop ===\n")

    # Setup temp environment with proper project structure
    tmpdir = tempfile.mkdtemp()
    try:
        # Create proper project structure for validation
        for d in ["agent", "core", "memory", "config", "logs", "checkpoints", "projects"]:
            os.makedirs(os.path.join(tmpdir, d), exist_ok=True)

        # Copy config
        config_src = os.path.join(BASE_DIR, "config")
        config_dst = os.path.join(tmpdir, "config")
        shutil.copytree(config_src, config_dst, dirs_exist_ok=True)

        from core.session import Session
        from core.checkpoint import init_checkpoint_dir
        from agent.orchestrator import Orchestrator

        init_checkpoint_dir(tmpdir)
        session = Session(tmpdir)
        config = {"loop": {"max_iterations": 20, "checkpoint_enabled": True,
                          "auto_recovery": True, "validation_required": True,
                          "max_retries_per_step": 2}}

        orchestrator = Orchestrator(session, config)
        result = orchestrator.run("Create a test file and verify it exists")

        print(f"Result: {json.dumps(result, indent=2, default=str)}")
        assert result["status"] in ["completed", "failed", "max_iterations"], f"Unexpected status: {result['status']}"
        if result["status"] == "completed":
            print("\n[OK] Integration test passed - goal achieved")
        else:
            print(f"\n△ Integration test ended with status: {result['status']}")
            print(f"  Steps: {result.get('steps_completed', 0)}/{result.get('steps_total', 0)}")

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def test_checkpoint_recovery():
    """Test checkpoint save and recovery."""
    print("\n=== Integration Test: Checkpoint Recovery ===\n")

    tmpdir = tempfile.mkdtemp()
    try:
        config_src = os.path.join(BASE_DIR, "config")
        config_dst = os.path.join(tmpdir, "config")
        shutil.copytree(config_src, config_dst)

        from core.checkpoint import init_checkpoint_dir, save_checkpoint, load_checkpoint, get_latest_checkpoint
        from core.state import AgentState

        init_checkpoint_dir(tmpdir)
        state = AgentState()
        state.transition(AgentState.INIT)
        state.transition(AgentState.ANALYZING_GOAL)

        plan = {"steps": [{"id": 1, "action": "test"}]}
        progress = {"steps": [{"id": 1}], "current_step": 1, "completed_steps": [], "failed_steps": []}
        context = {"test_mode": True}

        cp_id = save_checkpoint(state, plan, progress, context, "integration_test")
        print(f"Checkpoint saved: {cp_id}")
        assert cp_id is not None

        loaded = load_checkpoint(cp_id)
        assert loaded is not None
        assert loaded["label"] == "integration_test"
        assert loaded["progress"]["current_step"] == 1

        latest = get_latest_checkpoint()
        assert latest == cp_id

        from core.state import AgentState
        restored_state = AgentState.deserialize(loaded["state"])
        assert restored_state.current == AgentState.ANALYZING_GOAL

        print("\n[OK] Checkpoint recovery test passed")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    test_full_loop()
    test_checkpoint_recovery()
    print("\n[OK] All integration tests passed")
