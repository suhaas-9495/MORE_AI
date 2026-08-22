import time
from backend.app.agents.graph import build_graph
from backend.app.agents.state import AgentState
from backend.app.agents.prompts import AGENT_SYSTEM_PROMPTS
from backend.app.rag.pipeline import retrieve_context
from backend.app.memory.short_term import get_session
from backend.app.memory.long_term import store_memory, retrieve_memories
from backend.app.memory.conversation_state import create_state
from backend.app.core.observability import trace_agent_run
from backend.app.mlflow_tracking.tracker import log_agent_run


class BaseAgent:
    def __init__(self, agent_type: str):
        if agent_type not in AGENT_SYSTEM_PROMPTS:
            raise ValueError(f"Unknown agent type: {agent_type}")
        self.agent_type = agent_type
        self.graph = build_graph(agent_type)

    async def run(
        self,
        task: str,
        context: str = None,
        user: str = "anonymous",
        session_id: str = None,
    ) -> dict:
        trace = trace_agent_run(
            agent_type=self.agent_type,
            task=task,
            user=user,
            session_id=session_id,
        )

        session = get_session(session_id or user)
        short_term = session.get_context()
        long_term = retrieve_memories(user=user, query=task, top_k=3)
        rag = retrieve_context(query=task, top_k=3, user=user)

        full_context = ""
        if long_term:
            full_context += f"Relevant past experience:\n{long_term}\n\n"
        if short_term:
            full_context += f"{short_term}\n\n"
        if rag:
            full_context += f"Relevant knowledge:\n{rag}\n\n"
        if context:
            full_context += f"Additional context:\n{context}"

        conv_state = create_state(user=user, task=task)
        conv_state.update(agent=self.agent_type, output="", status="running")

        initial_state: AgentState = {
            "task": task,
            "context": full_context or None,
            "agent_type": self.agent_type,
            "research": None, "plan": None, "code": None,
            "review": None, "tests": None, "test_results": None,
            "documentation": None, "critique": None,
            "final_output": None, "iterations": 0,
            "should_retry": False, "errors": [],
            "trace": trace,
        }

        start = time.time()
        try:
            final_state = await self.graph.ainvoke(initial_state)
            latency = round(time.time() - start, 3)
            output = final_state["final_output"] or ""

            session.add(role="user", content=task, agent_type=self.agent_type)
            session.add(role="assistant", content=output[:500], agent_type=self.agent_type)
            store_memory(user=user, task=task, output=output,
                        agent_type=self.agent_type, success=True)

            conv_state.update(agent=self.agent_type, output=output, status="completed")
            conv_state.save()

            try:
                trace.update(
                    output={"output_preview": output[:300]},
                    metadata={"latency_s": latency, "iterations": final_state["iterations"]},
                )
            except Exception:
                pass

            try:
                log_agent_run(
                    agent_type=self.agent_type,
                    task=task, output=output,
                    latency_s=latency,
                    iterations=final_state["iterations"],
                    user=user,
                )
            except Exception:
                pass

            return {
                "output": output,
                "iterations": final_state["iterations"],
                "state_id": conv_state.state_id,
            }

        except Exception as e:
            conv_state.update(agent=self.agent_type, output=str(e), status="failed")
            conv_state.save()
            try:
                trace.update(output={"error": str(e)})
            except Exception:
                pass
            raise