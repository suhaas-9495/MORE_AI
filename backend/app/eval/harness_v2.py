import asyncio
import time
import uuid
import json
import csv
import os
from datetime import datetime, timezone
from typing import List, Optional, Dict
from enum import Enum
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.eval.schemas import EvalCriteria, EvalResult
from backend.app.eval.judge import llm_judge
from backend.app.eval.cost_tracker import estimate_cost
from backend.app.eval.success_tracker import rule_based_check, log_eval_result
from backend.app.agents.base_agent import BaseAgent


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    SKIPPED = "skipped"    # circuit breaker skipped this


class CircuitBreaker:
    """
    Stops hammering a failing service.
    After threshold consecutive failures — opens the circuit.
    All subsequent tasks are skipped until reset.
    Classic resilience pattern — prevents cascading failures.
    """

    def __init__(self, failure_threshold: int = 3):
        self.failure_threshold = failure_threshold
        self.consecutive_failures = 0
        self.is_open = False

    def record_success(self):
        self.consecutive_failures = 0
        self.is_open = False

    def record_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold:
            self.is_open = True
            print(f"[CircuitBreaker] OPEN after {self.consecutive_failures} consecutive failures")

    def should_skip(self) -> bool:
        return self.is_open


class HarnessRun:
    """Tracks the full state of one eval suite execution."""

    def __init__(self, run_id: str, total_tasks: int):
        self.run_id = run_id
        self.total_tasks = total_tasks
        self.completed = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.results: List[EvalResult] = []
        self.latencies: List[float] = []
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.finished_at: Optional[str] = None

    def add_result(self, result: EvalResult, status: TaskStatus):
        self.results.append(result)
        self.completed += 1
        if status == TaskStatus.SKIPPED:
            self.skipped += 1
        elif result.passed:
            self.passed += 1
            self.latencies.append(result.latency_s)
        else:
            self.failed += 1
            self.latencies.append(result.latency_s)

    def percentile(self, p: float) -> float:
        if not self.latencies:
            return 0.0
        sorted_lat = sorted(self.latencies)
        idx = int(len(sorted_lat) * p / 100)
        return round(sorted_lat[min(idx, len(sorted_lat) - 1)], 3)

    def summary(self) -> Dict:
        total_cost = sum(r.cost_usd or 0 for r in self.results)
        avg_judge = sum(r.judge_score or 0 for r in self.results) / max(len(self.results), 1)
        return {
            "run_id": self.run_id,
            "total_tasks": self.total_tasks,
            "completed": self.completed,
            "passed": self.passed,
            "failed": self.failed,
            "skipped": self.skipped,
            "success_rate": round(self.passed / max(self.completed - self.skipped, 1), 3),
            "avg_judge_score": round(avg_judge, 3),
            "total_cost_usd": round(total_cost, 6),
            "p50_latency_s": self.percentile(50),
            "p95_latency_s": self.percentile(95),
            "p99_latency_s": self.percentile(99),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _run_single_with_retry(criteria: EvalCriteria, user: str) -> EvalResult:
    """
    Runs one eval task with exponential backoff retry.
    Tenacity handles: attempt 1 → wait 2s → attempt 2 → wait 4s → attempt 3.
    Catches transient failures (Groq rate limits, network blips).
    """
    agent = BaseAgent(agent_type=criteria.agent_type)
    start = time.time()
    result = await agent.run(task=criteria.task, user=user)
    latency = round(time.time() - start, 3)
    output = result["output"] or ""

    passed = rule_based_check(output, criteria)
    verdict = await llm_judge(
        task=criteria.task,
        output=output,
        expected_behavior=criteria.expected_behavior,
    )
    cost_usd, tokens_in, tokens_out = estimate_cost(criteria.task, output)

    return EvalResult(
        task=criteria.task,
        agent_type=criteria.agent_type,
        output=output,
        passed=passed and verdict.passed,
        judge_score=verdict.score,
        judge_reasoning=verdict.reasoning,
        cost_usd=cost_usd,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        latency_s=latency,
        iterations=result["iterations"],
    )


async def _run_task_with_timeout(
    criteria: EvalCriteria,
    user: str,
    timeout: float,
    circuit_breaker: CircuitBreaker,
) -> tuple[EvalResult, TaskStatus]:
    """Wraps single task with timeout + circuit breaker check."""

    if circuit_breaker.should_skip():
        empty = EvalResult(
            task=criteria.task, agent_type=criteria.agent_type,
            output="", passed=False, latency_s=0,
        )
        return empty, TaskStatus.SKIPPED

    try:
        result = await asyncio.wait_for(
            _run_single_with_retry(criteria, user),
            timeout=timeout,
        )
        circuit_breaker.record_success()
        return result, TaskStatus.COMPLETED

    except asyncio.TimeoutError:
        circuit_breaker.record_failure()
        empty = EvalResult(
            task=criteria.task, agent_type=criteria.agent_type,
            output="TIMEOUT", passed=False, latency_s=timeout,
        )
        return empty, TaskStatus.TIMEOUT

    except Exception as e:
        circuit_breaker.record_failure()
        empty = EvalResult(
            task=criteria.task, agent_type=criteria.agent_type,
            output=f"ERROR: {str(e)}", passed=False, latency_s=0,
        )
        return empty, TaskStatus.FAILED


async def run_harness_v2(
    eval_suite: List[EvalCriteria],
    user: str = "eval-system",
    concurrency: int = 3,          # max parallel tasks
    timeout_per_task: float = 120, # seconds before a task is killed
    dry_run: bool = False,         # validate without executing
    output_format: str = "json",   # json | csv | markdown
) -> HarnessRun:
    """
    Production eval harness:
    - Parallel execution with semaphore-controlled concurrency
    - Per-task timeout
    - Exponential backoff retry (via tenacity)
    - Circuit breaker (stop after 3 consecutive failures)
    - Partial results (don't discard all if some fail)
    - P50/P95/P99 latency reporting
    - Multiple output formats
    """
    run_id = str(uuid.uuid4())[:8]
    run = HarnessRun(run_id=run_id, total_tasks=len(eval_suite))
    circuit_breaker = CircuitBreaker(failure_threshold=3)
    semaphore = asyncio.Semaphore(concurrency)

    print(f"\n[HarnessV2] Run {run_id} | {len(eval_suite)} tasks | concurrency={concurrency}")

    if dry_run:
        print(f"[HarnessV2] DRY RUN — validating {len(eval_suite)} tasks, no execution")
        for c in eval_suite:
            print(f"  ✓ {c.agent_type}: {c.task[:60]}")
        run.finished_at = datetime.now(timezone.utc).isoformat()
        return run

    async def bounded_task(criteria: EvalCriteria):
        async with semaphore:
            result, status = await _run_task_with_timeout(
                criteria, user, timeout_per_task, circuit_breaker
            )
            run.add_result(result, status)
            log_eval_result(result)
            icon = "✅" if result.passed else ("⏭️" if status == TaskStatus.SKIPPED else "❌")
            print(f"  {icon} [{criteria.agent_type}] {criteria.task[:50]} | score={result.judge_score} | {result.latency_s}s")

    # run all tasks concurrently (bounded by semaphore)
    await asyncio.gather(*[bounded_task(c) for c in eval_suite])

    run.finished_at = datetime.now(timezone.utc).isoformat()
    summary = run.summary()

    # output formats
    _save_results(run, output_format, run_id)

    print(f"\n[HarnessV2] Complete — success={summary['success_rate']} | "
          f"p50={summary['p50_latency_s']}s | p95={summary['p95_latency_s']}s | "
          f"cost=${summary['total_cost_usd']}")

    return run


def _save_results(run: HarnessRun, fmt: str, run_id: str):
    os.makedirs("eval_runs", exist_ok=True)

    if fmt == "json":
        path = f"eval_runs/{run_id}.json"
        with open(path, "w") as f:
            json.dump({
                "summary": run.summary(),
                "results": [r.model_dump() for r in run.results],
            }, f, indent=2)

    elif fmt == "csv":
        path = f"eval_runs/{run_id}.csv"
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=EvalResult.model_fields.keys())
            writer.writeheader()
            for r in run.results:
                writer.writerow(r.model_dump())

    elif fmt == "markdown":
        path = f"eval_runs/{run_id}.md"
        summary = run.summary()
        lines = [
            f"# Eval Run {run_id}",
            f"**Success Rate:** {summary['success_rate']}",
            f"**Avg Judge Score:** {summary['avg_judge_score']}",
            f"**Cost:** ${summary['total_cost_usd']}",
            f"**P50:** {summary['p50_latency_s']}s | **P95:** {summary['p95_latency_s']}s | **P99:** {summary['p99_latency_s']}s",
            "",
            "| Task | Agent | Passed | Score | Latency |",
            "|------|-------|--------|-------|---------|",
        ]
        for r in run.results:
            lines.append(f"| {r.task[:40]} | {r.agent_type} | {r.passed} | {r.judge_score} | {r.latency_s}s |")
        with open(path, "w") as f:
            f.write("\n".join(lines))

    print(f"[HarnessV2] Results saved → {path}")


def detect_regression(current_run: HarnessRun, baseline_path: str) -> Dict:
    """
    Compares current run against a saved baseline.
    Flags if success_rate or avg_judge_score dropped significantly.
    CI uses this to fail the build on regression.
    """
    if not os.path.exists(baseline_path):
        return {"regression_detected": False, "reason": "No baseline found"}

    with open(baseline_path) as f:
        baseline = json.load(f)["summary"]

    current = current_run.summary()
    score_drop = baseline["avg_judge_score"] - current["avg_judge_score"]
    rate_drop = baseline["success_rate"] - current["success_rate"]

    regression = score_drop > 0.1 or rate_drop > 0.1   # 10% drop threshold

    return {
        "regression_detected": regression,
        "score_drop": round(score_drop, 3),
        "rate_drop": round(rate_drop, 3),
        "baseline_success_rate": baseline["success_rate"],
        "current_success_rate": current["success_rate"],
    }