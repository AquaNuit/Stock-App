"""Ordered provider chain with read-through caching (ADR-0006, ADR-0007).

Order: NSE (official) → yfinance (fallback) → seed (deterministic offline).
Every fetch reports its provenance so the UI can flag cached/seed data
(docs/ui_wireframes.md §5).
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pandas as pd

from backend.app.cache import CacheManager
from backend.app.core.config import Settings, get_settings
from backend.app.core.constants import DataSource
from backend.app.core.logging import get_logger
from backend.app.providers.base import MarketDataProvider, ProviderError, Quote, SymbolInfo
from backend.app.providers.nse_provider import NSEProvider
from backend.app.providers.seed_provider import SeedDataProvider
from backend.app.providers.yfinance_provider import YFinanceProvider

log = get_logger(__name__)


class _CircuitBreaker:
    """Trip after `threshold` consecutive failures; stay open for `cooldown_s`.

    Prevents a dead upstream (e.g. blocked network) from adding latency to
    every request — after tripping, calls skip the provider until cooldown
    elapses, then a single probe is allowed.
    """

    def __init__(self, threshold: int = 4, cooldown_s: float = 300.0):
        self.threshold = threshold
        self.cooldown_s = cooldown_s
        self._failures = 0
        self._open_until = 0.0
        self._announced = False

    def allow(self) -> bool:
        import time

        if time.monotonic() < self._open_until:
            return False
        self._announced = False
        return True

    def record_success(self) -> None:
        self._failures = 0

    def record_failure(self, name: str) -> None:
        import time

        self._failures += 1
        if self._failures >= self.threshold:
            self._open_until = time.monotonic() + self.cooldown_s
            if not self._announced:
                log.warning("provider circuit OPEN for %s (cooldown %.0fs)", name, self.cooldown_s)
                self._announced = True
            self._failures = 0


def default_chain(settings: Settings | None = None, cache: CacheManager | None = None) -> ProviderChain:
    """Composition helper used by ``api.deps`` and scripts."""
    settings = settings or get_settings()
    providers: list[MarketDataProvider] = [
        # NSEProvider(timeout_s=settings.provider_timeout_s, enabled=settings.nse_enabled),
        YFinanceProvider(timeout_s=settings.provider_timeout_s),
    ]
    if settings.seed_fallback:
        providers.append(SeedDataProvider())
    return ProviderChain(providers, cache or CacheManager(settings), settings=settings)


class ProviderChain:
    def __init__(
        self,
        providers: list[MarketDataProvider],
        cache: CacheManager,
        *,
        settings: Settings | None = None,
    ):
        self.providers = providers
        self.cache = cache
        self.settings = settings or get_settings()
        # The seed provider is never broken (fully offline) — guard it.
        self._breakers = {id(p): _CircuitBreaker() for p in providers}
        self._unbreakable = {id(p) for p in providers if p.name == DataSource.SEED}

    # -- universe / discovery -----------------------------------------------
    def universe(self) -> list[SymbolInfo]:
        seen: dict[str, SymbolInfo] = {}
        for provider in reversed(self.providers):  # seed last in chain → lowest precedence wins reversed
            for info in provider.list_symbols():
                seen[info.symbol.upper()] = info
        return list(seen.values())

    def known_symbol(self, symbol: str) -> SymbolInfo | None:
        key = symbol.upper()
        return {s.symbol.upper(): s for s in self.universe()}.get(key)

    # -- history ----------------------------------------------------------------
    def get_history(
        self, symbol: str, start: date | None = None, end: date | None = None
    ) -> tuple[pd.DataFrame, DataSource]:
        symbol = symbol.upper()
        cache_key = f"hist:{symbol}:{start}:{end}"
        hit = self.cache.get(cache_key) if self.settings.cache_ttl_history_s > 0 else None
        if hit is not None:
            frame, source = hit
            return frame, DataSource(source)

        errors: list[str] = []
        for provider in self.providers:
            if not provider.supports(symbol):
                continue
            breaker = self._breakers[id(provider)]
            if id(provider) not in self._unbreakable and not breaker.allow():
                continue
            try:
                frame = provider.get_history(symbol, start, end)
            except ProviderError as exc:
                errors.append(f"{provider.name}={exc}")
                breaker.record_failure(provider.name.value)
                continue
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{provider.name}={type(exc).__name__}")
                breaker.record_failure(provider.name.value)
                log.debug("provider %s crashed on %s: %s", provider.name, symbol, exc)
                continue
            breaker.record_success()
            self.cache.set(cache_key, (frame, provider.name.value), self.settings.cache_ttl_history_s)
            return frame, provider.name
        raise ProviderError(f"no provider could serve history for {symbol} ({'; '.join(errors)})")

    # -- quotes -------------------------------------------------------------------
    def get_quote(self, symbol: str) -> Quote:
        symbol = symbol.upper()
        cache_key = f"quote:{symbol}"
        hit = self.cache.get(cache_key)
        if hit is not None:
            price, open_, high, low, prev_close, volume, as_of, source = hit
            return Quote(symbol, price, open_, high, low, prev_close, volume, as_of, DataSource(source))

        errors: list[str] = []
        for provider in self.providers:
            if not provider.supports(symbol):
                continue
            breaker = self._breakers[id(provider)]
            if id(provider) not in self._unbreakable and not breaker.allow():
                continue
            try:
                quote = provider.get_quote(symbol)
            except ProviderError as exc:
                errors.append(f"{provider.name}={exc}")
                breaker.record_failure(provider.name.value)
                continue
            except Exception as exc:  # noqa: BLE001
                errors.append(f"{provider.name}={type(exc).__name__}")
                breaker.record_failure(provider.name.value)
                continue
            breaker.record_success()
            self.cache.set(
                cache_key,
                (quote.price, quote.open, quote.high, quote.low, quote.prev_close,
                 quote.volume, quote.as_of, quote.source.value),
                self.settings.cache_ttl_quote_s,
            )
            return quote
        raise ProviderError(f"no provider could serve quote for {symbol} ({'; '.join(errors)})")

    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        pending = {s.upper() for s in symbols}
        results = {}
        for provider in self.providers:
            if not pending:
                break
            breaker = self._breakers[id(provider)]
            if id(provider) not in self._unbreakable and not breaker.allow():
                continue
            
            supported = [s for s in pending if provider.supports(s)]
            if not supported:
                continue
                
            try:
                quotes = provider.get_quotes(supported)
                for s, q in quotes.items():
                    results[s] = q
                    pending.discard(s)
                breaker.record_success()
            except Exception as exc:
                breaker.record_failure(provider.name.value)
                log.debug("provider %s bulk failed: %s", provider.name, exc)
                
        return results

    def index_history(self, index_key: str, start: date | None = None, end: date | None = None):
        return self.get_history(index_key, start, end)

    def health(self) -> dict[str, str]:
        """Best-effort liveness probe per provider (used by /ready)."""
        probe: dict[str, str] = {}
        for provider in self.providers:
            try:
                if provider.list_symbols():
                    probe[provider.name.value] = "ok(universe)"
                else:
                    probe[provider.name.value] = "idc"  # quote-only providers are probed lazily
            except Exception:  # noqa: BLE001
                probe[provider.name.value] = "error"
        probe["time"] = datetime.now(UTC).isoformat(timespec="seconds")
        return probe
