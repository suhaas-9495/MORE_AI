import os
from typing import Optional, List, Dict
from github import Github, GithubException
from backend.app.core.config import settings


def get_github_client() -> Github:
    token = os.getenv("GITHUB_TOKEN", "")
    if not token:
        raise ValueError("GITHUB_TOKEN not set in environment")
    return Github(token)


def get_pr_diff(repo_name: str, pr_number: int) -> Dict:
    """
    Fetches a PR diff from GitHub.
    This is what the PR Review Agent reads before generating review.
    """
    g = get_github_client()
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)

    files_changed = []
    for f in pr.get_files():
        files_changed.append({
            "filename": f.filename,
            "status": f.status,
            "additions": f.additions,
            "deletions": f.deletions,
            "patch": f.patch[:3000] if f.patch else "",  # truncate large diffs
        })

    return {
        "title": pr.title,
        "body": pr.body or "",
        "state": pr.state,
        "author": pr.user.login,
        "base_branch": pr.base.ref,
        "head_branch": pr.head.ref,
        "files_changed": files_changed,
        "additions": pr.additions,
        "deletions": pr.deletions,
    }


def post_pr_comment(repo_name: str, pr_number: int, comment: str) -> bool:
    """Posts a review comment on a GitHub PR."""
    try:
        g = get_github_client()
        repo = g.get_repo(repo_name)
        pr = repo.get_pull(pr_number)
        pr.create_issue_comment(comment)
        return True
    except GithubException as e:
        print(f"[GitHub] Failed to post comment: {e}")
        return False


def get_repo_info(repo_name: str) -> Dict:
    """Gets basic repo info — used by Research Agent for context."""
    g = get_github_client()
    repo = g.get_repo(repo_name)
    return {
        "name": repo.name,
        "description": repo.description,
        "language": repo.language,
        "stars": repo.stargazers_count,
        "open_issues": repo.open_issues_count,
        "default_branch": repo.default_branch,
        "topics": repo.get_topics(),
    }


def list_open_prs(repo_name: str) -> List[Dict]:
    """Lists all open PRs in a repo."""
    g = get_github_client()
    repo = g.get_repo(repo_name)
    prs = repo.get_pulls(state="open")
    return [
        {
            "number": pr.number,
            "title": pr.title,
            "author": pr.user.login,
            "created_at": pr.created_at.isoformat(),
            "files_changed": pr.changed_files,
        }
        for pr in prs
    ]


def create_github_issue(repo_name: str, title: str, body: str, labels: List[str] = None) -> Dict:
    """Creates a GitHub issue — used by agents to log bugs they find."""
    g = get_github_client()
    repo = g.get_repo(repo_name)
    issue = repo.create_issue(
        title=title,
        body=body,
        labels=labels or [],
    )
    return {
        "number": issue.number,
        "url": issue.html_url,
        "title": issue.title,
    }