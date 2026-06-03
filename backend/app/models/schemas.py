from pydantic import BaseModel, Field
from typing import Optional, Literal

class AgentRequest(BaseModel):
    task: str = Field(..., min_length=1, description="Task to send to the agent")
    agent_type: Literal["planner", "coder", "reviewer"] = Field(
        default="planner",
        description="Which agent handles this task"
    )
    context: Optional[str] = Field(None, description="Optional extra context")

class AgentResponse(BaseModel):
    agent_type: str
    task: str
    output: str
    model_used: str
    status: Literal["success", "error"]

class HealthResponse(BaseModel):
    status: str
    app: str
    env: str