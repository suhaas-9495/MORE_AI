import time
from backend.app.agents.graph import build_graph
from backend.app.agents.state import AgentState
from backend.app.agents.prompts import AGENT_SYSTEM_PROMPTS
from backend.app.rag.pipeline import retrieve_context
from backend.app.core.observability import get_langfuse_client, trace_observe


class BaseAgent:
    def __init__(self, agent_type: str):
        if agent_type not in AGENT_SYSTEM_PROMPTS:
            raise ValueError(f"Unknown agent type: {agent_type}")
        self.agent_type = agent_type
        self.graph = build_graph(agent_type)
        self.langfuse = get_langfuse_client()

    @trace_observe(name="agent_run")
    async def run(self, task: str, context: str = None, user: str = "anonymous") -> dict:
        # tag this trace with the user — lets you filter by user in dashboard
        self.langfuse.update_current_trace(
            user_id=user,
            tags=[self.agent_type],
            metadata={"agent_type": self.agent_type},
        )

        rag_context = retrieve_context(query=task, top_k=3, user=user)

        full_context = ""
        if rag_context:
            full_context += f"Relevant knowledge:\n{rag_context}\n\n"
        if context:
            full_context += f"Additional context:\n{context}"

        initial_state: AgentState = {
            "task": task, "context": full_context or None, "agent_type": self.agent_type,
            "plan": None, "code": None, "review": None, "critique": None,
            "final_output": None, "iterations": 0, "should_retry": False, "errors": [],
        }

        start = time.time()
        final_state = await self.graph.ainvoke(initial_state)
        latency = round(time.time() - start, 3)

        # custom metric — visible in Langfuse dashboard
        self.langfuse.update_current_trace(
            metadata={"latency_s": latency, "iterations": final_state["iterations"]},
        )

        return {
            "output": final_state["final_output"],
            "iterations": final_state["iterations"],
        }