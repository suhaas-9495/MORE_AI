import httpx
from backend.app.core.config import settings


AGENT_SYSTEM_PROMPTS = {
    "planner": """You are a senior software architect and project planner.
Given a task or requirement, break it down into clear, actionable steps.
Return a structured plan with numbered steps. Be concise and technical.""",

    "coder": """You are an expert Python backend engineer.
Given a task, write clean, production-grade code with proper error handling.
Always include docstrings and type hints.""",

    "reviewer": """You are a senior code reviewer.
Given code or a plan, identify issues, suggest improvements, and check for
security vulnerabilities, edge cases, and best practices.""",
}


class BaseAgent:
    def __init__(self, agent_type: str):
        if agent_type not in AGENT_SYSTEM_PROMPTS:
            raise ValueError(f"Unknown agent type: {agent_type}")
        self.agent_type = agent_type
        self.system_prompt = AGENT_SYSTEM_PROMPTS[agent_type]
        self.model = settings.ollama_model
        self.base_url = settings.ollama_base_url

    def run(self, task: str, context: str = None) -> str:
        """
        Send task to Ollama and return the agent's response.
        Each agent has a different system prompt = different personality/role.
        """
        user_message = task
        if context:
            user_message = f"Context:\n{context}\n\nTask:\n{task}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user",   "content": user_message},
            ],
            "stream": False,
        }

        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
            response.raise_for_status()
            return response.json()["message"]["content"]