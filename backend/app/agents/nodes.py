from langchain_core.messages import SystemMessage, HumanMessage
from backend.app.agents.state import AgentState
from backend.app.agents.llm_client import get_llm
from backend.app.agents.prompts import AGENT_SYSTEM_PROMPTS
import json

llm = get_llm()
llm_precise = get_llm(temperature=0.1)  # lower temp for critique/review


async def plan_node(state: AgentState) -> AgentState:
    """Planner node — breaks task into structured steps."""
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


async def code_node(state: AgentState) -> AgentState:
    """Coder node — writes code based on the plan."""
    context = f"Plan:\n{state.get('plan', '')}\n\nOriginal task:\n{state['task']}"
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["coder"]),
        HumanMessage(content=context),
    ]
    response = await llm.ainvoke(messages)
    return {**state, "code": response.content}


async def review_node(state: AgentState) -> AgentState:
    """Reviewer node — checks code quality."""
    content = state.get("code") or state.get("plan") or state["task"]
    messages = [
        SystemMessage(content=AGENT_SYSTEM_PROMPTS["reviewer"]),
        HumanMessage(content=content),
    ]
    response = await llm_precise.ainvoke(messages)
    return {**state, "review": response.content}


async def reflexion_node(state: AgentState) -> AgentState:
    """
    Reflexion — agent critiques its own output and decides
    whether to retry. This is the 'AGI-like' self-correction loop.
    Max 2 iterations to avoid infinite loops.
    """
    output = state.get("code") or state.get("plan") or ""
    messages = [
        SystemMessage(content="""You are a self-critique system.
Evaluate the output quality. Respond ONLY with JSON:
{"quality": "good|needs_improvement", "issues": [...], "should_retry": true|false}
Be strict. Only mark good if output is genuinely production-ready."""),
        HumanMessage(content=f"Output to evaluate:\n{output}"),
    ]
    response = await llm_precise.ainvoke(messages)

    try:
        # parse the JSON critique
        raw = response.content
        start = raw.find("{")
        end = raw.rfind("}") + 1
        critique_data = json.loads(raw[start:end])
        should_retry = critique_data.get("should_retry", False)
        critique_text = str(critique_data)
    except Exception:
        should_retry = False
        critique_text = response.content

    # never retry more than 2 times
    if state["iterations"] >= 2:
        should_retry = False

    return {
        **state,
        "critique": critique_text,
        "should_retry": should_retry,
        "iterations": state["iterations"] + 1,
    }


async def finalize_node(state: AgentState) -> AgentState:
    """Assembles final output from all nodes."""
    parts = []
    if state.get("plan"):
        parts.append(f"## Plan\n{state['plan']}")
    if state.get("code"):
        parts.append(f"## Code\n{state['code']}")
    if state.get("review"):
        parts.append(f"## Review\n{state['review']}")
    if state.get("critique"):
        parts.append(f"## Self-Critique\n{state['critique']}")

    return {**state, "final_output": "\n\n---\n\n".join(parts)}