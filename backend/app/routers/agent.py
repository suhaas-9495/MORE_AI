from fastapi import APIRouter, HTTPException, Depends
from backend.app.models.schemas import AgentRequest, AgentResponse
from backend.app.agents.base_agent import BaseAgent
from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_user

router = APIRouter(prefix="/agent", tags=["agents"])


@router.post("/run", response_model=AgentResponse)
async def run_agent(
    request: AgentRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        agent = BaseAgent(agent_type=request.agent_type)
        result = await agent.run(
            task=request.task,
            context=request.context,
            user=current_user["username"],
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    return AgentResponse(
        agent_type=request.agent_type,
        task=request.task,
        output=result["output"],
        model_used=settings.groq_model,
        status="success",
        iterations=result["iterations"],
    )