#!/usr/bin/env python3
"""Tests for LER v1.2 new layers: Governance, Architecture, Runtime."""

import os
import sys
import json
import tempfile
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


class TestSecurityEnforcer(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_detect_sensitive_data(self):
        from runtime.security import SecurityEnforcer
        sec = SecurityEnforcer(self.tmpdir)

        safe_file = os.path.join(self.tmpdir, "safe.py")
        with open(safe_file, "w") as f:
            f.write("x = 42")

        bad_file = os.path.join(self.tmpdir, "bad.py")
        with open(bad_file, "w") as f:
            f.write("api_key = 'sk-1234567890abcdef12345678'")

        self.assertTrue(sec.check_file_before_commit(safe_file))
        self.assertFalse(sec.check_file_before_commit(bad_file))

    def test_block_destructive_ops(self):
        from runtime.security import SecurityEnforcer
        sec = SecurityEnforcer(self.tmpdir)
        self.assertFalse(sec.verify_no_destructive_op("rm -rf /"))
        self.assertFalse(sec.verify_no_destructive_op("format C:"))
        self.assertTrue(sec.verify_no_destructive_op("python script.py"))

    def test_backup_before_modify(self):
        from runtime.security import SecurityEnforcer
        sec = SecurityEnforcer(self.tmpdir)
        test_file = os.path.join(self.tmpdir, "test.txt")
        with open(test_file, "w") as f:
            f.write("original")
        backup = sec.backup_before_modify(test_file)
        self.assertTrue(os.path.exists(backup))


class TestPersistence(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_save_mission_state(self):
        from runtime.persistence import Persistence
        p = Persistence(self.tmpdir)
        p.save_mission_state("test_001", {"status": "active"})
        state = p.load_mission_state("test_001")
        self.assertIsNotNone(state)
        self.assertEqual(state["state"]["status"], "active")

    def test_checkpoint_cycle(self):
        from runtime.persistence import Persistence
        p = Persistence(self.tmpdir)
        cp_id = p.save_checkpoint("test_cp", {"data": "value"})
        self.assertIsNotNone(cp_id)
        loaded = p.load_checkpoint(cp_id)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["data"], "value")

    def test_list_checkpoints(self):
        from runtime.persistence import Persistence
        p = Persistence(self.tmpdir)
        p.save_checkpoint("cp1", {"a": 1})
        p.save_checkpoint("cp2", {"b": 2})
        cps = p.list_checkpoints()
        self.assertEqual(len(cps), 2)

    def test_mission_survives_restart(self):
        from runtime.persistence import Persistence
        p = Persistence(self.tmpdir)
        p.save_mission_state("m1", {"status": "active"})
        p.save_checkpoint("mission_cp", {"step": 3})
        survival = p.mission_survives_restart("m1")
        self.assertTrue(survival["mission_state_exists"])
        self.assertTrue(survival["checkpoint_exists"])
        self.assertTrue(survival["can_restore"])


class TestAgentGovernance(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_initialize_creates_map(self):
        from governance.agent_governance import AgentGovernance
        gov = AgentGovernance(self.session, self.tmpdir)
        result = gov.initialize()
        map_file = os.path.join(self.tmpdir, "governance", "responsibility_map.json")
        self.assertTrue(os.path.exists(map_file))
        self.assertTrue(result["ready"])

    def test_all_agents_registered(self):
        from governance.agent_governance import AgentGovernance
        gov = AgentGovernance(self.session, self.tmpdir)
        gov.initialize()
        agents = gov.get_all_agents()
        self.assertGreater(len(agents), 5)
        names = [a["name"] for a in agents]
        self.assertIn("GoalAnalyzer", names)
        self.assertIn("Executor", names)
        self.assertIn("FinalAuditor", names)

    def test_conflict_detection(self):
        from governance.conflict_detector import ConflictDetector
        cd = ConflictDetector(self.tmpdir)
        from governance.agent_governance import AgentGovernance
        gov = AgentGovernance(self.session, self.tmpdir)
        gov.initialize()
        result = cd.detect_all()
        self.assertIn("conflicts", result)
        self.assertIn("safe", result)


class TestArchitectureReview(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_validation(self):
        from architecture.review_engine import ArchitectureReviewEngine
        arch = ArchitectureReviewEngine(self.session, {})
        result = arch.validate_current()
        self.assertIn("valid", result)
        self.assertIn("issues", result)
        self.assertIn("checks_performed", result)

    def test_architecture_report(self):
        from architecture.review_engine import ArchitectureReviewEngine
        arch = ArchitectureReviewEngine(self.session, {})
        report = arch.get_architecture_report()
        self.assertIn("architecture_rules", report)
        self.assertIn("module_count", report)
        self.assertIn("layers", report)
        self.assertGreater(len(report["layers"]), 3)


class TestMissionRuntime(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        from core.session import Session
        self.session = Session(self.tmpdir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_execute_simple_goal(self):
        from runtime.persistence import Persistence
        from runtime.security import SecurityEnforcer
        from runtime.mission import MissionRuntime

        persistence = Persistence(self.tmpdir)
        security = SecurityEnforcer(self.tmpdir)

        for d in ["agent", "core", "config", "memory", "governance", "architecture",
                  "runtime", "logs", "checkpoints", "omni_route"]:
            os.makedirs(os.path.join(self.tmpdir, d), exist_ok=True)

        config = {"loop": {"max_iterations": 10, "max_retries_per_step": 2,
                          "checkpoint_enabled": True, "auto_recovery": True,
                          "validation_required": True}}

        mission = MissionRuntime(self.session, config, persistence, security)
        result = mission.execute("Create a test file")
        self.assertIn("status", result)


def run_all():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    for tc in [TestSecurityEnforcer, TestPersistence, TestAgentGovernance,
               TestArchitectureReview, TestMissionRuntime]:
        suite.addTests(loader.loadTestsFromTestCase(tc))
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
