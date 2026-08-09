# MoreAI System Architecture

## High-Level Architecture

┌─────────────────────────────────────────────────────────────────┐
│ CLIENT LAYER │
│ │
│ React Dashboard (11 pages) MCP Clients │
│ localhost:3000 Claude Desktop / Cursor │
└──────────────────────┬───────────────────────┬──────────────────┘
│ HTTP/REST │ MCP Protocol
┌──────────────────────▼───────────────────────▼──────────────────┐
│ API GATEWAY LAYER │
│ │
│ FastAPI (port 8000) │
│ ├── JWT Auth + RBAC (Admin/Developer/Viewer) │
│ ├── Rate Limiting (10 req/min/IP) │
│ ├── Prompt Injection Defense │
│ ├── PII Redaction (Presidio) │
│ └── Audit Logging (append-only JSONL) │
└──────────────────────┬───────────────────────────────────────────┘
│
┌──────────────────────▼───────────────────────────────────────────┐
│ AGENT ORCHESTRATION LAYER │
│ │
│ LangGraph State Machine │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────┐ │
│ │ Research │──▶│ Planner │──▶│ Coder │──▶│ Tester │ │
│ └──────────┘ └──────────┘ └──────────┘ └─────┬──────┘ │
│ │ │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ │ │
│ │ Deploy │◀──│ Docs │◀──│ Review │◀────────┘ │
│ └──────────┘ └──────────┘ └──────────┘ │
│ │
│ Cross-cutting: Reflexion Loop │ Human Approval Gate │
│ Short+Long Term Memory │ RAG Context Injection │
└──────────────────────┬───────────────────────────────────────────┘
│
┌──────────┬───────────┴──────────┬──────────────────────────────┐
│ LLM │ MEMORY LAYER │ STORAGE LAYER │
│ LAYER │ │ │
│ │ Short-term │ ChromaDB (vectors) │
│ Groq │ (in-memory session) │ AWS S3 (artifacts) │
│ API │ │ JSONL (audit + eval logs) │
│ llama3 │ Long-term │ mlruns/ (MLflow) │
│ -70b │ (ChromaDB vectors) │ │
└──────────┴──────────────────────┴──────────────────────────────┘
│
┌──────────────────────▼───────────────────────────────────────────┐
│ OBSERVABILITY LAYER │
│ Langfuse (LLM traces) │ MLflow (experiments) │ Audit logs │
└───────────────────────────────────────────────────────────────────┘
│
┌──────────────────────▼───────────────────────────────────────────┐
│ INFRASTRUCTURE LAYER │
│ Docker + Docker Compose │ Kubernetes (HPA 2-10 replicas) │
│ Terraform (VPC/EC2/S3/IAM) │ GitHub Actions CI/CD │
└───────────────────────────────────────────────────────────────────┘
## Request Flow — Single Agent Run
User → POST /agent/run
→ JWT validation (dependencies.py)
→ RBAC permission check (rbac.py)
→ Rate limit check (slowapi)
→ Prompt injection scan (security_middleware.py)
→ BaseAgent.run()
→ retrieve_context() [ChromaDB hybrid search]
→ retrieve_memories() [long-term ChromaDB]
→ get_session() [short-term memory]
→ LangGraph.ainvoke(initial_state)
→ research_node() → Groq API call [traced in Langfuse]
→ plan_node() → Groq API call [traced in Langfuse]
→ code_node() → Groq API call [traced in Langfuse]
→ test_node() → Groq API call + subprocess pytest
→ review_node() → Groq API call [traced in Langfuse]
→ reflexion_node() → retry decision (max 2)
→ finalize_node() → assemble output
→ store_memory() [ChromaDB]
→ log_agent_run() [MLflow]
→ filter_output() [PII redaction]
→ return AgentResponse

## Pipeline Flow — Full SDLC

POST /pipeline/run
→ Background task spawned (returns immediately)
→ run_sdlc_pipeline()
→ Stage 1: researcher agent
→ Stage 2: planner agent
→ Stage 3: coder agent
→ Stage 4: tester agent
→ Stage 5: reviewer agent
→ HUMAN APPROVAL GATE (polls every 2s, 5min timeout)
→ POST /pipeline/approvals/{id}/decide
→ Stage 6: documenter agent
→ Stage 7: DeploymentAgent → AWS S3 upload
→ audit log: pipeline:completed

## Data Flow — RAG Pipeline

Ingest:
POST /rag/ingest
→ chunk_text() [RecursiveCharacterTextSplitter, 512 chars, 64 overlap]
→ embed_texts() [sentence-transformers all-MiniLM-L6-v2, 384-dim]
→ store_chunks() [ChromaDB, cosine similarity, tagged with user+source]

Retrieve:
retrieve_context(query, user=X)
→ embed_query() [384-dim vector]
→ retrieve_similar() [ChromaDB cosine, where={user: X}]
→ keyword_search() [BM25Okapi]
→ hybrid_merge() [70% semantic + 30% BM25]
→ format context string → injected into agent prompt
## Security Architecture
Input → Prompt injection scan → blocked? → 400 + audit log
→ JWT decode → invalid? → 401
→ RBAC check → denied? → 403
→ Rate limit → exceeded? → 429
↓
Agent → RAG retrieval (user-scoped, no cross-user leak)
→ LLM call (Groq, no training on requests)
↓
Output → PII redaction (Presidio) → EMAIL/PHONE/SSN/PERSON redacted
→ return to client
