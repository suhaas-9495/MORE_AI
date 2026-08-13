import time
import uuid
import logging
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from backend.app.core.audit import log_audit_event

logger = logging.getLogger("moreai")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request with timing, request ID, and status.
    Production pattern — every request traceable by request_id.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start = time.time()

        # inject request_id into request state
        request.state.request_id = request_id

        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"client={request.client.host if request.client else 'unknown'}"
        )

        try:
            response: Response = await call_next(request)
            latency = round(time.time() - start, 3)

            # add request ID to response headers — useful for debugging
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = str(latency)

            logger.info(
                f"[{request_id}] {response.status_code} "
                f"latency={latency}s path={request.url.path}"
            )
            return response

        except Exception as e:
            latency = round(time.time() - start, 3)
            logger.error(f"[{request_id}] ERROR {e} latency={latency}s")
            raise


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every response.
    These are standard production security requirements.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # XSS protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # HSTS — force HTTPS (uncomment in production with HTTPS)
        # response.headers["Strict-Transport-Security"] = "max-age=31536000"
        # prevent referrer leakage
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        # content security policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline';"
        )

        return response