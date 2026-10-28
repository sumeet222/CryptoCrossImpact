"""Monthly bounded features: economic units, prior-bar controls, test firewall."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import lfilter

from ..data.storage import sha256

ASSETS = ["BTCUSDT", "ETHUSDT"]
FIREWALL = pd.Timestamp("2026-01-01", tz="UTC")
RETURN_LAGS = [1, 2, 5, 15]
ACTIVITY = [5, 15, 60]
VOLS = [60, 1440]


def guard_times(times):
    times = pd.DatetimeIndex(times)
    if times.tz is None or str(times.tz) != "UTC" or (times >= FIREWALL).any():
        raise ValueError("Stage 2 firewall: UTC development observations only; no 2026 outcomes")


class DevelopmentStore:
    def __init__(self, root):
        self.root = Path(root)
        self.manifest = json.loads((self.root / "data/registry/source_manifest.json").read_text())
        if self.manifest["market"] != "futures/um" or self.manifest["interval"] != "1m":
            raise ValueError("Wrong source identity")
        self.verified, self.read_log = {}, []

    def read(self, symbol, month, columns=None):
        if symbol not in ASSETS or pd.Period(month, freq="M") >= pd.Period("2026-01", freq="M"):
            raise ValueError("Stage 2 firewall: partition refused before opening")
        entry = self.manifest["partitions"][f"{symbol}/{month}"]
        path = self.root / entry["canonical_path"]
        if path not in self.verified:
            if sha256(path) != entry["canonical_sha256"]:
                raise ValueError("Canonical input changed; rerun affected integrity review")
            self.verified[path] = entry["canonical_sha256"]
        self.read_log.append(f"{symbol}/{month}")
        frame = pd.read_parquet(path, columns=columns)
        if "bar_open_utc" in frame:
            guard_times(frame.bar_open_utc)
        return frame

    def paired(self, month):
        cols = ["open_time", "bar_open_utc", "available_at_utc", "close", "quote_volume",
                "signed_taker_quote_flow", "close_to_close_log_return", "valid_bar", "valid_return",
                "stale_close_flag", "jump_flag"]
        a, b = [self.read(s, month, cols) for s in ASSETS]
        if not np.array_equal(a.open_time, b.open_time):
            raise ValueError("Paired source timestamps differ; no silent inner join")
        out = pd.DataFrame({"time": a.bar_open_utc, "open_time": a.open_time})
        for j, frame in enumerate((a, b)):
            if not (frame.available_at_utc == frame.bar_open_utc + pd.Timedelta(minutes=1)).all():
                raise ValueError("Wrong bar availability")
            for name in cols[3:]:
                out[f"{name}_{j}"] = frame[name].to_numpy()
        return out

    def liquidity(self, start="2024-01-01", end="2025-07-01"):
        begin, finish = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
        if finish > FIREWALL or begin >= finish:
            raise ValueError("Refit window crosses Stage 2 firewall")
        values = [[], []]
        for month in pd.period_range(begin.tz_localize(None), (finish-pd.Timedelta(minutes=1)).tz_localize(None), freq="M").astype(str):
            for j, symbol in enumerate(ASSETS):
                frame = self.read(symbol, month, ["bar_open_utc", "quote_volume", "valid_bar"])
                mask = (frame.bar_open_utc >= begin) & (frame.bar_open_utc < finish) & frame.valid_bar & (frame.quote_volume > 0)
                values[j].append(frame.loc[mask, "quote_volume"].to_numpy())
        return np.array([np.median(np.concatenate(v)) for v in values])


def flow_basis(f, taus, memory=60, mode="primary"):
    """Shape (bars,K,assets). Eq(1), no H+1 truncated-level boundary term.

    This is an explanatory return basis. Lead mode is an explicitly future-flow
    falsification confined to development data; lag-only removes the f_t term.
    """
    f = np.asarray(f, dtype=float)
    result = []
    for tau in taus:
        level = np.exp(-np.arange(memory + 1) / tau)
        weights = np.r_[1., np.diff(level)]
        if mode == "lag_only":
            weights[0] = 0
        basis = lfilter(weights, [1.], f, axis=0)
        if mode == "lead_placebo":
            basis = np.vstack([basis[1:], np.full((1, 2), np.nan)])
        basis[:memory] = np.nan
        result.append(basis)
    return np.stack(result, axis=1)


def feature_names():
    names = []
    for j in range(2):
        names += [f"return_{j}_lag{lag}" for lag in RETURN_LAGS]
        names += [f"activity_{j}_{w}" for w in ACTIVITY]
        names += [f"volume_deviation_{j}"]
        names += [f"volatility_{j}_{w}" for w in VOLS]
    return names + ["tod_sin", "tod_cos", "dow_sin", "dow_cos"]


def construct(frame, liquidity, taus, memory=60, mode="primary"):
    """Return raw design, y and common eligibility; windows end at target t-1.

    r_t and f_t are available after target bar completion. Nuisances never use
    target-bar prices/volumes. Full 1440-return history and target must be valid.
    """
    guard_times(frame.time)
    if not np.all(np.isfinite(liquidity)) or np.any(np.asarray(liquidity) <= 0):
        raise ValueError("Positive training-only liquidity units required")
    n = len(frame)
    controls, valid = [], np.ones(n, dtype=bool)
    f = np.zeros((n, 2))
    r = np.zeros((n, 2))
    for j in range(2):
        ret = frame[f"close_to_close_log_return_{j}"]
        volume = frame[f"quote_volume_{j}"]
        controls.extend(ret.shift(lag).to_numpy() for lag in RETURN_LAGS)
        controls.extend(np.log1p(volume.shift(1).rolling(w, min_periods=w).mean()).to_numpy() for w in ACTIVITY)
        med = volume.shift(1).rolling(1440, min_periods=1440).median()
        controls.append((np.log1p(volume.shift(1)) - np.log1p(med)).to_numpy())
        controls.extend(np.sqrt(ret.shift(1).pow(2).rolling(w, min_periods=w).mean()).to_numpy() for w in VOLS)
        past_good = frame[f"valid_return_{j}"].astype(int).shift(1).rolling(1440, min_periods=1440).sum()
        valid &= (past_good.to_numpy() == 1440) & frame[f"valid_return_{j}"].to_numpy() & frame[f"valid_bar_{j}"].to_numpy()
        f[:, j] = frame[f"signed_taker_quote_flow_{j}"].to_numpy() / np.sqrt(liquidity[j])
        r[:, j] = ret.to_numpy()
    time = pd.DatetimeIndex(frame.time)
    tod = (time.hour * 60 + time.minute).to_numpy() / 1440
    dow = (time.day_of_week.to_numpy() + tod) / 7
    controls.extend([np.sin(2*np.pi*tod), np.cos(2*np.pi*tod), np.sin(2*np.pi*dow), np.cos(2*np.pi*dow)])
    basis = flow_basis(f, taus, memory, mode)
    design = np.column_stack([np.ones(n), *controls, basis.reshape(n, -1)])
    y = 1e4 * np.sqrt(liquidity) * r
    # Calendar continuity catches an omitted minute even when all stored flags pass.
    clock = frame.open_time
    valid &= (clock - clock.shift(1440)).to_numpy() == 1440 * 60000
    valid &= np.isfinite(design).all(axis=1) & np.isfinite(y).all(axis=1)
    return design, y, valid


def batches(store, liquidity, taus, memory=60, mode="primary", end="2025-12"):
    """Monthly batches with original chronological context; never a feature cache."""
    context = None
    for month in pd.period_range("2024-01", end, freq="M").astype(str):
        current = store.paired(month)
        offset = 0 if context is None else len(context)
        combined = current if context is None else pd.concat([context, current], ignore_index=True)
        design, y, valid = construct(combined, liquidity, taus, memory, mode)
        yield month, current, design[offset:], y[offset:], valid[offset:]
        context = combined.iloc[-1441:].copy()


def metadata():
    rows = []
    for name in feature_names():
        if name.startswith("return"):
            lag = int(name.split("lag")[-1]); lookback = lag + 1; units = "fraction log return"
        elif name.startswith("activity"):
            lookback = int(name.split("_")[-1]); units = "log1p(mean quote turnover / 1 USDT)"
        elif name.startswith("volume"):
            lookback = 1440; units = "log1p(previous USDT)-log1p(past median USDT)"
        elif name.startswith("volatility"):
            lookback = int(name.split("_")[-1]) + 1; units = "sqrt(mean squared log return), population RMS"
        else:
            lookback = 0; units = "dimensionless calendar sine/cosine"
        rows.append(dict(feature=name, source="UTC calendar" if lookback == 0 else "prior completed close/quote-volume bars",
                         units=units, lookback_minutes=lookback, cutoff="calendar known" if lookback == 0 else "target bar open; source <= t-1"))
    return rows
