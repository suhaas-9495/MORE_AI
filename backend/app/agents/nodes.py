from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.agents.state import AgentState
from backend.app.agents.llm_client import get_llm, get_llm_precise
from backend.app.agents.prompts import AGENT_SYSTEM_PROMPTS
from backend.app.agents.test_runner import run_generated_tests
import json


async def plan_node(state: AgentState) -> AgentState:
    trace = state.get("trace")
    llm = get_llm(trace=trace)

    span = trace.span(name="plan_node", input={"task": state["task"]}) if trace else None

    research_context = f"Research findings:\n{state.get('research', '')}\n\n" if state.get("research") else ""
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["planner"] + """
Always end your response with a JSON block:
````json
{"goal": "...", "steps": [{"step_number": 1, "action": "...", "reasoning": "..."}],
 "estimated_complexity": "low|medium|high", "requires_tools": [...]}
```"""),
        HumanMessage(content=f"{research_context}Task:\n{state['task']}"),
    ]
    response = await llm.ainvoke(messages)

    if span:
        span.end(output={"plan_preview": response.content[:200]})

    return {**state, "plan": response.content}


async def research_node(state: AgentState) -> AgentState:
    trace = state.get("trace")
    llm = get_llm(trace=trace)
    span = trace.span(name="research_node", input={"task": state["task"]}) if trace else None

    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["researcher"]),
        HumanMessage(content=f"Research this task:\n{state['task']}"),
    ]
    response = await llm.ainvoke(messages)

    if span:
        span.end(output={"research_preview": response.content[:200]})

    return {**state, "research": response.content}


async def code_node(state: AgentState) -> AgentState:
    trace = state.get("trace")
    llm = get_llm(trace=trace)
    span = trace.span(name="code_node", input={"task": state["task"]}) if trace else None

    context = f"Research:\n{state.get('research', '')}\n\nPlan:\n{state.get('plan', '')}"
    if state.get("test_results"):
        context += f"\n\nFix these failures:\n{state['test_results']}"

    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["coder"]),
        HumanMessage(content=f"{context}\n\nTask:\n{state['task']}"),
    ]
    response = await llm.ainvoke(messages)

    if span:
        span.end(output={"code_preview": response.content[:200]})

    return {**state, "code": response.content}


async def review_node(state: AgentState) -> AgentState:
    trace = state.get("trace")
    llm = get_llm_precise(trace=trace)
    span = trace.span(name="review_node") if trace else None

    content = state.get("code") or state.get("plan") or state["task"]
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["reviewer"]),
        HumanMessage(content=content),
    ]
    response = await llm.ainvoke(messages)

    if span:
        span.end(output={"review_preview": response.content[:200]})

    return {**state, "review": response.content}


async def test_node(state: AgentState) -> AgentState:
    trace = state.get("trace")
    llm = get_llm(trace=trace)
    span = trace.span(name="test_node") if trace else None

    code = state.get("code", "")
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["tester"]),
        HumanMessage(content=f"Write tests for:\n{code}"),
    ]
    response = await llm.ainvoke(messages)
    test_code = response.content
    result = run_generated_tests(code, test_code)
    test_summary = f"PASSED: {result['passed']}\n\n{result['output']}"

    if span:
        span.end(output={"test_passed": result["passed"], "exit_code": result["exit_code"]})

    return {**state, "tests": test_code, "test_results": test_summary}


async def documentation_node(state: AgentState) -> AgentState:
    trace = state.get("trace")
    llm = get_llm(trace=trace)
    span = trace.span(name="documentation_node") if trace else None

    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["documenter"]),
        HumanMessage(content=f"Document:\n{state.get('code', '')}\n\nReview:\n{state.get('review', '')}"),
    ]
    response = await llm.ainvoke(messages)

    if span:
        span.end(output={"docs_preview": response.content[:200]})

    return {**state, "documentation": response.content}


async def reflexion_node(state: AgentState) -> AgentState:
    trace = state.get("trace")
    llm = get_llm_precise(trace=trace)
    span = trace.span(name="reflexion_node") if trace else None

    if state.get("test_results") and "PASSED: False" in state["test_results"]:
        should_retry = state["iterations"] < 2
        if span:
            span.end(output={"decision": "retry_on_test_failure", "should_retry": should_retry})
        return {
            **state,
            "critique": f"Tests failed:\n{state['test_results']}",
            "should_retry": should_retry,
            "iterations": state["iterations"] + 1,
        }

    output = state.get("code") or state.get("plan") or ""
    messages = [
        SystemMessage(content="""Evaluate output quality. Respond ONLY with JSON:
{"quality": "good|needs_improvement", "issues": [...], "should_retry": true|false}"""),
        HumanMessage(content=f"Output:\n{output}"),
    ]
    response = await llm.ainvoke(messages)

    try:
        raw = response.content
        data = json.loads(raw[raw.find("{"):raw.rfind("}") + 1])
        should_retry = data.get("should_retry", False)
        critique = str(data)
    except Exception:
        should_retry = False
        critique = response.content

    if state["iterations"] >= 2:
        should_retry = False

    if span:
        span.end(output={"should_retry": should_retry, "critique_preview": critique[:100]})

    return {**state, "critique": critique, "should_retry": should_retry,
            "iterations": state["iterations"] + 1}


async def finalize_node(state: AgentState) -> AgentState:
    trace = state.get("trace")
    if trace:
        span = trace.span(name="finalize_node")

    parts = []
    if state.get("research"):
        parts.append(f"## Research\n{state['research']}")
    if state.get("plan"):
        parts.append(f"## Plan\n{state['plan']}")
    if state.get("code"):
        parts.append(f"## Code\n{state['code']}")
    if state.get("tests"):
        parts.append(f"## Tests\n{state['tests']}")
    if state.get("test_results"):
        parts.append(f"## Test Results\n{state['test_results']}")
    if state.get("review"):
        parts.append(f"## Review\n{state['review']}")
    if state.get("documentation"):
        parts.append(f"## Documentation\n{state['documentation']}")
    if state.get("critique"):
        parts.append(f"## Self-Critique\n{state['critique']}")

    if trace:
        span.end(output={"sections": len(parts)})

    return {**state, "final_output": "\n\n---\n\n".join(parts)}