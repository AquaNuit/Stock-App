"""Domain exception hierarchy.

Mapped to HTTP responses by ``api/errors.py`` (status codes documented in
docs/api_reference.md). Services/ML raise these; routers never translate
``ValueError`` themselves.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base for expected, user-facing failures."""

    code: str = "DOMAIN_ERROR"
    http_status: int = 500

    def __init__(self, message: str, *, code: str | None = None):
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class SymbolNotFoundError(DomainError):
    code = "SYMBOL_NOT_FOUND"
    http_status = 404


class ProviderUnavailableError(DomainError):
    code = "PROVIDER_UNAVAILABLE"
    http_status = 503


class InsufficientHistoryError(DomainError):
    code = "INSUFFICIENT_HISTORY"
    http_status = 409


class TrainingError(DomainError):
    code = "TRAINING_FAILED"
    http_status = 500


class NoModelAvailableError(DomainError):
    code = "NO_MODEL"
    http_status = 409


class ExporterUnavailableError(DomainError):
    code = "EXPORT_UNAVAILABLE"
    http_status = 501
