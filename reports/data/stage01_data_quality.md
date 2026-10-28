# Stage 1 data quality

Generated UTC: 2026-10-27T22:41:58.295149+00:00. Specification v1.0; Stage 1 only.

Binance Vision USD-M USDT-margined perpetual BTCUSDT/ETHUSDT last-trade 1m klines; 2024-01–2026-06.
Source: https://data.binance.vision/ ; schema: https://github.com/binance/binance-public-data .
Dataset attribution: Binance Vision. Derived QA summaries: CC BY-NC-SA 4.0.
Terms checked during preflight: https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md .

G0: PASS. G1: PASS.
Expected/downloaded/validated: 60/60/60. Qualified: 0; quarantined: 0; missing partitions: 0.
Source rows: 2,626,560; invalid bars: 0; missing minute keys: 0.
Scientific hypotheses were not evaluated; no model, kernel, strategy or backtest was run.

## Clock, units and quality rules

Vendor integer milliseconds UTC; close_time=open_time+59,999ms. All full-bar fields available_at_utc=open_time+60,000ms.
Split labels use the UTC bar-open date. Thus the final train bar is available exactly at validation start.
Flow is USDT: buy=taker_buy_quote_volume; sell=quote_volume-buy; q=2buy-quote_volume. It is aggregated aggressive flow, not L2 OFI or parent orders.
Returns are log(close_t)-log(close_previous), only for consecutive valid bars of the same symbol. Month context is carried forward; first sample bar has no return.
Raw values retained in float64 with round-trip parser; integer clocks/counts are exact. Parquet read-back and all source numeric fields compared exactly.
Quality bits: 1 nonfinite, 2 invalid OHLC, 4 negative volume/count, 8 taker exceeds total, 16 inconsistent volume/notional/count. No clipping/imputation.
Quote/base VWAP is checked against OHLC bounds. Volume comparisons allow 1e-8 absolute + 1e-12 relative rounding tolerance, not a fitted threshold.
Recorded zero-volume bars remain; q=0 when verified, ratio undefined. Missing bars are never invented; missing spans and reason counts remain in source_manifest.json.
Jump |log return|>0.05, identical-close runs >=30 minutes, and |flow ratio|>=0.999 are diagnostic counts only. No economic exclusions were selected from these flags.
Exact jump/stale intervals are in data/registry/qc_anomalies.csv. Reported zero-volume bars have zero base/quote/taker volume and trade count; they are source records, not filled gaps. This does not independently establish market-wide inactivity or executable liquidity.
Test-period integrity diagnostics use the same fixed rules. No flow/return relationships or predictive/trading outcomes inspected.

## Paired split coverage

| Split | Expected minutes | Paired present | Paired valid | Valid returns | Excluded invalid/missing |
|---|---:|---:|---:|---:|---:|
| test | 260640 | 260640 | 260640 | 260640 | 0 |
| train | 787680 | 787680 | 787680 | 787679 | 0 |
| validation | 264960 | 264960 | 264960 | 264960 | 0 |

## Per symbol and split

| Symbol | Split | Rows | Invalid | Missing | Zero volume | Jump flags | Stale flags | Extreme flow ratio |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | test | 260640 | 0 | 0 | 0 | 0 | 0 | 0 |
| BTCUSDT | train | 787680 | 0 | 0 | 108 | 0 | 46 | 0 |
| BTCUSDT | validation | 264960 | 0 | 0 | 18 | 1 | 0 | 1 |
| ETHUSDT | test | 260640 | 0 | 0 | 0 | 0 | 0 | 0 |
| ETHUSDT | train | 787680 | 0 | 0 | 109 | 6 | 46 | 0 |
| ETHUSDT | validation | 264960 | 0 | 0 | 18 | 1 | 0 | 0 |

## Per symbol/month QC

| Symbol | Month | Status | Rows/expected | Missing | Invalid | Valid returns | Zero volume | Jumps | Stale |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 2024-01 | PASS | 44640/44640 | 0 | 0 | 44639 | 0 | 0 | 0 |
| ETHUSDT | 2024-01 | PASS | 44640/44640 | 0 | 0 | 44639 | 0 | 1 | 0 |
| BTCUSDT | 2024-02 | PASS | 41760/41760 | 0 | 0 | 41760 | 0 | 0 | 0 |
| ETHUSDT | 2024-02 | PASS | 41760/41760 | 0 | 0 | 41760 | 0 | 1 | 0 |
| BTCUSDT | 2024-03 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2024-03 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| BTCUSDT | 2024-04 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| ETHUSDT | 2024-04 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| BTCUSDT | 2024-05 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2024-05 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| BTCUSDT | 2024-06 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| ETHUSDT | 2024-06 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| BTCUSDT | 2024-07 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2024-07 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| BTCUSDT | 2024-08 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2024-08 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 1 | 0 |
| BTCUSDT | 2024-09 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| ETHUSDT | 2024-09 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| BTCUSDT | 2024-10 | PASS | 44640/44640 | 0 | 0 | 44640 | 89 | 0 | 46 |
| ETHUSDT | 2024-10 | PASS | 44640/44640 | 0 | 0 | 44640 | 89 | 0 | 46 |
| BTCUSDT | 2024-11 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| ETHUSDT | 2024-11 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| BTCUSDT | 2024-12 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2024-12 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| BTCUSDT | 2025-01 | PASS | 44640/44640 | 0 | 0 | 44640 | 19 | 0 | 0 |
| ETHUSDT | 2025-01 | PASS | 44640/44640 | 0 | 0 | 44640 | 20 | 0 | 0 |
| BTCUSDT | 2025-02 | PASS | 40320/40320 | 0 | 0 | 40320 | 0 | 0 | 0 |
| ETHUSDT | 2025-02 | PASS | 40320/40320 | 0 | 0 | 40320 | 0 | 3 | 0 |
| BTCUSDT | 2025-03 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2025-03 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| BTCUSDT | 2025-04 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| ETHUSDT | 2025-04 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| BTCUSDT | 2025-05 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2025-05 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| BTCUSDT | 2025-06 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| ETHUSDT | 2025-06 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| BTCUSDT | 2025-07 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2025-07 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| BTCUSDT | 2025-08 | PASS | 44640/44640 | 0 | 0 | 44640 | 18 | 0 | 0 |
| ETHUSDT | 2025-08 | PASS | 44640/44640 | 0 | 0 | 44640 | 18 | 0 | 0 |
| BTCUSDT | 2025-09 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| ETHUSDT | 2025-09 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| BTCUSDT | 2025-10 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 1 | 0 |
| ETHUSDT | 2025-10 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 1 | 0 |
| BTCUSDT | 2025-11 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| ETHUSDT | 2025-11 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| BTCUSDT | 2025-12 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2025-12 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| BTCUSDT | 2026-01 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2026-01 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| BTCUSDT | 2026-02 | PASS | 40320/40320 | 0 | 0 | 40320 | 0 | 0 | 0 |
| ETHUSDT | 2026-02 | PASS | 40320/40320 | 0 | 0 | 40320 | 0 | 0 | 0 |
| BTCUSDT | 2026-03 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2026-03 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| BTCUSDT | 2026-04 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| ETHUSDT | 2026-04 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| BTCUSDT | 2026-05 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| ETHUSDT | 2026-05 | PASS | 44640/44640 | 0 | 0 | 44640 | 0 | 0 | 0 |
| BTCUSDT | 2026-06 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |
| ETHUSDT | 2026-06 | PASS | 43200/43200 | 0 | 0 | 43200 | 0 | 0 | 0 |

## Independent aggregate-trade audit

Status: QUALIFIED. Details: data/registry/trade_audit.json; data/registry/trade_audit.csv.
Buyer-maker=true is a passive buyer/aggressive seller: signed price×quantity is negative. Audit is source aggregation QA, not causal impact evidence.

## Provenance, resources and restart

Source URLs, retrieval UTC, official SHA-256, ZIP CRC, header, compressed/uncompressed bytes and HTTP revision metadata: data/registry/source_manifest.json.
Source metadata and license access: data/registry/preflight.json. Pilot extrapolation: data/registry/pilot.json. Software/config/spec/Git: data/registry/run_manifest.json.
Only compressed monthly ZIP plus one canonical Parquet per symbol-month retained; no extracted CSV or split-specific copies. Tick files are streamed and removed only when created by this run and audit summaries are durable.
Commands (from repo root): `.venv/bin/python scripts/stage01.py preflight`; `pilot`; `acquire`; `audit`; `qc` with the same prefix.
Tests: `.venv/bin/python -m pytest -q`. Resume is idempotent; fresh vendor checksum is checked for every cached partition and changed sources halt for review.
Stage 2 is not started. Liquidity normalizers, regression targets, kernels, solver and backtests are absent.

## Trade-audit qualification and anomaly review

All 14/14 audit symbol-days completed: 31,109,040 aggregate trades. Missing aggregate IDs: 0; out-of-order timestamps: 0.
Daily p99 absolute signed discrepancy / kline turnover: 0.4885%–1.6023%. Correct-sign mean absolute errors are 710–2827 times smaller than reversed-sign errors; this confirms orientation, not exact aggregation.
Each day has a minute exceeding the audit's 1%-of-turnover diagnostic discrepancy threshold, so supporting aggregation equivalence is QUALIFIED. Kline q remains exactly the prespecified exchange field identity; no stream was substituted.
Primary matching uses UTC floor(transact_time/60000); reversed sign is the negative control. No timestamp shift or bundle-splitting convention is substituted. Alternative sub-minute assignments remain unverified.
Current [official aggregate-trade documentation](https://developers.binance.com/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data) describes 100ms bundling by price/taking side and exclusion of insurance-fund/ADL trades. These are possible sources of differences, not a demonstrated historical explanation for every discrepancy.
The initial Stage 1 session rendered eight development-only jump/stale day plots with `scripts/stage01_qc_figures.py` and recorded a visual review (data/registry/qc_visual_review.json). They show source-record price moves/turnover bursts and a shared October 2024 zero-turnover plateau. Source keys, bounds and hashes pass; all observations are retained with flags. No test economic plots were generated.
A stale diagnostic means at least 30 identical closes observed consecutively **so far**; extending future data cannot relabel earlier bars. It is a QC flag, not a forecasting input.
