# Database Schema — StockSense AI

> Status: v1.1 · Last updated: 2026-07-19
> ORM source of truth: `backend/app/database/models/`. Engines: SQLite (dev), PostgreSQL (prod) via `DATABASE_URL`.
> Migrations: Alembic planned (R5.5); dev uses `Base.metadata.create_all`.

## ER Diagram

```mermaid
erDiagram
  STOCKS ||--o{ HISTORICAL_PRICES : has
  STOCKS ||--o{ PREDICTIONS : forecasts
  STOCKS ||--o{ TRAINING_RUNS : trains
  STOCKS ||--o{ WATCHLIST_ITEMS : watched
  MODELS ||--o{ TRAINING_RUNS : produced_by
  USERS ||--o{ WATCHLISTS : owns
  USERS ||--o{ SEARCH_HISTORY : performs
  WATCHLISTS ||--o{ WATCHLIST_ITEMS : contains

  STOCKS {
    int id PK
    string symbol UK "NSE ticker, e.g. RELIANCE"
    string company_name
    string sector
    string industry
    string exchange "default NSE"
    string yf_symbol "derived: SYMBOL.NS"
    float market_cap
    float pe_ratio
    float eps
    float dividend_yield
    float week52_high
    float week52_low
    datetime updated_at
  }
  HISTORICAL_PRICES {
    int id PK
    int stock_id FK
    date date
    float open
    float high
    float low
    float close
    float adj_close
    bigint volume
    string source "nse|yfinance|seed"
  }
  PREDICTIONS {
    int id PK
    int stock_id FK
    int training_run_id FK
    date prediction_date "when generated"
    date target_date "day being predicted"
    int horizon "1..7"
    float predicted_price
    float lower_bound
    float upper_bound
    float expected_change_pct
    string confidence "high|medium|low"
    string model_name
    float model_rmse
    string range_used "e.g. 1y"
  }
  MODELS {
    int id PK
    string name "linear|rf|xgboost|lgbm|arima|prophet|lstm"
    string version "v:{symbol}:{name}:{utc}"
    int stock_id FK
    string status "trained|selected|retired"
    json hyperparams
    json feature_list
    float rmse
    float mae
    float mape
    float r2
    datetime trained_at
    string data_range
    int train_rows
    int val_rows
  }
  TRAINING_RUNS {
    int id PK
    int stock_id FK
    int model_id FK "winner"
    string status "running|success|failed"
    string trigger_type "manual|scheduled|auto"
    json leaderboard "per-model metrics"
    string best_model
    float best_rmse
    string data_range
    datetime started_at
    datetime finished_at
    string error
  }
  USERS {
    int id PK
    string external_id UK "header identity (MVP)"
    string display_name
    datetime created_at
  }
  WATCHLISTS {
    int id PK
    int user_id FK
    string name
    datetime created_at
  }
  WATCHLIST_ITEMS {
    int id PK
    int watchlist_id FK
    int stock_id FK
    datetime added_at
  }
  SEARCH_HISTORY {
    int id PK
    int user_id FK
    string query
    string matched_symbol
    datetime created_at
  }
```

## Indexes

| Table | Index | Purpose |
|---|---|---|
| historical_prices | UNIQUE (stock_id, date) + IX (stock_id, date DESC) | upsert + range scans |
| predictions | IX (stock_id, prediction_date DESC) | latest forecast retrieval |
| predictions | IX (stock_id, target_date, horizon) | per-day lookup |
| models | IX (stock_id, trained_at DESC), UNIQUE(version) | latest model, idempotent versioning |
| stocks | IX (symbol), FTS-friendly columns (company_name, sector, industry) | search |
| watchlist_items | UNIQUE (watchlist_id, stock_id) | dup prevention |
| search_history | IX (user_id, created_at DESC) | recents |

## Retention & Growth

- `historical_prices`: ~130 symbols × 6000 sessions (max range) ≈ 0.8 M rows seeded; growth ~130/day.
- `predictions`: 7 rows per request per symbol; pruned older than 90 days by scheduled job (roadmap).
- SQLite pragmas set on connect: `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON`.
