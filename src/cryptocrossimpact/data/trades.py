"""Stream small prespecified daily aggTrades audits; no parent-order inference."""
import json
from zipfile import ZipFile

import numpy as np
import pandas as pd

from .pipeline import archive_url
from .schema import signed_trade_quote
from .storage import SourceError, utcnow, write_json

TRADE_HEADER = ["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id", "transact_time", "is_buyer_maker"]


def aggregate_zip(path, symbol, day):
    """Stream 200k rows at a time into 1440 signed/total/buy quote sums in USDT."""
    start = pd.Timestamp(day, tz="UTC").value // 10**6
    totals = np.zeros((1440, 3), dtype=float)
    counts = np.zeros(1440, dtype=np.int64)
    rows = gaps = out_of_order = 0
    last_id = last_timestamp = None
    with ZipFile(path) as archive:
        expected = f"{symbol}-aggTrades-{day}.csv"
        if archive.namelist() != [expected] or archive.testzip() is not None:
            raise ValueError("aggTrades ZIP member/CRC failure")
        with archive.open(expected) as stream:
            first = stream.readline().decode("utf-8-sig").strip().split(",")
        has_header = first[0] == "agg_trade_id"
        if has_header and first != TRADE_HEADER:
            raise ValueError(f"Unexpected aggTrades schema: {first}")
        with archive.open(expected) as stream:
            for chunk in pd.read_csv(stream, header=None, skiprows=int(has_header), chunksize=200000,
                                     float_precision="round_trip"):
                if chunk.shape[1] != 7:
                    raise ValueError("aggTrades expected 7 columns")
                chunk.columns = TRADE_HEADER
                ids = pd.to_numeric(chunk.agg_trade_id).to_numpy(dtype=np.int64)
                ts = pd.to_numeric(chunk.transact_time).to_numpy(dtype=np.int64)
                if (ts < start).any() or (ts >= start + 86400000).any():
                    raise ValueError("aggTrades wrong timestamp unit/UTC day")
                maker_text = chunk.is_buyer_maker.astype(str).str.lower()
                if not maker_text.isin(["true", "false"]).all():
                    raise ValueError("Invalid isBuyerMaker flag")
                maker = (maker_text == "true").to_numpy()
                price = chunk.price.to_numpy(dtype=float)
                qty = chunk.quantity.to_numpy(dtype=float)
                if not np.isfinite(price).all() or not np.isfinite(qty).all() or (price <= 0).any() or (qty <= 0).any():
                    raise ValueError("Invalid aggTrades price/quantity")
                first_ids = pd.to_numeric(chunk.first_trade_id).to_numpy(dtype=np.int64)
                last_ids = pd.to_numeric(chunk.last_trade_id).to_numpy(dtype=np.int64)
                if (first_ids > last_ids).any():
                    raise ValueError("Invalid first/last trade IDs")
                id_diff = np.diff(np.r_[ids[0] - 1 if last_id is None else last_id, ids])
                if (id_diff <= 0).any():
                    raise ValueError("Duplicate/nonmonotone aggregate trade IDs")
                gaps += int(np.maximum(id_diff - 1, 0).sum())
                time_diff = np.diff(np.r_[ts[0] if last_timestamp is None else last_timestamp, ts])
                out_of_order += int((time_diff < 0).sum())
                last_id, last_timestamp = ids[-1], ts[-1]
                minute = ((ts - start) // 60000).astype(int)
                notional = price * qty
                signed = signed_trade_quote(price, qty, maker)
                for column, values in enumerate((signed, notional, np.where(maker, 0, notional))):
                    totals[:, column] += np.bincount(minute, weights=values, minlength=1440)
                counts += np.bincount(minute, minlength=1440)
                rows += len(chunk)
    return totals, counts, dict(trade_rows=rows, missing_aggregate_ids=gaps, out_of_order_timestamps=out_of_order,
                                header=has_header, timestamp_unit="milliseconds UTC")


def audit(pipeline):
    dest = pipeline.registry / "trade_audit.json"
    existing = json.loads(dest.read_text()) if dest.exists() else {"days": [], "failures": []}
    days = {(d["symbol"], d["day"]): d for d in existing["days"]}
    failures = []
    for symbol in pipeline.config["data"]["symbols"]:
        for day in pipeline.config["audit_dates"]:
            known = days.get((symbol, day))
            url = archive_url(pipeline.config, symbol, day, "trades")
            if known:
                expected, _ = pipeline.http.checksum(url)
                if expected != known["source"]["vendor_sha256"]:
                    raise SourceError("UPSTREAM_CHANGED", url)
                print(f"Verified audit cache {symbol}/{day}", flush=True)
                continue
            try:
                path, source = pipeline.http.archive(url)
                totals, counts, metadata = aggregate_zip(path, symbol, day)
                entry = pipeline.manifest["partitions"][f"{symbol}/{day[:7]}"]
                bars = pd.read_parquet(pipeline.root / entry["canonical_path"])
                bars = bars.loc[bars.bar_open_utc.dt.strftime("%Y-%m-%d") == day]
                start = pd.Timestamp(day, tz="UTC").value // 10**6
                slots = ((bars.open_time.to_numpy() - start) // 60000).astype(int)
                expected_q = bars.signed_taker_quote_flow.to_numpy()
                errors = totals[slots, 0] - expected_q
                quote = bars.quote_volume.to_numpy()
                relative = np.abs(errors) / np.maximum(quote, 1)
                total_errors = totals[slots, 1] - quote
                inverse_errors = -totals[slots, 0] - expected_q
                stats = dict(symbol=symbol, day=day, split=str(bars.split.iloc[0]), status="PASS",
                    source=source, **metadata, matched_minutes=len(bars), empty_trade_minutes=int((counts == 0).sum()),
                    signed_abs_error_usdt_p50=float(np.median(np.abs(errors))),
                    signed_abs_error_usdt_p99=float(np.quantile(np.abs(errors), .99)),
                    signed_abs_error_usdt_max=float(np.abs(errors).max()),
                    signed_abs_error_over_turnover_p99=float(np.quantile(relative, .99)),
                    signed_abs_error_over_turnover_max=float(relative.max()),
                    total_turnover_abs_error_usdt_max=float(np.abs(total_errors).max()),
                    signed_mean_abs_error_usdt=float(np.mean(np.abs(errors))),
                    reversed_sign_mean_abs_error_usdt=float(np.mean(np.abs(inverse_errors))),
                    per_minute_convention="UTC floor(transact_time/60000) matching bar open",
                    discrepancy_note="Aggregate trade price×quantity may differ from kline reporting; no forced equality")
                if metadata["missing_aggregate_ids"] or metadata["out_of_order_timestamps"] or len(bars) != 1440 or relative.max() > .01:
                    stats["status"] = "QUALIFIED"
                days[(symbol, day)] = stats
                result = dict(status="QUALIFIED", updated_at_utc=utcnow(), expected_days=14,
                              days=list(days.values()), failures=failures)
                write_json(dest, result)
                # Only current operation's tick archives removed, after durable summary.
                if source["created_this_call"]:
                    path.unlink()
                    path.with_suffix(".zip.CHECKSUM").unlink(missing_ok=True)
                    stats["source"]["temporary_archive_removed_after_audit"] = True
                    write_json(dest, result)
                print(f"Audit {symbol}/{day}: {metadata['trade_rows']:,} trades; max |q error|={stats['signed_abs_error_usdt_max']:.6g} USDT; {stats['status']}", flush=True)
            except (SourceError, ValueError, KeyError) as error:
                failures.append(dict(symbol=symbol, day=day, status=getattr(error, "status", "INVALID"), reason=str(error)))
                print(f"Audit hold {symbol}/{day}: {error}", flush=True)
                if getattr(error, "status", "") in ("ACCESS_BLOCKED", "RATE_LIMITED", "NETWORK_ERROR", "SIZE_HOLD", "STORAGE_HOLD"):
                    break
    result = dict(status="PASS" if len(days) == 14 and not failures and all(d["status"] == "PASS" for d in days.values()) else "QUALIFIED",
                  updated_at_utc=utcnow(), expected_days=14, completed_days=len(days), days=list(days.values()), failures=failures,
                  qualification_rule="Any minute absolute signed difference >1% of kline turnover, missing IDs, out-of-order time or incomplete day; diagnostic threshold only",
                  matching_conventions="UTC floor of millisecond transact_time matches kline open. Reversed aggressor sign tested as negative control. No alternative timestamp shift applied; cannot disaggregate bundle constituents from one timestamp.",
                  interpretation="Independent aggressor sign and aggregation QC only, not causal execution validation")
    write_json(dest, result)
    pd.DataFrame([{k:v for k,v in d.items() if not isinstance(v, dict)} for d in days.values()]).to_csv(pipeline.registry / "trade_audit.csv", index=False)
    print(f"AggTrades audit {result['status']}: {len(days)}/14 symbol-days", flush=True)
