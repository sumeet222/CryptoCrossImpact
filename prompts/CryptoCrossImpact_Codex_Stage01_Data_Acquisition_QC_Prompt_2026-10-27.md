# Codex Stage 1 — Repository Bootstrap, BTC/ETH Data Acquisition, and Quality Control

**Project:** CryptoCrossImpact  
**Stage:** 1 of 6 — data and quality control only  
**Date:** 2026-10-27  
**Authorized outcome:** a working, reproducible, validated local data foundation for the later kernel-estimation stage. This prompt authorizes the bounded free/public downloads specified below, not model fitting or any trading activity.

## 0. Authority, starting point, and execution style

You are Codex working in the **existing CryptoCrossImpact repository root**. The user's initial root contains **only** `AGENTS.md`, `.gitignore`, and an existing `.venv/` with **no dependencies installed**, plus the research specification that the user must copy in before you start (see below). Do not assume an existing Python package, source tree, datasets, config, Git history, remote, or working install.

**Before touching source/data:**

1. Read `AGENTS.md` completely.
2. Read `CryptoCrossImpact_Research_Specification_v1_2026-10-27.md` completely, especially §§0, 2–4, 6.4, 13–14, 18–19. It is the governing scientific/data reference; do not edit it without explicit user authorization. If it is not present in the local repository, **do not improvise from this prompt**: report that missing prerequisite and complete only harmless environment/repository inspection.
3. Inspect `pwd`, the local file tree, available disk/RAM, Python version, `.venv/` interpreter, `git status --short` (or state that Git is not initialized), and whether any local data or scripts already exist. Preserve all user files. Avoid hard-coded `/Users/...` paths.
4. Check the official source documentation and current dataset terms, including [Binance public-data README](https://github.com/binance/binance-public-data), [Binance Vision dataset terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md), and [the public archive](https://data.binance.vision/). Record the source/terms access date. This is **non-commercial research**; do not scrape around geo/access restrictions or rate limits. The dataset terms published in August 2026 describe a CC BY-NC-SA 4.0 non-commercial license and attribution/share-alike obligations for redistributed derivatives. Keep raw vendor archives outside Git and include appropriate source attribution in resulting documentation.

Operate **autonomously** on ordinary coding, safe download retries, schema handling, tests, and quality reporting. Do not ask the user routine setup questions. Work sequentially and finish independently feasible tasks. Do not claim a stage has passed when its data or tests did not complete. Follow the mandatory concise session-report protocol in `AGENTS.md`.

**Stage boundary:** No A/B/U kernel estimation, no fitting against the final test outcomes, no CVXPY execution solver, no impact calibration, no backtest, no theoretical-paper numerical replication, no optional SOL, spot, OKX L2, or Hyperliquid bulk datasets in this stage. Install numerical-optimization dependencies in later stages when needed; keep this stage lightweight.

## 1. Environment and minimal project bootstrap

- **Use the existing `.venv/`**, provided it has a working Python **3.11+** interpreter. Check `.venv/bin/python --version` and its `pip`. If it is absent or invalid, identify a suitable installed Python and **safely repair or recreate only the agent-created/bare environment** without deleting or replacing pre-existing user work. If the machine has no compatible Python, explain the exact prerequisite and continue only safe independent repo tasks; do not install an unrelated system-wide framework.
- Install **stage-appropriate** minimal dependencies inside `.venv`, not system Python: `numpy`, `pandas`, `pyarrow`, `requests` (or a comparably simple HTTP client), `PyYAML`, `matplotlib` for small QC plots if helpful, and `pytest`. Use `python -m pip`; choose compatible, stable versions for the Mac CPU/Apple Silicon environment. Do **not** install PyTorch, TensorFlow, CUDA, databases, MLOps tooling, `cvxpy`/SDP solvers or production services simply to initialize the repo.
- Supply **one** reproducible dependency declaration (`pyproject.toml` with simple project metadata, or `requirements.txt`; choose the simpler maintainable option). Record the exact tested resolved versions in a small reproducibility note or run/session manifest. Verify imports in the existing `.venv` and that basic smoke tests run from the repo root.
- Create only necessary paths, e.g. `configs/core.yaml`, `src/cryptocrossimpact/` with a lightweight data submodule, `scripts/` if useful, `tests/`, `data/{raw,canonical,tmp,registry}/`, `data/README.md`, `reports/{sessions,data}/`, and `README.md`. Preserve the supplied `AGENTS.md` and `.gitignore`. Ensure ignored raw/canonical/tmp/ZIP/Parquet data cannot be accidentally added to Git. No CI, Docker, live feed, API key or cloud configuration.
- If this directory is not a Git repository, record that. You may initialize local Git if it is safe, but **do not commit, push, create a remote, rewrite history or delete branches** without a separate user request. If already initialized, preserve the branch and dirty state.
- Provide a small documented **command-line entry point** (e.g. `python -m cryptocrossimpact.data ...` or a thin script), with clear commands to run source preflight, pilot download, full-core acquisition, QC, and optionally trade-sign audit. The exact CLI syntax is your engineering choice; document real tested commands in `README.md`.

## 2. Exact scientific data contract — implement, do not redefine

Use specification §§2–4 and §18. **Required** two Binance **USDⓈ-M USDT-margined perpetual futures** contract streams, **not spot, COIN-M, mark/index prices or Coinbase/OKX substitutes**:

| Field | Fixed stage-1 setting |
|---|---|
| Symbols | `BTCUSDT`, `ETHUSDT` |
| Venue/market | Binance, `futures/um`, perpetual contracts |
| Historical bar resolution | One minute (`1m`); 24/7 UTC |
| Inclusive core data dates | `2024-01-01 00:00 UTC` through `2026-06-30 23:59 UTC` |
| Development train | `2024-01-01` through `2025-06-30` |
| Development validation | `2025-07-01` through `2025-12-31` |
| Locked final test | `2026-01-01` through `2026-06-30` — **data-integrity checks only** during Stage 1; no return/flow outcome-based model selection |
| Partition scheme | One compact canonical Parquet partition per `symbol × UTC month` (or equivalent compact nonduplicating layout) |
| Core expected inventory | **30 calendar months × 2 symbols = 60 monthly archive partitions**, subject to verified vendor availability |

Official archive templates (exact instrument/market path matters):

```text
https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM}.zip
https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM}.zip.CHECKSUM
```

For a verified unavailable/broken monthly partition, consult the **matching official daily futures/um 1m kline archives** for its missing days; never fill absent observations using a different market, aggregated historical price site, or synthetic data. Keep a specific missing-source/coverage entry when no legitimate fallback works. Do **not** silently shrink the sample.

The official **USD-M futures kline** fields in vendor order must be checked against actual files (header/no-header handling):

```text
open_time, open, high, low, close, volume,
close_time, quote_asset_volume, number_of_trades,
taker_buy_base_asset_volume, taker_buy_quote_asset_volume, ignore
```

Determine timestamp units empirically and verify against the official USD-M documentation; expected historical USD-M timestamps are **milliseconds**, while **spot timestamp conventions differ**. Parse bar *open* and *end/availability* timestamps explicitly: for a bar opening `t`, its closing price and full minute's taker volume are available **only after that bar is completed**. Document whether vendor `close_time` denotes `open_time + 59,999 ms`, and maintain consistent UTC indexing. Do not relabel open-time volume as knowable at the bar start.

Calculate these **observation-level** derived columns without lookahead or proxy substitution:

```text
quote_volume = quote_asset_volume                       # USDT turnover
buy_quote_volume = taker_buy_quote_asset_volume
sell_quote_volume = quote_volume - buy_quote_volume
signed_taker_quote_flow = 2*buy_quote_volume - quote_volume
signed_taker_flow_ratio = signed_taker_quote_flow / quote_volume  # only if quote_volume > 0
log_close = log(close)
close_to_close_log_return = log(close_t / close_t_minus_1)
```

Returns are defined only across **consecutive, valid 1-minute bars**; do not compute across a missing predecessor, asset discontinuity, or malformed partition boundary. For legitimate zero-volume rows, preserve recorded price/zero volume while leaving the ratio undefined, with a documented rule. **Do not calculate the specification's fitted liquidity normalizers `L_i`, kernel design, or regression targets `y_i` in this stage**: those depend on training/refit windows in Stage 2. Preserve enough base fields for exact subsequent reconstruction.

Keep vendor raw columns (or their lossless numeric equivalents), source lineage, `symbol`, UTC bar open/close times, and **explicit train/validation/test labels** from the fixed calendar. Do not create physically separate copies of the same cleaned observations for each split, model, seed or experiment. A logical split mask/filter is enough.

## 3. Acquisition plan: small validated pilot, then the full 60 archives

### 3A. Cheap source/schema/storage preflight — mandatory before bulk download

1. Check actual free access, current terms, expected paths and available local space; no VPN/proxy/circumvention. Detect HTTP errors, blocked access, network failures and missing archives as **different statuses**.
2. Inspect a **small, predeclared** sample from train, validation and test (for example `2024-05`, `2025-10`, `2026-05`, both assets). For the test month inspect **structure, dates, completeness and field bounds only**, not economic relationships or return/predictor plots used to tune the study. Preflight with archive metadata/checksums and no full-dataset duplication; do not repeatedly redownload an unchanged verified pilot.
3. Confirm real CSV schema, whether headers are present, UTC timestamp units, minute coverage, OHLC/quote-volume semantics, actual `quote_asset_volume` and taker-buy quote fields, compressed/uncompressed sizes, and a rough extrapolation to all 60 partitions. Do not treat synthetic fixture passes as real-vendor verification.
4. Set the initial **30 GB incremental on-disk budget** across repo downloads, installed packages and derived data. Warn near **25 GB**, **stop before >30 GB** for user approval; budget for peak temp files and free disk rather than assuming ZIP and extraction never coexist. Aim for under **8 GB RAM**. Do not silently truncate the 30-month study to fit. Delete only *this operation's* checked, superseded temporary archives after safe canonical conversion; don't remove pre-existing user data.
5. If the preflight fails, write a specific source/terms/schema/storage hold and continue safe setup/testing/report work; **do not pretend the full data were acquired**.

### 3B. Full-core acquisition — proceed automatically if preflight passes

- Obtain **all 60 required symbol-month partitions**; bounded retries (at most three attempts per failed request with backoff) and modest concurrency/streaming (sequential or few connections). A failed download must not leave a file marked valid. Do not use exchange accounts or API credentials.
- For each ZIP: obtain/check official `.CHECKSUM` where offered; verify SHA-256 against its contents, and ZIP CRC/decompression. If checksum unavailable, record that transparently plus your own content hash. Record the actual download URL, UTC retrieval date, hash, bytes, vendor revision when exposed, row count, first/last timestamp, all QA status and canonical path. Treat corrupted or inconsistent files as quarantined, not good data.
- Convert **one partition at a time** to compact Parquet with sane dtypes, preserving exact timestamps and sufficient numeric precision (especially prices/USDT quote notionals). Write atomically, validate the written partition's rows and schema, then safely discard only agent-created temporary ZIP/CSV artifacts where appropriate. Keep no duplicate `raw + extracted CSV + entire dataframe dump + per-split Parquet` set.
- Make the workflow **idempotent/resumable**: a successful partition with matching source identity and passing QA can be skipped; a failed partition is retried/diagnosed without losing previous validated partitions. Detect and report if an upstream source ZIP/checksum has changed rather than blindly trusting a stale cache.
- If the monthly archive is absent/corrupt, attempt official **daily futures/um klines for the affected dates**. Preserve source attribution to the daily substitute and flag differences. Missing dates after this are a **coverage issue**, not a reason to invent prices/trades.
- Do **not** download all raw ticks, all L2, or third-party archives just because they are linked in the research specification.

### 3C. Small independent taker-sign audit — supporting QA, not a new dataset

After the core pilot works, when public access and budget permit, use the official **daily** `futures/um` `aggTrades` archive for **both symbols** on the seven predeclared audit dates in specification §3.3:

```text
2024-05-06, 2024-11-04, 2025-05-05,
2025-08-04, 2025-11-03, 2026-02-02, 2026-05-04
```

Exact path pattern:

```text
https://data.binance.vision/data/futures/um/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{YYYY-MM-DD}.zip
```

Verify actual CSV column order and timestamps. For an aggregate trade, `isBuyerMaker=true` means the **buyer was passive** and the **aggressor was the seller**, so its signed quote notional is **negative** `price × quantity`; otherwise positive. Compare its minute aggregation with the official 1m `2*takerBuyQuote - quoteVolume` as a *diagnostic*. Log discrepancies, missing identifiers/timestamps, alternative matching conventions and absolute/relative error distributions. Avoid claiming exact equality without checking exchange conventions and timestamp boundary effects. Do not use aggregated trades to reconstruct parent orders. If the 14 daily tick files are too large, inaccessible or unusually burdensome, execute a **documented smaller set (at least one train and one validation date)** and label the audit `QUALIFIED`, not full coverage. It must **not prevent core completion**.

**Optional book-depth note:** The specification's Binance `bookDepth` one-week pilot and OKX L2 are **not required for this stage**. Do not run broad book-depth acquisition. If time and bandwidth remain, a tiny explicitly labeled metadata/schema probe is fine; do not treat band-depth as full executable order-book levels or make it a Stage-1 acceptance dependency.

## 4. Data quality checks and scientific safeguards

Implement modest, automated per-symbol/per-month checks plus cross-symbol alignment diagnostics. At a minimum:

1. **Identity:** correct provider, market `futures/um`, symbol, kline interval, monthly/date range, quote-volume field, price type. Wrong market or symbol must fail with a clear error; never accept spot or COIN-M just because columns look similar.
2. **Clock:** UTC, timestamp magnitude, one-minute alignment, verified open/close semantics, sorted strictly unique `(symbol, open_time)` keys, contiguous 60-second increments except explicitly documented gaps; no duplicate months, DST shifts, timestamp overflows or rows outside intended month. Evaluate expected bars using actual UTC calendar months (including leap days).
3. **Prices/volume:** finite positive OHLC prices and OHLC ordering (`low ≤ open,close ≤ high` allowing only justified numerical tolerance); nonnegative base/quote/taker-buy volumes and trade counts; `0 ≤ takerBuyQuote ≤ quoteVolume` within a small defensible rounding tolerance; never coerce large violations into clipping. Mark unexplained anomalies.
4. **Rows and gaps:** missing/duplicated-minute counts, raw row counts, zero-volume genuine bars versus missing data, and noncontiguous pairs. Do **not** forward-fill prices, backfill quote volume or construct fictional zero-volume bars to get exactly 1,440 observations/day.
5. **Derived definitions:** independently hand-calculate `buy/sell/q`, aggressor sign, quote-notional units, normalized imbalance bounds, return values, and the no-cross-gap rule on tiny fixtures. An already-return quantity must never be differenced twice. Test month boundary transitions where records remain contiguous.
6. **Paired coverage:** synchronized BTC/ETH timestamps and exact intersection counts by month/split, plus reasons for any unmatched minutes. **Do not** silently coerce an inner join without preserving how many observations were lost or why.
7. **Availability and leakage:** stage-1 features must have a declared bar-completion availability time. Assert fixed train/validation/test membership and correct boundaries. QC of locked 2026 test records is **allowed**; no 2026 response correlations, predictive performance, kernel tuning, sample cherry-picking or trading outcomes during Stage 1.
8. **Source/version:** checksum/ZIP integrity and read-back of canonical Parquet; verify canonical rows match the checked source, with no missing money fields after conversion. Record per-partition SHA/checksums, UTC source date and failures.

For suspicious price jumps, stale closes or other large flags, save compact *QC-only* summaries (and at most a few selected diagnostic plots of truly anomalous days). Do not hide or silently drop offending rows; create quality masks and an explicit exclusion-reason count. Determine actual valid paired core sample **without using economic outcome preferences**.

Save a concise **data registry** under `data/registry/` (small JSON/CSV, Git-trackable), `reports/data/stage01_data_quality.md` containing per-symbol, per-split and per-month QC summaries, source accessibility, anomaly/missing counts, aggregate-coverage statistics and reproducibility commands. Plot optional QC summaries only if genuinely informative.

## 5. Minimal code/tests and expected artifacts

Implement **only** the modules Stage 1 needs, roughly:

- `src/cryptocrossimpact/data/`: official archive URL manifest, downloader, hash/ZIP verification, schema parser, per-month canonicalization, QA/coverage, optional trade-sign audit, and small CLI.
- `configs/core.yaml`: exact Stage-1 sample, symbols, splits, archive templates, storage/QA defaults, seed `20261027` if randomness arises; later stages extend model configuration here without changing sample by accident. Don't introduce conflicting scientific defaults.
- `tests/`: a few fast unit tests and at least one real downloaded-vendor pilot integration test. Include negative cases for spot-vs-USD-M, wrong symbol, bad timestamp units/header, duplicate bars, missing predecessor return, future-looking bar labels, and incorrect aggressor sign.
- `data/registry/`: compact `source_manifest.json`/CSV and QC summaries, no large binary data.
- `data/canonical/`: the **one** local compact cleaned monthly corpus (Git-ignored).
- `data/README.md` and root `README.md`: official source links/license attribution, dataset identification, local disk estimate, exact setup and reproducible pilot/full/QC/audit commands, expected outputs, current known holds.
- `reports/data/stage01_data_quality.md` and one new mandatory `reports/sessions/YYYYMMDD_HHMM_stage01_data_session.md` report. If Stage 1 is incomplete, state the precise remaining partitions and commands to resume.

Tests to actually execute, with their outcomes recorded:

```text
Environment/import smoke
Synthetic parser + flow math + clock + gap handling fixtures
Wrong-source/schema/spot rejection fixtures
Canonical write/read and checksum failure handling
One or more real vendor pilot ZIP ↔ canonical rows cross-check
Full-core month/split coverage audit (only if acquired)
AggTrades sign/aggregation audit (if available)
Git ignore check for ZIP/Parquet/.venv and secrets
```

Avoid general-purpose data warehouse classes, excessive test matrices, unnecessary dashboards, giant raw logs and multiple redundant feature stores. Brief docstrings should state shape, timestamp units and notional/return units.

## 6. Stage-1 completion decision (G0/G1)

**G0 — source feasibility: PASS** only if at least a real correctly interpreted BTC and ETH USD-M 1m pilot is downloaded, verified against source, parsed, and the disk/terms/schema feasibility checks are documented. Tests alone do not satisfy G0.

**G1 — sample accepted: PASS** only when the **entire specified 2024-01 through 2026-06 core period** has an auditable manifest for every intended symbol-month, required data were obtained (or explicitly justified official daily fallback used), material invalid/missing intervals are precisely counted and flagged, BTC/ETH paired coverage is known, train/val/test boundaries are correct, the canonical dataset is reproducible, and the critical tests pass. A small number of documented quality exclusions does **not automatically invalidate** the study; a material source/coverage/units uncertainty must be labeled `QUALIFIED` or `BLOCKED` with why and its affected partitions. Do not pretend 60 successful archive reads means scientifically perfect bars.

**Meaningful Stage-1 deliverable:** the next Codex session can begin Stage 2's lag/normalization/PSD-constrained kernel estimation without redownloading or deciphering the base dataset; it can find all assumptions, split cutoffs, sample attrition, commands and provenance.

**End-of-session response must include:**

1. `PASS / QUALIFIED / BLOCKED` for G0 and G1 separately, with specific evidence rather than inflated claims.
2. Environment/dependencies installed and reproducible command(s).
3. Number of **expected/downloaded/validated/quarantined/missing partitions**, paired valid UTC minutes and exclusions by train/validation/test.
4. Actual tests executed and passing/failing counts; independent AggTrades sign audit results or reason not completed.
5. Important new paths, session report, Git start/end status, retained/peak disk use, and any licensing/access blockers.
6. Exact safe restart command for an incomplete run, and explicit statement: **no kernels/strategies/backtests were fitted or run**.

The project is **CV research**, not infrastructure engineering. Prioritize complete source integrity and economically correct data definitions over elaborate orchestration. Do not spend substantial time on optional streams or aesthetic reports while the core 60 partitions or critical integrity tests remain unresolved.
