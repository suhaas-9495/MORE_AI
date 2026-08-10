from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from backend.app.routers import (
    agent, auth, rag, eval, registry,
    memory, pipeline, artifacts, mlflow_router,
    prompts_router, github_router, bedrock_router
)
from backend.app.models.schemas import HealthResponse
from backend.app.core.config import settings
from backend.app.core.observability import get_langfuse_client, flush
from backend.app.core.rate_limiter import limiter
from backend.app.registry.startup import register_all
from backend.app.mlflow_tracking.tracker import setup_mlflow


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_all()
    setup_mlflow()
    yield
    flush()


app = FastAPI(
    title="MoreAI",
    description="Multi-Agent SDLC Automation Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded."})


app.include_router(auth.router)
app.include_router(agent.router)
app.include_router(rag.router)
app.include_router(eval.router)
app.include_router(registry.router)
app.include_router(memory.router)
app.include_router(pipeline.router)
app.include_router(artifacts.router)
app.include_router(mlflow_router.router)
app.include_router(prompts_router.router)
app.include_router(github_router.router)
app.include_router(bedrock_router.router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(status="ok", app=settings.app_name, env=settings.env)