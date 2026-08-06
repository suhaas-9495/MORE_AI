from fastapi import APIRouter, Depends
from backend.app.mlflow_tracking.tracker import get_experiment_summary, log_eval_run
from backend.app.core.dependencies import get_current_user

router = APIRouter(prefix="/mlflow", tags=["mlflow"])


@router.get("/experiments/{agent_type}")
async def get_agent_experiments(
    agent_type: str,
    current_user: dict = Depends(get_current_user),
):
    """Returns MLflow experiment history for an agent type."""
    return get_experiment_summary(agent_type)


@router.get("/experiments")
async def list_all_experiments(
    current_user: dict = Depends(get_current_user),
):
    """Returns experiment summaries for all agent types."""
    agent_types = ["planner", "coder", "reviewer", "tester", "researcher", "documenter", "eval_harness"]
    return {
        agent: get_experiment_summary(agent)
        for agent in agent_types
    }