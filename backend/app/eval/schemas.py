from pydantic import BaseModel, Field
from typing import Optional, Literal, List
from datetime import datetime


class EvalCriteria(BaseModel):
    """What counts as a passing output for a given task."""
    task: str
    expected_keywords: List[str] = Field(default_factory=list)
    expected_behavior: str = Field(..., description="Plain description of what a good output looks like")
    agent_type: Literal["planner", "coder", "reviewer", "tester"] = "coder"


class EvalResult(BaseModel):
    task: str
    agent_type: str
    output: str
    passed: bool  # rule-based pass/fail
    judge_score: Optional[float] = None   # 0.0-1.0 from LLM judge
    judge_reasoning: Optional[str] = None
    cost_usd: Optional[float] = None  # estimated cost for this run
    tokens_in: int = 0
    tokens_out: int = 0
    latency_s: float = 0.0
    iterations: int = 1
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class JudgeVerdict(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    correctness: float
    relevance: float
    safety: float
    reasoning: str
    passed: bool