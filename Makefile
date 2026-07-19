.PHONY: install dev test lint typecheck api seed demo frontend-install frontend-dev frontend-build compose-up clean

PY ?= .venv/bin/python
PIP ?= .venv/bin/pip

install:
	python3 -m venv .venv
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

test:
	$(PY) -m pytest backend/tests -q

lint:
	$(PY) -m ruff check backend frontend 2>/dev/null || $(PY) -m ruff check backend

typecheck:
	$(PY) -m mypy backend/app

api:
	$(PY) -m uvicorn backend.app.main:app --reload --port 8000

seed:
	$(PY) -m backend.scripts.seed_db

demo:
	$(PY) -m backend.scripts.demo_train RELIANCE --range 2y

frontend-install:
	cd frontend && npm ci

frontend-dev:
	cd frontend && npm run dev

frontend-build:
	cd frontend && npm run build

compose-up:
	docker compose -f deploy/docker-compose.yml up --build

clean:
	rm -rf .venv **/__pycache__ .pytest_cache .mypy_cache .ruff_cache stocksense.db frontend/dist
