"""Lossless integer-ms clocks and float64 money fields; no fitted features."""
from pathlib import Path
from urllib.parse import urlparse
from zipfile import ZipFile

import numpy as np
import pandas as pd

COLUMNS = ["open_time", "open", "high", "low", "close", "volume", "close_time",
           "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]
HEADER = ["open_time", "open", "high", "low", "close", "volume", "close_time",
          "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume", "ignore"]
DOCUMENTED_HEADER = ["open_time", "open", "high", "low", "close", "volume", "close_time",
                     "quote_asset_volume", "number_of_trades", "taker_buy_base_asset_volume",
                     "taker_buy_quote_asset_volume", "ignore"]


def validate_identity(url, symbol, period, kind="monthly"):
    """CSV alone cannot prove a market; bind exact official path and ZIP name."""
    if symbol not in ("BTCUSDT", "ETHUSDT"):
        raise ValueError("Wrong symbol: only BTCUSDT/ETHUSDT USD-M perpetuals")
    parsed = urlparse(url)
    if kind == "trades":
        path = f"/data/futures/um/daily/aggTrades/{symbol}/{symbol}-aggTrades-{period}.zip"
    elif kind in ("monthly", "daily"):
        path = f"/data/futures/um/{kind}/klines/{symbol}/1m/{symbol}-1m-{period}.zip"
    else:
        raise ValueError("Unknown stream")
    if (parsed.scheme, parsed.netloc, parsed.path, parsed.query, parsed.fragment) != (
            "https", "data.binance.vision", path, "", ""):
        raise ValueError("Wrong provider/market/symbol/interval/price-type source")


def split_labels(times):
    """Membership uses UTC bar-open calendar; data available at next minute."""
    times = pd.DatetimeIndex(times)
    if times.tz is None or str(times.tz) != "UTC":
        raise ValueError("UTC-aware bar timestamps required")
    result = np.full(len(times), "outside", dtype=object)
    for name, start, end in [("train", "2024-01-01", "2025-07-01"),
                             ("validation", "2025-07-01", "2026-01-01"),
                             ("test", "2026-01-01", "2026-07-01")]:
        result[(times >= pd.Timestamp(start, tz="UTC")) &
               (times < pd.Timestamp(end, tz="UTC"))] = name
    if "outside" in result:
        raise ValueError("Outside specified sample")
    return result


def parse_zip(path, symbol, period, url, kind="monthly"):
    validate_identity(url, symbol, period, kind)
    with ZipFile(path) as archive:
        names = archive.namelist()
        expected = Path(urlparse(url).path).name.replace(".zip", ".csv")
        if names != [expected]:
            raise ValueError(f"Unexpected ZIP members: {names}")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC failure")
        with archive.open(expected) as stream:
            first = stream.readline().decode("utf-8-sig").strip().split(",")
        has_header = first[0] == "open_time"
        if has_header and first not in (HEADER, DOCUMENTED_HEADER):
            raise ValueError(f"Unknown kline header {first}")
        with archive.open(expected) as stream:
            # round_trip prevents pandas' fast parser losing source float64 bits.
            frame = pd.read_csv(stream, header=None, skiprows=int(has_header),
                                float_precision="round_trip")
    if len(frame.columns) != 12 or frame.empty:
        raise ValueError("Expected nonempty 12-column USD-M kline CSV")
    frame.columns = COLUMNS
    for column in COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    for column in ("open_time", "close_time", "count"):
        values = frame[column].to_numpy()
        if not np.isfinite(values).all() or not (values == np.floor(values)).all():
            raise ValueError(f"Noninteger {column}")
        frame[column] = frame[column].astype("int64")
    for column in set(COLUMNS) - {"open_time", "close_time", "count"}:
        frame[column] = frame[column].astype("float64")
    frame.attrs["has_header"] = has_header
    return frame


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
    df["split"] = split_labels(df.bar_open_utc)
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


def signed_trade_quote(price, quantity, buyer_maker):
    """USDT: buyer maker=True means aggressive seller, hence negative sign."""
    return np.asarray(price) * np.asarray(quantity) * np.where(np.asarray(buyer_maker), -1, 1)


def summarize(df, month):
    begin = pd.Timestamp(month, tz="UTC")
    end = begin + pd.offsets.MonthBegin(1)
    expected = int((end - begin).total_seconds() // 60)
    missing = np.setdiff1d(np.arange(begin.value // 10**6, end.value // 10**6, 60000), df.open_time)
    # Exact missing spans, compact even for full-month outages.
    ranges = []
    for group in np.split(missing, np.where(np.diff(missing) != 60000)[0] + 1):
        if len(group):
            ranges.append({"first_open_ms": int(group[0]), "last_open_ms": int(group[-1]), "minutes": len(group)})
    reasons = {name: int(((df.quality_bits & bit) != 0).sum()) for bit, name in
               [(1, "nonfinite"), (2, "invalid_ohlc"), (4, "negative_volume_count"),
                (8, "taker_exceeds_total"), (16, "notional_volume_inconsistent")]}
    return dict(rows=len(df), expected_rows=expected, missing_minutes=len(missing),
                missing_ranges=ranges, invalid_bars=int((~df.valid_bar).sum()),
                valid_returns=int(df.valid_return.sum()), zero_volume=int((df.quote_volume == 0).sum()),
                jump_flags=int(df.jump_flag.sum()), stale_close_flags=int(df.stale_close_flag.sum()),
                extreme_flow_ratio=int((df.signed_taker_flow_ratio.abs() >= 0.999).sum()),
                exclusion_reasons=reasons, first_open_utc=str(df.bar_open_utc.iloc[0]),
                last_open_utc=str(df.bar_open_utc.iloc[-1]), split=str(df.split.iloc[0]))
