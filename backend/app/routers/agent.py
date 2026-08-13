from fastapi import APIRouter, HTTPException, Depends, Request
from backend.app.models.schemas import AgentRequest, AgentResponse
from backend.app.agents.base_agent import BaseAgent
from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_user
from backend.app.core.rbac import require_permission
from backend.app.core.audit import log_audit_event
from backend.app.core.security_middleware import detect_prompt_injection, filter_output
from backend.app.core.rate_limiter import limiter
from backend.app.core.sanitizer import sanitize_input

router = APIRouter(prefix="/agent", tags=["agents"])


@router.post("/run", response_model=AgentResponse)
@limiter.limit("10/minute")
async def run_agent(
    request: Request,
    payload: AgentRequest,
    current_user: dict = Depends(require_permission("agent:run")),
):
    # sanitize input
    clean_task = sanitize_input(payload.task, max_length=5000)
    clean_context = sanitize_input(payload.context or "", max_length=5000) or None

    # prompt injection defense
    is_injection, pattern = detect_prompt_injection(clean_task)
    if is_injection:
        log_audit_event(
            action="agent:run", user=current_user["username"],
            resource="agent", status="blocked",
            detail=f"Prompt injection: {pattern}",
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(
            status_code=400,
            detail="Request blocked: potential prompt injection detected.",
        )

    log_audit_event(
        action="agent:run", user=current_user["username"],
        resource=f"agent/{payload.agent_type}",
        ip_address=request.client.host if request.client else None,
    )

    try:
        agent = BaseAgent(agent_type=payload.agent_type)
        result = await agent.run(
            task=clean_task,
            context=clean_context,
            user=current_user["username"],
            session_id=payload.session_id,
        )
        safe_output = filter_output(result["output"])

    except Exception as e:
        log_audit_event(
            action="agent:run", user=current_user["username"],
            resource=f"agent/{payload.agent_type}",
            status="error", detail=str(e),
        )
        raise HTTPException(status_code=503, detail=str(e))

    return AgentResponse(
        agent_type=payload.agent_type,
        task=clean_task,
        output=safe_output,
        model_used=settings.groq_model,
        status="success",
        iterations=result["iterations"],
        state_id=result.get("state_id"),
    )