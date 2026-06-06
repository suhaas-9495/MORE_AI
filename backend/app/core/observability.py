from langfuse import Langfuse
from backend.app.core.config import settings

langfuse = Langfuse(
    public_key=settings.langfuse_public_key,
    secret_key=settings.langfuse_secret_key,
    host=settings.langfuse_host,
)

def get_langfuse():
    return langfuse