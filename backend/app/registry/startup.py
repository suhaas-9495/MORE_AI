from backend.app.registry.tool_registry import tool_registry
from backend.app.registry.agent_registry import agent_registry, register_default_agents
from backend.app.agents.base_agent import BaseAgent


async def run_agent_tool(task: str, agent_type: str = "planner", context: str = None) -> str:
    agent = BaseAgent(agent_type=agent_type)
    result = await agent.run(task=task, context=context, user="mcp-client")
    return result["output"]


async def search_docs_tool(query: str, top_k: int = 3) -> str:
    from backend.app.rag.pipeline import retrieve_context
    return retrieve_context(query=query, top_k=top_k)


def register_all():
    tool_registry.register(
        name="run_agent",
        description="Run a MoreAI agent on a task",
        input_schema={
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "agent_type": {
                    "type": "string",
                    "enum": ["planner", "coder", "reviewer", "tester", "researcher", "documenter"],
                    "default": "planner",
                },
                "context": {"type": "string"},
            },
            "required": ["task"],
        },
        handler=run_agent_tool,
    )

    tool_registry.register(
        name="search_docs",
        description="Search MoreAI knowledge base",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 3},
            },
            "required": ["query"],
        },
        handler=search_docs_tool,
    )

    # register all agents including new ones
    agent_registry.register(
        agent_id="researcher-v1", name="Research Agent", agent_type="researcher",
        description="Researches technical topics before planning or coding",
        capabilities=["research", "technical analysis", "best practices", "spike"],
    )
    agent_registry.register(
        agent_id="documenter-v1", name="Documentation Agent", agent_type="documenter",
        description="Generates technical documentation from code",
        capabilities=["documentation", "markdown", "api docs", "technical writing"],
    )

    register_default_agents()
    print(f"[startup] Registered {len(tool_registry.list_tools())} tools, {len(agent_registry.list_agents())} agents")