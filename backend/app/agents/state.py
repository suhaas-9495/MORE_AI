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
    plan: Optional[str]            
    code: Optional[str]           
    review: Optional[str]         
    critique: Optional[str]       # reflexion: self-critique
    tests: Optional[str]
    test_results: Optional[str]   # pass/fail output
    final_output: Optional[str]
    iterations: int               # how many reflexion loops ran
    should_retry: bool            # reflexion decision
    errors: List[str]