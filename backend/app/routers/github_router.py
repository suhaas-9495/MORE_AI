from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional
from backend.app.agents.github_agent import GitHubAgent
from backend.app.services.github_service import (
    list_open_prs, get_repo_info, create_github_issue
)
from backend.app.core.dependencies import get_current_user
from backend.app.core.rbac import require_permission

router = APIRouter(prefix="/github", tags=["github"])


class PRReviewRequest(BaseModel):
    repo_name: str = Field(..., description="e.g. 'suhaas-9495/MORE_AI'")
    pr_number: int
    post_comment: bool = Field(default=True)


class IssueRequest(BaseModel):
    repo_name: str
    title: str
    body: str
    labels: Optional[list] = []


@router.post("/pr/review")
async def review_pr(
    payload: PRReviewRequest,
    current_user: dict = Depends(require_permission("agent:run")),
):
    """AI-powered PR review — reads diff, runs reviewer agent, posts comment."""
    try:
        agent = GitHubAgent()
        result = await agent.review_pr(
            repo_name=payload.repo_name,
            pr_number=payload.pr_number,
            user=current_user["username"],
            post_comment=payload.post_comment,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/pr/docs")
async def generate_pr_docs(
    payload: PRReviewRequest,
    current_user: dict = Depends(get_current_user),
):
    """Generates documentation for PR code changes."""
    try:
        agent = GitHubAgent()
        return await agent.generate_pr_docs(
            repo_name=payload.repo_name,
            pr_number=payload.pr_number,
            user=current_user["username"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repo/{owner}/{repo}/prs")
async def list_prs(
    owner: str, repo: str,
    current_user: dict = Depends(get_current_user),
):
    """Lists all open PRs in a repository."""
    try:
        return list_open_prs(f"{owner}/{repo}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/repo/{owner}/{repo}/info")
async def repo_info(
    owner: str, repo: str,
    current_user: dict = Depends(get_current_user),
):
    """Gets repository info — used for research context."""
    try:
        return get_repo_info(f"{owner}/{repo}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/issues")
async def create_issue(
    payload: IssueRequest,
    current_user: dict = Depends(require_permission("agent:run")),
):
    """Creates a GitHub issue — agents log bugs they find here."""
    try:
        return create_github_issue(
            payload.repo_name, payload.title,
            payload.body, payload.labels,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))