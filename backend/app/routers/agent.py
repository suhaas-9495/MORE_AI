from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import AgentRequest, AgentResponse
from backend.app.agents.base_agent import BaseAgent
from backend.app.core.config import settings

router = APIRouter(prefix="/agent", tags=["agents"])


@router.post("/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    try:
        agent = BaseAgent(agent_type=request.agent_type)
        output = await agent.run(task=request.task, context=request.context)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    return AgentResponse(
        agent_type=request.agent_type,
        task=request.task,
        output=output,
        model_used=settings.groq_model,
        status="success",
    )