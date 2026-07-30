from langfuse import Langfuse
from functools import wraps
import time
from backend.app.core.config import settings

# singleton client — one instance shared across entire app
_langfuse_client = None


def get_langfuse_client() -> Langfuse:
    global _langfuse_client
    if _langfuse_client is None:
        _langfuse_client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
        )
    return _langfuse_client


def create_trace(name: str, user_id: str = None, session_id: str = None, tags: list = None, metadata: dict = None):
    """
    Creates a top-level Langfuse trace.
    One trace = one user-visible operation (one agent run, one pipeline run).
    Everything else is a span nested inside this trace.
    """
    client = get_langfuse_client()
    return client.trace(
        name=name,
        user_id=user_id,
        session_id=session_id,
        tags=tags or [],
        metadata=metadata or {},
    )


def trace_agent_run(agent_type: str, task: str, user: str, session_id: str = None):
    """Creates a trace specifically for an agent run."""
    return create_trace(
        name=f"agent.{agent_type}",
        user_id=user,
        session_id=session_id or user,
        tags=[agent_type, settings.env],
        metadata={"agent_type": agent_type, "task_preview": task[:100]},
    )


def trace_pipeline_run(task: str, user: str):
    """Creates a trace for a full SDLC pipeline run."""
    return create_trace(
        name="pipeline.sdlc",
        user_id=user,
        session_id=f"pipeline_{user}",
        tags=["pipeline", settings.env],
        metadata={"task_preview": task[:100]},
    )


def flush():
    """Flush all pending traces — call on shutdown."""
    client = get_langfuse_client()
    client.flush()