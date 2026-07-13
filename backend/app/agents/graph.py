from langgraph.graph import StateGraph, END
from backend.app.agents.state import AgentState
from backend.app.agents.nodes import (
    research_node, plan_node, code_node, review_node,
    test_node, documentation_node, reflexion_node, finalize_node,
)


def should_retry(state: AgentState) -> str:
    if state.get("should_retry") and state["iterations"] < 2:
        return "retry"
    return "done"


def build_graph(agent_type: str) -> StateGraph:
    graph = StateGraph(AgentState)

    if agent_type == "coder":
        # full pipeline: research → plan → code → test → review → docs → reflexion → finalize
        graph.add_node("research", research_node)
        graph.add_node("plan", plan_node)
        graph.add_node("code", code_node)
        graph.add_node("test", test_node)
        graph.add_node("review", review_node)
        graph.add_node("document", documentation_node)
        graph.add_node("reflexion", reflexion_node)
        graph.add_node("finalize", finalize_node)

        graph.set_entry_point("research")
        graph.add_edge("research", "plan")
        graph.add_edge("plan", "code")
        graph.add_edge("code", "test")
        graph.add_edge("test", "review")
        graph.add_edge("review", "document")
        graph.add_edge("document", "reflexion")
        graph.add_conditional_edges(
            "reflexion", should_retry, {"retry": "code", "done": "finalize"}
        )
        graph.add_edge("finalize", END)

    elif agent_type == "planner":
        graph.add_node("research", research_node)
        graph.add_node("plan", plan_node)
        graph.add_node("reflexion", reflexion_node)
        graph.add_node("finalize", finalize_node)

        graph.set_entry_point("research")
        graph.add_edge("research", "plan")
        graph.add_edge("plan", "reflexion")
        graph.add_conditional_edges(
            "reflexion", should_retry, {"retry": "plan", "done": "finalize"}
        )
        graph.add_edge("finalize", END)

    elif agent_type == "researcher":
        graph.add_node("research", research_node)
        graph.add_node("finalize", finalize_node)
        graph.set_entry_point("research")
        graph.add_edge("research", "finalize")
        graph.add_edge("finalize", END)

    elif agent_type == "documenter":
        graph.add_node("document", documentation_node)
        graph.add_node("finalize", finalize_node)
        graph.set_entry_point("document")
        graph.add_edge("document", "finalize")
        graph.add_edge("finalize", END)

    else:  # reviewer, tester
        graph.add_node("review", review_node)
        graph.add_node("reflexion", reflexion_node)
        graph.add_node("finalize", finalize_node)
        graph.set_entry_point("review")
        graph.add_edge("review", "reflexion")
        graph.add_conditional_edges(
            "reflexion", should_retry, {"retry": "review", "done": "finalize"}
        )
        graph.add_edge("finalize", END)

    return graph.compile()