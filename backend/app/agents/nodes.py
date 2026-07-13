from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.agents.state import AgentState
from backend.app.agents.llm_client import get_llm
from backend.app.agents.prompts import AGENT_SYSTEM_PROMPTS
from backend.app.agents.test_runner import run_generated_tests
from backend.app.core.observability import trace_observe
import json

llm = get_llm()
llm_precise = get_llm(temperature=0.1)


@trace_observe(name="research_node")
async def research_node(state: AgentState) -> AgentState:
    """
    Runs BEFORE planning — gathers technical context.
    Like a senior engineer doing a spike before writing code.
    Output feeds directly into plan_node as context.
    """
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["researcher"]),
        HumanMessage(content=f"Research this task thoroughly:\n{state['task']}"),
    ]
    response = await llm.ainvoke(messages)
    return {**state, "research": response.content}


@trace_observe(name="plan_node")
async def plan_node(state: AgentState) -> AgentState:
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
    return {**state, "plan": response.content}


@trace_observe(name="code_node")
async def code_node(state: AgentState) -> AgentState:
    context = f"Research:\n{state.get('research', '')}\n\nPlan:\n{state.get('plan', '')}"
    if state.get("test_results"):
        context += f"\n\nFix these test failures:\n{state['test_results']}"
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["coder"]),
        HumanMessage(content=f"{context}\n\nTask:\n{state['task']}"),
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
    code = state.get("code", "")
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["tester"]),
        HumanMessage(content=f"Write tests for:\n{code}"),
    ]
    response = await llm.ainvoke(messages)
    test_code = response.content
    result = run_generated_tests(code, test_code)
    test_summary = f"PASSED: {result['passed']}\n\n{result['output']}"
    return {**state, "tests": test_code, "test_results": test_summary}


@trace_observe(name="documentation_node")
async def documentation_node(state: AgentState) -> AgentState:
    """
    Runs AFTER code is reviewed and tested.
    Generates production-ready documentation from the final code.
    """
    code = state.get("code", "")
    review = state.get("review", "")
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["documenter"]),
        HumanMessage(content=f"Generate documentation for this code:\n\n{code}\n\nReview notes:\n{review}"),
    ]
    response = await llm.ainvoke(messages)
    return {**state, "documentation": response.content}


@trace_observe(name="reflexion_node")
async def reflexion_node(state: AgentState) -> AgentState:
    if state.get("test_results") and "PASSED: False" in state["test_results"]:
        should_retry = state["iterations"] < 2
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
    response = await llm_precise.ainvoke(messages)

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

    return {**state, "critique": critique, "should_retry": should_retry,
            "iterations": state["iterations"] + 1}


@trace_observe(name="finalize_node")
async def finalize_node(state: AgentState) -> AgentState:
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
    return {**state, "final_output": "\n\n---\n\n".join(parts)}