from fastmcp import FastMCP
from backend.app.registry.tool_registry import tool_registry

# FastMCP wraps your tools in the MCP protocol
# Any MCP client (Claude Desktop, Cursor, etc.) can now call your agents
mcp = FastMCP(
    name="MoreAI",
    instructions="MoreAI multi-agent SDLC platform. Use run_agent to execute AI agents on tasks.",
)


@mcp.tool(
    name="run_agent",
    description="Run a MoreAI agent on a task. agent_type: planner, coder, reviewer, tester",
)
async def run_agent_mcp(task: str, agent_type: str = "planner", context: str = None) -> str:
    return await tool_registry.execute("run_agent", {
        "task": task, "agent_type": agent_type, "context": context
    })


@mcp.tool(
    name="search_docs",
    description="Search MoreAI's knowledge base for relevant documentation or context",
)
async def search_docs_mcp(query: str, top_k: int = 3) -> str:
    return await tool_registry.execute("search_docs", {"query": query, "top_k": top_k})


def get_mcp_server():
    return mcp