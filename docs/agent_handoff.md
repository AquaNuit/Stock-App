# Agent Handoff — StockSense AI

> Status: v1.0 · Last updated: 2026-07-19 · **Read this first if you are a new agent.**
> Protocol (ADR-0002): at session end update this file + [implementation_status.md](implementation_status.md) + [changelog.md](changelog.md) in the same commit.

## Current Implementation Status
Bootstrap session S1 in progress. Design docs (1–10 from brief) are complete and approved-in-writing. Backend implementation starting in roadmap order R1 → R5.

## Modules Completed
- `docs/` — all 13 documents authored.

## Files Modified This Session
- `docs/*` (all new)

## Architecture Changes
- None beyond initial design (ADRs 0001–0012 logged).

## Environment Quickstart (verified in sandbox)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest backend/tests -q
uvicorn backend.app.main:app --reload
cd frontend && npm ci && npm run dev
```

## Known Bugs
- None yet (no code shipped). See [known_issues.md](known_issues.md) for design-level caveats (KI-001…006).

## Pending Tasks (priority order)
1. R1.1–R1.6 backend core + DB + repos + providers + cache + seed script
2. R2 ML engine with tests
3. R3 API with tests
4. R4 frontend
5. R5 CI/Docker, docs sync

## Suggested Next Task
**Implement R1.1–R1.3** (`core/`, `database/`, `repositories/`) with unit/integration tests. Contracts already fixed in [database_schema.md](database_schema.md) and [module_index.md](module_index.md) — do not rename tables/columns without updating both.

## Guardrails for Agents
- Keep dependency direction (architecture §1). No SQL in services; no ML imports in API.
- Any optional import (`xgboost`, `prophet`, `torch`, `redis`, `openpyxl`) **must** be guarded; tests must pass without them installed (except xgboost/lightgbm which are in dev extras).
- Update `docs/module_index.md` when adding/renaming modules.
