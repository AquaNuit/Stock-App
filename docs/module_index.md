# Module Index — StockSense AI

> Status: v1.1 · Last updated: 2026-07-19
> One row per module; keep this synchronized when files move. "Owner" = the agent-role responsible.

## backend/app

| Path | Purpose | Key exports | Depends on | Tests |
|---|---|---|---|---|
| `core/config.py` | env settings | `Settings, get_settings` | pydantic-settings | unit |
| `core/logging.py` | logging setup | `configure_logging` | core.config | — |
| `core/constants.py` | ranges/horizon/enums | `TimeRange, HORIZON_DAYS` | — | unit |
| `database/base.py` | declarative base | `Base` | sqlalchemy | — |
| `database/session.py` | engine + session | `get_engine, SessionLocal, init_db` | core.config | integration |
| `database/models/*.py` | 8 ORM models | see database_schema.md | database.base | integration |
| `repositories/base.py` | generic CRUD | `Repository[T]` | database | unit |
| `repositories/stocks.py` | universe + upsert | `StockRepository` | repos.base | integration |
| `repositories/prices.py` | OHLCV upsert/query | `PriceRepository` | repos.base | integration |
| `repositories/predictions.py` | forecast CRUD | `PredictionRepository` | repos.base | integration |
| `repositories/models_repo.py` | model versions + runs | `ModelRepository, TrainingRunRepository` | repos.base | integration |
| `repositories/watchlist.py` | users/lists/items/searches | `WatchlistRepository, UserRepository, SearchRepository` | repos.base | integration |
| `schemas/*.py` | API DTOs | see api_reference.md | pydantic | unit |
| `providers/base.py` | provider contract | `MarketDataProvider, SymbolInfo, Quote` | pandas | unit |
| `providers/yfinance_provider.py` | Yahoo fallback provider | `YFinanceProvider` | yfinance | unit(mocked) |
| `providers/nse_provider.py` | NSE/nsepython/nselib provider | `NSEProvider` | httpx (+optional libs) | unit(mocked) |
| `providers/seed_provider.py` | deterministic offline data | `SeedDataProvider, NSE_UNIVERSE` | numpy/pandas | unit |
| `providers/chain.py` | ordered fallback + search | `ProviderChain` | providers.*, cache | integration |
| `cache/manager.py` | L1 TTL / L2 redis | `CacheManager` | core.config | unit |
| `services/market_data.py` | overview/movers/indices | `MarketDataService` | providers, repos | integration |
| `services/stock_service.py` | search/detail/history/read-through | `StockService` | providers, repos | integration |
| `services/prediction_service.py` | train/forecast/persist | `PredictionService` | ml.*, repos | integration |
| `services/insights_service.py` | narrative AI insights | `InsightsService` | providers, ml.features | unit |
| `services/watchlist_service.py` | user features | `WatchlistService` | repos | integration |
| `services/export_service.py` | CSV/XLSX | `ExportService` | pandas/openpyxl | unit |
| `ml/data/preprocessing.py` | cleaning/reindex | `clean_ohlcv` | pandas | unit |
| `ml/features/technical_indicators.py` | indicator set | `add_technical_indicators` | pandas/numpy | unit |
| `ml/features/engineering.py` | lags/rolling/calendar | `build_feature_matrix` | features | unit |
| `ml/models/base.py` | forecaster contract | `BaseForecaster, DayForecast, ModelMetrics` | — | unit |
| `ml/models/registry.py` | guarded model zoo | `ModelRegistry` | models.* | unit |
| `ml/models/direct.py` | linear/RF/XGB/LGBM | `DirectForecaster` | sklearn | unit |
| `ml/models/arima.py` | ARIMA wrapper | `ARIMAForecaster` | statsmodels | unit |
| `ml/models/prophet_model.py` | Prophet wrapper | `ProphetForecaster` | prophet(opt) | — |
| `ml/models/lstm.py` | LSTM/GRU wrapper | `LSTMForecaster` | torch(opt) | — |
| `ml/evaluation/metrics.py` | RMSE/MAE/MAPE/R² | `regression_metrics` | numpy | unit |
| `ml/training/pipeline.py` | compare/select/refit | `TrainingPipeline, TrainingResult` | ml.* | integration |
| `ml/prediction/forecaster.py` | 7-day output + CI | `Forecaster` | ml.models | unit |
| `scheduler/jobs.py` | refresh/retrain jobs | `start_scheduler` | services | — |
| `api/deps.py` | DI composition root | `get_*` providers | all services | — |
| `api/middleware.py` | request-id, timing, rate limit | middlewares | core.config | api |
| `api/errors.py` | domain→HTTP mapping | handlers | — | api |
| `api/v1/router.py` | route aggregation | `api_router` | routes.* | api |
| `api/v1/routes/*.py` | resource endpoints | see api_reference.md | schemas, services | api |
| `data/seed/nse_universe.py` | curated universe (130 symbols) | `NSE_UNIVERSE` | — | unit |
| `main.py` | app factory + lifespan | `create_app, app` | api.* | api |

## scripts / frontend / tests

| Path | Purpose |
|---|---|
| `backend/scripts/seed_db.py` | seed universe + bulk history into DB |
| `backend/scripts/demo_train.py` | end-to-end CLI demo |
| `backend/tests/unit` | indicators, metrics, providers, features, interval widths |
| `backend/tests/integration` | repos, provider chain, prediction service |
| `backend/tests/api` | full FastAPI TestClient flows incl. train→predict→export→watchlist |
| `frontend/src` | React SPA (pages: Dashboard, StockDetail, Watchlist; design system in `styles/`) |
