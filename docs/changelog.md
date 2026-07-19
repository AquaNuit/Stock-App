# Changelog — StockSense AI

> Format: `## [version] — date`, grouped Added/Changed/Fixed/Docs. Keep newest on top.
> Every code change session appends an entry here and updates [agent_handoff.md](agent_handoff.md).

## [0.1.1] — 2026-07-19
### Added
- Added `JIOFIN` and `JIOFINANCE` (alias) equities to the seeded `NSE_UNIVERSE` so they are fully searchable, quote-retrievable, and forecastable.
- Added indices `NIFTY50`, `SENSEX`, `BANKNIFTY`, and `NIFTYBANK` (alias) to the seeded `NSE_UNIVERSE` so they are fully searchable and forecastable in the forecast studio.
- Added `NIFTYBANK` to `INDEX_META` to compute synthetic Nifty Bank indices deterministically, and mapped it inside the `YFinanceProvider` to query the real `^NSEBANK` ticker.
- Mapped `JIOFINANCE` symbol to the real `JIOFIN.NS` ticker inside `YFinanceProvider` to fetch authentic market data.

### Fixed
- Fixed "internal error" on stock detail and prediction load by returning an empty list of model versions instead of raising a 409 Conflict error when no models are trained yet (first page load), which was causing the UI/app to crash or show error toasts before any prediction was generated.
- Added `_clean_nan` safety wrappers to ensure NaN values in model metrics (such as `model_rmse`, `rmse`, `mae`, `mape`, `r2`) are always converted to `None` (JSON `null`) before being persisted or returned in API responses, eliminating potential pydantic/fastapi JSON serialization or validation failures.
- Excluded the duplicate `NIFTYBANK` index from the Market Overview grid on the home dashboard to keep the layout clean and readable.

## [0.1.0] — 2026-07-19 (bootstrap)
### Added
- Complete design documentation set: architecture (with class diagrams), database schema, ML pipeline, API reference, UI wireframes, deployment architecture, roadmap, decisions (ADRs), module index, known issues, implementation status, agent handoff protocol.
