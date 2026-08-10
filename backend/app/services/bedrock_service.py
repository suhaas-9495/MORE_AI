import boto3
import json
from typing import Optional, Dict, Any
from backend.app.core.config import settings


def get_bedrock_client():
    """
    Returns a Bedrock runtime client.
    Bedrock = AWS-hosted LLMs (Claude, Llama, Mistral, Titan).
    This lets you swap Groq for AWS-hosted models in production.
    Enterprise clients often require AWS-only due to compliance.
    """
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_bedrock_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def invoke_claude_bedrock(
    prompt: str,
    system_prompt: str = "You are a helpful AI assistant.",
    max_tokens: int = 4096,
    temperature: float = 0.7,
) -> str:
    """
    Calls Claude via AWS Bedrock.
    Uses the Messages API format (same as Anthropic API).
    Falls back gracefully if Bedrock is not configured.
    """
    try:
        client = get_bedrock_client()

        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": prompt}
            ],
        })

        response = client.invoke_model(
            modelId=settings.aws_bedrock_model_id,
            body=body,
            contentType="application/json",
            accept="application/json",
        )

        response_body = json.loads(response["body"].read())
        return response_body["content"][0]["text"]

    except Exception as e:
        raise RuntimeError(f"Bedrock invocation failed: {e}")


def list_available_models() -> list:
    """Lists all available foundation models in Bedrock."""
    try:
        client = boto3.client(
            "bedrock",
            region_name=settings.aws_bedrock_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        response = client.list_foundation_models()
        return [
            {
                "modelId": m["modelId"],
                "modelName": m["modelName"],
                "providerName": m["providerName"],
                "inputModalities": m.get("inputModalities", []),
                "outputModalities": m.get("outputModalities", []),
            }
            for m in response.get("modelSummaries", [])
        ]
    except Exception as e:
        return [{"error": str(e)}]


def get_bedrock_llm():
    """
    Returns a LangChain-compatible Bedrock LLM.
    Drop-in replacement for Groq in agent nodes.
    """
    try:
        from langchain_aws import ChatBedrock
        return ChatBedrock(
            model_id=settings.aws_bedrock_model_id,
            region_name=settings.aws_bedrock_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            model_kwargs={
                "temperature": 0.7,
                "max_tokens": 4096,
            },
        )
    except ImportError:
        raise ImportError("pip install langchain-aws")