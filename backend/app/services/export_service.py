"""CSV / XLSX export (PDF deferred to R4.6 — openpyxl optional, KI-005)."""

from __future__ import annotations

import io

import pandas as pd

from backend.app.core.exceptions import ExporterUnavailableError


def _to_csv(frame: pd.DataFrame) -> tuple[bytes, str, str]:
    return frame.to_csv(index=False).encode("utf-8"), "text/csv", "csv"


def _to_xlsx(frame: pd.DataFrame, sheet: str) -> tuple[bytes, str, str]:
    try:
        import openpyxl  # noqa: F401
    except ImportError as exc:
        raise ExporterUnavailableError("XLSX export needs the 'openpyxl' extra (pip install '.[export]')") from exc
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        frame.to_excel(writer, index=False, sheet_name=sheet[:31])
    return (
        buf.getvalue(),
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "xlsx",
    )


def export_frame(frame: pd.DataFrame, fmt: str, *, sheet: str = "data") -> tuple[bytes, str, str]:
    """Return (payload, media_type, extension)."""
    if fmt == "csv":
        return _to_csv(frame)
    if fmt == "xlsx":
        return _to_xlsx(frame, sheet)
    raise ExporterUnavailableError(f"unsupported export format '{fmt}' (csv|xlsx)")


def predictions_frame(rows: list[dict]) -> pd.DataFrame:
    cols = [
        "date", "day", "horizon", "predicted_price", "lower_bound", "upper_bound",
        "expected_change", "expected_change_pct", "confidence",
    ]
    df = pd.DataFrame(rows)
    return df[[c for c in cols if c in df.columns]]
