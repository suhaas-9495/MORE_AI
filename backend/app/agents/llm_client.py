import os
from langchain_groq import ChatGroq
from langfuse.callback import CallbackHandler
from backend.app.core.config import settings


def get_llm(temperature: float = 0.7, trace=None, provider: str = "groq"):
    """
    LLM factory — supports Groq (default) and AWS Bedrock.
    Swap provider without changing any agent code.
    Production pattern: use Bedrock for compliance, Groq for speed.
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

    if provider == "bedrock":
        try:
            from langchain_aws import ChatBedrock
            return ChatBedrock(
                model_id=settings.aws_bedrock_model_id,
                region_name=settings.aws_bedrock_region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
                model_kwargs={"temperature": temperature, "max_tokens": 4096},
                callbacks=callbacks if callbacks else None,
            )
        except Exception:
            # fallback to Groq if Bedrock fails
            print("[LLM] Bedrock unavailable, falling back to Groq")

    return ChatGroq(
        api_key=settings.groq_api_key,
        model=settings.groq_model,
        temperature=temperature,
        callbacks=callbacks if callbacks else None,
    )


def get_llm_precise(trace=None, provider: str = "groq"):
    return get_llm(temperature=0.0, trace=trace, provider=provider)
