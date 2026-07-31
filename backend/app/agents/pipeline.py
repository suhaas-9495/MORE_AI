import asyncio
from typing import Optional
from backend.app.agents.base_agent import BaseAgent
from backend.app.agents.deployment_agent import DeploymentAgent
from backend.app.core.approval import create_approval, get_approval, ApprovalStatus
from backend.app.memory.conversation_state import create_state
from backend.app.core.audit import log_audit_event
from backend.app.core.observability import trace_pipeline_run

APPROVAL_GATES = {"after_review": True}
GATE_TIMEOUT_SECONDS = 300


async def wait_for_approval(approval_id: str) -> bool:
    elapsed = 0
    while elapsed < GATE_TIMEOUT_SECONDS:
        approval = get_approval(approval_id)
        if not approval:
            return False
        if approval.status == ApprovalStatus.APPROVED:
            return True
        if approval.status == ApprovalStatus.REJECTED:
            return False
        await asyncio.sleep(2)
        elapsed += 2
    approval = get_approval(approval_id)
    if approval:
        approval.status = ApprovalStatus.EXPIRED
    return False


async def run_sdlc_pipeline(
    task: str,
    user: str,
    session_id: Optional[str] = None,
    require_approval: bool = True,
) -> dict:
    """Full 7-agent pipeline with Langfuse tracing across all stages."""

    # one trace for the entire pipeline — all agent spans nest inside
    pipeline_trace = trace_pipeline_run(task=task, user=user)
    conv_state = create_state(user=user, task=task)
    results = {}
    sid = session_id or user

    log_audit_event(action="pipeline:start", user=user,
                    resource=f"pipeline/{conv_state.state_id}", detail=task[:100])

    async def run_stage(agent_type: str, task_override: str = None, ctx: str = None):
        """Runs one pipeline stage, logs as a span under pipeline trace."""
        stage_span = pipeline_trace.span(
            name=f"stage.{agent_type}",
            input={"task": (task_override or task)[:100]},
        )
        agent = BaseAgent(agent_type=agent_type)
        result = await agent.run(
            task=task_override or task,
            context=ctx, user=user, session_id=sid,
        )
        stage_span.end(
            output={"output_length": len(result["output"]), "iterations": result["iterations"]}
        )
        return result

    # Stage 1: Research
    print("[Pipeline] 1/7 Research...")
    r = await run_stage("researcher")
    results["research"] = r["output"]

    # Stage 2: Plan
    print("[Pipeline] 2/7 Planning...")
    r = await run_stage("planner", ctx=results["research"])
    results["plan"] = r["output"]

    # Stage 3: Code
    print("[Pipeline] 3/7 Coding...")
    r = await run_stage("coder", ctx=f"Research:\n{results['research']}\n\nPlan:\n{results['plan']}")
    results["code"] = r["output"]

    # Stage 4: Test
    print("[Pipeline] 4/7 Testing...")
    r = await run_stage("tester", task_override=f"Write tests for:\n{results['code']}")
    results["tests"] = r["output"]

    # Stage 5: Review
    print("[Pipeline] 5/7 Reviewing...")
    r = await run_stage("reviewer", task_override=f"Review:\n{results['code']}")
    results["review"] = r["output"]

    # Human Approval Gate
    if require_approval and APPROVAL_GATES.get("after_review"):
        print("[Pipeline] ⏸ Awaiting human approval...")
        gate_span = pipeline_trace.span(name="human_approval_gate")
        approval = create_approval(
            state_id=conv_state.state_id, user=user,
            agent_type="deployment",
            action_description=f"Deploy: {task[:100]}",
            payload={"task": task, "code_preview": results["code"][:500]},
        )
        approved = await wait_for_approval(approval.approval_id)
        gate_span.end(output={"approved": approved, "approval_id": approval.approval_id})

        if not approved:
            pipeline_trace.update(
                output={"status": "rejected"},
                metadata={"approval_id": approval.approval_id},
            )
            results["status"] = "rejected"
            results["approval_id"] = approval.approval_id
            return results

    # Stage 6: Document
    print("[Pipeline] 6/7 Documenting...")
    r = await run_stage("documenter", task_override=f"Document:\n{results['code']}")
    results["documentation"] = r["output"]

    # Stage 7: Deploy
    print("[Pipeline] 7/7 Deploying...")
    deploy_span = pipeline_trace.span(name="stage.deployment")
    deployer = DeploymentAgent()
    deployment_result = await deployer.deploy(
        task=task, code=results["code"],
        documentation=results["documentation"],
        tests=results["tests"], review=results["review"],
        user=user, pipeline_state_id=conv_state.state_id,
    )
    deploy_span.end(output={"status": deployment_result["status"]})
    results["deployment"] = deployment_result

    # finalize trace
    pipeline_trace.update(
        output={"status": "completed", "stages_completed": 7},
        metadata={"state_id": conv_state.state_id},
    )

    conv_state.update(agent="deployer", output=str(deployment_result), status="completed")
    conv_state.save()

    log_audit_event(action="pipeline:completed", user=user,
                    resource=f"pipeline/{conv_state.state_id}")

    results["status"] = "completed"
    results["state_id"] = conv_state.state_id
    results["trace_id"] = pipeline_trace.id
    return results