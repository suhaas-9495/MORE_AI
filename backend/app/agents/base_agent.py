import time
from backend.app.agents.graph import build_graph
from backend.app.agents.state import AgentState
from backend.app.agents.prompts import AGENT_SYSTEM_PROMPTS
from backend.app.rag.pipeline import retrieve_context
from backend.app.memory.short_term import get_session
from backend.app.memory.long_term import store_memory, retrieve_memories
from backend.app.memory.conversation_state import create_state
from backend.app.core.observability import get_langfuse_client, trace_observe


class BaseAgent:
    def __init__(self, agent_type: str):
        if agent_type not in AGENT_SYSTEM_PROMPTS:
            raise ValueError(f"Unknown agent type: {agent_type}")
        self.agent_type = agent_type
        self.graph = build_graph(agent_type)
        self.langfuse = get_langfuse_client()

    @trace_observe(name="agent_run")
    async def run(
        self,
        task: str,
        context: str = None,
        user: str = "anonymous",
        session_id: str = None,
    ) -> dict:
        self.langfuse.update_current_trace(
            user_id=user,
            tags=[self.agent_type],
            metadata={"agent_type": self.agent_type},
        )

        # short-term memory — what happened earlier in this session
        session = get_session(session_id or user)
        short_term_context = session.get_context()

        # long-term memory — relevant past experiences for this task
        long_term_context = retrieve_memories(user=user, query=task, top_k=3)

        # RAG — relevant documents from knowledge base
        rag_context = retrieve_context(query=task, top_k=3, user=user)

        # build full context — memory + RAG combined
        full_context = ""
        if long_term_context:
            full_context += f"Relevant past experience:\n{long_term_context}\n\n"
        if short_term_context:
            full_context += f"{short_term_context}\n\n"
        if rag_context:
            full_context += f"Relevant knowledge:\n{rag_context}\n\n"
        if context:
            full_context += f"Additional context:\n{context}"

        # conversation state tracking
        conv_state = create_state(user=user, task=task)
        conv_state.update(agent=self.agent_type, output="", status="running")

        initial_state: AgentState = {
            "task": task,
            "context": full_context or None,
            "agent_type": self.agent_type,
            "plan": None, "code": None, "review": None,
            "tests": None, "test_results": None,
            "critique": None, "final_output": None,
            "iterations": 0, "should_retry": False, "errors": [],
        }

        start = time.time()
        try:
            final_state = await self.graph.ainvoke(initial_state)
            latency = round(time.time() - start, 3)
            output = final_state["final_output"] or ""

            # update short-term memory with this interaction
            session.add(role="user", content=task, agent_type=self.agent_type)
            session.add(role="assistant", content=output[:500], agent_type=self.agent_type)

            # store in long-term memory for future sessions
            store_memory(
                user=user, task=task, output=output,
                agent_type=self.agent_type, success=True,
            )

            conv_state.update(
                agent=self.agent_type, output=output, status="completed"
            )
            conv_state.save()

            self.langfuse.update_current_trace(
                metadata={"latency_s": latency, "iterations": final_state["iterations"]},
            )

            return {
                "output": output,
                "iterations": final_state["iterations"],
                "state_id": conv_state.state_id,
            }

        except Exception as e:
            conv_state.update(agent=self.agent_type, output=str(e), status="failed")
            conv_state.save()
            raise