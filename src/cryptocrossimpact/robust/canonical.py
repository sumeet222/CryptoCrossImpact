"""Stage1 QC body unchanged; only the new registered holdout split is authorized."""
import numpy as np
import pandas as pd
from ..data.schema import COLUMNS

def canonicalize(frame, symbol, month, config, previous=None):
    """Retain all source bars; quality_bits flags invalid values, never fills gaps.

    Bar close is open+59999 ms; full-bar observations are conservatively available
    at open+60000 ms. Returns are dimensionless log returns, not basis points.
    previous is only the immediately preceding canonical bar of the same asset.
    """
    if symbol not in ("BTCUSDT", "ETHUSDT"):
        raise ValueError("Wrong symbol")
    df = frame[COLUMNS].copy()
    t = df.open_time.to_numpy()
    begin = pd.Timestamp(month, tz="UTC")
    end = begin + pd.offsets.MonthBegin(1)
    lo, hi = begin.value // 10**6, end.value // 10**6
    if not ((t >= lo) & (t < hi)).all():
        raise ValueError("Wrong timestamp unit/month; expected UTC milliseconds")
    if (t % 60000 != 0).any() or (np.diff(t) <= 0).any():
        raise ValueError("Off-minute, duplicate or nonmonotone timestamps")
    if not (df.close_time.to_numpy() == t + 59999).all():
        raise ValueError("Invalid close_time; expected open_time + 59999 ms")
    bits = np.zeros(len(df), dtype=np.uint16)
    numeric = df[COLUMNS].to_numpy(dtype=float)
    bits[~np.isfinite(numeric).all(axis=1)] |= 1
    price = df[["open", "high", "low", "close"]]
    price_bad = ((price <= 0).any(axis=1) | (df.low > df.high) |
                 (df.open < df.low) | (df.open > df.high) |
                 (df.close < df.low) | (df.close > df.high))
    bits[price_bad] |= 2
    vols = ["volume", "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume"]
    bits[(df[vols] < 0).any(axis=1)] |= 4
    atol = config["qc"]["absolute_tolerance"]
    rtol = config["qc"]["relative_tolerance"]
    for buy, total in [("taker_buy_volume", "volume"), ("taker_buy_quote_volume", "quote_volume")]:
        bits[df[buy] > df[total] + atol + rtol * df[total].abs()] |= 8
    # Positive turnover must imply a trade and positive base volume (and vice versa).
    inconsistent = ((df.volume == 0) != (df.quote_volume == 0)) | ((df["count"] == 0) != (df.volume == 0))
    inconsistent |= (df.volume == 0) & ((df.taker_buy_volume != 0) | (df.taker_buy_quote_volume != 0))
    # Quote/base VWAP lies inside reported high/low, with decimal-rounding allowance.
    quote_lo, quote_hi = df.volume * df.low, df.volume * df.high
    inconsistent |= (df.quote_volume < quote_lo - atol - rtol * quote_lo.abs())
    inconsistent |= (df.quote_volume > quote_hi + atol + rtol * quote_hi.abs())
    bits[inconsistent] |= 16
    df["symbol"] = symbol
    df["bar_open_utc"] = pd.to_datetime(t, unit="ms", utc=True)
    df["bar_close_utc"] = pd.to_datetime(df.close_time, unit="ms", utc=True)
    df["available_at_utc"] = pd.to_datetime(t + 60000, unit="ms", utc=True)
    df["split"] = np.full(len(df), "holdout_X2X3")
    df["quality_bits"] = bits
    df["valid_bar"] = bits == 0
    df["buy_quote_volume"] = df.taker_buy_quote_volume
    df["sell_quote_volume"] = df.quote_volume - df.buy_quote_volume
    df["signed_taker_quote_flow"] = 2 * df.buy_quote_volume - df.quote_volume
    df["signed_taker_flow_ratio"] = df.signed_taker_quote_flow / df.quote_volume.where(df.quote_volume > 0)
    df["log_close"] = np.log(df.close.where(df.close > 0))
    prior_t = np.r_[np.nan, t[:-1]].astype(float)
    # pandas 3 copy-on-write exposes a read-only NumPy view by default.
    prior_close = df.close.shift(1).to_numpy(copy=True)
    prior_valid = np.r_[False, df.valid_bar.to_numpy()[:-1]]
    if previous is not None:
        if previous["symbol"] != symbol:
            raise ValueError("Cannot compute cross-asset return")
        prior_t[0], prior_close[0], prior_valid[0] = previous["open_time"], previous["close"], previous["valid_bar"]
    eligible = (t - prior_t == 60000) & df.valid_bar.to_numpy() & prior_valid
    ret = np.full(len(df), np.nan)
    ret[eligible] = np.log(df.close.to_numpy()[eligible]) - np.log(prior_close[eligible])
    df["close_to_close_log_return"] = ret
    df["valid_return"] = eligible
    df["jump_flag"] = np.abs(ret) > config["qc"]["jump_log_threshold"]
    # Long identical-close runs are diagnostics, not exclusions; no economic tuning.
    groups = ((df.close != df.close.shift()) | (df.open_time.diff() != 60000)).cumsum()
    # Strictly trailing run length: extending future data must not flag earlier bars.
    lengths = df.groupby(groups).cumcount() + 1
    df["stale_close_flag"] = lengths >= config["qc"]["stale_run_minutes"]
    return df
