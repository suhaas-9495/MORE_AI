import asyncio
import httpx

async def call_agent(task: str, agent_type: str):
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(
            "http://localhost:8000/agent/run",
            json={"task": task, "agent_type": agent_type},
        )
        data = r.json()
        print(f"\n[{agent_type.upper()}]")
        print(f"Full response: {data}")  # ← See what you actually get
        if 'output' in data:
            print(f"Output: {data['output'][:200]}...")
        else:
            print(f"Error or unexpected response structure")

async def main():
    await asyncio.gather(
        call_agent("Build a REST API for user authentication", "planner"),
        call_agent("Write a Python function to hash passwords", "coder"),
        call_agent("Review: using md5 for password hashing", "reviewer"),
    )

asyncio.run(main())