import json
import os

class AgentState:
    INIT = "INIT"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    RECOVERING = "RECOVERING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    WAITING_INPUT = "WAITING_INPUT"
    IDLE = "IDLE"

    TRANSITIONS = {
        INIT: [PLANNING, FAILED],
        PLANNING: [EXECUTING, WAITING_INPUT, FAILED],
        EXECUTING: [VALIDATING, FAILED],
        VALIDATING: [EXECUTING, COMPLETED, VALIDATION_FAILED],
        VALIDATION_FAILED: [RECOVERING, FAILED],
        RECOVERING: [EXECUTING, PLANNING, FAILED],
        COMPLETED: [IDLE],
        WAITING_INPUT: [PLANNING, EXECUTING, FAILED],
        IDLE: [INIT, PLANNING],
    }

    def __init__(self):
        self.current = self.IDLE
        self.history = []
        self.metadata = {}

    def can_transition(self, target):
        valid = self.TRANSITIONS.get(self.current, [])
        return target in valid

    def transition(self, target):
        if self.can_transition(target):
            self.history.append({"from": self.current, "to": target})
            self.current = target
            return True
        return False

    def serialize(self):
        return {"current": self.current, "history": self.history, "metadata": self.metadata}

    @classmethod
    def deserialize(cls, data):
        s = cls()
        s.current = data.get("current", cls.IDLE)
        s.history = data.get("history", [])
        s.metadata = data.get("metadata", {})
        return s
