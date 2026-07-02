from fastapi import APIRouter, HTTPException, Depends
from backend.app.eval.schemas import EvalCriteria, EvalResult
from backend.app.eval.harness import run_eval, run_regression_suite
from backend.app.eval.success_tracker import get_task_success_rate
from backend.app.core.dependencies import get_current_user
from typing import List

router = APIRouter(prefix="/eval", tags=["eval"])


@router.post("/run", response_model=EvalResult)
async def evaluate_agent(
    criteria: EvalCriteria,
    current_user: dict = Depends(get_current_user),
):
    """Run a single eval against one task with LLM-as-judge scoring."""
    try:
        return await run_eval(criteria, user=current_user["username"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regression", response_model=List[EvalResult])
async def run_regression(current_user: dict = Depends(get_current_user)):
    """
    Run the full regression eval set.
    Call this after every prompt or code change to catch score drops.
    """
    try:
        return await run_regression_suite(user=current_user["username"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/metrics")
async def get_metrics(current_user: dict = Depends(get_current_user)):
    """Task success rate, avg judge score, total cost — your headline AI metrics."""
    return get_task_success_rate()