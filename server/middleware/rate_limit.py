from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse
import time


class RateLimitMiddleware(BaseHTTPMiddleware):

    def __init__(self, app):
        super().__init__(app)
        self.requests = {}

    async def dispatch(self, request: Request, call_next):

        client_ip = request.client.host
        current_time = time.time()

        window_time = 60
        max_requests = 100

        if client_ip not in self.requests:
            self.requests[client_ip] = []

        self.requests[client_ip] = [
            req_time
            for req_time in self.requests[client_ip]
            if current_time - req_time < window_time
        ]

        if len(self.requests[client_ip]) >= max_requests:
            return JSONResponse(
                status_code=429,
                content={"message": "Rate limit exceeded"}
            )

        self.requests[client_ip].append(current_time)

        response = await call_next(request)

        return response