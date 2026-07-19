"""LSTM/GRU seq2one forecaster — registered only when torch is installed (ADR-0008).

Kept deliberately compact: a single-layer LSTM over sliding windows of scaled
log-returns, recursive multi-step rollout. GPU-optional; CPU default.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from backend.app.core.constants import RANDOM_SEED
from backend.app.ml.models.base import BaseForecaster

WINDOW = 30
EPOCHS = 24
HIDDEN = 32


class LSTMForecaster(BaseForecaster):
    kind = "series"

    def __init__(self, horizon: int = 7, cell: str = "lstm"):
        super().__init__(horizon, params={"window": WINDOW, "hidden": HIDDEN, "epochs": EPOCHS, "cell": cell})
        self.name = "lstm"
        self._net = None
        self._window: np.ndarray | None = None
        self._last_close = 0.0

    def fit(self, features: pd.DataFrame, feature_cols: list[str], close: pd.Series) -> None:  # noqa: ARG002
        import torch
        from torch import nn

        torch.manual_seed(RANDOM_SEED)
        values = close.to_numpy(dtype="float64")
        log_ret = np.diff(np.log(values))
        mu, sigma = log_ret.mean(), log_ret.std() or 1e-6
        scaled = ((log_ret - mu) / sigma).astype("float32")
        if len(scaled) < WINDOW + 32:
            raise ValueError("insufficient history for sequence model")
        X = np.stack([scaled[i : i + WINDOW] for i in range(len(scaled) - WINDOW)])
        y = scaled[WINDOW:]
        xt = torch.from_numpy(X).unsqueeze(-1)
        yt = torch.from_numpy(y).unsqueeze(-1)

        cell_cls = nn.GRU if self.params["cell"] == "gru" else nn.LSTM

        class _Net(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.rnn = cell_cls(1, HIDDEN, batch_first=True)
                self.head = nn.Linear(HIDDEN, 1)

            def forward(self, x):  # type: ignore[no-untyped-def]
                out, _ = self.rnn(x)
                return self.head(out[:, -1])

        self._net = _Net()
        opt = torch.optim.Adam(self._net.parameters(), lr=1e-3)
        loss_fn = nn.HuberLoss()
        self._net.train()
        for _ in range(EPOCHS):
            perm = torch.randperm(len(xt))
            for i in range(0, len(xt), 64):
                idx = perm[i : i + 64]
                opt.zero_grad()
                loss = loss_fn(self._net(xt[idx]), yt[idx])
                loss.backward()
                opt.step()
        self._net.eval()
        self._window = scaled[-WINDOW:].copy()
        self._mu, self._sigma = float(mu), float(sigma)
        self._last_close = float(values[-1])

        # residual bands from last 40 one-step predictions
        with torch.no_grad():
            tail = torch.from_numpy(X[-40:]).unsqueeze(-1)
            preds = self._net(tail).squeeze(-1).numpy()
        resid = (y[-40:] - preds) * sigma * self._last_close
        if resid.size >= 8:
            scale = np.sqrt(np.arange(1, self.horizon + 1))
            self._band_lo = np.quantile(resid, 0.05) * scale
            self._band_hi = np.quantile(resid, 0.95) * scale

    def _point_forecast(self, context_row: pd.Series, steps: int) -> np.ndarray:  # noqa: ARG002
        import torch

        assert self._net is not None and self._window is not None, "model not fit"
        window = self._window.copy()
        price = self._last_close
        out: list[float] = []
        with torch.no_grad():
            for _ in range(steps):
                x = torch.from_numpy(window[None, :, None].astype("float32"))
                step_scaled = float(self._net(x).item())
                step_ret = step_scaled * self._sigma + self._mu
                price *= math.exp(step_ret)
                out.append(price)
                window = np.roll(window, -1)
                window[-1] = step_scaled
        return np.asarray(out, dtype="float64")
