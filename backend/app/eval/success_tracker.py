from typing import List, Dict
from backend.app.eval.schemas import EvalCriteria, EvalResult
import json
import os

RESULTS_FILE = "eval_results.jsonl"   # append-only log — regression baseline

# Fixed regression eval set — run this on every code/prompt change
# If scores drop vs baseline, something regressed
REGRESSION_EVAL_SET: List[EvalCriteria] = [
    EvalCriteria(
        task="Write a Python function to validate an email address",
        expected_keywords=["def", "return", "re", "@"],
        expected_behavior="Returns a function that checks if a string is a valid email using regex",
        agent_type="coder",
    ),
    EvalCriteria(
        task="Create a plan to build a REST API",
        expected_keywords=["endpoint", "route", "auth", "database"],
        expected_behavior="Produces numbered steps covering API design, auth, and data layer",
        agent_type="planner",
    ),
    EvalCriteria(
        task="Review this code: x = input(); eval(x)",
        expected_keywords=["security", "dangerous", "eval", "injection"],
        expected_behavior="Flags eval() as a critical security vulnerability",
        agent_type="reviewer",
    ),
]


def rule_based_check(output: str, criteria: EvalCriteria) -> bool:
    """
    Fast deterministic check — did the output contain expected signals?
    Not a substitute for LLM judge, but cheap and instant.
    """
    output_lower = output.lower()
    return all(kw.lower() in output_lower for kw in criteria.expected_keywords)


def log_eval_result(result: EvalResult) -> None:
    """Append-only JSONL log — gives you a regression baseline over time."""
    with open(RESULTS_FILE, "a", encoding="utf-8") as f:
        f.write(result.model_dump_json() + "\n")


def load_eval_history() -> List[Dict]:
    """Read all past eval results for regression comparison."""
    if not os.path.exists(RESULTS_FILE):
        return []
    results = []
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            try:
                results.append(json.loads(line.strip()))
            except Exception:
                continue
    return results


def get_task_success_rate() -> Dict:
    """
    Aggregates pass/fail across all logged evals.
    This is your Task Success Rate — headline metric for interviews.
    """
    history = load_eval_history()
    if not history:
        return {"total": 0, "passed": 0, "success_rate": 0.0}

    total = len(history)
    passed = sum(1 for r in history if r.get("passed"))
    avg_judge_score = sum(
        r.get("judge_score", 0) or 0 for r in history
    ) / total
    total_cost = sum(r.get("cost_usd", 0) or 0 for r in history)

    by_agent = {}
    for r in history:
        agent = r.get("agent_type", "unknown")
        if agent not in by_agent:
            by_agent[agent] = {"total": 0, "passed": 0}
        by_agent[agent]["total"] += 1
        if r.get("passed"):
            by_agent[agent]["passed"] += 1

    return {
        "total_runs": total,
        "passed": passed,
        "success_rate": round(passed / total, 3),
        "avg_judge_score": round(avg_judge_score, 3),
        "total_cost_usd": round(total_cost, 6),
        "by_agent_type": by_agent,
    }