from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.app.routers import agent, auth, rag, eval, registry
from backend.app.models.schemas import HealthResponse
from backend.app.core.config import settings
from backend.app.core.observability import get_langfuse_client
from backend.app.registry.startup import register_all
from backend.app.mcp_server.server import get_mcp_server


@asynccontextmanager
async def lifespan(app: FastAPI):
    register_all()
    get_mcp_server()
    yield
    # flush pending traces before shutdown — don't lose telemetry
    get_langfuse_client().flush()


app = FastAPI(
    title="MoreAI",
    description="Multi-Agent SDLC Automation Platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(agent.router)
app.include_router(rag.router)
app.include_router(eval.router)
app.include_router(registry.router)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse(status="ok", app=settings.app_name, env=settings.env)