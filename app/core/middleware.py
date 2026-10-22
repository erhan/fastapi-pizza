from collections.abc import Awaitable, Callable
from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """Adds an `X-Process-Time` header: how long the kitchen took."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        started_at = perf_counter()
        response = await call_next(request)
        elapsed_ms = (perf_counter() - started_at) * 1000
        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"
        return response
