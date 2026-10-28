"""Frozen Stage2/5 feature mathematics, new registered period guard only."""
import numpy as np
import pandas as pd
from ..kernel.features import flow_basis,RETURN_LAGS,ACTIVITY,VOLS

def guard_times(times):
    t=pd.DatetimeIndex(times)
    if t.tz is None or str(t.tz)!="UTC" or (t>=pd.Timestamp("2026-10-01",tz="UTC")).any():raise ValueError("Wrong feature clock")

def construct_asof(frame, liquidity, taus, memory=60, mode="primary"):
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
