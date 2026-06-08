from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    """
    LangGraph passes this dict between nodes.
    Every node reads from it and writes back to it.
    This is how agents share memory within a run.
    """
    task: str
    context: Optional[str]
    agent_type: str
    plan: Optional[str]           # planner output
    code: Optional[str]           # coder output
    review: Optional[str]         # reviewer output
    critique: Optional[str]       # reflexion: self-critique
    final_output: Optional[str]
    iterations: int               # how many reflexion loops ran
    should_retry: bool            # reflexion decision
    errors: List[str]