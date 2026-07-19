"""Time-based train/validation split — never shuffled (docs/ml_pipeline.md §5)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class SplitSpec:
    """Indices into the *feature-complete* frame.

    For direct models the effective validation rows additionally shift by
    horizon ``h`` so that all validation targets fall inside
    ``[first_val_target, n)`` (leakage-free — pipeline.py applies this).
    """

    n: int
    fit_end: int  # exclusive end index of fit-window rows
    first_val_target: int  # first index whose close is part of the validation window
    n_val: int


def make_split(n: int, val_fraction: float = 0.15, min_val: int = 12, max_val: int = 30) -> SplitSpec:
    if n < 60:
        raise ValueError(f"not enough complete feature rows ({n}) to split")
    n_val = max(min_val, min(max_val, int(n * val_fraction)))
    first_val_target = n - n_val
    # Rows used to train horizon-h must satisfy t + h < first_val_target;
    # h=1 dominates the constraint for the shared fit window size.
    fit_end = max(30, first_val_target - 7)
    return SplitSpec(n=n, fit_end=fit_end, first_val_target=first_val_target, n_val=n_val)
