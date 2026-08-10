"""
MoreAI Python SDK
-----------------
Official Python client for the MoreAI Multi-Agent SDLC Platform.

Usage:
    from moreai_sdk import MoreAIClient

    client = MoreAIClient(base_url="http://localhost:8000")
    client.login("username", "password")

    # Run an agent
    result = client.run_agent("Build a rate limiter", agent_type="coder")
    print(result.output)

    # Run full pipeline
    pipeline = client.run_pipeline("Build a REST API for todos")
    print(pipeline.state_id)
"""

import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class AgentResult:
    agent_type: str
    task: str
    output: str
    model_used: str
    status: str
    iterations: int
    state_id: Optional[str] = None
    trace_id: Optional[str] = None


@dataclass
class EvalMetrics:
    total_runs: int
    passed: int
    success_rate: float
    avg_judge_score: float
    total_cost_usd: float
    by_agent_type: Dict


@dataclass
class MemoryStats:
    user: str
    total_memories: int


class MoreAIClient:
    """
    Python SDK for the MoreAI Multi-Agent SDLC Platform.

    Wraps the REST API into a clean, typed Python interface.
    Can be pip-installed and used in any Python project.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        token: Optional[str] = None,
        timeout: float = 120.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._token = token
        self._client = httpx.Client(timeout=timeout)

    def _headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self._token:
            headers["Authorization"] = f"Bearer {self._token}"
        return headers

    def _get(self, path: str, params: Dict = None) -> Dict:
        r = self._client.get(
            f"{self.base_url}{path}",
            headers=self._headers(),
            params=params or {},
        )
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, data: Dict = None) -> Dict:
        r = self._client.post(
            f"{self.base_url}{path}",
            headers=self._headers(),
            json=data or {},
        )
        r.raise_for_status()
        return r.json()

    # ── Auth ──────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> str:
        """Login and store token. Returns the access token."""
        data = self._post("/auth/login", {"username": username, "password": password})
        self._token = data["access_token"]
        return self._token

    def register(self, username: str, password: str) -> Dict:
        """Register a new user account."""
        return self._post("/auth/register", {"username": username, "password": password})

    # ── Agents ────────────────────────────────────────────────────

    def run_agent(
        self,
        task: str,
        agent_type: str = "planner",
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> AgentResult:
        """
        Run any MoreAI agent on a task.

        Args:
            task: What you want the agent to do
            agent_type: planner | coder | reviewer | tester | researcher | documenter
            context: Optional additional context
            session_id: Session ID for memory continuity

        Returns:
            AgentResult with output, iterations, trace_id
        """
        data = self._post("/agent/run", {
            "task": task,
            "agent_type": agent_type,
            "context": context,
            "session_id": session_id,
        })
        return AgentResult(**{k: data.get(k) for k in AgentResult.__dataclass_fields__})

    def run_pipeline(
        self,
        task: str,
        require_approval: bool = True,
        session_id: Optional[str] = None,
    ) -> Dict:
        """
        Run the full 7-agent SDLC pipeline.
        Returns immediately with a state_id.
        Pipeline runs in background.
        """
        return self._post("/pipeline/run", {
            "task": task,
            "require_approval": require_approval,
            "session_id": session_id,
        })

    def get_pending_approvals(self) -> List[Dict]:
        """Returns all pending human approval gates."""
        return self._get("/pipeline/approvals")

    def decide_approval(
        self, approval_id: str, approved: bool, reason: str = ""
    ) -> Dict:
        """Approve or reject a pipeline gate."""
        return self._post(
            f"/pipeline/approvals/{approval_id}/decide",
            {"approved": approved, "reason": reason},
        )

    # ── RAG ───────────────────────────────────────────────────────

    def ingest(
        self, text: str, source: str = "sdk", collection: str = "nexusai_docs"
    ) -> Dict:
        """Ingest a document into the knowledge base."""
        return self._post("/rag/ingest", {
            "text": text, "source": source, "collection": collection
        })

    def retrieve(
        self, query: str, top_k: int = 5, collection: str = "nexusai_docs"
    ) -> str:
        """Retrieve relevant context using hybrid search."""
        data = self._post("/rag/retrieve", {
            "query": query, "top_k": top_k, "collection": collection
        })
        return data.get("context", "")

    # ── Eval ──────────────────────────────────────────────────────

    def get_metrics(self) -> EvalMetrics:
        """Returns task success rate and cost metrics."""
        data = self._get("/eval/metrics")
        return EvalMetrics(**{k: data.get(k, 0) for k in EvalMetrics.__dataclass_fields__})

    def run_regression(self) -> Dict:
        """Runs the eval regression suite."""
        return self._post("/eval/v2/regression")

    # ── Memory ────────────────────────────────────────────────────

    def memory_stats(self) -> MemoryStats:
        """Returns memory statistics for the current user."""
        data = self._get("/memory/stats")
        return MemoryStats(**{k: data.get(k) for k in MemoryStats.__dataclass_fields__})

    def recall(self, query: str) -> str:
        """Query long-term agent memory."""
        data = self._get("/memory/recall", {"query": query})
        return data.get("memories", "")

    # ── Registry ──────────────────────────────────────────────────

    def list_tools(self) -> List[Dict]:
        """Lists all registered tools."""
        return self._get("/registry/tools")

    def list_agents(self) -> List[Dict]:
        """Lists all registered agent types."""
        return self._get("/registry/agents")

    # ── GitHub ────────────────────────────────────────────────────

    def review_pr(
        self, repo_name: str, pr_number: int, post_comment: bool = False
    ) -> Dict:
        """AI-powered PR review."""
        return self._post("/github/pr/review", {
            "repo_name": repo_name,
            "pr_number": pr_number,
            "post_comment": post_comment,
        })

    # ── Health ────────────────────────────────────────────────────

    def health(self) -> Dict:
        """Check API health."""
        return self._get("/health")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self._client.close()