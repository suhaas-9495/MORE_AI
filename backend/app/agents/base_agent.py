import time
from backend.app.agents.graph import build_graph
from backend.app.agents.state import AgentState
from backend.app.agents.prompts import AGENT_SYSTEM_PROMPTS
from backend.app.core.config import settings


class BaseAgent:
    def __init__(self, agent_type: str):
        if agent_type not in AGENT_SYSTEM_PROMPTS:
            raise ValueError(f"Unknown agent type: {agent_type}")
        self.agent_type = agent_type
        self.graph = build_graph(agent_type)

    async def run(self, task: str, context: str = None, user: str = "anonymous") -> dict:
        initial_state: AgentState = {
            "task": task,
            "context": context,
            "agent_type": self.agent_type,
            "plan": None,
            "code": None,
            "review": None,
            "critique": None,
            "final_output": None,
            "iterations": 0,
            "should_retry": False,
            "errors": [],
        }

        start = time.time()
        final_state = await self.graph.ainvoke(initial_state)
        latency = round(time.time() - start, 3)
        print(f"[{self.agent_type}] user={user} latency={latency}s iterations={final_state['iterations']}")

        return {
            "output": final_state["final_output"],
            "iterations": final_state["iterations"],
        }