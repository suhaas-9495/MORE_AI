from langfuse import Langfuse, observe
from backend.app.core.config import settings

langfuse_client = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
)


def get_langfuse_client() -> Langfuse:
    return langfuse_client


trace_observe = observe