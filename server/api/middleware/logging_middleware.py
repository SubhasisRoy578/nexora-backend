"""
Nexora AI — Request Logging Middleware
Structured logging for every request: method, path, status, duration.
"""

import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
import logging

logger = logging.getLogger("nexora.http")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Logs all HTTP requests with timing and request IDs."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        start = time.perf_counter()

        # Attach request ID to state
        request.state.request_id = request_id

        # Skip health checks
        if request.url.path == "/health":
            return await call_next(request)

        logger.info(
            f"→ [{request_id}] {request.method} {request.url.path}"
        )

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start) * 1000

            logger.info(
                f"← [{request_id}] {response.status_code} "
                f"{request.url.path} {duration_ms:.1f}ms"
            )

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000
            logger.error(
                f"✗ [{request_id}] ERROR {request.url.path} "
                f"{duration_ms:.1f}ms — {exc}",
                exc_info=True,
            )
            raise