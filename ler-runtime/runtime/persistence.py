"""
LER Persistence Module (Principio da Persistencia)
Mission must survive power loss, server crash, model swap, any interruption.
All state is file-based. Zero dependency on conversation context.
Delegates checkpoint operations to core/checkpoint.py (single source of truth).
"""

import json
import os
import shutil
import time
from datetime import datetime
from core.checkpoint import atomic_write_json, atomic_read_json, init_checkpoint_dir


class Persistence:
    def __init__(self, base_dir):
        self.base_dir = base_dir
        self.memory_dir = os.path.join(base_dir, "memory")
        self.checkpoint_dir = os.path.join(base_dir, "checkpoints")
        self.log_dir = os.path.join(base_dir, "logs")
        self.backup_dir = os.path.join(self.checkpoint_dir, "backups")
        for d in [self.memory_dir, self.checkpoint_dir, self.log_dir, self.backup_dir]:
            os.makedirs(d, exist_ok=True)
        init_checkpoint_dir(base_dir)

    def save_mission_state(self, mission_id, state):
        path = os.path.join(self.memory_dir, f"mission_{mission_id}.json")
        data = {
            "mission_id": mission_id,
            "state": state,
            "updated_at": datetime.now().isoformat(),
            "version": "2.0"
        }
        atomic_write_json(path, data)

    def load_mission_state(self, mission_id):
        path = os.path.join(self.memory_dir, f"mission_{mission_id}.json")
        return atomic_read_json(path)

    def save_checkpoint(self, label, data):
        from core.checkpoint import save_checkpoint as _save_cp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        cp_id = f"{timestamp}_{label}"
        cp_dir = os.path.join(self.checkpoint_dir, cp_id)
        os.makedirs(cp_dir, exist_ok=True)
        data["_meta"] = {
            "id": cp_id,
            "timestamp": timestamp,
            "label": label,
            "version": "2.0"
        }
        atomic_write_json(os.path.join(cp_dir, "checkpoint.json"), data)
        self._cleanup_old()
        return cp_id

    def load_checkpoint(self, cp_id=None):
        if cp_id is None:
            cp_id = self.get_latest_checkpoint()
            if cp_id is None:
                return None
        path = os.path.join(self.checkpoint_dir, cp_id, "checkpoint.json")
        return atomic_read_json(path)

    def get_latest_checkpoint(self):
        import core.checkpoint as cp
        return cp.get_latest_checkpoint()

    def list_checkpoints(self):
        import core.checkpoint as cp
        return cp.list_checkpoints()

    def _cleanup_old(self, max_count=50):
        dirs = sorted([d for d in os.listdir(self.checkpoint_dir)
                       if os.path.isdir(os.path.join(self.checkpoint_dir, d)) and d != "backups"],
                      reverse=True)
        for d in dirs[max_count:]:
            shutil.rmtree(os.path.join(self.checkpoint_dir, d), ignore_errors=True)

    def mission_survives_restart(self, mission_id):
        state = self.load_mission_state(mission_id)
        cp = self.get_latest_checkpoint()
        return {
            "mission_state_exists": state is not None,
            "checkpoint_exists": cp is not None,
            "can_restore": state is not None and cp is not None
        }
