"""Seed provider: determinism, OHLC invariants, calendar, index baskets."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np

from backend.app.providers.seed_provider import SeedDataProvider, generate_series


def test_series_is_deterministic():
    a = generate_series("RELIANCE")
    b = generate_series("RELIANCE")
    assert a.equals(b)
    c = generate_series("TCS")
    assert not np.isclose(a["close"].iloc[-1], c["close"].iloc[-1])


def test_ohlc_invariants_hold():
    df = generate_series("SBIN")
    assert (df["high"] >= df[["open", "close"]].max(axis=1) - 1e-6).all()
    assert (df["low"] <= df[["open", "close"]].min(axis=1) + 1e-6).all()
    assert (df["close"] > 0).all()
    assert (df["volume"] >= 0).all()


def test_business_day_calendar_only():
    df = generate_series("INFY")
    weekdays = {d.weekday() for d in df["date"]}
    assert weekdays <= {0, 1, 2, 3, 4}
    assert len(df) == df["date"].nunique()  # no duplicates


def test_provider_slicing_and_quote():
    sp = SeedDataProvider()
    end = date.today()
    start = end - timedelta(days=90)
    frame = sp.get_history("RELIANCE", start, end)
    assert frame["date"].min() >= start and frame["date"].max() <= end
    q = sp.get_quote("RELIANCE")
    assert q.price > 0 and q.source.value == "seed"
    assert abs(q.price - float(frame["close"].iloc[-1])) < 1e-9


def test_index_series_anchored_and_nonzero():
    sp = SeedDataProvider()
    frame = sp.get_history("NIFTY50", None, None)
    assert len(frame) > 1000
    assert 20_000 <= frame["close"].iloc[-1] <= 35_000


def test_universe_size_and_lookup():
    sp = SeedDataProvider()
    symbols = {s.symbol for s in sp.list_symbols()}
    for expected in ("RELIANCE", "TCS", "HDFCBANK", "INFY"):
        assert expected in symbols
    assert not sp.supports("NOT_A_STOCK")
