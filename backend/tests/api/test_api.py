"""Full HTTP surface via FastAPI TestClient (lifespan runs: schema + universe seed)."""

from __future__ import annotations

import io
import zipfile


def test_health_and_ready(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok" and "version" in body
    r = client.get("/api/v1/ready")
    assert r.status_code == 200 and r.json()["db"] == "up"
    assert "X-Request-ID" in r.headers and "X-Process-Time-Ms" in r.headers


def test_search_ranking(client):
    r = client.get("/api/v1/stocks/search", params={"q": "reliance"})
    assert r.status_code == 200
    items = r.json()["items"]
    assert items and items[0]["symbol"] == "RELIANCE"
    r = client.get("/api/v1/stocks/search", params={"q": "information technology"})
    assert any(i["symbol"] == "TCS" for i in r.json()["items"])
    assert client.get("/api/v1/stocks/search", params={"q": ""}).status_code == 422


def test_stock_detail_and_history(client):
    d = client.get("/api/v1/stocks/TITAN").json()
    for field in ("price", "open", "high", "low", "prev_close", "volume", "pe_ratio", "week52_high"):
        assert d[field] is not None, field
    assert d["source"] == "seed"
    h = client.get("/api/v1/stocks/TITAN/history", params={"range": "6m"}).json()
    assert h["count"] > 60 and h["source"] == "seed"
    first, last = h["bars"][0], h["bars"][-1]
    assert first["date"] < last["date"] and last["close"] > 0
    assert client.get("/api/v1/stocks/NOTREAL").status_code == 404
    assert client.get("/api/v1/stocks/TITAN/history", params={"range": "9x"}).status_code == 422


def test_market_overview_and_movers(client):
    o = client.get("/api/v1/market/overview").json()
    assert len(o["indices"]) == 3
    assert 0 <= o["sentiment_score"] <= 100
    assert o["advancers"] + o["decliners"] + o["unchanged"] > 50
    g = client.get("/api/v1/market/movers", params={"kind": "gainers", "limit": 5}).json()
    losers = client.get("/api/v1/market/movers", params={"kind": "losers", "limit": 5}).json()
    a = client.get("/api/v1/market/movers", params={"kind": "active", "limit": 5}).json()
    assert g["items"][0]["change_pct"] >= g["items"][-1]["change_pct"]
    assert losers["items"][0]["change_pct"] <= losers["items"][-1]["change_pct"]
    assert a["items"][0]["volume"] >= a["items"][-1]["volume"]


def test_indicators_snapshot(client):
    ind = client.get("/api/v1/indicators/ASIANPAINT", params={"range": "1y"}).json()
    assert 0 <= (ind["rsi_14"] or 50) <= 100
    assert ind["rsi_state"] in {"overbought", "neutral", "oversold"}
    assert len(ind["series"]["dates"]) == len(ind["series"]["close"])
    assert set(ind["sma"].keys()) >= {"20", "50"}


def test_insights_narrative(client):
    ins = client.get("/api/v1/insights/DRREDDY").json()
    assert ins["trend"] in {"uptrend", "downtrend", "sideways"}
    assert ins["outlook_label"] in {"bullish", "bearish", "neutral"}
    assert 0 <= ins["outlook_score"] <= 100
    assert ins["support_resistance"]["support"] < ins["support_resistance"]["resistance"]
    assert len(ins["bullets"]) >= 4


def test_train_predict_history_models_flow(client):
    tr = client.post("/api/v1/predictions/train", json={"symbol": "MARUTI", "range": "1y", "models": ["linear"]})
    assert tr.status_code == 200, tr.text
    body = tr.json()
    assert body["best_model"] == "linear"
    assert body["leaderboard"][0]["model"] in {"linear", "naive_baseline"}
    assert "RMSE" in body["leadership_note"] or "naive" in body["leadership_note"].lower()

    fc = client.post("/api/v1/predictions/MARUTI", json={"range": "1y", "force_retrain": True})
    assert fc.status_code == 200
    forecasts = fc.json()["forecasts"]
    assert len(forecasts) == 7
    day0 = forecasts[0]
    assert day0["horizon"] == 1 and day0["lower_bound"] <= day0["predicted_price"] <= day0["upper_bound"]
    assert day0["confidence"] in {"high", "medium", "low"}

    cached = client.get("/api/v1/predictions/MARUTI", params={"range": "1y"})
    assert cached.status_code == 200 and cached.json()["cached"] is True

    hist = client.get("/api/v1/predictions/MARUTI/history").json()
    assert hist["count"] >= 7
    models = client.get("/api/v1/predictions/models/MARUTI").json()
    assert models["count"] >= 1
    assert client.get("/api/v1/predictions/models/UNKNOWN1").status_code == 404


def test_watchlist_roundtrip(client):
    headers = {"X-User-Id": "apitest"}
    w0 = client.get("/api/v1/watchlist", headers=headers).json()
    w1 = client.post("/api/v1/watchlist", json={"symbol": "NTPC"}, headers=headers)
    assert w1.status_code == 201 and w1.json()["count"] == w0["count"] + 1
    dup = client.post("/api/v1/watchlist", json={"symbol": "NTPC"}, headers=headers)
    assert dup.json()["count"] == w1.json()["count"]  # dedup
    w2 = client.delete("/api/v1/watchlist/NTPC", headers=headers)
    assert w2.json()["count"] == w0["count"]
    s = client.get("/api/v1/users/me/searches", headers={"X-User-Id": "apitest"}).json()
    assert s["count"] >= 0


def test_export_csv_and_xlsx(client):
    r = client.get("/api/v1/export/history/COALINDIA", params={"range": "3m", "format": "csv"})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    assert "date,open,high,low,close" in r.text.splitlines()[0]
    r2 = client.get("/api/v1/export/history/COALINDIA", params={"range": "3m", "format": "xlsx"})
    assert r2.status_code == 200
    z = zipfile.ZipFile(io.BytesIO(r2.content))  # xlsx is a zip — validates the payload
    assert "[Content_Types].xml" in z.namelist()
    bad = client.get("/api/v1/export/history/COALINDIA", params={"format": "pdf"})
    assert bad.status_code == 422
