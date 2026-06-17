from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
import time


class RequestLoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        process_time = time.time() - start_time

        print(
            f"{request.method} {request.url.path} "
            f"completed in {process_time:.4f} sec"
        )

        return response