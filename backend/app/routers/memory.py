from fastapi import APIRouter, Depends
from backend.app.core.dependencies import get_current_user
from backend.app.memory.short_term import get_session, clear_session
from backend.app.memory.long_term import get_user_memory_stats, retrieve_memories
from backend.app.memory.conversation_state import list_user_states

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/stats")
async def memory_stats(current_user: dict = Depends(get_current_user)):
    """How much does this agent remember about you?"""
    return get_user_memory_stats(user=current_user["username"])


@router.get("/recall")
async def recall(query: str, current_user: dict = Depends(get_current_user)):
    """Manually query long-term memory — what has the agent learned from past runs?"""
    memories = retrieve_memories(user=current_user["username"], query=query)
    return {"query": query, "memories": memories}


@router.delete("/session")
async def clear_my_session(current_user: dict = Depends(get_current_user)):
    """Clear short-term session memory."""
    clear_session(current_user["username"])
    return {"status": "session cleared"}


@router.get("/states")
async def get_states(current_user: dict = Depends(get_current_user)):
    """Get all active pipeline states for this user — needed for Human Approval gate."""
    return list_user_states(user=current_user["username"])