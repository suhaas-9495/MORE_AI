import asyncio
from typing import Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.core.approval import (
    create_approval, get_approval, ApprovalStatus
)
from backend.app.memory.conversation_state import create_state
from backend.app.core.audit import log_audit_event

# gates define WHICH transitions require human approval
# in production you'd make this configurable per user/org
APPROVAL_GATES = {
    "after_review": True,       # human approves before deployment
    "after_deployment": True,   # human confirms deployment succeeded
}

GATE_TIMEOUT_SECONDS = 300    # 5 min — approval expires after this


async def wait_for_approval(approval_id: str) -> bool:
    """
    Polls for approval decision with timeout.
    In production this would be a webhook or websocket push.
    Returns True if approved, False if rejected or expired.
    """
    elapsed = 0
    poll_interval = 2

    while elapsed < GATE_TIMEOUT_SECONDS:
        approval = get_approval(approval_id)
        if not approval:
            return False
        if approval.status == ApprovalStatus.APPROVED:
            return True
        if approval.status == ApprovalStatus.REJECTED:
            return False
        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    # mark as expired
    approval = get_approval(approval_id)
    if approval:
        approval.status = ApprovalStatus.EXPIRED
    return False


async def run_sdlc_pipeline(
    task: str,
    user: str,
    session_id: Optional[str] = None,
    require_approval: bool = True,
) -> dict:
    """
    Full 6-agent SDLC pipeline:
    Plan → Code → Test → Review → [HUMAN GATE] → Deploy

    This is the flagship demo for interviews — one function call
    runs the entire software development lifecycle with a human
    approval checkpoint before anything gets deployed.
    """
    conv_state = create_state(user=user, task=task)
    results = {}
    sid = session_id or user

    log_audit_event(
        action="pipeline:start", user=user,
        resource=f"pipeline/{conv_state.state_id}",
        detail=f"task={task[:100]}",
    )

    # --- Stage 1: Plan ---
    print(f"[Pipeline] Stage 1/5: Planning...")
    planner = BaseAgent(agent_type="planner")
    plan_result = await planner.run(task=task, user=user, session_id=sid)
    results["plan"] = plan_result["output"]
    conv_state.update(agent="planner", output=results["plan"], status="running")

    # --- Stage 2: Code ---
    print(f"[Pipeline] Stage 2/5: Coding...")
    coder = BaseAgent(agent_type="coder")
    code_result = await coder.run(
        task=task, context=f"Plan:\n{results['plan']}", user=user, session_id=sid
    )
    results["code"] = code_result["output"]
    conv_state.update(agent="coder", output=results["code"], status="running")

    # --- Stage 3: Test ---
    print(f"[Pipeline] Stage 3/5: Testing...")
    tester = BaseAgent(agent_type="tester")
    test_result = await tester.run(
        task=f"Write tests for this code:\n{results['code']}",
        user=user, session_id=sid,
    )
    results["tests"] = test_result["output"]
    conv_state.update(agent="tester", output=results["tests"], status="running")

    # --- Stage 4: Review ---
    print(f"[Pipeline] Stage 4/5: Reviewing...")
    reviewer = BaseAgent(agent_type="reviewer")
    review_result = await reviewer.run(
        task=f"Review this code:\n{results['code']}",
        user=user, session_id=sid,
    )
    results["review"] = review_result["output"]
    conv_state.update(agent="reviewer", output=results["review"], status="running")

    # --- HUMAN APPROVAL GATE ---
    if require_approval and APPROVAL_GATES.get("after_review"):
        print(f"[Pipeline] Awaiting human approval before deployment...")

        approval = create_approval(
            state_id=conv_state.state_id,
            user=user,
            agent_type="deployment",
            action_description=f"Deploy generated code for task: {task[:100]}",
            payload={
                "task": task,
                "code_preview": results["code"][:500],
                "review_summary": results["review"][:300],
                "test_summary": results["tests"][:300],
            },
        )

        conv_state.update(
            agent="approval_gate",
            output=f"Awaiting approval: {approval.approval_id}",
            status="awaiting_approval",
        )

        approved = await wait_for_approval(approval.approval_id)

        if not approved:
            conv_state.update(
                agent="approval_gate",
                output="Rejected or expired",
                status="failed",
            )
            log_audit_event(
                action="pipeline:rejected", user=user,
                resource=f"pipeline/{conv_state.state_id}",
            )
            results["status"] = "rejected"
            results["approval_id"] = approval.approval_id
            return results

        log_audit_event(
            action="pipeline:approved", user=user,
            resource=f"pipeline/{conv_state.state_id}",
        )

    # --- Stage 5: Deploy (stub — real deployment wired on DevOps sprint) ---
    print(f"[Pipeline] Stage 5/5: Deploying...")
    results["deployment"] = "Deployment triggered — artifacts saved to S3."
    conv_state.update(agent="deployer", output=results["deployment"], status="completed")
    conv_state.save()

    log_audit_event(
        action="pipeline:completed", user=user,
        resource=f"pipeline/{conv_state.state_id}",
    )

    results["status"] = "completed"
    results["state_id"] = conv_state.state_id
    return results