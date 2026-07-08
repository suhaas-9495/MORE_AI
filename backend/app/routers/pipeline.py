from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.agents.pipeline import run_sdlc_pipeline
from backend.app.core.approval import (
    create_approval, get_approval, list_pending_approvals,
    list_all_approvals, ApprovalStatus
)
from backend.app.core.dependencies import get_current_user
from backend.app.core.rbac import require_permission

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

# active pipeline runs — keyed by state_id
_running_pipelines = {}


class PipelineRequest(BaseModel):
    task: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    require_approval: bool = Field(default=True)


class ApprovalDecision(BaseModel):
    approved: bool
    reason: Optional[str] = None


@router.post("/run")
async def run_pipeline(
    payload: PipelineRequest,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(require_permission("agent:run")),
):
    """
    Kicks off the full SDLC pipeline in the background.
    Returns immediately with a state_id to track progress.
    Client polls /pipeline/status/{state_id} or /pipeline/approvals
    to check what's happening and approve/reject gates.
    """
    import asyncio

    async def _run():
        try:
            await run_sdlc_pipeline(
                task=payload.task,
                user=current_user["username"],
                session_id=payload.session_id,
                require_approval=payload.require_approval,
            )
        except Exception as e:
            print(f"[Pipeline error] {e}")

    background_tasks.add_task(asyncio.ensure_future, _run())

    return {
        "status": "started",
        "message": "Pipeline running in background. Check /pipeline/approvals for gates.",
        "task": payload.task,
    }


@router.get("/approvals")
async def get_pending_approvals(
    current_user: dict = Depends(get_current_user),
):
    """Returns all pending approval gates waiting for human decision."""
    return list_pending_approvals(user=current_user["username"])


@router.get("/approvals/all")
async def get_all_approvals(current_user: dict = Depends(get_current_user)):
    return list_all_approvals(user=current_user["username"])


@router.post("/approvals/{approval_id}/decide")
async def decide_approval(
    approval_id: str,
    decision: ApprovalDecision,
    current_user: dict = Depends(get_current_user),
):
    """
    Human makes the call — approve or reject the pending gate.
    Pipeline is polling for this decision and will resume immediately.
    """
    approval = get_approval(approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
    if approval.user != current_user["username"]:
        raise HTTPException(status_code=403, detail="Not your approval")
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail=f"Already decided: {approval.status}")

    if decision.approved:
        approval.approve(decided_by=current_user["username"])
    else:
        approval.reject(
            decided_by=current_user["username"],
            reason=decision.reason or "",
        )

    return {
        "approval_id": approval_id,
        "status": approval.status,
        "decided_by": current_user["username"],
    }