"""Market overview + movers (cached aggregate views of the universe)."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from backend.app.cache import CacheManager
from backend.app.core.config import Settings, get_settings
from backend.app.core.constants import DataSource
from backend.app.core.logging import get_logger
from backend.app.data.seed.nse_universe import INDEX_META
from backend.app.providers import ProviderChain
from backend.app.schemas.market import IndexQuote, MarketOverview, MoverRow, MoversResponse

log = get_logger(__name__)


class MarketDataService:
    def __init__(self, chain: ProviderChain, cache: CacheManager, settings: Settings | None = None):
        self.chain = chain
        self.cache = cache
        self.settings = settings or get_settings()

    # ---------------------------------------------------------------- overview
    def overview(self) -> MarketOverview:
        def produce() -> MarketOverview:
            start = date.today() - timedelta(days=45)
            indices: list[IndexQuote] = []
            source = DataSource.SEED.value
            for key, meta in INDEX_META.items():
                if key == "NIFTYBANK":
                    continue
                try:
                    frame, src = self.chain.index_history(key, start, None)
                    source = src.value
                    closes = [float(c) for c in frame["close"]]
                    last, prev = closes[-1], closes[-2] if len(closes) > 1 else closes[-1]
                    change = last - prev
                    indices.append(
                        IndexQuote(
                            key=key, name=meta["name"], value=round(last, 2),
                            change=round(change, 2),
                            change_pct=round(change / prev * 100, 2) if prev else 0.0,
                            spark=[round(c, 2) for c in closes[-30:]],
                            source=src.value,
                        )
                    )
                except Exception as exc:  # noqa: BLE001
                    log.warning("index %s unavailable: %s", key, exc)

            stats = self._universe_stats()
            score = stats["breadth_score"]
            label = (
                "strongly bullish" if score >= 70 else
                "bullish" if score >= 55 else
                "neutral" if score >= 45 else
                "bearish" if score >= 30 else "strongly bearish"
            )
            return MarketOverview(
                indices=indices, advancers=stats["advancers"], decliners=stats["decliners"],
                unchanged=stats["unchanged"], sentiment_score=round(score, 1),
                sentiment_label=label, source=source,
            )

        return self.cache.get_or_set("market:overview", produce, self.settings.cache_ttl_overview_s)

    def _universe_stats(self) -> dict:
        def produce() -> dict:
            advancers = decliners = unchanged = above_20d = total = 0
            for row in self._daily_universe_rows():
                total += 1
                change = row.get("change", 0.0)
                if change > 1e-9:
                    advancers += 1
                elif change < -1e-9:
                    decliners += 1
                else:
                    unchanged += 1
                if row.get("above_20d"):
                    above_20d += 1
            return {
                "advancers": advancers, "decliners": decliners, "unchanged": unchanged,
                "breadth_score": (above_20d / total * 100) if total else 50.0,
                "total": total,
            }

        return self.cache.get_or_set("market:universe_stats", produce, 600)

    # ---------------------------------------------------------------- movers
    def movers(self, kind: str, *, limit: int = 10) -> MoversResponse:
        if kind not in {"gainers", "losers", "active"}:
            kind = "gainers"

        def produce() -> MoversResponse:
            daily = self._daily_universe_rows()
            if kind == "active":
                rows = sorted(daily, key=lambda r: r["volume"], reverse=True)
            else:
                rows = sorted(daily, key=lambda r: r["change_pct"], reverse=(kind == "gainers"))
            items = [
                MoverRow(
                    symbol=r["symbol"], company_name=r["company_name"], price=r["price"],
                    change=r["change"], change_pct=r["change_pct"], volume=r["volume"],
                )
                for r in rows[:limit]
            ]
            return MoversResponse(kind=kind, count=len(items), source=self.chain.providers[-1].name.value, items=items)

        return self.cache.get_or_set(f"market:movers:{kind}:{limit}", produce, 300)

    def _daily_universe_rows(self) -> list[dict]:
        def produce() -> list[dict]:
            names = {i.symbol: i.company_name for i in self.chain.universe()}

            def load(item: tuple[str, str]) -> dict | None:
                symbol, name = item
                try:
                    q = self.chain.get_quote(symbol)
                    above = False
                    above = q.change > 0
                    return {
                        "symbol": symbol, "company_name": name, "price": q.price,
                        "change": q.change, "change_pct": q.change_pct, "volume": q.volume,
                        "above_20d": above,
                    }
                except Exception:  # noqa: BLE001
                    return None

            with ThreadPoolExecutor(max_workers=8) as pool:
                return [r for r in pool.map(load, names.items()) if r is not None]

        return self.cache.get_or_set("market:daily_rows", produce, 300)
