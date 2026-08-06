import time
from opentelemetry import trace
from backend.app.agents.graph import build_graph
from backend.app.agents.state import AgentState
from backend.app.agents.prompts import AGENT_SYSTEM_PROMPTS
from backend.app.rag.pipeline import retrieve_context
from backend.app.memory.short_term import get_session
from backend.app.memory.long_term import store_memory, retrieve_memories
from backend.app.memory.conversation_state import create_state
from backend.app.core.observability import get_langfuse_client, trace_observe
from backend.app.mlflow_tracking.tracker import log_agent_run


class BaseAgent:
    def __init__(self, agent_type: str):
        if agent_type not in AGENT_SYSTEM_PROMPTS:
            raise ValueError(f"Unknown agent type: {agent_type}")
        self.agent_type = agent_type
        self.graph = build_graph(agent_type)
        self.langfuse = get_langfuse_client()
        self.tracer = trace.get_tracer("moreai.agents")

    @trace_observe(name="agent_run")
    async def run(
        self,
        task: str,
        context: str = None,
        user: str = "anonymous",
        session_id: str = None,
    ) -> dict:
        # OpenTelemetry span — wraps the entire agent run
        with self.tracer.start_as_current_span(
            f"agent.{self.agent_type}.run",
            attributes={
                "agent.type": self.agent_type,
                "agent.user": user,
                "agent.task_length": len(task),
            }
        ) as span:
            self.langfuse.update_current_trace(
                user_id=user,
                tags=[self.agent_type],
                metadata={"agent_type": self.agent_type},
            )

            # memory retrieval span
            with self.tracer.start_as_current_span("agent.memory.retrieve"):
                session = get_session(session_id or user)
                short_term_context = session.get_context()
                long_term_context = retrieve_memories(user=user, query=task, top_k=3)
                rag_context = retrieve_context(query=task, top_k=3, user=user)

            full_context = ""
            if long_term_context:
                full_context += f"Relevant past experience:\n{long_term_context}\n\n"
            if short_term_context:
                full_context += f"{short_term_context}\n\n"
            if rag_context:
                full_context += f"Relevant knowledge:\n{rag_context}\n\n"
            if context:
                full_context += f"Additional context:\n{context}"

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
                # LangGraph execution span
                with self.tracer.start_as_current_span("agent.graph.invoke"):
                    final_state = await self.graph.ainvoke(initial_state)

                latency = round(time.time() - start, 3)
                output = final_state["final_output"] or ""

                # update spans with results
                span.set_attribute("agent.latency_s", latency)
                span.set_attribute("agent.iterations", final_state["iterations"])
                span.set_attribute("agent.output_length", len(output))

                # memory update span
                with self.tracer.start_as_current_span("agent.memory.store"):
                    session.add(role="user", content=task, agent_type=self.agent_type)
                    session.add(role="assistant", content=output[:500], agent_type=self.agent_type)
                    store_memory(user=user, task=task, output=output,
                                agent_type=self.agent_type, success=True)

                conv_state.update(agent=self.agent_type, output=output, status="completed")
                conv_state.save()

                self.langfuse.update_current_trace(
                    metadata={"latency_s": latency, "iterations": final_state["iterations"]},
                )

                # MLflow logging — async fire-and-forget style
                try:
                    log_agent_run(
                        agent_type=self.agent_type,
                        task=task,
                        output=output,
                        latency_s=latency,
                        iterations=final_state["iterations"],
                        user=user,
                    )
                except Exception:
                    pass  # never block on MLflow failures

                return {
                    "output": output,
                    "iterations": final_state["iterations"],
                    "state_id": conv_state.state_id,
                }

            except Exception as e:
                span.record_exception(e)
                span.set_status(trace.status.StatusCode.ERROR, str(e))
                conv_state.update(agent=self.agent_type, output=str(e), status="failed")
                conv_state.save()
                raise