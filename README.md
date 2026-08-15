# MoreAI — Multi-Agent SDLC Automation Platform

![CI](https://github.com/suhaas-9495/MORE_AI/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![LangGraph](https://img.shields.io/badge/LangGraph-Latest-purple)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20EC2%20%7C%20Bedrock-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

> Production-grade multi-agent AI platform that automates the entire software
> development lifecycle — from requirements to deployed, documented, tested code.

---

## 🎯 What is MoreAI?

Give it a requirement like *"Build a rate limiter for a FastAPI app"* and a
pipeline of 7 AI agents handles everything autonomously:

Research → Plan → Code → Test → Review → [Human Approval] → Document → Deploy

Built with **LangGraph**, **Groq/AWS Bedrock**, **ChromaDB**, **Langfuse**,
**MLflow**, **FastAPI**, **React**, **Docker**, **Kubernetes**, and **Terraform**.

---

## 🏗️ Architecture

┌─────────────────────────────────────────────────────────────────┐
│ REACT FRONTEND (12 pages) │
│ Dashboard │ Agent Runner │ Pipeline │ Eval │ GitHub │ +7 more │
└──────────────────────┬──────────────────────────────────────────┘
│ REST API + MCP Protocol
┌──────────────────────▼──────────────────────────────────────────┐
│ FASTAPI BACKEND │
│ JWT Auth │ RBAC │ Rate Limiting │ Prompt Injection Defense │
│ PII Redaction │ Audit Logs │ Security Headers │ CORS │
└──────────────────────┬──────────────────────────────────────────┘
│
┌──────────────────────▼──────────────────────────────────────────┐
│ AGENT ORCHESTRATION (LangGraph) │
│ │
│ Research → Planner → Coder → Tester → Reviewer → Docs → Deploy │
│ │
│ ✦ Reflexion self-correction loop (max 2 retries) │
│ ✦ Human approval gate before deployment │
│ ✦ Short + long term memory per user │
│ ✦ RAG context injection on every run │
└──────────┬───────────────────────────┬───────────────────────────┘
│ │
┌──────────▼──────────┐ ┌───────────▼───────────────────────────┐
│ LLM PROVIDERS │ │ STORAGE LAYER │
│ │ │ │
│ Groq (primary) │ │ ChromaDB — vectors + memory │
│ AWS Bedrock │ │ AWS S3 — artifacts (encrypted) │
│ (enterprise) │ │ JSONL — audit + eval logs │
│ │ │ mlruns/ — MLflow experiments │
└─────────────────────┘ └───────────────────────────────────────┘
│
┌──────────▼──────────────────────────────────────────────────────┐
│ OBSERVABILITY LAYER │
│ Langfuse (LLM traces) │ MLflow (experiments) │ Audit logs │
└─────────────────────────────────────────────────────────────────┘
│
┌──────────▼──────────────────────────────────────────────────────┐
│ INFRASTRUCTURE │
│ Docker │ Kubernetes (HPA 2-10 replicas) │ GitHub Actions CI/CD │
│ Terraform (VPC/EC2/S3/IAM) │ AWS Bedrock │ MCP Server │
└─────────────────────────────────────────────────────────────────┘

---

## 🤖 Agents

| Agent | Role | Key Capability |
|-------|------|---------------|
| 🔍 Research | Gathers technical context | Best practices, patterns, pitfalls |
| 📋 Planner | Breaks requirements into steps | Complexity estimation, tool selection |
| 💻 Coder | Writes production Python | Type hints, docstrings, error handling |
| 🧪 Tester | Generates + executes pytest | Real subprocess execution, ground-truth pass/fail |
| 👀 Reviewer | Security + quality review | CVE detection, edge cases, best practices |
| 📝 Documenter | Generates technical docs | API docs, usage examples, architecture notes |
| 🚀 Deployment | Uploads to AWS S3 | Encrypted artifacts, deployment manifests |

**Every agent has:**
- Reflexion self-correction (critiques own output, retries if needed)
- Short-term memory (session context)
- Long-term memory (learns from past runs via ChromaDB)
- RAG context injection (retrieves relevant knowledge before answering)
- Langfuse tracing (tokens, cost, latency per node)
- MLflow experiment logging

---

## ✨ Key Features

### 🔄 Full SDLC Pipeline
One API call triggers all 7 agents in sequence with a human approval gate
before deployment. Pipeline runs in background, client polls for status.

### 📊 Production Eval Harness
- LLM-as-judge scoring (correctness 50%, relevance 30%, safety 20%)
- P50/P95/P99 latency percentiles
- Cost-per-task tracking (tokens × price)
- Regression detection — flags score drops vs baseline
- Circuit breaker — stops after 3 consecutive failures
- CI exit codes — fails GitHub Actions if success rate < 70%
- JSON/CSV/Markdown output formats

### 🔍 Hybrid RAG Pipeline
- BM25 keyword + semantic embedding similarity (70/30 weighted merge)
- Per-user document isolation (data security)
- Auto-context injection before every agent task
- GDPR-style document deletion

### 🔌 MCP Integration
- All agents exposed as MCP server tools
- Claude Desktop + Cursor compatible at `/mcp`
- Tool Registry + Agent Registry with capability routing

### 🔐 Enterprise Security
- JWT + bcrypt + RBAC (Admin/Developer/Viewer)
- Prompt injection detection + blocking
- PII redaction (Microsoft Presidio)
- Rate limiting per route (5/min register, 10/min login, 10/min agents)
- Input sanitization (null bytes, control chars, length limits)
- Security headers (X-Frame-Options, CSP, HSTS)
- S3 server-side encryption (AES256)
- Non-root Docker user
- Append-only audit logs

### 🐙 GitHub Integration
- PR diff reader + AI-powered review
- Auto-posts review as GitHub PR comment
- Issue creation from agent findings
- Open PR listing and one-click review

### ☁️ AWS Integration
- S3 artifact storage (encrypted, versioned, private)
- AWS Bedrock (Claude via AWS — enterprise compliance)
- Groq/Bedrock provider switching without code changes
- EC2 deployment + Terraform infrastructure

### 📦 Python SDK
```python
from moreai_sdk import MoreAIClient

client = MoreAIClient("http://localhost:8000")
client.login("username", "password")

result = client.run_agent("Build a JWT auth system", agent_type="coder")
print(result.output)

metrics = client.get_metrics()
print(f"Success rate: {metrics.success_rate:.1%}")
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+, Node.js 18+, Docker Desktop
- Groq API key → [console.groq.com](https://console.groq.com) (free)
- Langfuse account → [langfuse.com](https://langfuse.com) (free)

### 1 — Clone + setup
```bash
git clone https://github.com/suhaas-9495/MORE_AI.git
cd MORE_AI
conda create -n moreai python=3.11 -y
conda activate moreai
pip install -r requirements.txt
```

### 2 — Configure
```bash
cp .env.example .env
# edit .env with your keys
```

### 3 — Run backend
```bash
uvicorn backend.app.main:app --reload
# API docs: http://localhost:8000/docs
```

### 4 — Run frontend
```bash
cd frontend
npm install && npm start
# Dashboard: http://localhost:3000
```

### 5 — Run with Docker
```bash
docker-compose up --build
```

### 6 — Install SDK
```bash
cd sdk && pip install -e .
```

---

## 📡 API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/auth/register` | POST | Register user |
| `/auth/login` | POST | Login → JWT |
| `/agent/run` | POST | Run any agent |
| `/pipeline/run` | POST | Full SDLC pipeline |
| `/pipeline/approvals` | GET | Pending approval gates |
| `/pipeline/approvals/{id}/decide` | POST | Approve/reject |
| `/rag/ingest` | POST | Ingest document |
| `/rag/retrieve` | POST | Hybrid search |
| `/eval/run` | POST | Single eval |
| `/eval/v2/regression` | POST | Regression suite |
| `/eval/metrics` | GET | Success rate + costs |
| `/memory/recall` | GET | Query long-term memory |
| `/registry/tools` | GET | List MCP tools |
| `/registry/agents` | GET | List agents |
| `/github/pr/review` | POST | AI PR review |
| `/bedrock/invoke` | POST | AWS Bedrock LLM |
| `/mlflow/experiments` | GET | Experiment history |
| `/prompts/` | GET | Prompt versions |
| `/artifacts/` | GET | S3 artifacts |
| `/mcp` | MCP | MCP server endpoint |

---

## 📈 Eval Results

Run `POST /eval/v2/regression` to generate benchmarks:

| Metric | Value |
|--------|-------|
| Task Success Rate | Run regression to populate |
| Avg Judge Score | Run regression to populate |
| P50 Latency | Run regression to populate |
| P95 Latency | Run regression to populate |
| Cost per Task | Run regression to populate |

---

## 🏗️ Project Structure
more_ai/
├── backend/
│ └── app/
│ ├── agents/ # LangGraph nodes, graph, prompts
│ ├── core/ # Auth, RBAC, security, logging, middleware
│ ├── db/ # User store
│ ├── eval/ # Eval harness v2, judge, cost tracker
│ ├── memory/ # Short + long term memory
│ ├── mcp_server/ # MCP server
│ ├── mlflow_tracking/ # MLflow experiment tracker
│ ├── models/ # Pydantic schemas
│ ├── prompts/ # YAML version-controlled system prompts
│ ├── rag/ # Chunking, embeddings, hybrid search
│ ├── registry/ # Tool + Agent registry
│ ├── routers/ # FastAPI routes (12 routers)
│ └── services/ # AWS S3, Bedrock, GitHub
├── frontend/ # React dashboard (12 pages)
├── sdk/ # Python SDK package
├── k8s/ # Kubernetes manifests
├── terraform/ # AWS infrastructure as code
├── tests/ # pytest unit tests
├── scripts/ # CI regression scripts
├── docs/ # Architecture documentation
├── .github/workflows/ # GitHub Actions CI/CD
├── Dockerfile
├── docker-compose.yml
├── SECURITY.md
├── RELIABILITY.md
└── requirements.txt

---

## 🔒 Security

See [SECURITY.md](SECURITY.md) for full security documentation including:
- Prompt injection test cases
- PII redaction coverage
- RBAC permission matrix
- Rate limiting configuration
- Audit log format

---

## ⚡ Production Reliability

See [RELIABILITY.md](RELIABILITY.md) for documented failure modes:
- LLM timeout handling
- Reflexion infinite loop prevention
- Generated code sandbox timeout
- S3 graceful failure
- Circuit breaker pattern
- Langfuse non-blocking failure

---

## 🗺️ Roadmap

- [x] Multi-agent LangGraph pipeline (7 agents)
- [x] Hybrid RAG (BM25 + semantic)
- [x] JWT auth + RBAC
- [x] Production eval harness with LLM-as-judge
- [x] MCP server integration
- [x] Human approval gates
- [x] Short + long term memory
- [x] Docker + Kubernetes + Terraform
- [x] GitHub Actions CI/CD
- [x] AWS S3 + EC2 + Bedrock
- [x] React frontend (12 pages)
- [x] MLflow experiment tracking
- [x] Langfuse full observability
- [x] GitHub PR review agent
- [x] Python SDK package
- [x] Prompt-as-code (YAML + changelog)
- [x] Production hardening (CORS, security headers, logging)
- [ ] PostgreSQL (replacing in-memory user store)
- [ ] Redis (session + state management)
- [ ] Slack notifications on pipeline completion
- [ ] vLLM self-hosted inference option
- [ ] OCR pipeline for PDF ingestion

---

## 👨‍💻 Built By

**Suhaas** — AI Engineer
- GitHub: [@suhaas-9495](https://github.com/suhaas-9495)
- Built: June–September 2026 (4 months)
- Stack: Python · FastAPI · LangGraph · React · AWS · Docker · Kubernetes

---

## 📄 License

MIT