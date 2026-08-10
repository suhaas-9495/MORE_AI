# MoreAI Python SDK

```bash
pip install -e .   # install locally from sdk/ folder
```

## Quick Start

```python
from moreai_sdk import MoreAIClient

client = MoreAIClient(base_url="http://localhost:8000")
client.login("suhaas", "password123")

# health check
print(client.health())

# run planner agent
result = client.run_agent(
    "Design a microservices architecture for an e-commerce platform",
    agent_type="planner"
)
print(result.output)
print(f"Iterations: {result.iterations}")

# run full pipeline
pipeline = client.run_pipeline("Build a JWT auth API", require_approval=False)
print(f"Pipeline state: {pipeline['status']}")

# ingest knowledge
client.ingest("FastAPI uses Pydantic v2 for validation.", source="fastapi_docs")

# retrieve context
context = client.retrieve("how does FastAPI validation work?")
print(context)

# eval metrics
metrics = client.get_metrics()
print(f"Success rate: {metrics.success_rate:.1%}")
print(f"Total cost: ${metrics.total_cost_usd:.6f}")

# PR review
review = client.review_pr("suhaas-9495/MORE_AI", pr_number=5)
print(review["review"])
```

## Context manager

```python
with MoreAIClient(base_url="http://localhost:8000") as client:
    client.login("suhaas", "password123")
    result = client.run_agent("Write a binary search function", agent_type="coder")
    print(result.output)
```