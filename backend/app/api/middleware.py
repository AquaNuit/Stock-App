"""HTTP middleware: request-id, timing, sliding-window rate limiting."""

from __future__ import annotations

import threading
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from backend.app.core.config import Settings
from backend.app.core.logging import reset_request_id, set_request_id


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        rid = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        token = set_request_id(rid)
        try:
            response = await call_next(request)
        finally:
            reset_request_id(token)
        response.headers["X-Request-ID"] = rid
        return response


class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Process-Time-Ms"] = f"{(time.perf_counter() - start) * 1000:.1f}"
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory sliding-window per-client limiter (per-process; KI-006 for replicas)."""

    def __init__(self, app, settings: Settings):  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.limit = settings.rate_limit_per_minute
        self.window_s = 60.0
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _key(self, request: Request) -> str:
        return request.client.host if request.client else "anonymous"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if self.limit <= 0 or request.url.path in ("/api/v1/health",):
            return await call_next(request)
        now = time.monotonic()
        key = self._key(request)
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window_s:
                hits.popleft()
            if len(hits) >= self.limit:
                retry = int(self.window_s - (now - hits[0])) + 1
                return Response(
                    content='{"detail":"rate limit exceeded","code":"RATE_LIMITED"}',
                    status_code=429,
                    media_type="application/json",
                    headers={"Retry-After": str(retry)},
                )
            hits.append(now)
        return await call_next(request)
