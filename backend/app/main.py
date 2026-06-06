from fastapi import FastAPI
from backend.app.routers import agent
from backend.app.core.config import settings

app = FastAPI(
    title="more_ai",
    description="Multi-Agent SDLC Automation Platform",
    version="0.1.0",
)

# THIS LINE IS CRITICAL - registers the agent routes
app.include_router(agent.router)

# THIS ENDPOINT IS CRITICAL - for health check
@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name, "env": settings.env}