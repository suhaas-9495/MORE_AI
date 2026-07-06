from fastapi import APIRouter, HTTPException, Depends, Request
from backend.app.models.schemas import AgentRequest, AgentResponse
from backend.app.agents.base_agent import BaseAgent
from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_user
from backend.app.core.rbac import require_permission
from backend.app.core.audit import log_audit_event
from backend.app.core.security_middleware import detect_prompt_injection, filter_output
from backend.app.core.rate_limiter import limiter

router = APIRouter(prefix="/agent", tags=["agents"])


@router.post("/run", response_model=AgentResponse)
@limiter.limit("10/minute")          # max 10 agent calls per minute per IP
async def run_agent(
    request: Request,
    payload: AgentRequest,
    current_user: dict = Depends(require_permission("agent:run")),
):
    # prompt injection defense
    is_injection, pattern = detect_prompt_injection(payload.task)
    if is_injection:
        log_audit_event(
            action="agent:run", user=current_user["username"],
            resource="agent", status="blocked",
            detail=f"Prompt injection detected: {pattern}",
            ip_address=request.client.host,
        )
        raise HTTPException(
            status_code=400,
            detail="Request blocked: potential prompt injection detected.",
        )

    log_audit_event(
        action="agent:run", user=current_user["username"],
        resource=f"agent/{payload.agent_type}",
        ip_address=request.client.host,
    )

    try:
        agent = BaseAgent(agent_type=payload.agent_type)
        result = await agent.run(
            task=payload.task, context=payload.context,
            user=current_user["username"],
        )
        # PII redaction before output leaves system
        safe_output = filter_output(result["output"])

    except Exception as e:
        log_audit_event(
            action="agent:run", user=current_user["username"],
            resource=f"agent/{payload.agent_type}", status="error",
            detail=str(e),
        )
        raise HTTPException(status_code=503, detail=str(e))

    return AgentResponse(
        agent_type=payload.agent_type, task=payload.task,
        output=safe_output, model_used=settings.groq_model,
        status="success", iterations=result["iterations"],
    )