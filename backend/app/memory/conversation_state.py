from typing import Dict, Optional, Any
from datetime import datetime
import uuid
import json
import os

STATE_FILE = "conversation_states.jsonl"


class ConversationState:
    """
    Tracks the full state of a multi-agent pipeline run.
    Enables Human Approval gate (Day 14) — pipeline pauses here,
    waits for human input, then resumes from this saved state.
    """

    def __init__(self, user: str, task: str):
        self.state_id = str(uuid.uuid4())
        self.user = user
        self.task = task
        self.status = "pending"      # pending / running / awaiting_approval / completed / failed
        self.created_at = datetime.utcnow().isoformat()
        self.updated_at = self.created_at
        self.agent_outputs: Dict[str, str] = {}
        self.current_agent: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def update(self, agent: str, output: str, status: str = "running"):
        self.agent_outputs[agent] = output
        self.current_agent = agent
        self.status = status
        self.updated_at = datetime.utcnow().isoformat()

    def to_dict(self) -> Dict:
        return {
            "state_id": self.state_id,
            "user": self.user,
            "task": self.task,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "agent_outputs": self.agent_outputs,
            "current_agent": self.current_agent,
            "metadata": self.metadata,
        }

    def save(self):
        with open(STATE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(self.to_dict()) + "\n")


# in-memory state store for active runs
_active_states: Dict[str, ConversationState] = {}


def create_state(user: str, task: str) -> ConversationState:
    state = ConversationState(user=user, task=task)
    _active_states[state.state_id] = state
    return state


def get_state(state_id: str) -> Optional[ConversationState]:
    return _active_states.get(state_id)


def list_user_states(user: str) -> list:
    return [
        s.to_dict() for s in _active_states.values()
        if s.user == user
    ]