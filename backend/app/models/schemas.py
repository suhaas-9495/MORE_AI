from pydantic import BaseModel, Field
from typing import Optional, Literal, List


class AgentRequest(BaseModel):
    task: str = Field(..., min_length=1)
    agent_type: Literal[
        "planner", "coder", "reviewer", "tester", "researcher", "documenter"
    ] = "planner"
    context: Optional[str] = None
    session_id: Optional[str] = None


class AgentResponse(BaseModel):
    agent_type: str
    task: str
    output: str
    structured: Optional[dict] = None
    model_used: str
    status: Literal["success", "error"]
    iterations: int = 1
    state_id: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    app: str
    env: str


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=72)


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    username: str
    is_active: bool = True