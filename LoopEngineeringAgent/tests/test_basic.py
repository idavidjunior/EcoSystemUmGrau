#!/usr/bin/env python3
"""Basic tests for Loop Engineering Agent core components."""

import os
import sys
import json
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

class TestState(unittest.TestCase):
    def test_state_transitions(self):
        from core.state import AgentState
        s = AgentState()
        self.assertEqual(s.current, AgentState.IDLE)
        self.assertTrue(s.transition(AgentState.INIT))
        self.assertEqual(s.current, AgentState.INIT)
        self.assertTrue(s.transition(AgentState.PLANNING))
        self.assertTrue(s.transition(AgentState.EXECUTING))
        self.assertTrue(s.transition(AgentState.VALIDATING))
        self.assertTrue(s.transition(AgentState.COMPLETED))
        self.assertTrue(s.transition(AgentState.IDLE))

    def test_invalid_transition(self):
        from core.state import AgentState
        s = AgentState()
        self.assertFalse(s.transition(AgentState.COMPLETED))

    def test_serialize_deserialize(self):
        from core.state import AgentState
        s = AgentState()
        s.transition(AgentState.INIT)
        s.transition(AgentState.PLANNING)
        data = s.serialize()
        s2 = AgentState.deserialize(data)
        self.assertEqual(s2.current, AgentState.PLANNING)
        self.assertEqual(len(s2.history), 2)

class TestCheckpoint(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.checkpoint import init_checkpoint_dir
        init_checkpoint_dir(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_and_load(self):
        from core.checkpoint import save_checkpoint, load_checkpoint, get_latest_checkpoint
        from core.state import AgentState
        state = AgentState()
        plan = {"steps": [{"id": 1, "action": "test"}]}
        progress = {"steps": [{"id": 1}], "current_step": 1}
        context = {"key": "value"}

        cp_id = save_checkpoint(state, plan, progress, context, "test")
        self.assertIsNotNone(cp_id)

        latest = get_latest_checkpoint()
        self.assertEqual(latest, cp_id)

        data = load_checkpoint(cp_id)
        self.assertIsNotNone(data)
        self.assertEqual(data["label"], "test")
        self.assertIn("state", data)
        self.assertIn("plan", data)
        self.assertIn("progress", data)

class TestSession(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_session_basics(self):
        from core.session import Session
        s = Session(self.tmpdir)
        s.set_goal("Test goal")
        self.assertIsNotNone(s.get_goal())
        self.assertIn("Test goal", s.get_goal())

        s.save_progress({"steps": [1, 2], "current_step": 1})
        progress = s.load_progress()
        self.assertEqual(progress["current_step"], 1)

        s.save_context({"test": "data"})
        ctx = s.load_context()
        self.assertEqual(ctx["test"], "data")

        s.record_decision("Test decision")
        s.record_error("Test error")

class TestPlanner(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def test_create_plan(self):
        from agent.planner import Planner
        planner = Planner(self.session, {})
        steps = planner.create_plan("Create a hello world Python script")
        self.assertGreater(len(steps), 0)
        self.assertEqual(steps[0]["status"], "pending")

    def test_plan_for_fix(self):
        from agent.planner import Planner
        planner = Planner(self.session, {})
        steps = planner.create_plan("Fix the login bug in the authentication module")
        self.assertGreater(len(steps), 0)

    def test_update_step_status(self):
        from agent.planner import Planner
        planner = Planner(self.session, {})
        steps = planner.create_plan("Test status updates")
        planner.update_step_status(steps[0]["id"], "completed")
        progress = self.session.load_progress()
        self.assertIn(steps[0]["id"], progress["completed_steps"])

class TestOmniRoute(unittest.TestCase):
    def test_route_loading(self):
        from omni_route.router import OmniRoute
        try:
            router = OmniRoute(os.path.join(BASE_DIR, "config"))
            self.assertIsNotNone(router)
            self.assertIn("opencode", router.providers)
            self.assertIn("shell", router.providers)
        except Exception as e:
            self.fail(f"OmniRoute init failed: {e}")

def run_all():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTests(loader.loadTestsFromTestCase(TestState))
    suite.addTests(loader.loadTestsFromTestCase(TestCheckpoint))
    suite.addTests(loader.loadTestsFromTestCase(TestSession))
    suite.addTests(loader.loadTestsFromTestCase(TestPlanner))
    suite.addTests(loader.loadTestsFromTestCase(TestOmniRoute))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
