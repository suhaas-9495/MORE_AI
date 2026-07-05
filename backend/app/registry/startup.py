from backend.app.registry.tool_registry import tool_registry
from backend.app.registry.agent_registry import agent_registry, register_default_agents
from backend.app.agents.base_agent import BaseAgent


async def run_agent_tool(task: str, agent_type: str = "planner", context: str = None) -> str:
    """Tool handler — what MCP clients actually call."""
    agent = BaseAgent(agent_type=agent_type)
    result = await agent.run(task=task, context=context, user="mcp-client")
    return result["output"]


async def search_docs_tool(query: str, top_k: int = 3) -> str:
    """Tool handler for RAG retrieval."""
    from backend.app.rag.pipeline import retrieve_context
    return retrieve_context(query=query, top_k=top_k)


def register_all():
    """Called on FastAPI startup — wires up everything."""

    # register tools
    tool_registry.register(
        name="run_agent",
        description="Run a MoreAI agent (planner/coder/reviewer/tester) on a task",
        input_schema={
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "The task to perform"},
                "agent_type": {
                    "type": "string",
                    "enum": ["planner", "coder", "reviewer", "tester"],
                    "default": "planner",
                },
                "context": {"type": "string", "description": "Optional extra context"},
            },
            "required": ["task"],
        },
        handler=run_agent_tool,
    )

    tool_registry.register(
        name="search_docs",
        description="Search MoreAI's knowledge base for relevant context",
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

    # register agents
    register_default_agents()

    print(f"[startup] Registered {len(tool_registry.list_tools())} tools, {len(agent_registry.list_agents())} agents")