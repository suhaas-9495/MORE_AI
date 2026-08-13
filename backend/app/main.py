import logging
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
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
from backend.app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from backend.app.core.error_handlers import (
    validation_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from backend.app.core.logging_config import setup_logging
from backend.app.registry.startup import register_all
from backend.app.mlflow_tracking.tracker import setup_mlflow

logger = logging.getLogger("moreai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    # validate environment on startup
    from backend.app.core.startup_checks import validate_environment
    if not validate_environment(settings):
        logger.critical("Startup validation failed — check your .env file")
        sys.exit(1)

    register_all()
    setup_mlflow()
    logger.info(f"MoreAI started — env={settings.env} version=0.1.0")
    yield
    logger.info("MoreAI shutting down")
    flush()


app = FastAPI(
    title="MoreAI",
    description="Multi-Agent SDLC Automation Platform",
    version="0.1.0",
    lifespan=lifespan,
    # hide docs in production
    docs_url="/docs" if settings.env != "production" else None,
    redoc_url="/redoc" if settings.env != "production" else None,
)

# ── Middleware (order matters — outermost first) ──────────────────
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Rate limiting ─────────────────────────────────────────────────
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"status": "error", "code": 429, "detail": "Rate limit exceeded."},
    )


# ── Error handlers ────────────────────────────────────────────────
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── Routers ───────────────────────────────────────────────────────
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
    return HealthResponse(
        status="ok",
        app=settings.app_name,
        env=settings.env,
    )


@app.get("/", include_in_schema=False)
def root():
    return {
        "app": "MoreAI",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }