"""Stock use-cases: search, details, read-through history (docs/architecture.md §7)."""

from __future__ import annotations

import hashlib
from datetime import date, timedelta

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.core.constants import DataSource, TimeRange
from backend.app.core.exceptions import SymbolNotFoundError
from backend.app.core.logging import get_logger
from backend.app.database.models import Stock
from backend.app.ml.data.preprocessing import clean_ohlcv
from backend.app.providers import ProviderChain
from backend.app.repositories import PredictionRepository, PriceRepository, StockRepository
from backend.app.schemas.stocks import HistoryBar, HistoryResponse, SearchResult, StockDetail

log = get_logger(__name__)


def derive_fundamentals(symbol: str, last_close: float) -> dict:
    """Deterministic plausible fundamentals when providers lack them (seed/offline).

    Clearly synthetic ratios — flagged via ``source`` fields upstream (KI-001).
    """
    seed = int(hashlib.sha256(f"fund::{symbol}".encode()).hexdigest()[:12], 16)
    r = (seed % 10_000) / 10_000  # 0..1
    pe = round(8 + r * 40, 2)
    eps = round(last_close / pe, 2) if pe else None
    return {
        "pe_ratio": pe,
        "eps": eps,
        "dividend_yield": round(r * 3.0, 2),
        "market_cap": round(last_close * (1e9 + (seed % 9) * 1.2e9), 0),
    }


class StockService:
    def __init__(self, session: Session, chain: ProviderChain):
        self.session = session
        self.chain = chain
        self.stocks = StockRepository(session)
        self.prices = PriceRepository(session)

    # ---------------------------------------------------------------- search
    def search(self, query: str, *, limit: int = 10) -> list[SearchResult]:
        rows = self.stocks.search(query, limit=limit)
        if len(rows) < limit:
            known = {s.symbol.upper() for s in rows}
            for info in self.chain.universe():
                q = query.strip().upper()
                if (
                    q in info.symbol.upper()
                    or q in info.company_name.upper()
                    or q in info.sector.upper()
                    or q in info.industry.upper()
                ) and info.symbol.upper() not in known:
                    rows.append(
                        Stock(
                            symbol=info.symbol, company_name=info.company_name,
                            sector=info.sector, industry=info.industry, exchange=info.exchange,
                        )
                    )
                if len(rows) >= limit:
                    break
        out: list[SearchResult] = []
        q = query.strip().upper()
        for s in rows[:limit]:
            field = "symbol" if q in s.symbol.upper() else (
                "name" if q in s.company_name.upper() else "sector"
            )
            out.append(
                SearchResult(
                    symbol=s.symbol, company_name=s.company_name,
                    sector=s.sector or "", industry=s.industry or "", match_field=field,
                )
            )
        return out

    # ---------------------------------------------------------------- universe
    def ensure_universe_seeded(self) -> int:
        """Idempotent: insert any universe symbols missing from the DB."""
        added = 0
        for info in self.chain.universe():
            if self.stocks.by_symbol(info.symbol) is None:
                self.stocks.upsert(
                    symbol=info.symbol, company_name=info.company_name,
                    sector=info.sector, industry=info.industry, exchange=info.exchange,
                )
                added += 1
        if added:
            self.session.commit()
        return added

    def _require_stock(self, symbol: str) -> Stock:
        stock = self.stocks.by_symbol(symbol.upper())
        if stock is None:
            info = self.chain.known_symbol(symbol)
            if info is None:
                raise SymbolNotFoundError(f"'{symbol.upper()}' is not a known NSE symbol")
            stock = self.stocks.upsert(
                symbol=info.symbol, company_name=info.company_name,
                sector=info.sector, industry=info.industry, exchange=info.exchange,
            )
            self.session.commit()
        return stock

    # ---------------------------------------------------------------- history
    def get_history_frame(
        self, symbol: str, tr: TimeRange, *, refresh: bool = True
    ) -> tuple[pd.DataFrame, DataSource]:
        """Read-through: DB → provider on miss/staleness → upsert → cleaned frame."""
        stock = self._require_stock(symbol)
        end = date.today()
        days = tr.calendar_days
        start = end - timedelta(days=days) if days else None

        latest = self.prices.latest_date(stock.id)
        have = self.prices.count_for(stock.id)
        stale_cutoff = end - timedelta(days=3)  # weekend/holiday tolerant
        if refresh and (latest is None or latest < stale_cutoff or (days and have < days * 0.5)):
            try:
                frame, source = self.chain.get_history(stock.symbol, start, end)
                self.prices.bulk_upsert(stock.id, frame, source=source.value)
                self.session.commit()
            except Exception as exc:  # noqa: BLE001 — DB may still have usable rows
                log.warning("provider refresh failed for %s: %s", stock.symbol, exc)

        frame = self.prices.to_frame(stock.id, start, end)
        if frame.empty:
            frame, source = self.chain.get_history(stock.symbol, start, end)
            self.prices.bulk_upsert(stock.id, frame, source=source.value)
            self.session.commit()
        source_str = self._last_source(stock.id) or DataSource.SEED.value
        return clean_ohlcv(frame, min_sessions=30), DataSource(source_str)

    def _last_source(self, stock_id: int) -> str | None:
        rows = self.prices.get_range(stock_id)
        return rows[-1].source if rows else None

    def history(self, symbol: str, range_value: str) -> HistoryResponse:
        tr = TimeRange(range_value)
        frame, source = self.get_history_frame(symbol, tr)
        bars = [
            HistoryBar(
                date=r.date, open=round(float(r.open), 2), high=round(float(r.high), 2),
                low=round(float(r.low), 2), close=round(float(r.close), 2),
                adj_close=round(float(r.adj_close), 2), volume=int(r.volume),
            )
            for r in frame.itertuples(index=False)
        ]
        closes = frame["close"]
        return HistoryResponse(
            symbol=symbol.upper(),
            range=tr.value,
            source=source.value,
            count=len(bars),
            start=bars[0].date,
            end=bars[-1].date,
            bars=bars,
            meta={
                "sma_20": round(float(closes.rolling(20).mean().iloc[-1]), 2) if len(closes) >= 20 else None,
                "period_return_pct": round(
                    (float(closes.iloc[-1]) / float(closes.iloc[0]) - 1) * 100, 2
                ),
                "week52_high": round(float(frame["high"].tail(252).max()), 2),
                "week52_low": round(float(frame["low"].tail(252).min()), 2),
            },
        )

    # ---------------------------------------------------------------- details
    def details(self, symbol: str) -> StockDetail:
        stock = self._require_stock(symbol)
        quote = self.chain.get_quote(stock.symbol)
        # Fundamentals: DB → deterministic derivation (offline completeness).
        if stock.pe_ratio is None or stock.week52_high is None:
            derived = derive_fundamentals(stock.symbol, quote.price)
            frame = self.prices.to_frame(stock.id)
            w52_high = float(frame["high"].tail(252).max()) if len(frame) else None
            w52_low = float(frame["low"].tail(252).min()) if len(frame) else None
            self.stocks.upsert(
                symbol=stock.symbol,
                pe_ratio=stock.pe_ratio or derived["pe_ratio"],
                eps=stock.eps or derived["eps"],
                dividend_yield=stock.dividend_yield or derived["dividend_yield"],
                market_cap=stock.market_cap or derived["market_cap"],
                week52_high=w52_high,
                week52_low=w52_low,
            )
            self.session.commit()
            stock = self.stocks.by_symbol(stock.symbol)  # refresh

        return StockDetail(
            symbol=stock.symbol,
            company_name=stock.company_name,
            sector=stock.sector or "",
            industry=stock.industry or "",
            exchange=stock.exchange,
            price=quote.price,
            open=quote.open,
            high=quote.high,
            low=quote.low,
            prev_close=quote.prev_close,
            change=quote.change,
            change_pct=quote.change_pct,
            volume=quote.volume,
            as_of=quote.as_of,
            source=quote.source.value,
            market_cap=stock.market_cap,
            pe_ratio=stock.pe_ratio,
            eps=stock.eps,
            dividend_yield=stock.dividend_yield,
            week52_high=stock.week52_high,
            week52_low=stock.week52_low,
        )

    # ---------------------------------------------------------------- misc
    def latest_forecast_map(self) -> dict[str, float]:
        """symbol → mean expected 7d change pct of its latest prediction batch."""
        out: dict[str, float] = {}
        repo = PredictionRepository(self.session)
        for stock in self.stocks.list_all(limit=1000):
            batch = repo.latest_batch(stock.id)
            if batch:
                out[stock.symbol] = round(sum(p.expected_change_pct for p in batch) / len(batch), 2)
        return out
