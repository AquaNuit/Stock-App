"""Stock universe persistence + ranked search (DB-backed autocomplete)."""

from __future__ import annotations

from sqlalchemy import or_, select

from backend.app.database.models import Stock
from backend.app.repositories.base import Repository


class StockRepository(Repository[Stock]):
    model = Stock

    def by_symbol(self, symbol: str) -> Stock | None:
        return self.session.scalar(select(Stock).where(Stock.symbol == symbol.upper()))

    def upsert(self, *, symbol: str, **fields) -> Stock:
        stock = self.by_symbol(symbol)
        if stock is None:
            stock = Stock(symbol=symbol.upper(), company_name=fields.pop("company_name", symbol.upper()))
            self.session.add(stock)
        for key, value in fields.items():
            if hasattr(stock, key) and value is not None:
                setattr(stock, key, value)
        self.session.flush()
        return stock

    def list_all(self, *, sector: str | None = None, limit: int = 500, offset: int = 0) -> list[Stock]:
        stmt = select(Stock).order_by(Stock.symbol).limit(limit).offset(offset)
        if sector:
            stmt = stmt.where(Stock.sector == sector)
        return list(self.session.scalars(stmt))

    def search(self, query: str, *, limit: int = 10) -> list[Stock]:
        """Ranked search: exact ticker > ticker-prefix > name substring > sector/industry."""
        q = query.strip().upper()
        if not q:
            return []
        like = f"%{q}%"
        stmt = select(Stock).where(
            or_(
                Stock.symbol.ilike(like),
                Stock.company_name.ilike(like),
                Stock.sector.ilike(like),
                Stock.industry.ilike(like),
            )
        )
        rows = list(self.session.scalars(stmt.limit(limit * 4)))

        def rank(s: Stock) -> tuple[int, str]:
            sym = s.symbol.upper()
            name = s.company_name.upper()
            if sym == q:
                return (0, sym)
            if sym.startswith(q):
                return (1, sym)
            if q in name:
                return (2, name)
            return (3, sym)

        return sorted(rows, key=rank)[:limit]

    def sectors(self) -> list[str]:
        stmt = select(Stock.sector).where(Stock.sector != "").distinct().order_by(Stock.sector)
        return list(self.session.scalars(stmt))
