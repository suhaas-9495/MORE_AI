from fastapi import APIRouter, HTTPException, Depends
from backend.app.agents.prompt_loader import (
    get_prompt_version, get_prompt_changelog,
    reload_prompt, load_prompt
)
from backend.app.core.dependencies import get_current_user
from backend.app.core.rbac import require_permission

router = APIRouter(prefix="/prompts", tags=["prompts"])

AGENT_TYPES = ["planner", "coder", "reviewer", "tester", "researcher", "documenter"]


@router.get("/")
async def list_prompts(current_user: dict = Depends(get_current_user)):
    """Returns all prompt versions — shows prompt-as-code in action."""
    return [
        {
            "agent_type": agent,
            "version": get_prompt_version(agent),
            "changelog_entries": len(get_prompt_changelog(agent)),
        }
        for agent in AGENT_TYPES
    ]


@router.get("/{agent_type}")
async def get_prompt(
    agent_type: str,
    current_user: dict = Depends(get_current_user),
):
    """Returns full prompt config including changelog."""
    if agent_type not in AGENT_TYPES:
        raise HTTPException(status_code=404, detail=f"Agent type not found: {agent_type}")
    return load_prompt(agent_type)


@router.get("/{agent_type}/changelog")
async def get_changelog(
    agent_type: str,
    current_user: dict = Depends(get_current_user),
):
    """Returns prompt version history — every change is tracked."""
    return {
        "agent_type": agent_type,
        "current_version": get_prompt_version(agent_type),
        "changelog": get_prompt_changelog(agent_type),
    }


@router.post("/{agent_type}/reload")
async def reload_agent_prompt(
    agent_type: str,
    current_user: dict = Depends(require_permission("agent:run")),
):
    """Hot-reloads a prompt from disk without restarting the server."""
    if agent_type not in AGENT_TYPES:
        raise HTTPException(status_code=404, detail=f"Agent type not found: {agent_type}")
    config = reload_prompt(agent_type)
    return {
        "status": "reloaded",
        "agent_type": agent_type,
        "version": config.get("version"),
    }