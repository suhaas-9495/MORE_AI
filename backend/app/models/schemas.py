from pydantic import BaseModel, Field
from typing import Optional, Literal, List

class AgentRequest(BaseModel):
    task: str = Field(..., min_length=1)
    agent_type: Literal["planner", "coder", "reviewer"] = "planner"
    context: Optional[str] = None

class PlanStep(BaseModel):
    step_number: int
    action: str
    reasoning: str

class StructuredPlan(BaseModel):
    goal: str
    steps: List[PlanStep]
    estimated_complexity: Literal["low", "medium", "high"]
    requires_tools: List[str]

class AgentResponse(BaseModel):
    agent_type: str
    task: str
    output: str
    structured: Optional[dict] = None   # parsed JSON when available
    model_used: str
    status: Literal["success", "error"]
    iterations: int = 1                 # reflexion loop count

class HealthResponse(BaseModel):
    status: str
    app: str
    env: str