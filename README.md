# StockSense AI

StockSense AI is a React + FastAPI application for NSE stock analysis and seven-business-day forecasts. It includes an offline seed-data fallback, so it can be run locally without market-data credentials.

> **Forecasts are informational/demo output, not investment advice.**

## Run locally on Linux

### Prerequisites

Install Python **3.11 or newer**, Node.js **18.18 or newer** (Node 20 LTS recommended), npm, and Git. On Ubuntu/Debian:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv python3-pip
```

Clone the repository and enter it:

```bash
git clone https://github.com/AquaNuit/Stock-App.git
cd Stock-App
```

### Backend

Create the local configuration, virtual environment, and install **all runtime ML dependencies**:

```bash
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

`prophet`, `torch`, XGBoost, and LightGBM are included in the normal project dependencies. This prevents the missing-optional-dependency notices shown by older installs. Installation may take a while because PyTorch and Prophet are large packages.

Start the API from the repository root:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

The API and interactive documentation are now available at:

- `http://127.0.0.1:8000/api/v1/health`
- `http://127.0.0.1:8000/docs`

### Frontend

In another terminal:

```bash
cd Stock-App/frontend
npm ci
npm run dev
```

Open `http://localhost:5173`. In development, Vite automatically forwards `/api` requests to the backend at port 8000; leave `VITE_API_BASE` blank.

## Low-memory / Hugging Face Spaces configuration

The default configuration is intentionally conservative for a 1 GB Space:

- automatic forecasts compare only `linear` and a compact `random_forest`;
- tree models use one CPU worker and small estimator counts;
- the training window is capped at the latest 750 market sessions;
- only one training run can execute at a time.

The heavy models are installed and can still be selected explicitly in the Forecast Studio, but they are not part of the automatic model zoo. In particular, do not select `lstm` or `prophet` on a 1 GB CPU Space unless you have verified the available memory.

These settings are in `.env` and can be adjusted:

```dotenv
MAX_CONCURRENT_TRAINS=1
ML_MAX_TRAINING_ROWS=750
ML_DEFAULT_MODELS=linear,random_forest
```

For the fastest forecast, choose only `linear` in Forecast Studio. Forecasts are saved for the current day; repeated non-forced requests reuse the saved result instead of retraining.

## Useful commands

```bash
make test             # backend tests
make lint             # Python linting
make typecheck        # backend type checks
make frontend-build   # type-check and production-build the frontend
make demo             # train a demonstration forecast
```

## Environment variables

See `.env.example` for all supported settings. The default database is SQLite (`stocksense.db`) and `SEED_FALLBACK=true` keeps the app usable if NSE or Yahoo Finance is unavailable.
