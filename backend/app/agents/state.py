from typing import TypedDict, Optional, List, Any


class AgentState(TypedDict):
    task: str
    context: Optional[str]
    agent_type: str
    research: Optional[str]
    plan: Optional[str]
    code: Optional[str]
    review: Optional[str]
    tests: Optional[str]
    test_results: Optional[str]
    documentation: Optional[str]
    critique: Optional[str]
    final_output: Optional[str]
    iterations: int
    should_retry: bool
    errors: List[str]
    trace: Optional[Any] 