import uuid
import json
import os
from datetime import datetime, timezone
from typing import Optional, Dict, Literal
from enum import Enum


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalRequest:
    """
    Represents a pause point in the agent pipeline.
    Agent hits this, saves state, waits for human decision.
    Pipeline cannot proceed until status changes from PENDING.
    """

    def __init__(
        self,
        state_id: str,
        user: str,
        agent_type: str,
        action_description: str,
        payload: Dict,
    ):
        self.approval_id = str(uuid.uuid4())
        self.state_id = state_id
        self.user = user
        self.agent_type = agent_type
        self.action_description = action_description
        self.payload = payload
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.decided_at: Optional[str] = None
        self.decided_by: Optional[str] = None
        self.rejection_reason: Optional[str] = None

    def approve(self, decided_by: str):
        self.status = ApprovalStatus.APPROVED
        self.decided_at = datetime.now(timezone.utc).isoformat()
        self.decided_by = decided_by

    def reject(self, decided_by: str, reason: str = ""):
        self.status = ApprovalStatus.REJECTED
        self.decided_at = datetime.now(timezone.utc).isoformat()
        self.decided_by = decided_by
        self.rejection_reason = reason

    def to_dict(self) -> Dict:
        return {
            "approval_id": self.approval_id,
            "state_id": self.state_id,
            "user": self.user,
            "agent_type": self.agent_type,
            "action_description": self.action_description,
            "payload": self.payload,
            "status": self.status,
            "created_at": self.created_at,
            "decided_at": self.decided_at,
            "decided_by": self.decided_by,
            "rejection_reason": self.rejection_reason,
        }


# in-memory approval store — swap for Redis/DB in production
_approvals: Dict[str, ApprovalRequest] = {}
APPROVAL_LOG = "approval_log.jsonl"


def create_approval(
    state_id: str,
    user: str,
    agent_type: str,
    action_description: str,
    payload: Dict,
) -> ApprovalRequest:
    approval = ApprovalRequest(
        state_id=state_id, user=user, agent_type=agent_type,
        action_description=action_description, payload=payload,
    )
    _approvals[approval.approval_id] = approval
    _log_approval(approval)
    return approval


def get_approval(approval_id: str) -> Optional[ApprovalRequest]:
    return _approvals.get(approval_id)


def list_pending_approvals(user: str) -> list:
    return [
        a.to_dict() for a in _approvals.values()
        if a.user == user and a.status == ApprovalStatus.PENDING
    ]


def list_all_approvals(user: str) -> list:
    return [a.to_dict() for a in _approvals.values() if a.user == user]


def _log_approval(approval: ApprovalRequest):
    with open(APPROVAL_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(approval.to_dict()) + "\n")