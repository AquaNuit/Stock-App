"""Repository layer against a real (temp) SQLite DB."""

from __future__ import annotations

from datetime import date

from backend.app.database.models import Model, Prediction
from backend.app.providers.seed_provider import generate_series
from backend.app.repositories import (
    ModelRepository,
    PredictionRepository,
    PriceRepository,
    SearchRepository,
    StockRepository,
    TrainingRunRepository,
    UserRepository,
    WatchlistRepository,
)


def test_stock_upsert_and_ranked_search(session):
    stocks = StockRepository(session)
    stocks.upsert(symbol="ZZTOP", company_name="ZZ Top Industries", sector="Materials", industry="Paper")
    rest = stocks.by_symbol("ZZTOP")
    assert rest is not None and rest.company_name == "ZZ Top Industries"
    rest2 = stocks.upsert(symbol="ZZTOP", pe_ratio=12.5)
    assert rest2.id == rest.id and rest2.pe_ratio == 12.5  # upsert not insert

    hits = stocks.search("reliance")
    assert hits and hits[0].symbol == "RELIANCE"
    hits = stocks.search("bank")
    assert any(s.symbol == "HDFCBANK" for s in hits)
    assert stocks.search("") == []


def test_price_bulk_upsert_idempotent(session):
    stocks = StockRepository(session)
    stock = stocks.upsert(symbol="IDEM", company_name="Idempotent Ltd")
    prices = PriceRepository(session)
    frame = generate_series("RELIANCE").tail(60)
    n1 = prices.bulk_upsert(stock.id, frame, source="seed")
    n2 = prices.bulk_upsert(stock.id, frame, source="seed")  # same data again
    assert n1 == n2 == 60
    assert prices.count_for(stock.id) == 60  # unique constraint, no dupes
    out = prices.to_frame(stock.id)
    assert len(out) == 60 and list(out.columns) == ["date", "open", "high", "low", "close", "adj_close", "volume"]
    assert prices.latest_date(stock.id) == date.today() or prices.latest_date(stock.id) is not None


def test_prediction_and_models_repos(session):
    stocks = StockRepository(session)
    stock = stocks.upsert(symbol="PRED", company_name="Predictable Ltd")
    runs = TrainingRunRepository(session)
    models = ModelRepository(session)
    preds = PredictionRepository(session)

    run = runs.create_run(stock_id=stock.id, trigger_type="manual", data_range="2y")
    model = models.add(Model(name="linear", version="v:PRED:linear:test", stock_id=stock.id, rmse=9.9))
    run.model_id = model.id
    run.status = "success"
    rows = [
        Prediction(
            stock_id=stock.id, training_run_id=run.id, prediction_date=date.today(),
            target_date=date.today(), horizon=h, predicted_price=100 + h,
            lower_bound=95 + h, upper_bound=105 + h, model_name="linear",
        )
        for h in range(1, 8)
    ]
    preds.save_batch(rows)
    batch = preds.latest_batch(stock.id)
    assert len(batch) == 7 and batch[0].horizon == 1
    assert len(preds.history(stock.id, limit=2)) == 7  # only one batch exists; limit caps batches×horizons
    assert models.by_version("v:PRED:linear:test").rmse == 9.9


def test_watchlist_and_search_history(session):
    stocks = StockRepository(session)
    stock = stocks.upsert(symbol="WL", company_name="Watch Me Ltd")
    users = UserRepository(session)
    wls = WatchlistRepository(session)
    searches = SearchRepository(session)

    user = users.get_or_create("agent-tester")
    assert users.get_or_create("agent-tester").id == user.id  # idempotent
    wl = wls.default_list_for(user)
    assert wls.add_symbol(wl, stock) is True
    assert wls.add_symbol(wl, stock) is False  # dup guard
    assert [s.symbol for s in wls.items(wl)] == ["WL"]
    assert wls.remove_symbol(wl, stock) is True
    assert wls.remove_symbol(wl, stock) is False

    searches.record(user, "reliance", "RELIANCE")
    searches.record(user, "tcs", "TCS")
    recent = searches.recent(user, limit=5)
    assert recent[0].query == "tcs"
