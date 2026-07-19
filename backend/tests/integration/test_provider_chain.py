"""Provider chain: fall-through, circuit breaker, cache hit provenance."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from backend.app.cache import CacheManager
from backend.app.core.constants import DataSource
from backend.app.providers.base import MarketDataProvider, ProviderError, Quote, SymbolInfo
from backend.app.providers.chain import ProviderChain, _CircuitBreaker
from backend.app.providers.seed_provider import SeedDataProvider


class _FlakyProvider(MarketDataProvider):
    """Always fails — stands in for a dead network provider."""

    name = DataSource.NSE

    def __init__(self):
        self.calls = 0

    def list_symbols(self) -> list[SymbolInfo]:
        return []

    def get_history(self, symbol, start, end):  # type: ignore[no-untyped-def]
        self.calls += 1
        raise ProviderError("dead")

    def get_quote(self, symbol):  # type: ignore[no-untyped-def]
        self.calls += 1
        raise ProviderError("dead")


class _CountingSeed(SeedDataProvider):
    def get_history(self, symbol, start, end):  # type: ignore[no-untyped-def]
        self.calls = getattr(self, "calls", 0) + 1
        return super().get_history(symbol, start, end)


def test_fallthrough_and_breaker_opens(settings):
    flaky = _FlakyProvider()
    seed = SeedDataProvider()
    chain = ProviderChain([flaky, seed], CacheManager(settings), settings=settings)
    start = date.today() - timedelta(days=60)
    for i in range(8):  # distinct cache keys per call, so every call exercises the chain
        frame, source = chain.get_history("RELIANCE", start + timedelta(days=i), None)
        assert source == DataSource.SEED and not frame.empty
    # Breaker opens after 4 consecutive failures → later calls skip flaky entirely.
    assert flaky.calls == 4


def test_breaker_allows_after_cooldown():
    b = _CircuitBreaker(threshold=2, cooldown_s=0.0)
    b.record_failure("x")
    b.record_failure("x")
    assert b.allow()  # cooldown 0 → probe allowed
    b.record_success()
    assert b.allow()


def test_cache_hit_skips_provider(counting_seed_ctx):
    settings, seed, chain = counting_seed_ctx
    start = date.today() - timedelta(days=60)
    chain.get_history("TCS", start, None)
    calls_after_first = seed.calls
    frame, source = chain.get_history("TCS", start, None)
    assert seed.calls == calls_after_first  # served from cache
    assert not frame.empty


@pytest.fixture()
def counting_seed_ctx(settings):
    seed = _CountingSeed()
    chain = ProviderChain([seed], CacheManager(settings), settings=settings)
    return settings, seed, chain


def test_seed_only_history_and_quote(chain):
    start = date.today() - timedelta(days=120)
    frame, source = chain.get_history("HDFCBANK", start, None)
    assert source.value == "seed"
    assert list(frame.columns) == ["date", "open", "high", "low", "close", "adj_close", "volume"]
    quote = chain.get_quote("HDFCBANK")
    assert isinstance(quote, Quote) and quote.price > 0
