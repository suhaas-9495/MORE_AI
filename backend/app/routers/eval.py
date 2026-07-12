from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List
from backend.app.eval.schemas import EvalCriteria, EvalResult
from backend.app.eval.harness import run_eval
from backend.app.eval.harness_v2 import run_harness_v2, detect_regression
from backend.app.eval.success_tracker import (
    get_task_success_rate, REGRESSION_EVAL_SET
)
from backend.app.core.dependencies import get_current_user

router = APIRouter(prefix="/eval", tags=["eval"])


@router.post("/run", response_model=EvalResult)
async def evaluate_agent(
    criteria: EvalCriteria,
    current_user: dict = Depends(get_current_user),
):
    try:
        return await run_eval(criteria, user=current_user["username"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/run")
async def run_eval_suite_v2(
    suite: List[EvalCriteria],
    concurrency: int = Query(default=3, ge=1, le=10),
    timeout: float = Query(default=120.0),
    dry_run: bool = Query(default=False),
    output_format: str = Query(default="json"),
    current_user: dict = Depends(get_current_user),
):
    """
    Production eval harness — parallel, with circuit breaker,
    timeouts, retries, P95 latencies, and saved artifacts.
    """
    try:
        run = await run_harness_v2(
            eval_suite=suite,
            user=current_user["username"],
            concurrency=concurrency,
            timeout_per_task=timeout,
            dry_run=dry_run,
            output_format=output_format,
        )
        return run.summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/v2/regression")
async def regression_suite_v2(
    concurrency: int = Query(default=3),
    output_format: str = Query(default="markdown"),
    current_user: dict = Depends(get_current_user),
):
    """Run fixed regression set — call this in CI on every PR."""
    try:
        run = await run_harness_v2(
            eval_suite=REGRESSION_EVAL_SET,
            user=current_user["username"],
            concurrency=concurrency,
            output_format=output_format,
        )
        summary = run.summary()
        # CI exit signal — if success rate < 0.7, this is a regression
        summary["ci_passed"] = summary["success_rate"] >= 0.7
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics(current_user: dict = Depends(get_current_user)):
    return get_task_success_rate()