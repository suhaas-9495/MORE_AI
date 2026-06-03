from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import AgentRequest, AgentResponse
from backend.app.agents.base_agent import BaseAgent
from backend.app.core.config import settings

router = APIRouter(prefix="/agent", tags=["agents"])


@router.post("/run", response_model=AgentResponse)
def run_agent(request: AgentRequest):
    """
    Run any agent type against a task.
    Day 1: single agent. Day 5+: chained multi-agent pipeline.
    """
    try:
        agent = BaseAgent(agent_type=request.agent_type)
        output = agent.run(task=request.task, context=request.context)
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

    return AgentResponse(
        agent_type=request.agent_type,
        task=request.task,
        output=output,
        model_used=settings.ollama_model,
        status="success",
    )