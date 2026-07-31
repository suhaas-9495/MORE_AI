from langchain_groq import ChatGroq
from langfuse.callback import CallbackHandler
from backend.app.core.config import settings
from backend.app.core.observability import get_langfuse_client


def get_llm(temperature: float = 0.7, trace=None) -> ChatGroq:
    """
    Returns a Groq LLM instance.
    When a trace is passed, attaches Langfuse callback handler
    so every LLM call inside this trace is automatically logged:
    - prompt tokens, completion tokens
    - latency per call
    - input messages, output content
    - cost estimation
    """
    callbacks = []
    if trace:
        handler = CallbackHandler(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key,
            host=settings.langfuse_host,
            trace_id=trace.id,
        )
        callbacks.append(handler)

    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=temperature,
        callbacks=callbacks if callbacks else None,
    )


def get_llm_precise(trace=None) -> ChatGroq:
    return get_llm(temperature=0.0, trace=trace)