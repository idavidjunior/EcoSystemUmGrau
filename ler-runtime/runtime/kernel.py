"""
LER Kernel - Initializes all layers in correct order.

Camada 1: Governance
Camada 2: Architecture
Camada 3: Planning
Camada 4: Execution
Camada 5: Validation
Camada 6: Recovery
Camada 7: Persistence
Camada 8: Versioning
Camada 9: Audit
"""

import os
import sys
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)


class LERKernel:
    def __init__(self):
        self.layers = {}
        self.initialization_order = [
            "persistence",
            "security",
            "governance",
            "architecture",
            "session",
            "mission",
        ]
        self.initialized = {}

    def boot(self):
        print("[LER] Booting Loop Engineering Runtime v2.0...")

        from runtime.persistence import Persistence
        from runtime.security import SecurityEnforcer
        from core.session import Session
        from core.checkpoint import init_checkpoint_dir

        config = self._load_config()

        init_checkpoint_dir(BASE_DIR)

        session = Session(BASE_DIR)
        persistence = Persistence(BASE_DIR)
        security = SecurityEnforcer(BASE_DIR)

        self.layers["persistence"] = persistence
        self.layers["security"] = security
        self.layers["session"] = session
        self.layers["config"] = config

        from governance.agent_governance import AgentGovernance
        gov = AgentGovernance(session, BASE_DIR)
        gov.initialize()
        self.layers["governance"] = gov

        from architecture.review_engine import ArchitectureReviewEngine
        arch = ArchitectureReviewEngine(session, config)
        self.layers["architecture"] = arch

        self.initialized = {k: True for k in self.initialization_order}

        session.log("[LER] All layers initialized successfully")
        session.log(f"[LER] Base directory: {BASE_DIR}")

        return self.layers

    def _load_config(self):
        config_path = os.path.join(BASE_DIR, "config", "config.json")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def get_layer(self, name):
        return self.layers.get(name)

    def get_session(self):
        return self.layers.get("session")

    def shutdown(self):
        session = self.get_session()
        if session:
            session.log("[LER] Kernel shutdown complete")
