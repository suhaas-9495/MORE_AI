import mlflow
import mlflow.pyfunc
from datetime import datetime
from typing import Optional, Dict, Any
from backend.app.core.config import settings


# MLflow experiment setup — one experiment per agent type
MLFLOW_TRACKING_URI = "mlruns"   # local by default, swap for remote server
EXPERIMENT_PREFIX = "moreai"


def setup_mlflow():
    """Initialize MLflow tracking — called on startup."""
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    print(f"[MLflow] Tracking URI: {MLFLOW_TRACKING_URI}")


def get_or_create_experiment(agent_type: str) -> str:
    """Gets or creates an MLflow experiment for an agent type."""
    experiment_name = f"{EXPERIMENT_PREFIX}/{agent_type}"
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        experiment_id = mlflow.create_experiment(
            experiment_name,
            tags={"agent_type": agent_type, "project": "moreai"},
        )
    else:
        experiment_id = experiment.experiment_id
    return experiment_id


def log_agent_run(
    agent_type: str,
    task: str,
    output: str,
    latency_s: float,
    iterations: int,
    judge_score: Optional[float] = None,
    cost_usd: Optional[float] = None,
    passed: Optional[bool] = None,
    user: str = "anonymous",
    extra_tags: Optional[Dict] = None,
):
    """
    Logs one agent run as an MLflow run.
    Tracks: params (inputs), metrics (performance), tags (metadata).
    Over time this builds a full experiment history you can compare.
    """
    experiment_id = get_or_create_experiment(agent_type)

    with mlflow.start_run(experiment_id=experiment_id):
        # params — what went in
        mlflow.log_params({
            "agent_type": agent_type,
            "task_length": len(task),
            "task_preview": task[:100],
            "model": settings.groq_model,
            "user": user,
            "env": settings.env,
        })

        # metrics — what came out
        metrics = {
            "latency_s": latency_s,
            "iterations": iterations,
            "output_length": len(output),
        }
        if judge_score is not None:
            metrics["judge_score"] = judge_score
        if cost_usd is not None:
            metrics["cost_usd"] = cost_usd
        if passed is not None:
            metrics["passed"] = int(passed)

        mlflow.log_metrics(metrics)

        # tags — for filtering in UI
        tags = {
            "agent_type": agent_type,
            "timestamp": datetime.utcnow().isoformat(),
            "passed": str(passed),
        }
        if extra_tags:
            tags.update(extra_tags)
        mlflow.set_tags(tags)

        # log output as artifact — searchable history
        with open("agent_output.txt", "w") as f:
            f.write(f"Task: {task}\n\nOutput:\n{output}")
        mlflow.log_artifact("agent_output.txt")

        import os
        os.remove("agent_output.txt")


def log_eval_run(
    run_id: str,
    success_rate: float,
    avg_judge_score: float,
    total_cost: float,
    p50_latency: float,
    p95_latency: float,
    total_tasks: int,
    passed: int,
):
    """Logs a full eval regression suite run to MLflow."""
    experiment_id = get_or_create_experiment("eval_harness")

    with mlflow.start_run(
        experiment_id=experiment_id,
        run_name=f"regression_{run_id}",
    ):
        mlflow.log_params({
            "run_id": run_id,
            "total_tasks": total_tasks,
            "model": settings.groq_model,
        })
        mlflow.log_metrics({
            "success_rate": success_rate,
            "avg_judge_score": avg_judge_score,
            "total_cost_usd": total_cost,
            "p50_latency_s": p50_latency,
            "p95_latency_s": p95_latency,
            "passed": passed,
            "failed": total_tasks - passed,
        })
        mlflow.set_tags({
            "type": "regression_suite",
            "timestamp": datetime.utcnow().isoformat(),
            "ci_passed": str(success_rate >= 0.7),
        })


def get_experiment_summary(agent_type: str) -> Dict[str, Any]:
    """Returns recent run history for an agent — used by frontend."""
    try:
        experiment_name = f"{EXPERIMENT_PREFIX}/{agent_type}"
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if not experiment:
            return {"runs": [], "best_score": None, "avg_latency": None}

        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            order_by=["start_time DESC"],
            max_results=20,
        )

        if runs.empty:
            return {"runs": [], "best_score": None, "avg_latency": None}

        return {
            "total_runs": len(runs),
            "best_judge_score": runs["metrics.judge_score"].max() if "metrics.judge_score" in runs else None,
            "avg_latency_s": runs["metrics.latency_s"].mean() if "metrics.latency_s" in runs else None,
            "avg_cost_usd": runs["metrics.cost_usd"].mean() if "metrics.cost_usd" in runs else None,
            "recent_runs": runs[["start_time", "metrics.latency_s", "metrics.judge_score", "metrics.passed"]].head(5).to_dict("records"),
        }
    except Exception as e:
        return {"error": str(e)}