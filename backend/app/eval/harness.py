import time
from backend.app.eval.schemas import EvalCriteria, EvalResult
from backend.app.eval.judge import llm_judge
from backend.app.eval.cost_tracker import estimate_cost
from backend.app.eval.success_tracker import rule_based_check, log_eval_result
from backend.app.agents.base_agent import BaseAgent


async def run_eval(criteria: EvalCriteria, user: str = "eval-system") -> EvalResult:
    """
    Full eval pipeline for one task:
    1. Run the agent
    2. Rule-based pass/fail check
    3. LLM-as-judge scoring
    4. Cost estimation
    5. Log result to JSONL
    """
    agent = BaseAgent(agent_type=criteria.agent_type)

    start = time.time()
    result = await agent.run(task=criteria.task, user=user)
    latency = round(time.time() - start, 3)

    output = result["output"] or ""

    # rule-based check
    passed = rule_based_check(output, criteria)

    # LLM judge
    verdict = await llm_judge(
        task=criteria.task,
        output=output,
        expected_behavior=criteria.expected_behavior,
    )

    # cost tracking
    cost_usd, tokens_in, tokens_out = estimate_cost(
        input_text=criteria.task,
        output_text=output,
    )

    eval_result = EvalResult(
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

    log_eval_result(eval_result)
    return eval_result


async def run_regression_suite(user: str = "eval-system") -> list:
    """
    Runs the full fixed regression set.
    Call this on every prompt/code change to catch regressions.
    """
    from backend.app.eval.success_tracker import REGRESSION_EVAL_SET
    results = []
    for criteria in REGRESSION_EVAL_SET:
        result = await run_eval(criteria, user=user)
        results.append(result)
    return results