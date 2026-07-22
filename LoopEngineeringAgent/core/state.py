import json
import os


class AgentState:
    IDLE = "IDLE"
    INIT = "INIT"
    ANALYZING_GOAL = "ANALYZING_GOAL"
    CREATING_STRATEGY = "CREATING_STRATEGY"
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    RECOVERING = "RECOVERING"
    LEARNING = "LEARNING"
    REPLANNING = "REPLANNING"
    SUCCESS_EVALUATING = "SUCCESS_EVALUATING"
    FINAL_AUDITING = "FINAL_AUDITING"
    SUCCESS_VERIFIED = "SUCCESS_VERIFIED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    WAITING_INPUT = "WAITING_INPUT"

    TRANSITIONS = {
        IDLE: [INIT, ANALYZING_GOAL, FAILED],
        INIT: [ANALYZING_GOAL, FAILED],
        ANALYZING_GOAL: [CREATING_STRATEGY, PLANNING, FAILED],
        CREATING_STRATEGY: [PLANNING, ANALYZING_GOAL, FAILED],
        PLANNING: [EXECUTING, WAITING_INPUT, REPLANNING, FAILED],
        EXECUTING: [VALIDATING, FAILED],
        VALIDATING: [EXECUTING, LEARNING, VALIDATION_FAILED, SUCCESS_EVALUATING, COMPLETED],
        VALIDATION_FAILED: [RECOVERING, LEARNING, FAILED],
        RECOVERING: [EXECUTING, REPLANNING, LEARNING, FAILED],
        LEARNING: [EXECUTING, REPLANNING, PLANNING, SUCCESS_EVALUATING, FAILED],
        REPLANNING: [ANALYZING_GOAL, PLANNING, FAILED],
        SUCCESS_EVALUATING: [FINAL_AUDITING, REPLANNING, FAILED],
        FINAL_AUDITING: [SUCCESS_VERIFIED, REPLANNING, FAILED],
        SUCCESS_VERIFIED: [COMPLETED, IDLE],
        COMPLETED: [IDLE],
        WAITING_INPUT: [PLANNING, EXECUTING, ANALYZING_GOAL, FAILED],
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
