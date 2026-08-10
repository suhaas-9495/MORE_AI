"""
MoreAI SDK — basic usage examples.
Run this with the MoreAI backend running on localhost:8000.
"""
from moreai_sdk import MoreAIClient


def main():
    client = MoreAIClient(base_url="http://localhost:8000")

    # authenticate
    print("Logging in...")
    client.login("suhaas", "suhaas9495")

    # health check
    health = client.health()
    print(f"API status: {health['status']}")

    # run each agent type
    agents = ["researcher", "planner", "coder", "reviewer"]
    task = "Build a Redis-based caching layer for a FastAPI application"

    for agent_type in agents:
        print(f"\nRunning {agent_type} agent...")
        result = client.run_agent(task, agent_type=agent_type)
        print(f"  Status: {result.status}")
        print(f"  Iterations: {result.iterations}")
        print(f"  Output preview: {result.output[:150]}...")

    # eval metrics
    print("\nFetching eval metrics...")
    metrics = client.get_metrics()
    print(f"  Total runs: {metrics.total_runs}")
    print(f"  Success rate: {metrics.success_rate:.1%}")

    # registry
    tools = client.list_tools()
    agents_list = client.list_agents()
    print(f"\nRegistered tools: {len(tools)}")
    print(f"Registered agents: {len(agents_list)}")


if __name__ == "__main__":
    main()