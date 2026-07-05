from typing import Dict, Optional, List
from pydantic import BaseModel
from datetime import datetime


class AgentDefinition(BaseModel):
    agent_id: str
    name: str
    agent_type: str
    description: str
    capabilities: List[str]
    version: str = "1.0.0"
    registered_at: str = ""
    active: bool = True


class AgentRegistry:
    """
    Registry of all available agent types.
    Lets you query: what agents exist? what can each one do?
    Deployment Agent and Planner Agent will query this to build pipelines dynamically.
    """

    def __init__(self):
        self._agents: Dict[str, AgentDefinition] = {}

    def register(
        self, agent_id: str, name: str, agent_type: str,
        description: str, capabilities: List[str], version: str = "1.0.0"
    ):
        self._agents[agent_id] = AgentDefinition(
            agent_id=agent_id, name=name, agent_type=agent_type,
            description=description, capabilities=capabilities,
            version=version, registered_at=datetime.utcnow().isoformat(),
        )

    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        return self._agents.get(agent_id)

    def list_agents(self) -> List[AgentDefinition]:
        return [a for a in self._agents.values() if a.active]

    def find_by_capability(self, capability: str) -> List[AgentDefinition]:
        """Planner uses this to dynamically pick the right agent for a subtask."""
        return [
            a for a in self._agents.values()
            if a.active and any(capability.lower() in c.lower() for c in a.capabilities)
        ]


# singleton
agent_registry = AgentRegistry()


def register_default_agents():
    """Register all built-in agents on startup."""
    agent_registry.register(
        agent_id="planner-v1", name="Planner Agent", agent_type="planner",
        description="Breaks down tasks into structured execution plans",
        capabilities=["planning", "task decomposition", "step generation"],
    )
    agent_registry.register(
        agent_id="coder-v1", name="Coder Agent", agent_type="coder",
        description="Writes production-grade Python code with tests",
        capabilities=["code generation", "python", "fastapi", "testing"],
    )
    agent_registry.register(
        agent_id="reviewer-v1", name="Reviewer Agent", agent_type="reviewer",
        description="Reviews code for bugs, security, and best practices",
        capabilities=["code review", "security", "bug detection"],
    )
    agent_registry.register(
        agent_id="tester-v1", name="Tester Agent", agent_type="tester",
        description="Generates and executes pytest unit tests",
        capabilities=["test generation", "pytest", "qa", "validation"],
    )