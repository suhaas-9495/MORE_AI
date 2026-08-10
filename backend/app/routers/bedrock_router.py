from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.services.bedrock_service import (
    invoke_claude_bedrock, list_available_models
)
from backend.app.core.dependencies import get_current_user
from backend.app.core.rbac import require_permission

router = APIRouter(prefix="/bedrock", tags=["aws-bedrock"])


class BedrockRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    system_prompt: str = Field(default="You are a helpful AI assistant.")
    max_tokens: int = Field(default=4096, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)


@router.post("/invoke")
async def invoke_bedrock(
    payload: BedrockRequest,
    current_user: dict = Depends(require_permission("agent:run")),
):
    """
    Direct Bedrock invocation — Claude via AWS.
    Used when enterprise compliance requires AWS-only LLM calls.
    """
    try:
        response = invoke_claude_bedrock(
            prompt=payload.prompt,
            system_prompt=payload.system_prompt,
            max_tokens=payload.max_tokens,
            temperature=payload.temperature,
        )
        return {
            "response": response,
            "model": "claude-3-5-sonnet via AWS Bedrock",
            "user": current_user["username"],
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.get("/models")
async def get_models(current_user: dict = Depends(get_current_user)):
    """Lists all foundation models available in your AWS Bedrock region."""
    return list_available_models()


@router.get("/status")
async def bedrock_status(current_user: dict = Depends(get_current_user)):
    """Checks if Bedrock is configured and reachable."""
    from backend.app.core.config import settings
    configured = bool(
        settings.aws_access_key_id and
        settings.aws_secret_access_key and
        settings.aws_bedrock_region
    )
    return {
        "configured": configured,
        "region": settings.aws_bedrock_region,
        "model_id": settings.aws_bedrock_model_id,
        "note": "Enable Bedrock model access in AWS Console before invoking",
    }