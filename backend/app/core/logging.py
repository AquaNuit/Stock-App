"""Structured-ish logging setup (docs/architecture.md §6).

Format: ``time level logger [request_id] message`` — request-id is injected by
``api.middleware.RequestIDMiddleware`` via a contextvar filter.
"""

from __future__ import annotations

import contextvars
import logging
import sys

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


def set_request_id(rid: str) -> contextvars.Token[str]:
    return _request_id.set(rid)


def reset_request_id(token: contextvars.Token[str]) -> None:
    _request_id.reset(token)


class _RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = _request_id.get()  # type: ignore[attr-defined]
        return True


_FORMAT = "%(asctime)s %(levelname)-7s %(name)s [%(request_id)s] %(message)s"
_configured = False


def configure_logging(level: str = "INFO") -> None:
    global _configured
    if _configured:
        logging.getLogger().setLevel(level)
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt="%Y-%m-%d %H:%M:%S"))
    handler.addFilter(_RequestContextFilter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    # Tame noisy third parties (network providers log loudly on expected failures;
    # the chain's circuit breaker + fallthrough handles them).
    for name in ("urllib3", "httpx", "apscheduler", "curl_cffi", "peewee"):
        logging.getLogger(name).setLevel(logging.WARNING)
    logging.getLogger("yfinance").setLevel(logging.CRITICAL)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
