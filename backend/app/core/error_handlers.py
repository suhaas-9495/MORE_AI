import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("moreai")


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom 422 handler — returns clean error messages.
    Default FastAPI validation errors are verbose and expose internals.
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " → ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        })

    logger.warning(f"Validation error on {request.url.path}: {errors}")

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "status": "validation_error",
            "detail": errors,
            "path": str(request.url.path),
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Custom HTTP exception handler — consistent error format."""
    logger.warning(
        f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}"
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "code": exc.status_code,
            "detail": exc.detail,
            "path": str(request.url.path),
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    """
    Catch-all for unhandled exceptions.
    Never expose stack traces to clients in production.
    """
    logger.error(
        f"Unhandled exception on {request.url.path}: {exc}",
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": 500,
            "detail": "Internal server error",
            "path": str(request.url.path),
        },
    )