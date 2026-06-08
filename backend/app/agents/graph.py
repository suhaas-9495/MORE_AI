from langgraph.graph import StateGraph, END
from backend.app.agents.state import AgentState
from backend.app.agents.nodes import (
    plan_node, code_node, review_node, reflexion_node, finalize_node
)


def should_retry(state: AgentState) -> str:
    """Edge condition — routes back to coder if reflexion says retry."""
    if state.get("should_retry") and state["iterations"] < 2:
        return "retry"
    return "done"


def build_graph(agent_type: str) -> StateGraph:
    """
    Builds the LangGraph for a given agent type.
    planner  → reflexion → finalize
    coder    → review → reflexion → (retry loop) → finalize
    reviewer → reflexion → finalize
    """
    graph = StateGraph(AgentState)

    if agent_type == "coder":
        graph.add_node("plan", plan_node)
        graph.add_node("code", code_node)
        graph.add_node("review", review_node)
        graph.add_node("reflexion", reflexion_node)
        graph.add_node("finalize", finalize_node)

        graph.set_entry_point("plan")
        graph.add_edge("plan", "code")
        graph.add_edge("code", "review")
        graph.add_edge("review", "reflexion")
        graph.add_conditional_edges(
            "reflexion",
            should_retry,
            {"retry": "code", "done": "finalize"},
        )
        graph.add_edge("finalize", END)

    elif agent_type == "planner":
        graph.add_node("plan", plan_node)
        graph.add_node("reflexion", reflexion_node)
        graph.add_node("finalize", finalize_node)

        graph.set_entry_point("plan")
        graph.add_edge("plan", "reflexion")
        graph.add_conditional_edges(
            "reflexion",
            should_retry,
            {"retry": "plan", "done": "finalize"},
        )
        graph.add_edge("finalize", END)

    else:  # reviewer
        graph.add_node("review", review_node)
        graph.add_node("reflexion", reflexion_node)
        graph.add_node("finalize", finalize_node)

        graph.set_entry_point("review")
        graph.add_edge("review", "reflexion")
        graph.add_conditional_edges(
            "reflexion",
            should_retry,
            {"retry": "review", "done": "finalize"},
        )
        graph.add_edge("finalize", END)

    return graph.compile()