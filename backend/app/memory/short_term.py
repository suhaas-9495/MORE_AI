from typing import List, Optional, Dict
from datetime import datetime
from collections import deque

class ShortTermMemory:
    """stores conversation turns within a single session and capped at a max_turns to prevent the context overflow
    its a agent memory right.
    """
    
    def __init__(self,session_id: str, max_turns: int = 10):
        self.session_id = session_id
        self.max_turns = max_turns
        self._turns: deque = deque(maxlen=max_turns)  # store conversation turns as a deque with a maximum length
        
    def add (self,role: str, content: str,agent_type: str = "unknown"):
        self._turns.append({
            "role": role,
            "content": content,
            "agent_type": agent_type,
            "timestamp": datetime.now()
        })
    def get_context(self) -> str:
        """Formats recent turns as context string for agent prompt injection."""
        if not self._turns:
            return ""
        lines = []
        for turn in self._turns:
            lines.append(f"[{turn['agent_type']}] {turn['role']}: {turn['content'][:300]}")
        return "Recent conversation:\n" + "\n".join(lines)

    def clear(self):
        self._turns.clear()

    def to_list(self) -> List[Dict]:
        return list(self._turns)


# in-memory session store — swap for Redis in production
_sessions: Dict[str, ShortTermMemory] = {}


def get_session(session_id: str, max_turns: int = 10) -> ShortTermMemory:
    if session_id not in _sessions:
        _sessions[session_id] = ShortTermMemory(session_id, max_turns)
    return _sessions[session_id]


def clear_session(session_id: str):
    if session_id in _sessions:
        del _sessions[session_id]
