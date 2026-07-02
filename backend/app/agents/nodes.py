from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.agents.state import AgentState
from backend.app.agents.llm_client import get_llm
from backend.app.agents.prompts import AGENT_SYSTEM_PROMPTS
from backend.app.agents.test_runner import run_generated_tests
from backend.app.core.observability import trace_observe
import json

llm = get_llm()
llm_precise = get_llm(temperature=0.1)


@trace_observe(name="plan_node")
async def plan_node(state: AgentState) -> AgentState:
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["planner"] + """
Always end your response with a JSON block like:
````json
{"goal": "...", "steps": [{"step_number": 1, "action": "...", "reasoning": "..."}],
 "estimated_complexity": "low|medium|high", "requires_tools": [...]}
```"""),
        HumanMessage(content=state["task"]),
    ]
    response = await llm.ainvoke(messages)
    return {**state, "plan": response.content}


@trace_observe(name="code_node")
async def code_node(state: AgentState) -> AgentState:
    context = f"Plan:\n{state.get('plan', '')}\n\nOriginal task:\n{state['task']}"
    if state.get("test_results"):
        context += f"\n\nPrevious test failures to fix:\n{state['test_results']}"
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["coder"]),
        HumanMessage(content=context),
    ]
    response = await llm.ainvoke(messages)
    return {**state, "code": response.content}


@trace_observe(name="review_node")
async def review_node(state: AgentState) -> AgentState:
    content = state.get("code") or state.get("plan") or state["task"]
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["reviewer"]),
        HumanMessage(content=content),
    ]
    response = await llm_precise.ainvoke(messages)
    return {**state, "review": response.content}


@trace_observe(name="test_node")
async def test_node(state: AgentState) -> AgentState:
    """
    Generates pytest tests for the code, then ACTUALLY RUNS them.
    This is ground-truth validation, not LLM opinion.
    """
    code = state.get("code", "")
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["tester"]),
        HumanMessage(content=f"Code to test:\n{code}"),
    ]
    response = await llm.ainvoke(messages)
    test_code = response.content

    result = run_generated_tests(code, test_code)
    test_summary = f"PASSED: {result['passed']}\n\n{result['output']}"

    return {**state, "tests": test_code, "test_results": test_summary}


@trace_observe(name="reflexion_node")
async def reflexion_node(state: AgentState) -> AgentState:
    # if real tests ran and failed, that's ground truth — trust it over LLM opinion
    if state.get("test_results") and "PASSED: False" in state["test_results"]:
        should_retry = state["iterations"] < 2
        critique_text = f"Tests failed:\n{state['test_results']}"
        return {
            **state,
            "critique": critique_text,
            "should_retry": should_retry,
            "iterations": state["iterations"] + 1,
        }

    output = state.get("code") or state.get("plan") or ""
    messages = [
        SystemMessage(content="""You are a self-critique system.
Evaluate the output quality. Respond ONLY with JSON:
{"quality": "good|needs_improvement", "issues": [...], "should_retry": true|false}"""),
        HumanMessage(content=f"Output to evaluate:\n{output}"),
    ]
    response = await llm_precise.ainvoke(messages)

    try:
        raw = response.content
        start = raw.find("{")
        end = raw.rfind("}") + 1
        critique_data = json.loads(raw[start:end])
        should_retry = critique_data.get("should_retry", False)
        critique_text = str(critique_data)
    except Exception:
        should_retry = False
        critique_text = response.content

    if state["iterations"] >= 2:
        should_retry = False

    return {**state, "critique": critique_text, "should_retry": should_retry, "iterations": state["iterations"] + 1}


@trace_observe(name="finalize_node")
async def finalize_node(state: AgentState) -> AgentState:
    parts = []
    if state.get("plan"):
        parts.append(f"## Plan\n{state['plan']}")
    if state.get("code"):
        parts.append(f"## Code\n{state['code']}")
    if state.get("review"):
        parts.append(f"## Review\n{state['review']}")
    if state.get("tests"):
        parts.append(f"## Tests\n{state['tests']}")
    if state.get("test_results"):
        parts.append(f"## Test Results\n{state['test_results']}")
    if state.get("critique"):
        parts.append(f"## Self-Critique\n{state['critique']}")
    return {**state, "final_output": "\n\n---\n\n".join(parts)}