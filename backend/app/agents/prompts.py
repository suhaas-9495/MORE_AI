from backend.app.agents.prompt_loader import get_system_prompt

# dynamically loaded from YAML files — version controlled
AGENT_SYSTEM_PROMPTS = {
    agent_type: get_system_prompt(agent_type)
    for agent_type in ["planner", "coder", "reviewer", "tester", "researcher", "documenter"]
}