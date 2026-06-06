import time
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.core.config import settings
from backend.app.core.observability import get_langfuse

AGENT_SYSTEM_PROMPTS = {
    "planner": """You are a senior software architect and project planner.
Given a task, break it down into clear, actionable numbered steps. Be concise and technical.""",

    "coder": """You are an expert Python backend engineer.
Write clean, production-grade code with type hints, docstrings, and error handling.""",

    "reviewer": """You are a senior code reviewer.
Identify bugs, security issues, edge cases, and suggest concrete improvements.""",
}


class BaseAgent:
    def __init__(self, agent_type: str):
        if agent_type not in AGENT_SYSTEM_PROMPTS:
            raise ValueError(f"Unknown agent type: {agent_type}")

        self.agent_type = agent_type
        self.system_prompt = AGENT_SYSTEM_PROMPTS[agent_type]

        # Groq — fastest inference available, drop-in LangChain compatible
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.7,
        )
        self.langfuse = get_langfuse()

    async def run(self, task: str, context: str = None) -> str:
        """
        Async agent run with Groq + full Langfuse tracing.
        Every call is visible in dashboard: inputs, output, latency, model.
        """
        user_message = f"Context:\n{context}\n\nTask:\n{task}" if context else task

        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=user_message),
        ]

        # Langfuse trace — one trace per agent run
        trace = self.langfuse.trace(
            name=f"agent-{self.agent_type}",
            input={"task": task, "context": context},
            tags=[self.agent_type, settings.env],
        )
        span = trace.span(
            name="groq-llm-call",
            input={"model": settings.groq_model, "messages": str(messages)},
        )

        start = time.time()
        try:
            response = await self.llm.ainvoke(messages)
            output = response.content
            latency = round(time.time() - start, 3)

            span.end(output={"response": output, "latency_s": latency})
            trace.update(
                output={"response": output},
                metadata={"latency_s": latency, "model": settings.groq_model},
            )
            return output

        except Exception as e:
            span.end(output={"error": str(e)}, level="ERROR")
            trace.update(output={"error": str(e)})
            raise