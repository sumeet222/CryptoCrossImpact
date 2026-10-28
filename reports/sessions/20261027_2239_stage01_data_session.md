# Stage 1 — data acquisition and QC session

**UTC:** 2026-10-27, approximately 22:23–22:41. **Task:** execute Stage 1 only;
G0 **PASS**, G1 **PASS** (core source/implementation correctness). Supporting
aggTrades aggregation audit **QUALIFIED**. **Scientific conclusion:** not evaluated;
no causal, fit or execution-performance finding. No kernels, strategies or
backtests were fitted or run; Stage 2 has not begun.

## Authority, environment and Git

Read repository AGENTS.md and the full specification v1.0 dated 2026-10-27. The
requested short prompt filename did not exist; used the supplied
`prompts/CryptoCrossImpact_Codex_Stage01_Data_Acquisition_QC_Prompt_2026-10-27.md`.
No earlier config, changelog, code, data or session report existed. The approved
specification and existing tracked files are unchanged. No scientific deviation
or SPEC_CHANGELOG entry was necessary.

Branch `main`, initial/final HEAD `6d5639af60649a80b9dccffeaf63d99a49d4b780`.
Initial dirty state: supplied untracked `prompts/` only; preserved. Final dirty
state: that prompt plus new `.gitignore`, README, configs, data documentation and
small registry files, requirements, pytest.ini, scripts, src, tests and reports.
No existing tracked modifications, deletion, commit, push or branch change.
`git diff --check` passed. The supplied ignore rules were named `gitignore`;
copied them to active `.gitignore` without altering the original. Raw ZIPs,
canonical Parquet, `.venv`, temporary data and `.env` are ignored; registries are
trackable.

Used the existing **Python 3.14.6** `.venv` on an **8 GiB Apple Silicon Mac**.
Installed numpy, pandas, pyarrow, requests, PyYAML, matplotlib and pytest, with
exact resolved dependencies in `requirements.txt`. Imports and `pip check` pass.
No solver/ML packages, exchange credentials or system frameworks were installed.
Config/spec/working-code hashes, package versions and Git state are bound in
`data/registry/run_manifest.json` and command-specific run manifests.

## Actual acquisition, coverage and interpretation

Official Binance Vision USD-M perpetual last-trade **1m BTCUSDT/ETHUSDT**,
2024-01-01–2026-06-30 UTC. Checked current official README, archive and dataset
terms on 2026-10-27; retained accessed text locally. Dataset terms v1.0 updated
2026-08-26 permit this noncommercial research under **CC BY-NC-SA 4.0** with
attribution/share-alike for redistributed derivatives. Source attribution is in
the READMEs and QA report; raw data are excluded from Git.

Initial sandbox DNS failure was resolved by approved direct-network execution;
no provider restriction, authentication or rate limit was bypassed. Preflight
checked six pilot archives: May 2024, October 2025, May 2026, both assets. Pilot
ZIP/schema/coverage tests passed before full acquisition. Actual vendor headers
match the 12-column USD-M schema, UTC millisecond timestamps and
`close_time=open_time+59999ms`.

**60 expected / 60 downloaded / 60 validated / 0 quarantined / 0 missing**
symbol-months; all official SHA-256 checksums and ZIP CRC checks pass. No daily
fallback was needed. **2,626,560 source rows**; **1,313,280 paired valid minutes**;
zero missing keys, invalid bars or unmatched symbol minutes.

| Split | Paired valid minutes | Paired valid returns | Invalid/missing exclusions |
|---|---:|---:|---:|
| Train | 787,680 | 787,679 | 0 |
| Validation | 264,960 | 264,960 | 0 |
| Locked test, QC only | 260,640 | 260,640 | 0 |

The first sample bar has no preceding close. Returns carry valid prior-month
context, including formerly isolated pilots; none cross gaps or assets. Fields
are available at **open+60,000ms**, not at bar start. Flow is exactly exchange
quote-notional `2*taker_buy_quote_volume-quote_volume` in USDT. Values are retained
in float64 with exact source-to-Parquet numeric read-back; clocks/counts are
integer. No fitted liquidity normalization or regression target was computed.

Source-reported zero-volume bars: BTC 126, ETH 127; preserved with undefined flow
ratio and zero signed flow. October 28, 2024 includes shared zero-turnover/stale
intervals. All October zero bars have identical recorded OHLC and zero trade/
volume fields; genuine market-wide inactivity is **not independently established**.
Eight large-return minutes and 46 trailing stale flags per asset are diagnostics,
not exclusions. Eight development-only anomaly-day plots were rendered and
visually inspected; exact intervals and review evidence are in
`qc_anomalies.csv` and `qc_visual_review.json`. No test economic plots,
flow/return relationships or model-selection outcomes were inspected.

All **14 predeclared aggTrades symbol-days** completed, **31,109,040 aggregates**,
with official hashes/CRC, no missing aggregate IDs or out-of-order timestamps.
Buyer-maker=true gives negative aggressive flow; correct-sign mean absolute
errors are much smaller than reversed-sign errors. Daily p99 absolute signed
differences/turnover are **0.4885%–1.6023%**; at least one minute per day exceeds the
1% diagnostic threshold, so exact minute reconstruction is **QUALIFIED**. UTC
timestamp-floor matching and reversed-sign control were tested; shifted/bundle-
split conventions remain unverified. Official current documentation describes
100ms bundling and exclusions for insurance/ADL trades; these are possible causes,
not proven explanations of the historical discrepancies. The required kline
flow definition was retained. Only this operation's verified temporary tick ZIPs
were removed after durable audit summaries.

## Implementation, checks and reproducibility

Created `configs/core.yaml`, `src/cryptocrossimpact/data/{schema,storage,pipeline,trades}.py`,
thin Stage 1/figure scripts, tests, READMEs, 60 ignored canonical partitions and
the compact source/QC/audit/run registries. The CLI streams downloads with at
most three request attempts, checks identity/hash/CRC, writes Parquet atomically,
preserves quality masks and gaps, supports official daily fallback, and rechecks
upstream checksums on resume. Six cached pilots and all 14 cached audits were
reverified without downloading unchanged source data again.

Commands actually run: `pip install --no-cache-dir` for the seven Stage 1 packages;
`scripts/stage01.py preflight`, `pilot`, `acquire`, `audit`, `qc`;
`scripts/stage01_qc_figures.py`; pytest, import smoke, `pip check`, compile and
Git-ignore/diff checks. Each Python command used `.venv/bin/python`.

**Final pytest: 27 passed, 0 failed, 0 skipped**, including synthetic negative
fixtures, all six real-source pilots and full-core inventory. Ten pandas parser
deprecation warnings remain; explicit round-trip float parsing is intentional.
Initial month-boundary tests caught a pandas read-only view; fixed with an
explicit copy. A review caught future-sensitive stale-run labeling; changed it
to trailing run length, regenerated only the two affected agent-created
diagnostic columns and recorded the repair in their manifests. A regression
test verifies appending future bars cannot change prior flags. These repairs
changed no source fields, sample, split or research parameter. Final full QC
rebuilds all source fields/features and passes exact comparisons.

Safe verification/restart from the repository root:

```sh
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
.venv/bin/python scripts/stage01.py acquire
.venv/bin/python scripts/stage01.py audit
.venv/bin/python scripts/stage01.py qc
.venv/bin/python -m pytest -q
```

No required data or test remains pending. Daily fallback/blocked-provider branches
were not exercised on real failed sources because all monthly archives worked;
checksum/source-identity failures were exercised with fixtures. Stage 2/solver/
economic hypothesis tests were not run.

## Resources and handoff

Retained compressed monthly sources **113,291,084 bytes**; canonical data
**363,877,618 bytes**; environment about **351 MiB**. Total project approximately
**0.85 GB**, incremental about **0.84 GB**; conservative peak below **1 GB**,
including the largest temporary tick ZIP (80.7 MB) and atomic-write allowance.
Initial full-audit peak RSS **454,590,464 bytes** (about 434 MiB). Final disk has
about 41 GiB free; no storage ceiling approached. Precise measured/estimated
distinctions are recorded in `data/registry/resource_summary.json`.

Primary handoff: `reports/data/stage01_data_quality.md`,
`data/registry/source_manifest.json`, `qc_summary.json`, `trade_audit.json`,
`test_results.json`, and ignored `data/canonical/{symbol}/{month}.parquet`.
Safe checkpoint is complete Stage 1. **No user decision is required.** Await
separate Stage 2 authorization; preserve the locked-test firewall and the
supporting trade-aggregation qualification.
