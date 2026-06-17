"""
Nexora AI — Rate Limiting Middleware
Redis-backed sliding window rate limiter.
Different limits per subscription tier and endpoint.
"""

import time
import json
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional, Tuple
import logging

from app.config import settings

logger = logging.getLogger("nexora.ratelimit")


# Rate limits per tier (requests per minute)
RATE_LIMITS: dict[str, dict[str, int]] = {
    "free": {
        "default": 20,
        "/api/v1/chat/stream": 10,
        "/api/v1/image": 3,
        "/api/v1/voice": 5,
        "/api/v1/agents": 2,
    },
    "pro": {
        "default": 100,
        "/api/v1/chat/stream": 60,
        "/api/v1/image": 20,
        "/api/v1/voice": 30,
        "/api/v1/agents": 15,
    },
    "team": {
        "default": 300,
        "/api/v1/chat/stream": 200,
        "/api/v1/image": 60,
        "/api/v1/voice": 100,
        "/api/v1/agents": 50,
    },
    "enterprise": {
        "default": 1000,
        "/api/v1/chat/stream": 500,
        "/api/v1/image": 200,
        "/api/v1/voice": 300,
        "/api/v1/agents": 200,
    },
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Sliding window rate limiter using Redis sorted sets.
    Exempt: /health, /api/docs, /api/redoc, static files.
    """

    EXEMPT_PATHS = {"/health", "/api/docs", "/api/redoc", "/openapi.json"}

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Skip exempt paths
        if path in self.EXEMPT_PATHS or not path.startswith("/api/"):
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)
        tier = self._get_tier(request)
        limit = self._get_limit(tier, path)
        window = 60  # 1 minute sliding window

        # Check rate limit
        allowed, remaining, reset_at = await self._check_limit(
            client_id, path, limit, window
        )

        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": f"Too many requests. Limit: {limit}/min for your tier ({tier}).",
                    "retry_after": reset_at,
                },
                headers={
                    "Retry-After": str(reset_at),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_at),
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_at)
        return response

    @staticmethod
    def _get_client_id(request: Request) -> str:
        """Extract client identifier from token or IP."""
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            # Use first 32 chars of token as ID (avoid storing full token)
            return f"token:{auth[7:39]}"
        forwarded = request.headers.get("X-Forwarded-For", "")
        ip = forwarded.split(",")[0].strip() if forwarded else request.client.host
        return f"ip:{ip}"

    @staticmethod
    def _get_tier(request: Request) -> str:
        """Get subscription tier from request state (set by auth middleware)."""
        user = getattr(request.state, "user", None)
        if user:
            return getattr(user, "subscription_tier", "free")
        return "free"

    @staticmethod
    def _get_limit(tier: str, path: str) -> int:
        tier_limits = RATE_LIMITS.get(tier, RATE_LIMITS["free"])
        # Check path-specific limit first
        for route, limit in tier_limits.items():
            if path.startswith(route) and route != "default":
                return limit
        return tier_limits.get("default", 20)

    @staticmethod
    async def _check_limit(
        client_id: str,
        path: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, int, int]:
        """
        Sliding window rate limit using Redis sorted set.
        Returns (allowed, remaining, reset_timestamp).
        """
        from app.database import get_redis

        try:
            redis = await get_redis()
            key = f"nexora:rl:{client_id}:{path[:50]}"
            now = time.time()
            window_start = now - window
            reset_at = int(now + window)

            pipe = redis.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zadd(key, {str(now): now})
            pipe.zcard(key)
            pipe.expire(key, window)
            results = await pipe.execute()

            count = results[2]
            allowed = count <= limit
            remaining = max(0, limit - count)

            return allowed, remaining, reset_at

        except Exception as e:
            logger.warning(f"Rate limit check failed (Redis error): {e}")
            return True, limit, int(time.time() + window)