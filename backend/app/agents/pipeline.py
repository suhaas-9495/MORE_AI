import asyncio
from typing import Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.core.approval import create_approval, get_approval, ApprovalStatus
from backend.app.memory.conversation_state import create_state
from backend.app.core.audit import log_audit_event

APPROVAL_GATES = {"after_review": True}
GATE_TIMEOUT_SECONDS = 300


async def wait_for_approval(approval_id: str) -> bool:
    elapsed = 0
    while elapsed < GATE_TIMEOUT_SECONDS:
        approval = get_approval(approval_id)
        if not approval:
            return False
        if approval.status == ApprovalStatus.APPROVED:
            return True
        if approval.status == ApprovalStatus.REJECTED:
            return False
        await asyncio.sleep(2)
        elapsed += 2
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
    Full 7-agent SDLC pipeline:
    Research → Plan → Code → Test → Review → [HUMAN GATE] → Document → Deploy
    """
    conv_state = create_state(user=user, task=task)
    results = {}
    sid = session_id or user

    log_audit_event(action="pipeline:start", user=user,
                    resource=f"pipeline/{conv_state.state_id}", detail=task[:100])

    # Stage 1: Research
    print("[Pipeline] Stage 1/7: Researching...")
    researcher = BaseAgent(agent_type="researcher")
    r = await researcher.run(task=task, user=user, session_id=sid)
    results["research"] = r["output"]

    # Stage 2: Plan
    print("[Pipeline] Stage 2/7: Planning...")
    planner = BaseAgent(agent_type="planner")
    r = await planner.run(task=task, context=results["research"], user=user, session_id=sid)
    results["plan"] = r["output"]

    # Stage 3: Code
    print("[Pipeline] Stage 3/7: Coding...")
    coder = BaseAgent(agent_type="coder")
    r = await coder.run(
        task=task,
        context=f"Research:\n{results['research']}\n\nPlan:\n{results['plan']}",
        user=user, session_id=sid,
    )
    results["code"] = r["output"]

    # Stage 4: Test
    print("[Pipeline] Stage 4/7: Testing...")
    tester = BaseAgent(agent_type="tester")
    r = await tester.run(task=f"Write tests for:\n{results['code']}", user=user, session_id=sid)
    results["tests"] = r["output"]

    # Stage 5: Review
    print("[Pipeline] Stage 5/7: Reviewing...")
    reviewer = BaseAgent(agent_type="reviewer")
    r = await reviewer.run(task=f"Review:\n{results['code']}", user=user, session_id=sid)
    results["review"] = r["output"]

    # Human Approval Gate
    if require_approval and APPROVAL_GATES.get("after_review"):
        print("[Pipeline] Awaiting human approval...")
        approval = create_approval(
            state_id=conv_state.state_id, user=user, agent_type="deployment",
            action_description=f"Approve deployment for: {task[:100]}",
            payload={
                "task": task,
                "code_preview": results["code"][:500],
                "review_summary": results["review"][:300],
            },
        )
        conv_state.update(agent="approval_gate",
                          output=f"Awaiting: {approval.approval_id}",
                          status="awaiting_approval")

        approved = await wait_for_approval(approval.approval_id)
        if not approved:
            results["status"] = "rejected"
            results["approval_id"] = approval.approval_id
            return results

    # Stage 6: Document
    print("[Pipeline] Stage 6/7: Documenting...")
    documenter = BaseAgent(agent_type="documenter")
    r = await documenter.run(
        task=f"Document this code:\n{results['code']}",
        user=user, session_id=sid,
    )
    results["documentation"] = r["output"]

    # Stage 7: Deploy (stub — real AWS deployment on Day 17)
    print("[Pipeline] Stage 7/7: Deploying...")
    results["deployment"] = "Artifacts saved. Deployment triggered."
    conv_state.update(agent="deployer", output=results["deployment"], status="completed")
    conv_state.save()

    log_audit_event(action="pipeline:completed", user=user,
                    resource=f"pipeline/{conv_state.state_id}")

    results["status"] = "completed"
    results["state_id"] = conv_state.state_id
    return results