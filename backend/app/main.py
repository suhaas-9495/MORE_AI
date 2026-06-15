from fastapi import FastAPI
from backend.app.routers import agent, auth, rag
from backend.app.models.schemas import HealthResponse
from backend.app.core.config import settings

app = FastAPI(
    title="MoreAI",
    description="Multi-Agent SDLC Automation Platform",
    version="0.1.0",
)

app.include_router(auth.router)
app.include_router(agent.router)
app.include_router(rag.router)

@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(status="ok", app=settings.app_name, env=settings.env)