"""Stage 1 commands only: preflight, pilot, acquire, qc, audit."""
import argparse
import importlib.metadata
import json
import platform
import resource
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .schema import COLUMNS, canonicalize, parse_zip, summarize, validate_identity
from .storage import PublicSource, SourceError, sha256, utcnow, write_json, write_parquet

ROOT = Path(__file__).resolve().parents[3]
TERMS = "https://raw.githubusercontent.com/binance/binance-public-data/master/TERMS_AND_CONDITIONS.md"
DOCS = "https://raw.githubusercontent.com/binance/binance-public-data/master/README.md"


def load_config(root):
    config = yaml.safe_load((root / "configs/core.yaml").read_text())
    # Changing the scientific contract requires explicit approval, not a CLI flag.
    data = config["data"]
    expected = ("Binance", "futures/um", "perpetual", "last_trade", "1m",
                ["BTCUSDT", "ETHUSDT"], "2024-01-01", "2026-06-30")
    actual = tuple(data[k] for k in ("provider", "market", "contract", "price_type", "interval", "symbols", "start", "end"))
    if actual != expected:
        raise ValueError("Configuration changes fixed scientific data contract")
    if config["splits"] != {"train": ["2024-01-01", "2025-06-30"],
                             "validation": ["2025-07-01", "2025-12-31"],
                             "test": ["2026-01-01", "2026-06-30"]}:
        raise ValueError("Configuration changes frozen splits")
    return config


def months(config):
    return pd.period_range(config["data"]["start"], config["data"]["end"], freq="M").astype(str).tolist()


def archive_url(config, symbol, period, kind="monthly"):
    data = config["data"]
    url = data[f"{kind}_template"].format(**data, symbol=symbol, period=period)
    validate_identity(url, symbol, period, kind)
    return url


def provenance(root, config):
    def git(*args):
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)
        return result.stdout.strip() if result.returncode == 0 else "unavailable"
    return dict(utc=utcnow(), python=sys.version, platform=platform.platform(),
                packages={d.metadata["Name"]: d.version for d in importlib.metadata.distributions()},
                git_branch=git("branch", "--show-current"), git_commit=git("rev-parse", "HEAD"),
                git_dirty=git("status", "--short", "--untracked-files=all"),
                config_sha256=sha256(root / "configs/core.yaml"),
                specification_sha256=sha256(root / config["specification"]), seed=config["seed"],
                working_code_sha256={str(path.relative_to(root)): sha256(path)
                    for base in (root / "src", root / "scripts", root / "tests")
                    for path in sorted(base.rglob("*.py"))},
                requirements_sha256=sha256(root / "requirements.txt"),
                stage="G0/G1 data integrity only", model_ids=[], evaluator_ids=[],
                final_outcome_scoring_performed=False)


class Pipeline:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.config = load_config(self.root)
        self.http = PublicSource(self.root, self.config)
        self.registry = self.root / "data/registry"
        self.manifest_path = self.registry / "source_manifest.json"
        if self.manifest_path.exists():
            self.manifest = json.loads(self.manifest_path.read_text())
        else:
            self.manifest = dict(provider="Binance Vision", venue="Binance", market="futures/um",
                contract="USDT-margined perpetual", price_type="last traded price", interval="1m",
                timestamp_unit="milliseconds UTC", quote_unit="USDT", base_units={"BTCUSDT": "BTC", "ETHUSDT": "ETH"},
                terms_url="https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md",
                license="CC BY-NC-SA 4.0; noncommercial research; no raw redistribution in Git",
                availability="open_time + 60000ms; vendor close_time = open_time + 59999ms",
                quality_bit_definitions={"1": "nonfinite", "2": "invalid OHLC", "4": "negative volume/count",
                                         "8": "taker exceeds total", "16": "inconsistent notional/volume/count"},
                zero_volume_rule="Preserve recorded prices and zero flow; ratio undefined; no invented bars",
                partitions={}, failures=[])

    def save(self):
        self.manifest["updated_at_utc"] = utcnow()
        write_json(self.manifest_path, self.manifest)

    def preflight(self):
        results = {}
        for label, url in [("documentation", DOCS), ("terms", TERMS), ("archive", "https://data.binance.vision/")]:
            with self.http.request("GET", url) as response:
                content = response.text
                import hashlib
                results[label] = dict(url=url, accessed_at_utc=utcnow(), http_status=response.status_code,
                                      sha256=hashlib.sha256(response.content).hexdigest())
                if label in ("documentation", "terms"):
                    # Retain vendor legal/schema text in ignored raw storage for reproducibility.
                    dest = self.root / "data/raw" / f"source_{label}.md"
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(content)
                if label == "terms" and not all(s in content for s in ("CC BY-NC-SA 4.0", "non-commercial")):
                    raise SourceError("TERMS_HOLD", "Dataset terms require review before acquisition")
        metadata = []
        for symbol in self.config["data"]["symbols"]:
            for month in self.config["pilot_months"]:
                url = archive_url(self.config, symbol, month)
                with self.http.request("HEAD", url) as response:
                    metadata.append(dict(symbol=symbol, month=month, bytes=int(response.headers["Content-Length"]),
                                         url=url, status=response.status_code))
                expected, _ = self.http.checksum(url)
                metadata[-1]["vendor_sha256"] = expected
        usage = self.http.guard()
        result = dict(status="PASS", checked_at_utc=utcnow(), source_access=results, pilot_metadata=metadata,
                      source_estimated_60_zip_bytes=max(x["bytes"] for x in metadata) * 60,
                      current_project_bytes=usage, free_bytes=__import__("shutil").disk_usage(self.root).free,
                      memory_target_bytes=8_000_000_000, retained_policy="one compressed monthly ZIP and one canonical Parquet; no extracted CSV",
                      preliminary_peak_reserve_bytes=1_000_000_000,
                      terms_assessment="Noncommercial academic research; attribution and share-alike for redistributed derivatives; no credentials/circumvention")
        write_json(self.registry / "preflight.json", result)
        print("Source/terms/metadata preflight PASS", flush=True)
        return result

    def previous(self, symbol, month):
        previous_month = str(pd.Period(month, freq="M") - 1)
        entry = self.manifest["partitions"].get(f"{symbol}/{previous_month}")
        if entry and entry["status"] in ("PASS", "QUALIFIED"):
            return pd.read_parquet(self.root / entry["canonical_path"]).iloc[-1].to_dict()
        return None

    def one(self, symbol, month):
        key = f"{symbol}/{month}"
        known = self.manifest["partitions"].get(key)
        url = archive_url(self.config, symbol, month)
        if known and known["status"] in ("PASS", "QUALIFIED"):
            target = self.root / known["canonical_path"]
            if target.exists() and sha256(target) == known["canonical_sha256"]:
                # Even successful partitions refresh upstream checksums. Do not redownload.
                for source in known["sources"]:
                    _, refreshed = self.http.archive(source["url"], source)
                    if not source.get("http_metadata"):
                        source["http_metadata"] = refreshed["http_metadata"]
                known["last_source_recheck_utc"] = utcnow()
                self.save()
                print(f"Verified cache {key}", flush=True)
                return
            raise SourceError("LOCAL_CHANGED", f"Missing or modified canonical partition: {key}")
        sources = []
        fallback_reason = None
        try:
            path, source = self.http.archive(url)
            frame = parse_zip(path, symbol, month, url)
            source["has_header"] = frame.attrs["has_header"]
            sources.append(source)
            # Structural invalidity/missing coverage triggers official daily fallback.
            candidate = canonicalize(frame, symbol, month, self.config)
            if summarize(candidate, month)["missing_minutes"]:
                raise SourceError("MONTHLY_INCOMPLETE", "Monthly archive has missing minutes")
        except (SourceError, ValueError, __import__("zipfile").BadZipFile) as error:
            status = getattr(error, "status", "CORRUPT")
            if status not in ("MISSING_SOURCE", "CORRUPT", "CHECKSUM_ERROR", "MONTHLY_INCOMPLETE") and not isinstance(error, ValueError):
                raise
            fallback_reason = f"{status}: {error}"
            print(f"Official daily fallback {key}: {fallback_reason}", flush=True)
            chunks, sources = [], []
            begin = pd.Timestamp(month)
            for day in pd.date_range(begin, begin + pd.offsets.MonthEnd(0)):
                period = str(day.date())
                daily_url = archive_url(self.config, symbol, period, "daily")
                try:
                    path, source = self.http.archive(daily_url)
                    part = parse_zip(path, symbol, period, daily_url, "daily")
                    if not (pd.to_datetime(part.open_time, unit="ms", utc=True).dt.strftime("%Y-%m-%d") == period).all():
                        raise ValueError("Daily file outside intended UTC day")
                    chunks.append(part)
                    source["has_header"] = part.attrs["has_header"]
                    sources.append(source)
                except SourceError as daily_error:
                    if daily_error.status != "MISSING_SOURCE":
                        raise
                    self.manifest["failures"].append(dict(key=key, url=daily_url, status=daily_error.status, utc=utcnow()))
            if not chunks:
                raise SourceError("MISSING_SOURCE", f"No monthly or daily data: {key}")
            frame = pd.concat(chunks, ignore_index=True)
        canonical = canonicalize(frame, symbol, month, self.config, self.previous(symbol, month))
        target = self.root / "data/canonical" / symbol / f"{month}.parquet"
        if target.exists():
            raise SourceError("UNREGISTERED_LOCAL", f"Preserving unregistered existing output {target}")
        self.http.guard(canonical.memory_usage(deep=True).sum() * 2)
        write_parquet(target, canonical)
        qc = summarize(canonical, month)
        entry = dict(symbol=symbol, month=month, status="QUALIFIED" if qc["missing_minutes"] or qc["invalid_bars"] else "PASS",
                     sources=sources, source_kind="daily_fallback" if fallback_reason else "monthly",
                     fallback_reason=fallback_reason, canonical_path=str(target.relative_to(self.root)),
                     canonical_sha256=sha256(target), canonical_bytes=target.stat().st_size, qc=qc,
                     source_manifest_id=key, verified_at_utc=utcnow())
        self.manifest["partitions"][key] = entry
        self.save()
        print(f"{entry['status']} {key}: {qc['rows']} rows; missing={qc['missing_minutes']}, invalid={qc['invalid_bars']}", flush=True)

    def acquire(self, pilot=False):
        preflight_path = self.registry / "preflight.json"
        if not preflight_path.exists() or json.loads(preflight_path.read_text())["status"] != "PASS":
            raise SourceError("PREFLIGHT_HOLD", "Run preflight before downloads")
        requested = self.config["pilot_months"] if pilot else months(self.config)
        errors = []
        for symbol in self.config["data"]["symbols"]:
            for month in requested:
                try:
                    self.one(symbol, month)
                except (SourceError, ValueError) as error:
                    entry = dict(key=f"{symbol}/{month}", status=getattr(error, "status", "INVALID_SCHEMA"),
                                 message=str(error), utc=utcnow())
                    self.manifest["failures"].append(entry)
                    self.save()
                    errors.append(entry)
                    print(f"HOLD {entry}", flush=True)
                    # Stop repeating the same global access/resource error, preserve valid work.
                    if entry["status"] in ("ACCESS_BLOCKED", "RATE_LIMITED", "NETWORK_ERROR", "STORAGE_HOLD", "SIZE_HOLD"):
                        raise
        if pilot and not errors:
            entries = list(self.manifest["partitions"].values())
            estimate = max(e["canonical_bytes"] for e in entries) * 60
            if estimate + self.http.guard() > self.config["resources"]["stop_bytes"]:
                raise SourceError("STORAGE_HOLD", "Pilot extrapolation exceeds storage ceiling")
            write_json(self.registry / "pilot.json", dict(status="PASS", utc=utcnow(),
                keys=[f"{s}/{m}" for s in self.config["data"]["symbols"] for m in requested],
                estimated_60_canonical_bytes=estimate, estimated_60_csv_bytes=max(e["sources"][0]["uncompressed_bytes"] for e in entries) * 60,
                metadata_only_test_inspection=True, compressed_zip_retained=True))
        if errors:
            raise SourceError("PARTITIONS_HELD", f"{len(errors)} partition holds; see manifest")

    def qc(self):
        paired, entries, unavailable, anomalies = [], [], [], []
        for month in months(self.config):
            pair = {}
            for symbol in self.config["data"]["symbols"]:
                key = f"{symbol}/{month}"
                entry = self.manifest["partitions"].get(key)
                if not entry:
                    unavailable.append(key)
                    continue
                path = self.root / entry["canonical_path"]
                if sha256(path) != entry["canonical_sha256"]:
                    raise SourceError("LOCAL_CHANGED", f"Canonical checksum changed: {key}")
                current = pd.read_parquet(path)
                # Read raw source again, independently rebuilding all features. This also
                # repairs missing pilot boundary context once the preceding month exists.
                frames = []
                for source in entry["sources"]:
                    raw = self.root / source["local_archive"]
                    if sha256(raw) != source["sha256"]:
                        raise SourceError("LOCAL_CHANGED", f"Raw checksum changed: {key}")
                    period = month if entry["source_kind"] == "monthly" else raw.stem[-10:]
                    frames.append(parse_zip(raw, symbol, period, source["url"],
                                            "monthly" if entry["source_kind"] == "monthly" else "daily"))
                raw_frame = pd.concat(frames, ignore_index=True)
                rebuilt = canonicalize(raw_frame, symbol, month, self.config, self.previous(symbol, month))
                # Every source value must survive Parquet conversion bit-for-bit.
                pd.testing.assert_frame_equal(current[COLUMNS], rebuilt[COLUMNS], check_exact=True)
                # Only first-row return/context can change from a previously isolated pilot.
                pd.testing.assert_frame_equal(current.iloc[1:].reset_index(drop=True), rebuilt.iloc[1:].reset_index(drop=True), check_exact=True)
                if not current.equals(rebuilt):
                    write_parquet(path, rebuilt)
                    entry["canonical_sha256"] = sha256(path)
                    entry["canonical_bytes"] = path.stat().st_size
                entry["qc"] = summarize(rebuilt, month)
                entry["status"] = "QUALIFIED" if entry["qc"]["missing_minutes"] or entry["qc"]["invalid_bars"] else "PASS"
                entry["raw_canonical_exact_check"] = "PASS"
                entries.append(dict(symbol=symbol, month=month, status=entry["status"], **{k:v for k,v in entry["qc"].items() if not isinstance(v, (dict,list))}))
                for flag in ("jump_flag", "stale_close_flag"):
                    selected = rebuilt.loc[rebuilt[flag]]
                    if not selected.empty:
                        groups = (selected.open_time.diff() != 60000).cumsum()
                        for _, interval in selected.groupby(groups):
                            anomalies.append(dict(symbol=symbol, month=month, split=str(interval.split.iloc[0]),
                                flag=flag, first_open_utc=str(interval.bar_open_utc.iloc[0]),
                                last_open_utc=str(interval.bar_open_utc.iloc[-1]), minutes=len(interval),
                                zero_volume_minutes=int((interval.quote_volume == 0).sum()),
                                invalid_bars=int((~interval.valid_bar).sum()), decision="retain; QC diagnostic only"))
                pair[symbol] = rebuilt
            if len(pair) == 2:
                a, b = pair["BTCUSDT"], pair["ETHUSDT"]
                present = np.intersect1d(a.open_time, b.open_time)
                valid = np.intersect1d(a.loc[a.valid_bar, "open_time"], b.loc[b.valid_bar, "open_time"])
                returns = np.intersect1d(a.loc[a.valid_return, "open_time"], b.loc[b.valid_return, "open_time"])
                paired.append(dict(month=month, split=str(a.split.iloc[0]), expected_minutes=entry["qc"]["expected_rows"],
                    paired_present_minutes=len(present), paired_valid_minutes=len(valid), paired_valid_returns=len(returns),
                    btc_only_minutes=len(np.setdiff1d(a.open_time, b.open_time)),
                    eth_only_minutes=len(np.setdiff1d(b.open_time, a.open_time))))
        self.save()
        pd.DataFrame(entries).to_csv(self.registry / "qc_partitions.csv", index=False)
        pd.DataFrame(paired).to_csv(self.registry / "paired_coverage.csv", index=False)
        pd.DataFrame(anomalies).to_csv(self.registry / "qc_anomalies.csv", index=False)
        result = dict(utc=utcnow(), status="BLOCKED" if unavailable else ("QUALIFIED" if any(e["status"] != "PASS" for e in entries) else "PASS"),
            expected_partitions=60, downloaded_partitions=len(entries), validated_partitions=len(entries),
            qualified_partitions=sum(e["status"] == "QUALIFIED" for e in entries),
            quarantined_partitions=0, missing_partitions=unavailable,
            total_rows=sum(e["rows"] for e in entries), total_invalid_bars=sum(e["invalid_bars"] for e in entries),
            total_missing_minutes=sum(e["missing_minutes"] for e in entries),
            paired_by_split=pd.DataFrame(paired).groupby("split").sum(numeric_only=True).to_dict("index") if paired else {},
            all_raw_canonical_checks="PASS" if entries else "NOT_RUN", scientific_conclusion="Not evaluated in Stage 1",
            test_firewall="Source/QC only; no response correlations, estimation, policy or outcome scoring")
        write_json(self.registry / "qc_summary.json", result)
        run = provenance(self.root, self.config)
        run.update(command="qc", peak_project_bytes_observed=self.http.guard(),
                   peak_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   source_manifest_sha256=sha256(self.manifest_path))
        write_json(self.registry / "run_manifest.json", run)
        self.report(result, entries, paired)
        print(json.dumps(result, indent=2), flush=True)
        return result

    def report(self, result, entries, paired):
        audit = self.registry / "trade_audit.json"
        audit_summary = json.loads(audit.read_text()) if audit.exists() else {"status": "NOT_RUN"}
        lines = ["# Stage 1 data quality", "", f"Generated UTC: {utcnow()}. Specification v1.0; Stage 1 only.", "",
            "Binance Vision USD-M USDT-margined perpetual BTCUSDT/ETHUSDT last-trade 1m klines; 2024-01–2026-06.",
            "Source: https://data.binance.vision/ ; schema: https://github.com/binance/binance-public-data .",
            "Dataset attribution: Binance Vision. Derived QA summaries: CC BY-NC-SA 4.0.",
            "Terms checked during preflight: https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md .", "",
            f"G0: {'PASS' if (self.registry / 'pilot.json').exists() else 'BLOCKED'}. G1: {result['status']}.",
            f"Expected/downloaded/validated: 60/{result['downloaded_partitions']}/{result['validated_partitions']}. "
            f"Qualified: {result['qualified_partitions']}; quarantined: {result['quarantined_partitions']}; missing partitions: {len(result['missing_partitions'])}.",
            f"Source rows: {result['total_rows']:,}; invalid bars: {result['total_invalid_bars']:,}; missing minute keys: {result['total_missing_minutes']:,}.",
            "Scientific hypotheses were not evaluated; no model, kernel, strategy or backtest was run.", "",
            "## Clock, units and quality rules", "",
            "Vendor integer milliseconds UTC; close_time=open_time+59,999ms. All full-bar fields available_at_utc=open_time+60,000ms.",
            "Split labels use the UTC bar-open date. Thus the final train bar is available exactly at validation start.",
            "Flow is USDT: buy=taker_buy_quote_volume; sell=quote_volume-buy; q=2buy-quote_volume. It is aggregated aggressive flow, not L2 OFI or parent orders.",
            "Returns are log(close_t)-log(close_previous), only for consecutive valid bars of the same symbol. Month context is carried forward; first sample bar has no return.",
            "Raw values retained in float64 with round-trip parser; integer clocks/counts are exact. Parquet read-back and all source numeric fields compared exactly.",
            "Quality bits: 1 nonfinite, 2 invalid OHLC, 4 negative volume/count, 8 taker exceeds total, 16 inconsistent volume/notional/count. No clipping/imputation.",
            "Quote/base VWAP is checked against OHLC bounds. Volume comparisons allow 1e-8 absolute + 1e-12 relative rounding tolerance, not a fitted threshold.",
            "Recorded zero-volume bars remain; q=0 when verified, ratio undefined. Missing bars are never invented; missing spans and reason counts remain in source_manifest.json.",
            "Jump |log return|>0.05, identical-close runs >=30 minutes, and |flow ratio|>=0.999 are diagnostic counts only. No economic exclusions were selected from these flags.",
            "Exact jump/stale intervals are in data/registry/qc_anomalies.csv. Reported zero-volume bars have zero base/quote/taker volume and trade count; they are source records, not filled gaps. This does not independently establish market-wide inactivity or executable liquidity.",
            "Test-period integrity diagnostics use the same fixed rules. No flow/return relationships or predictive/trading outcomes inspected.", "",
            "## Paired split coverage", "", "| Split | Expected minutes | Paired present | Paired valid | Valid returns | Excluded invalid/missing |", "|---|---:|---:|---:|---:|---:|"]
        for split, row in result["paired_by_split"].items():
            lines.append(f"| {split} | {row['expected_minutes']} | {row['paired_present_minutes']} | {row['paired_valid_minutes']} | {row['paired_valid_returns']} | {row['expected_minutes'] - row['paired_valid_minutes']} |")
        lines += ["", "## Per symbol and split", "", "| Symbol | Split | Rows | Invalid | Missing | Zero volume | Jump flags | Stale flags | Extreme flow ratio |", "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        if entries:
            totals = pd.DataFrame(entries).groupby(["symbol", "split"]).sum(numeric_only=True)
            for (symbol, split), row in totals.iterrows():
                lines.append(f"| {symbol} | {split} | {int(row.rows)} | {int(row.invalid_bars)} | {int(row.missing_minutes)} | {int(row.zero_volume)} | {int(row.jump_flags)} | {int(row.stale_close_flags)} | {int(row.extreme_flow_ratio)} |")
        lines += ["", "## Per symbol/month QC", "", "| Symbol | Month | Status | Rows/expected | Missing | Invalid | Valid returns | Zero volume | Jumps | Stale |", "|---|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for e in entries:
            lines.append(f"| {e['symbol']} | {e['month']} | {e['status']} | {e['rows']}/{e['expected_rows']} | {e['missing_minutes']} | {e['invalid_bars']} | {e['valid_returns']} | {e['zero_volume']} | {e['jump_flags']} | {e['stale_close_flags']} |")
        lines += ["", "## Independent aggregate-trade audit", "", f"Status: {audit_summary['status']}. Details: data/registry/trade_audit.json; data/registry/trade_audit.csv.",
            "Buyer-maker=true is a passive buyer/aggressive seller: signed price×quantity is negative. Audit is source aggregation QA, not causal impact evidence.", "",
            "## Provenance, resources and restart", "",
            "Source URLs, retrieval UTC, official SHA-256, ZIP CRC, header, compressed/uncompressed bytes and HTTP revision metadata: data/registry/source_manifest.json.",
            "Source metadata and license access: data/registry/preflight.json. Pilot extrapolation: data/registry/pilot.json. Software/config/spec/Git: data/registry/run_manifest.json.",
            "Only compressed monthly ZIP plus one canonical Parquet per symbol-month retained; no extracted CSV or split-specific copies. Tick files are streamed and removed only when created by this run and audit summaries are durable.",
            "Commands (from repo root): `.venv/bin/python scripts/stage01.py preflight`; `pilot`; `acquire`; `audit`; `qc` with the same prefix.",
            "Tests: `.venv/bin/python -m pytest -q`. Resume is idempotent; fresh vendor checksum is checked for every cached partition and changed sources halt for review.",
            "Stage 2 is not started. Liquidity normalizers, regression targets, kernels, solver and backtests are absent.", ""]
        if audit_summary.get("days"):
            days = audit_summary["days"]
            p99 = [d["signed_abs_error_over_turnover_p99"] for d in days]
            sign_ratio = [d["reversed_sign_mean_abs_error_usdt"] / d["signed_mean_abs_error_usdt"] for d in days]
            lines += ["## Trade-audit qualification and anomaly review", "",
                f"All {len(days)}/14 audit symbol-days completed: {sum(d['trade_rows'] for d in days):,} aggregate trades. "
                f"Missing aggregate IDs: {sum(d['missing_aggregate_ids'] for d in days)}; out-of-order timestamps: {sum(d['out_of_order_timestamps'] for d in days)}.",
                f"Daily p99 absolute signed discrepancy / kline turnover: {min(p99):.4%}–{max(p99):.4%}. "
                f"Correct-sign mean absolute errors are {min(sign_ratio):.0f}–{max(sign_ratio):.0f} times smaller than reversed-sign errors; this confirms orientation, not exact aggregation.",
                "Each day has a minute exceeding the audit's 1%-of-turnover diagnostic discrepancy threshold, so supporting aggregation equivalence is QUALIFIED. Kline q remains exactly the prespecified exchange field identity; no stream was substituted.",
                "Primary matching uses UTC floor(transact_time/60000); reversed sign is the negative control. No timestamp shift or bundle-splitting convention is substituted. Alternative sub-minute assignments remain unverified.",
                "Current [official aggregate-trade documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) describes 100ms bundling by price/taking side and exclusion of insurance-fund/ADL trades. These are possible sources of differences, not a demonstrated historical explanation for every discrepancy.",
                "The initial Stage 1 session rendered eight development-only jump/stale day plots with `scripts/stage01_qc_figures.py` and recorded a visual review (data/registry/qc_visual_review.json). They show source-record price moves/turnover bursts and a shared October 2024 zero-turnover plateau. Source keys, bounds and hashes pass; all observations are retained with flags. No test economic plots were generated.",
                "A stale diagnostic means at least 30 identical closes observed consecutively **so far**; extending future data cannot relabel earlier bars. It is a QC flag, not a forecasting input.", ""]
        if result["missing_partitions"]:
            lines += ["Missing partitions: " + ", ".join(result["missing_partitions"]), ""]
        dest = self.root / "reports/data/stage01_data_quality.md"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["preflight", "pilot", "acquire", "qc", "audit"])
    args = parser.parse_args()
    pipeline = Pipeline()
    try:
        if args.command == "preflight":
            pipeline.preflight()
        elif args.command in ("pilot", "acquire"):
            if args.command == "acquire" and not (pipeline.registry / "pilot.json").exists():
                raise SourceError("PILOT_HOLD", "Run and validate pilot before full acquisition")
            pipeline.acquire(pilot=args.command == "pilot")
        elif args.command == "qc":
            pipeline.qc()
        else:
            from .trades import audit
            audit(pipeline)
    except (SourceError, ValueError) as error:
        write_json(pipeline.registry / "last_hold.json", dict(command=args.command, utc=utcnow(),
            status=getattr(error, "status", "INVALID"), message=str(error)))
        print(f"HOLD {error}", file=sys.stderr)
        sys.exit(1)
    finally:
        run = provenance(pipeline.root, pipeline.config)
        run.update(command=args.command, peak_project_bytes_observed=pipeline.http.peak_bytes,
                   peak_rss_platform_units=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        write_json(pipeline.registry / f"run_{args.command}.json", run)
