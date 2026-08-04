# MoreAI — Production Reliability

## Failure Modes Handled

### 1. LLM Timeout (Handled Day 3)
**Failure:** Groq API takes > 120 seconds or never responds.
**Impact:** Request hangs indefinitely, blocking the event loop.
**Fix:** `asyncio.wait_for()` with 120s timeout on every agent run.
**Code:** `backend/app/eval/harness_v2.py` — `_run_task_with_timeout()`
**Result:** Timed-out tasks return `PASSED: False` with a clear timeout message
instead of hanging the server.

---

### 2. Reflexion Infinite Loop (Handled Day 3)
**Failure:** Reflexion node decides `should_retry: true` every iteration,
causing infinite LLM calls and unlimited cost accumulation.
**Impact:** $$$, server unresponsive, Groq rate limit hit.
**Fix:** Hard cap at `iterations >= 2` — reflexion is forced to `should_retry: false`
regardless of LLM opinion.
**Code:** `backend/app/agents/nodes.py` — `reflexion_node()`
**Result:** Maximum 3 LLM calls per node (1 initial + 2 retries) — predictable cost.

---

### 3. Generated Code Infinite Loop (Handled Day 9)
**Failure:** Tester agent generates code with `while True` or recursive 
infinite loops. Subprocess runs forever.
**Impact:** CI hangs, server thread blocked.
**Fix:** `subprocess.run()` with `timeout=30` — kills the process after 30 seconds.
**Code:** `backend/app/agents/test_runner.py` — `run_generated_tests()`
**Result:** Test execution always terminates. Returns timeout message as
test failure result.

---

### 4. S3 Upload Failure (Handled Day 19)
**Failure:** AWS S3 is unreachable, credentials expired, or bucket
doesn't exist during deployment.
**Impact:** Full pipeline crash, all results lost.
**Fix:** Try/except around each individual artifact upload.
Partial results returned — whatever was uploaded is saved.
**Code:** `backend/app/agents/deployment_agent.py` — `deploy()`
**Result:** Pipeline returns `{"status": "partial", "artifacts": {...}, "error": "..."}`
instead of crashing. Already-uploaded artifacts are preserved.

---

### 5. Circuit Breaker (Handled Day 15)
**Failure:** Eval harness hammers a failing service — Groq rate limit hit,
all 20 eval tasks fail in sequence, wasting time and money.
**Impact:** Full eval suite fails expensively.
**Fix:** Circuit breaker opens after 3 consecutive failures —
all subsequent tasks are skipped with `SKIPPED` status.
**Code:** `backend/app/eval/harness_v2.py` — `CircuitBreaker`
**Result:** A broken service causes 3 failures then stops.
Partial results reported. Circuit can be reset manually.

---

### 6. Langfuse Failure (Handled Day 23)
**Failure:** Langfuse cloud is unreachable or API key is invalid.
**Impact:** Every agent run crashes because observability is blocking.
**Fix:** MLflow logging wrapped in try/except — Langfuse failures
never surface to the user. Agent completes, observability fails silently
with a logged warning.
**Code:** `backend/app/agents/base_agent.py`
**Result:** Observability is best-effort — production never goes down
because a monitoring tool is down.

---

## Reliability Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Agent timeout | < 120s | Enforced |
| Max reflexion iterations | ≤ 2 | Enforced |
| Test execution timeout | < 30s | Enforced |
| Eval circuit breaker | 3 failures | Enforced |
| S3 failure handling | Graceful partial | Implemented |
| Observability failure | Non-blocking | Implemented |

---

## What I Would Add in Production

1. **Redis** for session/state management — currently in-memory, lost on restart
2. **PostgreSQL** for user store — currently in-memory
3. **Dead letter queue** for failed pipeline runs — retry later
4. **Alerting** — Slack notification when circuit breaker opens
5. **Health checks** per dependency — S3, Groq, Langfuse, ChromaDB
6. **Graceful shutdown** — drain in-flight requests before pod termination
