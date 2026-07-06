import json
import os
from datetime import datetime, timezone
from typing import Optional
from fastapi import Request

AUDIT_LOG_FILE = "audit_log.jsonl"


def log_audit_event(
    action: str,
    user: str,
    resource: str,
    status: str = "success",
    detail: Optional[str] = None,
    ip_address: Optional[str] = None,
):
    """
    Append-only audit log — every sensitive action recorded.
    Who did what, when, from where, and did it succeed.
    This is what compliance + security interviews ask about.
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": user,
        "action": action,
        "resource": resource,
        "status": status,
        "detail": detail,
        "ip_address": ip_address,
    }
    with open(AUDIT_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def get_audit_logs(limit: int = 100) -> list:
    if not os.path.exists(AUDIT_LOG_FILE):
        return []
    logs = []
    with open(AUDIT_LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except Exception:
                continue
    return logs[-limit:]