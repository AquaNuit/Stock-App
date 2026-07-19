"""Exception → JSON mapping (docs/api_reference.md#error-codes)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.exceptions import DomainError
from backend.app.core.logging import get_logger
from backend.app.providers import ProviderError

log = get_logger(__name__)


def _payload(detail: str, code: str) -> dict:
    return {"detail": detail, "code": code}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(status_code=exc.http_status, content=_payload(exc.message, exc.code))

    @app.exception_handler(ProviderError)
    async def provider_handler(_: Request, exc: ProviderError) -> JSONResponse:
        return JSONResponse(status_code=503, content=_payload(str(exc), "PROVIDER_UNAVAILABLE"))

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        detail = f"{'.'.join(str(p) for p in first.get('loc', []))}: {first.get('msg', 'invalid')}"
        return JSONResponse(
            status_code=422, content={"detail": detail, "code": "VALIDATION_ERROR", "errors": exc.errors()}
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "NOT_FOUND" if exc.status_code == 404 else "HTTP_ERROR"
        return JSONResponse(status_code=exc.status_code, content=_payload(str(exc.detail), code))

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
        log.exception("unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content=_payload("internal error", "INTERNAL_ERROR"))
