from fastapi import APIRouter, HTTPException, Depends
from backend.app.registry.tool_registry import tool_registry
from backend.app.registry.agent_registry import agent_registry
from backend.app.core.dependencies import get_current_user

router = APIRouter(prefix="/registry", tags=["registry"])


@router.get("/tools")
async def list_tools(current_user: dict = Depends(get_current_user)):
    """Returns all registered tools — what MCP clients can call."""
    return tool_registry.list_tools()


@router.get("/agents")
async def list_agents(current_user: dict = Depends(get_current_user)):
    """Returns all registered agent types and their capabilities."""
    return agent_registry.list_agents()


@router.get("/agents/search")
async def find_agents(
    capability: str,
    current_user: dict = Depends(get_current_user),
):
    """Find agents by capability — used by Planner for dynamic routing."""
    return agent_registry.find_by_capability(capability)


@router.post("/tools/{tool_name}/execute")
async def execute_tool(
    tool_name: str,
    inputs: dict,
    current_user: dict = Depends(get_current_user),
):
    """Execute any registered tool by name."""
    try:
        result = await tool_registry.execute(tool_name, inputs)
        return {"tool": tool_name, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))