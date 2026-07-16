"""Posts eval results as a comment on the GitHub PR."""
import asyncio
import sys
import os
import httpx

sys.path.insert(0, os.getcwd())

from backend.app.eval.harness_v2 import run_harness_v2
from backend.app.eval.success_tracker import REGRESSION_EVAL_SET


async def main():
    run = await run_harness_v2(
        eval_suite=REGRESSION_EVAL_SET,
        user="ci-system",
        concurrency=2,
        timeout_per_task=90,
        output_format="markdown",
    )
    summary = run.summary()
    ci_passed = summary["success_rate"] >= 0.7
    status = "✅ PASSED" if ci_passed else "❌ FAILED"

    comment = f"""## MoreAI Eval Regression {status}

| Metric | Value |
|--------|-------|
| Success Rate | {summary['success_rate']} |
| Avg Judge Score | {summary['avg_judge_score']} |
| P50 Latency | {summary['p50_latency_s']}s |
| P95 Latency | {summary['p95_latency_s']}s |
| Total Cost | ${summary['total_cost_usd']} |
| Tasks Run | {summary['completed']} |

{' Safe to merge.' if ci_passed else ' Do not merge — eval scores dropped below threshold.'}
"""

    token = os.getenv("GITHUB_TOKEN")
    pr = os.getenv("PR_NUMBER")
    repo = os.getenv("GITHUB_REPOSITORY")

    if token and pr and repo:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://api.github.com/repos/{repo}/issues/{pr}/comments",
                headers={"Authorization": f"Bearer {token}"},
                json={"body": comment},
            )
        print("PR comment posted.")

    if not ci_passed:
        sys.exit(1)


asyncio.run(main())