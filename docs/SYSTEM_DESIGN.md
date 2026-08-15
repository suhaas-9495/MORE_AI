# MoreAI System Design

## Why LangGraph over LangChain LCEL?

LangGraph uses a stateful graph model — each node reads from and writes to
a shared `AgentState` TypedDict. This means:
- Nodes can access outputs from any previous node
- Conditional edges enable retry loops (reflexion)
- State is serializable — enables checkpointing and resumption
- Human approval gates are natural — pipeline pauses at a node, waits, resumes

LCEL is better for simple chains. LangGraph is better for stateful, branching workflows.

## Why Hybrid Search over pure semantic search?

Pure semantic search misses exact terms — error codes, function names, library names.
BM25 catches exact keyword matches but misses paraphrased meaning.

Hybrid merge (70% semantic + 30% BM25) captures both:
- "JWT authentication" matches semantically similar content
- "HS256" matches the exact algorithm name even if not semantically close

## Why LLM-as-judge over rule-based eval?

Rule-based checks (keyword matching) are fast but brittle.
They don't capture whether code is actually correct or secure.

LLM-as-judge with a fixed rubric (correctness/relevance/safety) gives
nuanced evaluation. Using temperature=0.0 makes it deterministic.
Judge calibration against hand-labeled examples measures agreement %.

## Why separate Langfuse and MLflow?

- **Langfuse** = real-time LLM observability (token-level, per-call)
- **MLflow** = experiment tracking over time (compare runs, track drift)

They solve different problems. Langfuse answers "what happened in this call?"
MLflow answers "is the agent getting better or worse over time?"

## Why async everywhere?

LLM calls are I/O bound — they block waiting for HTTP responses.
Async allows the event loop to handle other requests while waiting.
Without async, one slow LLM call blocks ALL other users.

With async + FastAPI, 10 concurrent agent runs execute in parallel
instead of sequentially.

## Trade-offs made

| Decision | Chosen | Alternative | Reason |
|----------|--------|-------------|--------|
| Vector DB | ChromaDB | Pinecone/Weaviate | Local-first, no cloud cost for dev |
| LLM | Groq | OpenAI | Speed (fastest inference), free tier |
| Auth | JWT stateless | Session-based | Scales horizontally, no shared state |
| User store | In-memory | PostgreSQL | Speed of development, swap later |
| Embeddings | all-MiniLM-L6-v2 | text-embedding-ada-002 | Local, no API cost |
| Eval | LLM-as-judge | Human labels | Scale, cost — calibrate with small labeled set |

## Scalability bottlenecks

1. **In-memory user store** — lost on restart, doesn't scale horizontally
   → Fix: PostgreSQL with connection pooling

2. **ChromaDB single instance** — not distributed
   → Fix: Pinecone or Qdrant for production scale

3. **Synchronous pipeline** — long-running, holds connection open
   → Fix: Celery + Redis task queue (async task pattern from Atlassian diagram)

4. **Rate limiting per-process** — doesn't work with multiple workers
   → Fix: Redis-backed rate limiting

## Interview talking points

- "I chose LangGraph over simple chaining because SDLC workflows have conditional
  branches — code can fail tests and retry, reviewers can reject and trigger rework.
  LangGraph's conditional edges model this naturally."

- "The reflexion loop was inspired by the Reflexion paper — agents that critique
  their own outputs perform significantly better than single-pass generation.
  I capped it at 2 iterations to prevent cost explosion."

- "Hybrid search outperforms pure semantic search in RAG systems because
  domain-specific terms like error codes and library names are exact matches,
  not semantic ones. BM25 catches what embeddings miss."

- "I built an LLM-as-judge evaluator because task success rate alone doesn't
  tell you if the output is actually good. The judge scores correctness,
  relevance, and safety on a 0-1 rubric with temperature=0 for determinism."