from langchain_groq import ChatGroq
from backend.app.core.config import settings

def get_llm(temperature: float = 0.7) -> ChatGroq:
    """
    Single place to swap LLM provider.
    Change this file = change provider everywhere.
    """
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=temperature,
    )