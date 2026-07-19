"""Metrics + splitter + confidence labels."""

from __future__ import annotations

import numpy as np

from backend.app.core.constants import Confidence, confidence_from_half_width
from backend.app.ml.evaluation.metrics import regression_metrics
from backend.app.ml.training.splitter import make_split


def test_metrics_known_values():
    y = np.array([100.0, 101.0, 102.0, 103.0])
    p = np.array([100.0, 101.0, 102.0, 103.0])
    m = regression_metrics(y, p)
    assert m["rmse"] == 0 and m["mae"] == 0 and m["mape"] == 0 and m["r2"] == 1.0


def test_metrics_robust_to_nan_and_zero():
    y = np.array([0.0, np.nan, 10.0, 20.0])
    p = np.array([0.0, 5.0, 12.0, 18.0])
    m = regression_metrics(y, p)
    assert np.isfinite(m["rmse"]) and np.isfinite(m["mape"])  # ε-guarded MAPE
    assert m["rmse"] > 0


def test_r2_negative_allowed():
    m = regression_metrics(np.array([1, 2, 3, 4]), np.array([4, 3, 2, 1]))
    assert m["r2"] < 0


def test_split_bounds():
    s = make_split(500)
    assert s.n == 500
    assert 12 <= s.n_val <= 30
    assert s.first_val_target == 500 - s.n_val
    assert s.fit_end <= s.first_val_target - 1
    # every tabular validation row t has its target inside the window:
    lo = s.first_val_target - 7
    assert lo >= s.fit_end - 6 - 1  # sanity on horizon alignment


def test_split_rejects_tiny():
    import pytest

    with pytest.raises(ValueError):
        make_split(40)


def test_confidence_label_thresholds():
    assert confidence_from_half_width(0.01 * 100, 100) == Confidence.HIGH
    assert confidence_from_half_width(0.03 * 100, 100) == Confidence.MEDIUM
    assert confidence_from_half_width(0.10 * 100, 100) == Confidence.LOW
    assert confidence_from_half_width(10, 0) == Confidence.LOW  # zero-price safety
