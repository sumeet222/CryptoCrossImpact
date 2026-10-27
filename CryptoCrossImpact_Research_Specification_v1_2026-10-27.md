# CryptoCrossImpact — Research and Experimental Specification

**Version:** 1.0 (initial executable research specification)  
**Date:** 2026-10-27  
**Working project:** `CryptoCrossImpact`  
**Research title:** *Learning Admissible Cross-Impact Propagators for Joint Execution of Cryptocurrency Perpetual Futures*  
**Status:** Proposed protocol; **no data have been downloaded, models fitted, experiments run, or empirical conclusions established**.  
**Intended use:** Stable reference for this ChatGPT Project and the eventual Codex implementation. This is **not** an `AGENTS.md`, a prompt for Codex, a deployment design, or an assertion that the experiment has succeeded.

> **Scope and provenance.** This document turns `CryptoCrossImpact_Research_Handoff_2026-10-27.md` into a concrete proposed experiment, with additional review of the 2026 Abi Jaber–Neuman–Tuschmann paper, related literature, exchange data documentation, and known archive defects as of the date above. **New configurations below are design decisions proposed here, not earlier decisions already made by the user.** Exact file accessibility, download sizes, schema variations, geographic access, and reuse terms must pass the acquisition checks before the protocol is regarded as operational. Public-flow calibration is *not* identification of the causal effect of our own trades.

## 0. How this specification is to be used

- **Core protocol (default):** Two Binance USDⓈ-M/USDT-margined perpetual contracts, `BTCUSDT` and `ETHUSDT`; 1-minute historical flow; admissible **diagonal versus matrix-valued transient impact**; a mathematically verified deterministic execution solver; chronological, independent **scenario-based** evaluation with honest limitations. This is the minimum complete CV project.
- **Core-plus (conditional):** Deterministic, time-inhomogeneous nonconvolution Volterra kernel informed by *ex-ante* liquidity forecasts; optional small-sample same-venue L2 checks; predictive-signal experiment **only if an out-of-sample signal survives its gate**.
- **Extensions, not obligations:** SOL as third asset; genuine stochastic Fredholm/conditional-expectation solution; spot–perpetual execution; trader/order-lifecycle analysis using Hyperliquid L4; new mathematical theorem.
- **Change control without bureaucracy:** Frozen *scientific principles* are noncausality awareness, chronology, equal constraints, admissibility, independent evaluation, and accurate claim labeling. Numerical defaults (listed in §2) may be revised **before test inspection**, based on data validation or training/validation evidence. Record a short dated `SPEC_CHANGELOG.md` entry giving parameter, reason, and whether the untouched test period was viewed. If the test set has been inspected, any redesign requires a newly reserved test period or must be called exploratory. There is no need for formal tickets or production-grade processes.
- **Reference priority:** Primary source [R01] for the continuous-time theory; [R02–R06] for admissibility/calibration/identification; official venue documentation [D01–D05] for data semantics. A source citation is **not** a claim that associated data have been obtained.

## 1. Research problem, contribution and nonclaims

### 1.1 Main question

**Can a parsimonious, economically admissible matrix-valued transient impact model, calibrated from freely available BTC/ETH perpetual-futures order-flow data, provide a more stable description of joint flow–price responses and more robust *model-based* joint-liquidation decisions than separate single-asset models?**

More specifically:

1. **Statistical question:** After controlling for lagged own/cross flow and common price dynamics, are nonzero off-diagonal coefficients stable across time and useful on held-out data? Are they robust to a no-manipulation restriction?
2. **Control question:** How does a calibrated matrix Volterra propagator affect multi-asset liquidation schedules relative to TWAP, *forecast* VWAP, independent optimal execution, and a joint risk-aware optimizer with zero cross-impact?
3. **Robustness question:** Do alleged improvements persist when the evaluation kernel, temporary liquidity cost, parameter estimates, and market regimes differ from those assumed by the optimizing strategy?
4. **Conditional additional question:** Does a simple ex-ante, deterministic *nonstationary* kernel (and, separately, a genuinely available predictive signal) add enough empirical value to justify the added complexity?

### 1.2 Expected contribution, without prejudging results

The intended contribution is an **auditable applied mathematical-finance study**: real crypto public data → constrained statistical response estimation → admissible multivariate Volterra cost model → verified deterministic execution optimization → matched out-of-sample scenario comparison and misspecification analysis. A strong **negative result** on cross-impact identifiability/stability is publishable-quality research practice and valuable on a CV when adequately supported.

**Do not claim** to have invented multivariate impact, Volterra optimal control, no-manipulation criteria, the Fredholm resolvent, or the AJNT theorem. The 2016 Alfonsi–Klöck–Schied and 2017 Mastromatteo et al. papers already supply major precedents [R02, R04]. A prior search did **not identify** the exact end-to-end crypto empirical treatment, but it did **not prove priority**. Never describe simulation-only cost differences as demonstrated live savings. See §15 for allowable CV wording.

### 1.3 Structural versus reduced-form impact: the governing limitation

Let public aggressive-flow signed notional in asset `j` be `q_j,t`; suppose returns satisfy a statistical response equation. Its coefficients are **conditional public-flow/price associations**, contaminated by correlated information, autocorrelated flow, feedback and unobserved parent orders. They need not equal the **causal propagator for a trader's intervention**. More precisely:

- Cross-venue BTC transmission ≠ BTC-to-ETH cross-asset response ≠ causal displacement of ETH by **our BTC execution**.
- A fitted response kernel is suitable for **conditional price-response description**. Its use as an execution kernel is an **explicit structural modeling assumption** tested through sensitivity/independent scenarios, not a finding about hypothetical interventions.
- Historical top-of-book/depth lets us estimate **mechanical liquidity consumption**; it cannot reconstruct participants' responses to an order that never occurred.
- Evaluation on the identical calibrated cost function optimized by a policy is **in-sample-by-construction**, even if the prices originally used for calibration were historically held out. All policies must face separate evaluation assumptions or separately estimated parameters.

The distinction is central to [R05, R06, R08, R09, R25]. **The lack of parent-order/intervention data is the principal scientific risk**; solver implementation is not.

## 2. Frozen initial experiment configuration

This table gives concrete defaults. Changes may be made according to §0, not silently.

| Element | Initial specification |
|---|---|
| Instruments | Binance USDⓈ-M perpetual futures `BTCUSDT`, `ETHUSDT`; no contract rolls. SOL only after core succeeds. |
| Quotation / clock | All timestamps **UTC**. Quotes in USDT; trade directions relative to buyer aggressor. Holidays/weekends included (24/7). |
| Primary data | Exchange-public **1-minute futures kline archives** (OHLC, volume, **taker-buy quote volume**) [D01]; optional Binance **daily 30-second band-depth** [D02]. |
| Sample | **2024-01-01 00:00 UTC to 2026-06-30 23:59 UTC**, inclusive, subject to validated availability and QA. No use of later data to set hyperparameters. |
| Development train | 2024-01-01 through **2025-06-30**. |
| Development validation | **2025-07-01 through 2025-12-31**. |
| Locked final test | **2026-01-01 through 2026-06-30**. |
| Aggregation | 1 minute; keep trades/returns synchronized by **bar closing time**. |
| Maximum impact memory | 60 minutes at 1-minute intervals; sensitivity 30 and 120 minutes if validated. |
| Initial kernel family | One or two exponential components; initial half-life/decay **time constants** `τ ∈ {5, 30}` minutes (time constant, **not** half-life). Secondary train/validation search `τ ∈ {2, 5, 10, 30, 60}` minutes, at most two components. |
| Main fitted models | `A`: diagonal, stationary admissible; `B`: full `2×2`, symmetric-PSD, stationary admissible; shared nuisance regressors. |
| Nonstationary extension | `C`: preannounced deterministic liquidity-scaled `G(t,s)`, **only** if model B calibrates sensibly (§7.4). |
| Predictive signal | `D`: gated **secondary** experiment, not presumed successful. |
| Execution | Sell **both** initially positive inventories, no purchases/shorting/round trips; hard terminal liquidation, 60-minute horizon, 1-minute slices. |
| Horizon sensitivity | `T ∈ {30, 60, 120}` minutes; primary `60`. |
| Episode starts | 00:00, 06:00, 12:00, 18:00 UTC every eligible day; predetermined, nonoverlapping for the primary horizon. |
| Start quantity | For each contract, `2%` of **ex-ante predicted 60-minute traded USDT notional**; robustness `0.5%, 1%, 5%`. Fixed-dollar examples only as secondary. |
| Child-order participation cap | Maximum `10%` of **forecast** (never future realized) 1-minute volume; sensitivity `5%, 20%`; all baselines identical. |
| Reference forecasting lookback | Trailing 28 calendar days, excluding the current bar and all future observations. |
| Optimization | Risk-adjusted, hard-inventory, nonnegative, convex quadratic program; available-information temporary-cost proxy (§9). |
| Main benchmarks | Forecast-TWAP, causal forecast-VWAP, independent single-asset optimizer, joint zero-cross-impact risk-aware optimizer, cross-impact optimizer. |
| Fees/spread sensitivities | Taker `5` bps/side as **illustrative** primary cost assumption, `2, 5, 10` bps stress; half-spread `0, 1, 2` bps if BBO unavailable. These are **not measured historical trading fees or spreads** [D05]. |
| Regularization | Ridge penalty on matrix-kernel parameters; initial standardised-loss grid `0, 10^-4, 10^-3, 10^-2, 10^-1, 1`. Validation selects within this prespecified grid. |
| Primary repeated fitting | Select hyperparameters using train/validation, then walk-forward **monthly** on test with a trailing **365-day** estimation window ending strictly before the refit month. |
| Primary uncertainty | Paired **moving seven-day block bootstrap**, 500 replicates, by **day** of execution episodes; train-calibration uncertainty separately (§12). |
| Compute expectation | CPU-only MacBook Air-scale models; no deep nets, cloud deployment, streaming infra, live trading, or massive L4 download required. |

**Calendar exclusions:** Missing/inconsistent required BTC/ETH bars invalidate an affected regression range or execution window; never silently fill prices or signed flow. Funding-settlement windows should be marked and handled consistently (§4.6); do **not** pick windows based on observed profits/returns. Data QC may exclude intervals by **ex-ante specified quality rules**, with counts by split.

## 3. Required data — what exactly to obtain, where, and why

### 3.1 Primary archive: Binance USDⓈ-M BTCUSDT/ETHUSDT **1-minute klines** (required)

**Official source:** [Binance Public Data — repository and documented schema](https://github.com/binance/binance-public-data) [D01]. Data site: <https://data.binance.vision/>. Obtain **monthly futures `um/klines`** data in `1m` resolution for `BTCUSDT` and `ETHUSDT` for **every month 2024-01 through 2026-06** (30 monthly ZIPs per symbol, **60 ZIPs** total; check each corresponding `.CHECKSUM` and manifest). Filename template:

```text
https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM}.zip
https://data.binance.vision/data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM}.zip.CHECKSUM
```

**Examples, paths not separately downloaded as part of writing this document:**

```text
https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2025-01.zip
https://data.binance.vision/data/futures/um/monthly/klines/ETHUSDT/1m/ETHUSDT-1m-2026-06.zip
```

Expected documented futures kline columns, in CSV field order: `open_time`, `open`, `high`, `low`, `close`, `volume` (base), `close_time`, `quote_asset_volume`, `number_of_trades`, `taker_buy_base_asset_volume`, `taker_buy_quote_asset_volume`, `ignore`. Check whether actual archived ZIP includes a CSV header; make parsing resilient to either case. Binance **USD-M futures** timestamps are documented in **milliseconds** in the example; **do not assume the same for spot** (spot archive convention changed to microseconds in 2025). Validate timestamp magnitudes for every stream.

The 1-minute bars provide **exact exchange-reported within-bar taker-buy quote volume** and total quote volume; their difference yields a coarse signed-taker-flow estimate without downloading millions of individual ticks:

\[
Q^{\mathrm{buy}}_{i,t}=\mathrm{takerBuyQuote}_{i,t},\qquad
Q^{\mathrm{sell}}_{i,t}=\mathrm{quoteVolume}_{i,t}-Q^{\mathrm{buy}}_{i,t},\qquad
q_{i,t}=Q^{\mathrm{buy}}_{i,t}-Q^{\mathrm{sell}}_{i,t}
=2\,\mathrm{takerBuyQuote}_{i,t}-\mathrm{quoteVolume}_{i,t}.
\]

Here `q>0` denotes **net buyer-initiated** USDT notional. Retain the raw buy/sell/total quote volumes, trade count and OHLC, not merely derived imbalance. This is an **aggregated signed notional per minute**, not individual parent orders, full L2, or the price path inside the minute.

**Acquisition acceptance:** All 60 expected months exist and decompress; file and checksum match when published; exactly one ordered UTC row per instrument per minute; bar interval and timestamp unit confirmed; values finite and economically consistent; `0 ≤ takerBuyQuote ≤ quoteVolume` up to explicitly justified rounding tolerance; both instruments aligned. If a file is absent/corrupt, use the official `daily/klines` archive for the missing period and record the substitution; do not create synthetic fills.

**Storage:** Keep compressed ZIPs outside Git or delete after checksummed, schema-audited Parquet extraction according to available disk. Reuse one canonical cleaned Parquet partition per symbol/month; no redundant feature-dataset copies.

### 3.2 Optional same-venue Binance **bookDepth** at ~30-second cadence (depth proxy, not full L2)

Official public archive prefix: <https://data.binance.vision/?prefix=data/futures/um/daily/bookDepth/BTCUSDT/> and equivalent `ETHUSDT`. Expected daily file template:

```text
https://data.binance.vision/data/futures/um/daily/bookDepth/{SYMBOL}/{SYMBOL}-bookDepth-{YYYY-MM-DD}.zip
```

Expected CSV schema **from published archive issue examples**: `timestamp,percentage,depth,notional`; rows report cumulative depth/notional for signed percentage bands from the reference market price, often ~30-second snapshots. They are **NOT** full price-level order books, exact best bid/ask, queue position, or necessarily a directly executable depth curve. Do not infer a spread or arbitrary tick-price bookwalk from these columns. Use only for **lagged band-liquidity proxies, depth asymmetry checks, and validation of traded-flow/liquidity magnitudes**.

**Important known integrity warnings, both independently published in the Binance public-data issue tracker:** [Issue #431: some 2025 bookDepth inconsistencies](https://github.com/binance/binance-public-data/issues/431), [Issue #496: 2026-09 frozen ask-side bands](https://github.com/binance/binance-public-data/issues/496), and [Issue #512: incomplete October 2026 archives](https://github.com/binance/binance-public-data/issues/512). Do **not** blindly rely on a clean checksum or assume all historical days are intact. The core final test is deliberately limited to **2026-06**, not the later September/October defect interval, but earlier days still require independent sanity checks. If band-depth fails QC, retain the 1-minute flow model and use **scenario-only liquidity assumptions**, labeling the limitation.

**Practical acquisition:** Download an initial **one-week pilot** for BTC/ETH near **2025-05-05**, then, if valid and small enough, preselect **first Monday of each month and the following six days** within the training/validation/test ranges (a systematic sampled subset). Do not download the entire daily archive up front. Matching episodes remain selected from the complete 1-minute bar series regardless of the depth subset.

### 3.3 Optional **tick-level aggressor flow** for checking 1-minute aggregation

Official Binance USDT-M **daily `aggTrades`** files (not 1m kline or raw individual fills):

```text
https://data.binance.vision/data/futures/um/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{YYYY-MM-DD}.zip
```

Expected columns: aggregate trade ID, price, base quantity, first/last trade ID, timestamp, `isBuyerMaker`. When `isBuyerMaker=true`, the **buyer was passive (maker)** and **the seller was aggressive**; assign negative trade-sign to its `price × quantity`. When false, assign positive. Do not reverse signs. Trade aggregation reduces records but does not identify parent orders. Sample **seven predeclared UTC pilot dates** across periods: **2024-05-06, 2024-11-04, 2025-05-05, 2025-08-04, 2025-11-03, 2026-02-02, 2026-05-04** (both symbols). These dates were set for calendar distribution, **not on market outcomes**.

Checks: signed quote turnover from ticks approximately matches 1-minute `2*takerBuyQuote - quoteVolume`, allowing for exchange aggregation/reporting differences; timestamps/rounding consistent; higher-frequency 1s/10s sensitivity if useful; publication lag and out-of-order records diagnosed. This is **supporting QA only** in the minimum project and does not justify replacing the long 1-minute sample. If archives exceed the Mac storage budget, use **two dates per split** selected in advance and disclose the change.

### 3.4 Deep-book execution-cost **supplement**: OKX historical L2 (conditional, separate venue)

**Official landing page:** <https://www.okx.com/en-us/historical-data> [D03]. The exchange advertises tick-trade history since 2021-09 and historical high-resolution L2 order-book data since 2023-03. Official documentation records a historical download endpoint `GET /api/v5/public/market-data-history` (announced 2025-09-02; see [OKX changelog](https://www.okx.com/docs-v5/log_en/)); use the **public** service appropriate to the user's permitted regional domain. A documented parameter summary in API-client documentation [D04] gives:

- `module=1`: tick trades; `2`: 1-minute candles; `3`: funding; `4`: 400-level order books; `5`: 5,000-level books **from 2025-11-01**; `6`: older 50-level depth (being deprecated).
- `instType=SWAP`, `instFamilyList=BTC-USDT,ETH-USDT`, `dateAggrType=daily`, UTC dates `begin`/`end` as Unix milliseconds; **current** documented maximum is **10 inclusive days** per request (not older 20-day examples). Responses point to historical download files; parse file metadata and check availability rather than guessing a static ZIP URL.
- Book modules use **UTC** daily dates; other archived modules can use **UTC+8** date boundaries. Derivatives book sizes can be measured in **contracts**, requiring the historical instrument's **contract multiplier** and quote conversion, not just raw size.

**Pilot target:** 400-level historical order books **plus same-venue trades** for `BTC-USDT-SWAP` and `ETH-USDT-SWAP` on **2025-05-05** (train), **2025-10-06** (validation), and **2026-05-04** (test), at most **one UTC day per split** initially. Before downloading more, check actual record granularity, volume, accessible history, public/free status, regional restrictions and total byte size. Process **streaming** to sparse 1-minute or 10-second snapshots and basic spread/depth/book-walk summaries, then discard unneeded raw bytes if allowed. **Never combine Binance BTC trades with OKX BTC book levels as though they were a matched single-venue historical execution.** OKX is a separate calibration/evaluation vignette: its own trades, symbol/contract convention, fee assumptions, and forecasts must be used.

If the OKX public download is blocked, costly, unreasonably large, or unavailable in the user's region, **skip this optional supplement**; it is not a precondition for the core. A historical book snapshot gives **mechanical** bookwalking and immediate spread only, not a simulated market's adaptive response.

### 3.5 Other public archives — only if justified by a specific extension

| Candidate | URL, verified scope and usage rule |
|---|---|
| **Hyperliquid public Level-4 research dataset** | <https://zenodo.org/records/18184441> [D06]. Zenodo lists **195.3 GB**: BTC/ETH/SOL order-status and book diffs in **Dec 2025**, trades Oct 2025–Jan 2026, a reader and `SCHEMA.md`; order-status archive includes pseudonymous lifecycle information. **Do not download the full dataset** for the CV minimum. Small-file previews/schema can guide a **future** parent-order proxy study; downloads are mostly large **monthly TARs**, not conveniently per-day ZIPs, so per-day partial downloading is **not guaranteed**. Check usage rights. |
| **Bybit public trade files** | <https://public.bybit.com/>; possible event-level replication but **historical L2 availability is not established** by the existence of public trade files. |
| **CryptoHFTData** | <https://www.cryptohftdata.com/>; exchange-specific tick/depth collections reportedly starting around mid-2025. **Actual free access, licensing, and data limits were not confirmed**; not a core dependency. |
| **Binance spot and cross-venue pair** | Spot trade archives under `data/spot/...`; instrument conventions and timestamp units differ; reserve for a **separately specified spot/perp extension**. |

### 3.6 Optional settlement, funding and fee inputs

- **Historical futures funding:** Official Binance `GET https://fapi.binance.com/fapi/v1/fundingRate?symbol=BTCUSDT&startTime=...&endTime=...&limit=1000` and analog for ETH; pagination required [D05]. Records include `fundingTime`, `fundingRate` and mark price. Treat access restrictions explicitly. Funding is **not simply a constant 8-hour rate for every contract/date**; use recorded settlement times. For the primary 60-minute schedule, mark windows crossing actual settlements. If the strategy holds residual contracts across a settlement, compute the corresponding inventory-weighted cash flow for every policy; if funding data are inaccessible, report/exclude affected windows by **timestamp-only fixed rule**, not by realized rate sign.
- **Fees:** Binance publishes **illustrative regular-user maker 0.02% / taker 0.05%** in its fee-structure explainer, while saying fee schedules can change [D07]. Consequently `5 bps` is an **assumption** (not reconstructed historic tier), tested at `2/5/10 bps`. Pure *sell-only, equal-total-notional, all-taker* strategies pay approximately equal total fees, so **constant fees do not create a scheduling advantage**; round trips, heterogeneous venue/tier, and participation-related slippage change that.
- **Spread/BBO:** There is no validated historical BBO in the required Binance 1m kline files. `0/1/2 bps` half-spread is an openly labeled **sensitivity proxy**, never a claimed measured Binance spread. If using OKX L2 for same-venue book-walk vignettes, use the actual pre-execution bid/ask of that venue/date.

### 3.7 Feasibility/security/resource gate

Before bulk collection, run a 3-day **metadata and sample QA** check on each required stream, documenting time units, archive layout, byte size, missing bars, download legality, number of files, and observed compression ratio. Aim for **well under 30 GB** local working storage for the minimum study and typically **under 8 GB RAM** by processing in monthly partitions. These are **project budgets, not established data sizes**. If free depth data require hundreds of GB, **do not scale blindly**; preserve the minimum study instead. No credentials in repository, generated configs, docs or prompts. Git holds code, configuration and small figures, **not raw financial data**.

## 4. Data definitions, conditioning and QC

### 4.1 Time, prices and signed order flow

Each exchange kline is indexed by its **bar end** `t`; close-to-close log return is `r_i,t = log(C_i,t/C_i,t-1)` and available only **after** bar `t` closes. The signed flow `q_i,t` describes **trades during that same closing bar**, and is likewise known only at its end. Future `q_i,t` may be used in an **ex-post contemporaneous response regression** but **cannot** be an input to a trade decision made before or during bar `t`. Distinguish:

1. **Descriptive nowcast/response**: explain bar `t` return with its *contemporaneous* recorded flow, plus lagged predictors; **not tradable forecasting**.
2. **Deployable signal**: predict returns from information ending at **bar `t-1` or earlier**, with honest available-time assumptions; its performance is measured separately.

Compute `q` in **USDT notional**, not base coins. `vbuy_i,t = takerBuyQuote / quoteVolume` if denominator positive; normalized order-flow imbalance `ofi_i,t = q_i,t / quoteVolume_i,t`; mark zero-volume bars **missing or zero-flow after explicit verification**, never infer a price. Distinguish **trade-based signed volume** from *true L2 order-flow imbalance*, which additionally includes limit submissions and cancellations [R17].

### 4.2 Physical-unit normalization (important for no-manipulation)

Using raw per-asset percentage returns with differently scaled BTC/ETH volume can invalidate a naive symmetric/PSD constraint. Define **one fixed, positive, train-only liquidity unit** `L_i` as the **median positive 1-minute quote volume (USDT)** in the estimation window, recomputed only at authorized monthly refit times. For a signed USDT flow `q_i,t`, define:

\[
f_{i,t}=\frac{q_{i,t}}{\sqrt{L_i}},\qquad
 y_{i,t}=10^{4}\sqrt{L_i}\,\Delta\log C_{i,t}.
\]

The impact matrix `C` now maps `f` to `y`; for a planned trade **USDT notional** `z_i` at reference price, its percentage-price displacement due to the signed trade sequence is, to first order,

\[
\delta\log P_i(t)\approx\frac{1}{10^4\sqrt{L_i}}
 \sum_{j,s\le t}G_{ij}(t,s)\frac{u_{j,s}}{\sqrt{L_j}}.
\]

With `u` and `z` representing signed USDT notional (buy positive; sell negative), the associated cash cost is quadratic in `u/√L` and **PSD constraints apply to the symmetrically scaled `G`**, not to an arbitrary raw response matrix in `bps per coin`. This is a **small-impact, reference-price notional approximation**. Report it; check alternative fixed-share formulation using the exact AJNT paper notation in a synthetic replication. **Never silently enforce symmetry on raw BTC/ETH bp-versus-USD coefficients.**

For OOS monthly refits, `L` is recalculated only from the past training window; the fitted coefficients and liquidity units travel together as a calibrated model for that month. Validation/test observations do not set `L` for their own fitted month.

### 4.3 Price/flow diagnostics and gaps

Required checks, by asset/month/split: timestamp uniqueness and monotonicity, expected 1m coverage, positive finite `close`/high/low/open, OHLC ordering, nonnegative base/quote volumes/trade counts, taker-buy ≤ total, no impossible price gaps due to schema/timestamp parsing, absence of duplicate ZIP partitions, and BTC/ETH synchronous intersection. Give anomaly counts and **plot the affected day** before decisions. Keep raw values and a small **quality mask**; no forward-filled prices, fabricated trades, artificial midpoint reconstruction or across-gap returns. Regression needs its entire lag window plus target present. Execution episode needs all future bars for **evaluation**, but its **decision** uses only past data; after selection, missing evaluation bars cause an explicit QC exclusion.

Report especially: severe jumps, stale close, extreme `ofi`, quote/base notional identity approximations, abnormal funding/bar discontinuities, and gaps at midnight/month boundaries. For optional `bookDepth`, check time cadence, price-band ordering, nonnegative depth, stable/non-stale independent band values, asymmetric freeze, implausible implied band prices and percentage bands. Never impute broken 2026 depth values.

### 4.4 Forward-looking contamination and preprocessing

- Compute train/val/test boundaries **before** feature operations. Fit all normalizers/regularizers only on prior data; lagged rolling statistics at time `t` use data up to `t-1` for a decision at `t`.
- No centered rolling windows, future realized volume for forecast-VWAP/caps, test-wide normalization, hindsight selection of crash days, or oracle same-minute order flow as alpha.
- An OOS evaluation uses the realized price path **only to score completed strategies**; future prices are never read by the optimizer.
- For lagged controls and seasonal statistics, carry historical context across month boundaries **without allowing labels/targets from future periods**.

### 4.5 Liquidity forecasts known when orders are placed

For each execution episode at time `t0`, generate `Vhat_i,k` (minute-`k` predicted quote volume, USDT) from the median 1-minute turnover over the **previous 28 days**, preferably by **hour-of-week** with a shrinkage fallback to hour-of-day/overall trailing median if insufficient clean observations. The entire 60-minute forecast is frozen at `t0` in the basic open-loop schedule. Clip each forecast to a training-derived positive floor and report how often this clip activates; never use realized `V_i,t0+k` to define cap or target. A simple **past-only 28-day median** is acceptable as the first benchmark if hour-specific seasonal forecasts are poor on validation.

### 4.6 Perpetual funding and instrument conventions

Historical funding is relevant only if a simulated inventory would be exposed at a settlement; the **funding schedule and rate are separate**. Do not assume the permanent price `mark` equals last traded `close`. Cross-sectional covariance and execution P&L are quote-USDT approximations at reference mid/close unless actual BBO exists. Binance perpetual contract **lot size, tick size, and fee tier** should be recorded from official instrument rules if a unit-to-contract conversion is used; simulated continuous USDT sizes are rounded **only after** converting to valid instrument quantities, with a residual inventory check. No fabricated maker fills. No liquidation/leverage/margin modeling in the minimum study; therefore this is **execution cost modeling, not a complete funded derivatives P&L strategy**.

## 5. Mathematical model and mapping to the primary reference

### 5.1 AJNT continuous-time formulation (reference, not original research)

Abi Jaber, Neuman & Tuschmann (AJNT) [R01] take inventory `X_t` with `dX_t=u_t dt`, unaffected semimartingale price `P=A+M`, covariance `Σ`, temporary matrix `Λ` (positive-definite symmetric part), and transient displacement

\[
D_t^u=\int_0^t G(t,s)u_s\,ds.
\]

Their admissible (deterministic) Volterra kernel lies in a nonnegative-definite class, with risk/revenue objective (paper (2.16)); terminal inventory penalty is introduced in **Remark 2.10, equations (2.35)–(2.37)**. **Theorem 2.8** solves the stochastic-signal portfolio problem through an operator/Fredholm resolvent, and **Corollary 2.9** reduces the deterministic-signal case to `u*=D^{-1}g`. **Theorem 2.15** and **Corollary 2.18** give useful no-manipulation sufficient conditions for certain symmetric nonnegative, decreasing, convex convolution kernels. **Section 3.4** describes a Nyström-style numerical scheme; **Sections 3.1–3.3 already contain synthetic two- and three-asset experiments**. These are published results to **reproduce/benchmark**, not claims of novelty.

The paper's exact general stochastic formula should be invoked only when its conditional-expectation and kernel assumptions hold. A repeated **deterministic QP with updated forecasts** is *receding-horizon control*, **not in itself an implementation of AJNT Theorem 2.8**.

### 5.2 Execution variant chosen here

The primary task is to **liquidate two positive USDT-notional inventories** over a fixed horizon. Let `z_i,k ≥ 0` be **sale notional** in minute `k`, and `u_i,k=-z_i,k` the signed impact flow. Let `h_i,k = X_i,0 - ∑_{a<k}z_i,a` be remaining **pre-trade** USDT-notional inventory. Enforce `∑_{k=1}^n z_i,k = X_i,0` and `0≤z_i,k≤0.10 Vhat_i,k` (other caps by validation/sensitivity). No inter-asset self-financing trick, buy round trip, or new position is allowed in the **main comparison**. This hard terminal constraint is stricter than the *terminal-penalty* illustration in AJNT Remark 2.10; its discrete QP is an **explicit applied constraint variant**, not the literal unconstrained theorem's optimizer.

Minimize expected **impact + temporary participation cost + pre-trade inventory risk + optional predictable drift cost**, subject to these constraints. All models/baselines use **identical** inventory, caps, horizon, risk coefficient, spread/fees and information. Negative signed `u` is important: for sells, own induced price distortion is adverse, while quadratic trading cost is nonnegative for an admissible kernel.

### 5.3 Admissibility / no-manipulation definition

For any square-integrable signed trading rate `u(t)` (already scaled in §4.2), require

\[
\mathcal C_G(u)=\int_0^T u(t)^\top\left[\int_0^t G(t,s)u(s)ds\right]dt\;\ge0.
\]

This is necessary for the chosen impact-only round-trip pathology check. **Positive entries and individually decaying coefficients alone are insufficient**. The discrete symmetrized Hessian should be PSD (up to numerical tolerance); all chosen fit families are designed to satisfy a stronger **constructive sufficient condition**.

### 5.4 Admissible low-dimensional families

All candidate matrices `C_a` are **symmetric positive semidefinite** in the scaled *cash-consistent* coordinates. For distinct positive times `τ_a`:

\[
G_B(t,s)=\mathbf 1_{t\ge s}\sum_{a=1}^{K}C_a\exp[-(t-s)/\tau_a],\qquad
C_a=C_a^\top\succeq0,\quad K\in\{1,2\}.
\]

Each `exp(-lag/τ)` is nonnegative, nonincreasing and convex; positive sums of `C_a` yield admissible convolution kernels under AJNT's sufficient conditions. Allow **negative off-diagonal entries only if the whole `C_a` is PSD**. The single-asset null model `A` sets *each* off-diagonal entry to 0 with otherwise identical lag/penalty structure. A simpler *common-decay* sensitivity model is `G(t,s)=C φ(t-s)` with `C⪰0` and `φ(lag)=(1+lag/t0)^(-β)` for `β∈(0,1)`, `t0>0`; cap complexity to small grids and integrate the cell average near lag zero.

**No unrestricted free `G_ij(t,s)` or arbitrary empirical lag-by-lag matrix** enters the optimizer unless it passes an independently verified PSD/admissibility test. Unconstrained response estimates are **diagnostic only**.

### 5.5 Discrete price-response identification equation

A transient displacement `d_t = ∑_{s≤t}G(t,s) f_s` implies **return**, rather than level, response

\[
y_{i,t}\approx\sum_j\left[G_{ij}(0)f_{j,t}+\sum_{\ell=1}^{L}
  \big(G_{ij}(\ell)-G_{ij}(\ell-1)\big)f_{j,t-\ell}\right]
 +\beta_i^\top x_{t-1}+\varepsilon_{i,t},\tag{1}
\]

Here `y_i,t = 10^4√L_i Δlog C_i,t` is **already the scaled one-bar return**; do not difference `y` again. The coefficient of same-bar flow is `G(0)` and of lagged flow `ℓ≥1` is `G(ℓ)−G(ℓ−1)`. Equation (1) describes the **difference of the transient displacement**. **Do not mistakenly regress returns on the level kernel `G(ℓ)` at every lag**. Existing outstanding impact beyond truncated `L` is a modeling error measured by memory sensitivity.

`x_{t-1}` consists of strictly past-known nuisance controls (see §6); same-bar flow is permitted **only** for conditional response estimation/nowcasting, never treated as tradable alpha. A regression containing `q_t` is conditional on realized flow—not a forecast observable at the episode start. High-frequency correlated demand, informed trading, and price-changing limit activity can bias `(1)`, even if its predictive fit is strong.

## 6. Statistical estimation of self- and cross-impact

### 6.1 Competing conditional-response regressions

Estimate **jointly** across the two assets on the same synchronized observations, preserving common time windows and nuisance controls:

- **N0 — no-flow control:** past returns, volatility, turnover, seasonality; **no contemporaneous public flow**.
- **U — unconstrained diagnostic:** a low-dimensional or ridge regularized regression allowing distinct directional `BTC→ETH` and `ETH→BTC` flow coefficients, with no symmetry/PSD restriction; **never use U as an execution kernel without repair and re-estimation**. It measures the explanatory cost of enforcing admissibility.
- **A — constrained diagonal propagator:** `C_a = diag(c_a,BTC,c_a,ETH)` with nonnegative diagonals.
- **B — constrained full propagator:** each `C_a` is **2×2 symmetric PSD**; identical decay candidates, controls, observation weights and hyperparameter-selection budget as A.
- **C — optional nonstationary admissible B:** deterministic `G(t,s)` of §7.4, included only after successful stationary tests.

**Same sample for A/B.** Use **per-asset training-set standard deviations of the dependent scaled returns** as loss weights so that a liquid BTC leg cannot swamp the ETH leg by raw scale. Retain units and PSD constraints on the **unwhitened economic `C_a` matrices**. All per-asset nuisance coefficients may differ. Training target is the **same-minute conditional response** in §5.5, not purported causal impact.

### 6.2 Nuisance features and econometric discipline

Initial **lagged** controls, computed before bar `t`: each asset's log returns at lags **1, 2, 5, 15** minutes; lagged (strictly past) **market activity** over **5, 15, 60** minute windows measured in unsigned total quote turnover, **not** redundant lagged signed-flow sums; log quote volume deviation from a trailing **1-day** median; trailing realized volatility over **60** and **1,440** minutes; and cyclic UTC time-of-day / day-of-week seasonality. Use a parsimonious common-factor proxy from the **lagged** equally weighted BTC/ETH return, not future or same-minute total-market return. Do **not** include lagged signed-flow sums as nuisance covariates in A/B: they are linear combinations of the flow-lag design used to identify `G`, and would make fitted kernel coefficients non-identifiable or unstable. Past flow is represented **only via the explicit kernel basis**; separate forward-prediction experiments may construct lagged flow features. In a strict sensitivity, omit lagged common-factor terms to expose collinearity. Do not flood the specification with indicators or create an additional ML feature-engineering project.

**Important identification caveat:** Lagged returns, correlated flows and common factors can themselves be endogenous; nuisance adjustment does **not** recover an exogenous intervention kernel. Specifically, never put a contemporaneous **BTC/ETH return** on the RHS of the other asset's same-minute return and then interpret a remaining flow coefficient as structural. Include separate diagnostics without lagged-return controls and with a **lag-only/no-contemporaneous-flow** design to assess robustness.

### 6.3 Fit method, parameter grid and constraint enforcement

For **fixed** decay times `τ_a`, the coefficients `C_a` and linear nuisance coefficients enter (1) linearly. For MacBook-scale computing, accumulate `XᵀX`, `Xᵀy` and weighted losses in chronological monthly batches and solve the small **sufficient-statistics** quadratic/SDP rather than handing millions of dense rows to a conic solver; verify this equals a small direct-design fit. Fit **penalized weighted least squares** with PSD constraints; e.g. use a small convex semidefinite/quadratic optimization solver (`cvxpy` plus an SDP-capable backend for PSD fitting), not a multi-hundred-parameter neural net. In `2×2`, explicit PSD constraints `C11≥0`, `C22≥0`, `C11 C22≥C12²` are intuitive but the quadratic product is **not directly DCP-compatible**; prefer `C >> 0` or valid second-order-cone form. Distinguish the estimator solver from the faster **execution QP** solver.

Initial grid:

| Component | Values / rule |
|---|---|
| Number of exponentials | `K=1` or `K=2`, not more in the core. |
| Default decays | `(5)` or `(5,30)` **time constants in minutes**. |
| Expanded candidate decays | `τ` from `{2,5,10,30,60}` minutes; at most **two ordered distinct values**, validated for stability. |
| Memory truncation | 60 minutes; repeat at 30 and 120 if tail/stability diagnostics demand it. |
| Ridge penalty | `λ ∈ {0, 10^-4, 10^-3, 10^-2, 10^-1, 1}` on coefficients after a fixed, **training-only** design/target standardization; rescale to economic matrices for PSD. |
| Additional optional cross penalty | If unstable, one extra preannounced `λ_cross ∈ {0, λ, 10λ}`; tune **without** looking at test, log why introduced. |
| Optimizer | Convex constrained LS / SDP; numerical tolerance `1e-6` relative if stable, practical tolerance escalated and recorded if ill-conditioned. |
| Missing lag windows | Exclude and count; never inject zeros into absent price/flow history. |

Use the **same λ/decay search** for A and B to avoid granting the more complex matrix model a hidden advantage. Model U is diagnostic, and may have its own ridge penalty selected on the same validation window. Fit *separate* flow and nuisance terms on synchronized data; if computationally convenient, partially residualize controls **within training only** and verify equivalence to joint regression.

Training/validation selection metric: **mean standardized 1-minute squared response error**, reported per asset and together; ties (improvement < **0.1%** relative) choose simpler model/fewer decays/stronger regularization. Do not automatically interpret a tiny statistical MSE advantage as meaningful execution gain.

### 6.4 Walk-forward and untouched test procedure

1. **Development:** Train models on 2024-01 to 2025-06 and select features, decay family, penalty, and model complexity using **2025-07 through 2025-12 only**. Do not consult January–June 2026 test performance when making choices.
2. **Lock a settings manifest:** Fix preprocessing, candidate families, episode starts, baseline definitions, significance metric, risk/cap grid, independent evaluator families and evaluation caveats **before** scoring any 2026 test outcome.
3. **Monthly test refit:** On first UTC day of each test month, refit using **the preceding 365 complete UTC days** with fixed hyperparameters; only **past** observations may enter. Choose a consistent treatment of the last minute of the previous day and its lag context. Freeze this fitted model for the whole test month (no intramonth retrospective revision).
4. **Store estimates as of origin:** Each episode records its actual fitted matrix components, `τ`, past-only liquidity normalization `L`, nuisance controls and volume forecast. An implementation must be able to reconstruct **what the strategy knew** when the episode began.
5. **Evaluate** all prespecified models and baselines on exactly the same eligible test episodes, including weeks in which coefficients or optimization change unfavorably.

The 365-day lookback overlaps earlier periods intentionally; it does **not** use the held-out episode's future. If fewer than 365 valid calendar days exist at a chosen start, skip rather than silently shorten the history. A completely frozen 2025-year-end estimate (no walk-forward) is a useful stability sensitivity, not the main method.

### 6.5 Reported calibration quantities (required)

For each monthly fit: `C_a` numeric values, eigenvalues, condition numbers, diagonal size, normalized off-diagonal ratio `C12/√(C11 C22)` when denominator positive, implied instantaneous self/cross price displacement for a predeclared dollar trade, decay curve at 0/1/5/15/30/60 minutes, training/validation and true OOS model loss, tail sensitivity, estimated residual correlation, and fraction of near-binding PSD constraints. Report BTC/ETH outcomes separately.

Model comparisons:

- `A` vs `B`: held-out response MSE/MAE, standardized and in actual bps; response `R²` **conditional on contemporaneous flow** labelled **explanatory/nowcast**, never a return forecast/trading alpha.
- `N0` vs `A/B`: what flow adds beyond past-only controls.
- `U` vs `B`: empirical fit surrendered for economic admissibility; **U is not a valid strategy kernel by default**.
- No same-minute flow version: genuinely **predictive** effect of **past** flow, evaluated independently at `t+1` and 5-minute forward returns with all information available at `t`. A predictive score **does not** identify structural impact.

A full-matrix model that fits well **only when unconstrained** but fails under admissibility is a **negative scientific finding**, not a reason to discard the constraint.

### 6.6 Confounding, placebo and uncertainty checks

Mandatory light-weight falsifications:

1. **Cross-flow removal:** Does removing BTC flow from ETH and ETH flow from BTC materially change OOS error after the same lag/controls?
2. **Temporal stability:** Monthly off-diagonal sign/magnitude plot; fit each development half separately; analyze weekend versus weekday and low/high **past-based** liquidity regimes.
3. **Lag-only sensitivity:** If cross coefficients vanish without same-bar flow, distinguish contemporaneous association from usable forward prediction.
4. **Lead-flow placebo (diagnostic only):** Does **future** flow apparently explain today's return after controls? A nonzero coefficient exposes correlated information/feedback and should **not** be marketed as a predictor or interpreted as a causal direction.
5. **Cross-asset temporal permutation:** Circularly shift one asset's entire flow stream by **whole days** within the **training** period (at least seven days displacement), preserving own autocorrelation but destroying precise BTC–ETH alignment; refit the complete chosen model on **at least 50** prespecified shifts for a placebo distribution. This does not prove identification but detects mechanically spurious cross fits.
6. **Uncertainty:** Resample **seven-day chronological blocks** from past calibration data and refit **at least 50** times to show uncertainty bands for off-diagonal magnitude/decay. Full 500-fold calibration refits are **not necessary** for a CV project. Distinguish this estimation variability from episode-level evaluation bootstrap.

Do not run dozens of unregistered feature/lag permutations against test data. Reference [R03, R05, R06, R08, R09] for why learning/identification claims need caution.

## 7. Kernel extensions and selection rules

### 7.1 Model A: separate single-asset propagators

`G_A(t,s)=diag(g_BTC(t-s),g_ETH(t-s))`, each `g_i` an admissible positive mixture of exponentials. This model **removes the execution cross-impact** but still uses the same BTC/ETH market data, same full risk covariance in the **joint no-cross baseline**, and the same liquidity/risk constraints. Don't confound a zero cross-impact assumption with a zero **return covariance** assumption.

### 7.2 Model B: stationary `2×2` matrix convolution

`G_B(t,s)=1_(s≤t)∑_a C_a exp(-(t-s)/τ_a)`, each `C_a=C_a^T⪰0`. This is the **primary scientific comparison**. A fitted off-diagonal term can be positive or negative while the matrix remains PSD, but any matrix with negative eigenvalues fails the admissibility gate. A **zero** off-diagonal within sampling uncertainty is an acceptable outcome.

### 7.3 Model B′: alternative stationary decay (optional sensitivity)

Use `G_B′(t,s)=1_(s≤t) C (1+(t-s)/t0)^(-β)` with common `C⪰0`; choose `β ∈ {0.2,0.4,0.6,0.8}` and `t0 ∈ {1,5,15}` minutes by development validation **if and only if** exponential diagnostics show material missed slow tail. This is still a **stationary convolution**, not the genuinely nonconvolution generality of AJNT. Don't turn kernel-family expansion into an indefinite grid search.

### 7.4 Model C: time-inhomogeneous **deterministic**, nonconvolution Volterra extension

Only if B is numerically credible, explore

\[
G_C(t,s)=\mathbf 1_{t\ge s}\,A(t)\Big(\sum_a C_a e^{-(t-s)/\tau_a}\Big)A(s),
\quad A(t)=\operatorname{diag}(a_{BTC}(t),a_{ETH}(t)),
\]
\[
a_i(t)=\operatorname{clip}_{[0.5,2]}
 \left(\frac{\widetilde V_i^{\mathrm{train}}}{\widehat V_i(t)}\right)^{\eta/2},
 \quad\eta\in\{0,0.5,1\}.
\]

`Vhat_i(t)` is the **ex-ante** scheduled 1-minute liquidity forecast computed **at episode start** (§4.5), held as a known deterministic function over the horizon; `Vtilde` is the relevant past-only trailing reference turnover, defined once when fitting the model. In training, simulate these forecasts with the same past-only construction; never replace with realized future `V`. At `η=0`, model C reduces exactly to B. Fitted/selected `C_a` remain symmetric PSD. For any deterministic `A(t)`, the quadratic form equals that of the stationary PSD kernel acting on the transformed control `A(t)u(t)`; thus **the constructive admissibility condition survives**. This is an **author-chosen structured extension**, not a formula claimed to be in AJNT.

**Crucial measurement detail:** If `A(t)` changes, the **return response** is the **time difference of the full time-varying displacement**, i.e. `d(t)-d(t-1)`. It is **not** obtained by multiplying the fixed stationary return-regression coefficients by today's liquidity scalar. Recompute both `G_C(t,s)` and `G_C(t-1,s)` against all earlier flows when fitting/scoring.

**Kernel-determinism rule:** AJNT's `G(t,s)` is deterministic, while signals/strategies may be stochastic. An **actual future realized random liquidity path** cannot simply be plugged into AJNT Theorem 2.8. Treat this as an **episode-conditional deterministic optimization**, with its liquidity forecast frozen from prior information; conditional-on-history application should not be misrepresented as a new unconditional stochastic-kernel theorem.

**Gate to keep C:** At least **0.5% reduction** in aggregate *development-validation* standardized response MSE over B **and** stable PSD/inventory checks. Otherwise C is a clearly labeled sensitivity result only, and the final primary study is A vs B. This numeric threshold is a **project complexity filter**, not a universal significance rule.

### 7.5 Model D: stochastic predictive signals (conditional stretch)

A minimum real-data signal candidate uses only *past* information: lagged 1/5/15-minute BTC/ETH returns, signed-flow imbalance and turnover/volatility z-scores from previous 28 days; fit **ridge linear regressions** to the **next 1-minute** asset returns, aggregate conditional forecasts over the execution horizon using a documented decay rule. Tune **only** in development and measure genuine validation `R²` versus a **zero-return prediction**. Gate: do not add D if predictive OOS performance is consistently nonpositive, confidence intervals overlap the baseline strongly, or implementation inflates scope. This protects time for the core control study.

If D passes, distinguish two distinct implementations and claims:

- **D1, practical:** At episode start, insert frozen **conditional expected unaffected price increments** as the linear expected-price term in the deterministic constrained execution QP. This is **forecast-aware/receding-horizon scheduling**; **do not call it exact Theorem 2.8**.
- **D2, mathematical stretch:** Implement/verify AJNT **Theorem 2.8's stochastic Fredholm/resolvent** on a small simulated **OU/AR(1)** alpha model with *known* conditional-expectation law, then, **only if justified**, couple an estimated signal law to rolling application. Benchmark against a Monte Carlo or direct discretized first-order condition and the deterministic Corollary 2.9. Do not pretend a forecast vector alone determines the conditional expectations of an arbitrary future signal process.

No 100-model alpha search, deep learning, RL, high-frequency market making, or speculative trading overlay is part of the minimum CV project.

## 8. The numerical execution problem

### 8.1 Discretization, cash units and causality

Use `n=T/Δt` one-minute execution **intervals**. For sells define `z_k∈R²_+` (USDT-notional per interval), `w_k=diag(L)^(-1/2) z_k`. Denote `G_(k,j)` the impact of a signed flow executed in interval `j` as felt in interval `k≥j`; include the appropriate **cell-integral average** of continuous kernels, not the singular evaluation at a cell endpoint if power-law is used. Use **half** of same-cell impact in the average execution price as the initial uniform-within-cell convention (verify against continuous integration on a constant-flow benchmark):

\[
C_{\mathrm{transient}}(z;G)=10^{-4}\sum_{k=1}^n w_k^\top\left[
 \frac12 G_{k,k}w_k+\sum_{j<k}G_{k,j}w_j\right].\tag{2}
\]

This has units of **USDT**. For a sell, the signed impact direction is negative, so its induced reduction in sale proceeds appears as the **positive** quadratic cost above. The symmetrized matrix of (2) must be PSD; verify this against the continuous theory in synthetic tests. Confirm all factors of 2, interval lengths and `10^-4` in unit tests. When the same within-cell sign/normalization is used in the response estimator, the **calibration→control conversion must not silently alter kernel amplitude**.

Inventory: `h_k = X_0-∑_{j<k}z_j`; terminal equality `∑_{k=1}^n z_{i,k}=X_{0,i}`, `z_{i,k}∈[0, pmax Vhat_{i,k}]`; all are linear constraints. A state or trade in **base-token quantity** must be converted from the frozen episode reference mid and rounded consistently; ensure liquidation to permitted lot-size tolerance.

### 8.2 Temporary slippage, spread, fee and risk

Chosen convex **scenario approximation**, separate from transient cross-impact:

\[
C_{\mathrm{temporary}}(z)=\kappa\sum_{i,k}\frac{z_{i,k}^{2}}{\widehat V_{i,k}},\qquad
\kappa\in\{0.0005,0.001,0.005\};\tag{3}
\]

`κ` is a **dimensionless curvature**, representing `5/10/50` bps per unit participation (e.g. `κ=0.001`, 2% participation → approximately **0.2 bp** average incremental cost). Forecast `Vhat` is positive and known when deciding. This is a **proxy**, not an empirically fitted market-order depth curve. If optional matched L2 supports a defensible piecewise convex empirical cost curve, use it as a **separate evaluation scenario**, not as a no-warning substitution in the primary optimizer.

Spread and fees, scenario-only unless venue/date verified:

\[
C_{\mathrm{linear}}=10^{-4}(b_{\mathrm{halfspread}}+b_{\mathrm{takerfee}})\sum_{i,k}z_{i,k},
\quad b_{\mathrm{halfspread}}\in\{0,1,2\},\ b_{\mathrm{takerfee}}\in\{2,5,10\}\ \mathrm{bps}.
\]

As noted in §3.6, a uniform all-taker linear fee has **no schedule-ranking effect** among equal-total monotone liquidations. It does affect reported absolute costs. Do not present a fee scenario as improving optimization when the objective differs by a constant.

Let `Σhat` be the **past-only trailing 28-day** covariance of BTC/ETH **one-minute log returns**; compute remaining-inventory variance exposure

\[
R_{\mathrm{raw}}(z)=\sum_{k=1}^n h_k^\top\widehat\Sigma h_k.
\]

Normalize risk cost to a clear **TWAP-relative scale**, shared across every method:

\[
C_{\mathrm{risk}}(z)=\frac{\theta\,(W/10^4)}{R_{\mathrm{raw}}(z^{\mathrm{TWAP}})}R_{\mathrm{raw}}(z),
\qquad \theta\in\{0,1,2\},\quad W=\sum_iX_{0,i},\tag{4}
\]

with `θ=1` primary; if `R_raw(TWAP)` is numerically zero, use `θ=0` and record that episode's abnormal covariance. Equation (4) means TWAP's risk penalty is **θ basis points of total starting notional**. It is a **project-specific preference normalization**, not an empirical estimate of institutional risk aversion.

If using a genuine **past-only** expected return curve `m_i,k`, add the linear expected drift/arrival shortfall term, in USDT, `C_drift = -∑_(i,k) z_(i,k) m_(i,k)` where `m_(i,k)` is expected fractional price increase from episode start; selling later when price rises reduces cost. Default **`m=0` for the core**. Do not use realized future drift as a policy input.

Total optimization target:

\[
\min_{z\ge0}\;C_{\mathrm{transient}}(z;G_{\mathrm{fitted}})+C_{\mathrm{temporary}}(z)
+C_{\mathrm{risk}}(z)+C_{\mathrm{linear}}(z)+C_{\mathrm{drift}}(z)
\quad\mathrm{s.t.}\quad \sum_k z_{i,k}=X_{0,i},\; z_{i,k}\le p_{\max}\widehat V_{i,k}.\tag{5}
\]

For each episode, choose `X_i,0 = 0.02∑_k Vhat_i,k` (with sensitivities). `pmax=0.10` makes the nominal 2% liquidation feasible by construction under a valid positive volume forecast. If lot-size rounding induces a small shortfall, apply a common deterministic final-bin repair **only within cap**, or declare infeasible.

### 8.3 Exact-paper reproduction and constrained engineering solver are two checks

Implement both mathematical verification levels, but keep scope small:

**Verification V1 (paper):** Reproduce representative **two-asset** deterministic-signal examples from AJNT §3.1, including `C=diag(0.06,0.06)` and `C=[[0.06,0.05],[0.05,0.06]]` with their reported `Λ=diag(0.03,0.03)` and terminal penalty, using **the paper's exact dimensionless synthetic conventions**, not cryptocurrency-calibrated numbers. Verify the sign/qualitative pattern of cross-impact and changes in liquidation/round trips, and replicate the simplified deterministic condition `u*=D^{-1}g` (Corollary 2.9) by Nyström-type discretization (§3.4). **The paper's synthetic unrestricted round trips are allowed in this verification**, unlike the real-data primary sell-only problem.

**Verification V2 (project):** Solve the **hard-terminal, no-round-trip constrained QP** (5) using `cvxpy` plus a CPU QP backend such as OSQP; `n=60`, two assets ⇒ **120 sale variables**, economically trivial at laptop scale. Verify the convex Hessian and that a second solver or analytic special case gives the same optimum within tolerance. Any non-PSD matrix from discretization or fitting is a **failure**, not silently repaired by adding arbitrary large diagonal regularization and calling it the same model.

**Important theoretical nuance:** AJNT's stochastic resolvent and terminal-penalty portfolio optimizer are not identical to the constrained QP even when they share `G`. Clearly mark which code path implements published analytic formulas and which implements the **constrained applied extension**. A proper theorem implementation claim needs V1, not merely solving (5).

### 8.4 Mandatory solver unit/synthetic tests

- `G=0`, `θ=0`, `κ>0`: optimizer follows the analytically derived **volume-weighted quadratic participation allocation** (subject to constraints); when `Vhat` equal, returns uniform TWAP.
- `C_a` diagonal and diagonal `Σhat`: the joint QP decomposes exactly into two single-asset problems.
- `C_a` full PSD: no negative eigenvalues beyond `1e-8` relative numerical tolerance in the symmetrized cost Hessian; check random signed **round-trip perturbations** for nonnegative impact cost.
- Numerical convergence at `Δt=2, 1, 0.5` minutes on a synthetic continuous benchmark (use 0.5m **synthetic grid only**; the empirical bars remain 1m); report objective/schedule differences.
- Inventory equality `abs(residual_i) ≤ max(1e-6 W_i, applicable lot-size tolerance)`; cap feasibility, no negative sales, no unintentional cross-asset/speculative inventory.
- Scaling: USD→USDT notional normalization, basis-point conversion, factor-of-two and diagonal self-impact; double notional should give **quadratic** pure impact before caps change.
- Symmetric permutations of asset labels yield permuted solutions; zero cross term recovers the no-cross solution.
- All models solve on exactly the same observed history, forecast volumes, risk covariance and constraints.
- For fitted nonstationary `G_C`, verify the **integral quadratic form**, not just the PSD of individual `G(t,s)` matrices.

## 9. Execution scenarios and matched baselines

### 9.1 Initial inventory/episode definitions

Start episodes at **00:00, 06:00, 12:00, 18:00 UTC**, every day of the 2026 final-test half-year that passes predeclared QC. Both `BTC` and `ETH` have positive starting inventory sized from **known** predicted turnover (`0.02 × next 60-minute predicted quote volume`), not a future volume measurement. This yields **four nonoverlapping 60-minute windows per eligible day**, diverse days of week, and an interpretable **approximately 2% forecast participation** under a uniform-volume schedule. Record the actual typical USDT starting inventories; provide a secondary illustrative **$100,000 per leg** scenario **only when participation caps permit**.

Secondary sensitivity: target participation `0.5%,1%,5%`, horizon `30,120` minutes, cap `5%,20%`. For `120` minutes the four episode starts remain six hours apart; no overlap. For horizon changes, **recompute** forecast-total-volume and initial inventory from the same targeted participation, rather than inadvertently changing both the trading horizon and size in unexplained ways. Also report a **fixed-notional alternative** at 60 minutes to separate horizon effect from size scaling.

The primary symmetric two-leg portfolio creates legitimate reasons to coordinate *both actual sells*. A one-leg `BTC-only` inventory test would force ETH trade to zero under sell-only terminal constraints, **so it is not a valid test of cross-asset scheduling benefits**. Synthetic zero-inventory-in-ETH round-trip examples belong to AJNT replication or a clearly marked unconstrained speculative extension, not the primary performance table.

### 9.2 Policies — same constraints, same information

| Policy | Rule | Role |
|---|---|---|
| **T0: Capped TWAP** | Target equal **USDT notional** each minute per asset (`X_i,0/n`), then project to the **closest feasible** schedule under the same forecast participation caps/terminal equality; all projections are deterministic, past-only. | Standard transparent baseline. |
| **T1: Forecast-VWAP** | Allocate each asset proportional to **ex-ante forecast** `Vhat_i,k`, normalized over horizon and cap-repaired; **never hindsight realized VWAP**. | Liquidity-aware benchmark. |
| **T2: Independent optimizers** | Solve (5) **separately for each asset** with its fitted diagonal self kernel and own diagonal inventory risk; shared fees/temp/caps. | Practical per-asset control baseline. |
| **T3: Joint/no cross-impact** | Solve **joint (5)** with diagonal fitted kernel **and full cross-asset `Σhat` risk covariance**. | **Critical controlled comparison** isolating cross-impact rather than covariance/cap differences. |
| **T4: Joint full matrix stationary** | Solve **joint (5)** using B's full admissible matrix propagator, same full `Σhat`. | Primary proposed strategy. |
| **T5: Joint nonstationary** | T4 with qualifying **deterministic** model C. | Optional general-Volterra comparison. |
| **T6: Forecast-aware** | T4 or T5 with gated real predictive signal and **no hindsight inputs**. | Optional, clearly distinguished from exact stochastic theorem. |

No participation upper bound uses actual future `V`. If a TWAP allocation exceeds its cap due to forecast seasonality, solve a tiny cap-constrained projection `argmin ∑(z_k−target_k)²` at fixed total; show adjustment counts and avoid calling the repaired version plain unconstrained TWAP. The comparator always maintains the exact same total inventory, horizon and **risk-score definition**, even if it does not optimize the risk term itself.

### 9.3 Risk, common shocks, and fees are controlled explicitly

Report risk penalty *and* raw realized inventory variance proxy for every schedule, not just cost. The primary comparison **T4 vs T3** keeps the same full `Σhat`; the **T4 vs T2** comparison is informative operationally but changes both covariance treatment and cross-impact. Any reported improvement must be attributed to the correct comparator. A constant **uniform taker fee** will largely cancel between sell-only, equal-notional policies; keep it in absolute shortfall but do not use it to explain why one timing strategy wins.


## 10. Out-of-sample evaluation: what is and is not measurable

### 10.1 Separate three evidentiary layers

The main research result must **not** be a number obtained by optimizing the fitted cross-impact model and then evaluating only under that same model. Use three explicitly distinguished layers:

1. **Observed-data evidence (primary empirical layer).** For each test month, compare A and B on **actual held-out, synchronized BTC/ETH 1-minute returns and public flow**, using the pre-fitted parameters. Report standardized response MSE/MAE and incremental explanatory improvement over N0, stability of cross coefficients, and placebo outcomes. These are **observational explanatory results**, not counterfactual trade-cost results.
2. **Model-based execution evidence (primary decision layer).** For each episode, generate *causal* candidate policies T0–T4 from information available at arrival, then score them under **separately specified execution environments** E1–E4 below. Compare risk, impact, temporary/slippage proxy, implementation shortfall and feasibility. These are **scenario-conditional policy results**, not realized execution profits.
3. **Matched, mechanical book evidence (optional).** On a small same-venue OKX L2 pilot, calculate spread and book-walk costs for simulated orders using the visible historical snapshot. Such calculations establish **static depth-consuming cost estimates** and can reveal grossly implausible schedules, but do **not** account for queue evolution, replenishment or the market's response to our hypothetical orders.

### 10.2 Scoring a hypothetical liquidation against the recorded unaffected path

For each episode start `t0`, set reference prices `P0_i` to the most recently **completed** one-minute close. Interpret initial actual contract/base quantity as `N_i = X_i,0/P0_i` in a small-impact *reference-notional* approximation. Executing nominal sale `z_i,k` means selling quantity `z_i,k/P0_i`; simulated gross reference-market proceeds are `z_i,k × (P_i,k/P0_i)`, using a declared **next interval execution-price proxy** (primary: the next minute's observed close; separately: open and TWAP-of-OHLC proxy to quantify timing sensitivity). The **recorded-price-path** component of arrival-price implementation shortfall, in USDT, is

\[
C_{\mathrm{path}}(z)=\sum_{i,k}z_{i,k}\left(1-\frac{P_{i,k}}{P_{0,i}}\right).
\]

This is **identical for all policies if they share identical timing**, but varies by chosen schedule and realized market movements. It is **not an estimate of impact caused by our own trades**: the historical `P_i,k` already reflects what actual historical participants did. Open/close price proxies approximate a market-order execution reference and should **not** be sold as executable fills absent contemporaneous BBO.

For an evaluation environment `E`, compute total scenario shortfall

\[
C_E(z)=C_{\mathrm{path}}(z)+C_{\mathrm{transient}}(z;G_E)
+C_{\mathrm{temporary}}(z;\kappa_E,\widehat V^{E})
+C_{\mathrm{spread/fee}}(z;E)+C_{\mathrm{funding}}(z;E).\tag{6}
\]

Report both **cash USDT** and **basis points of initial quote notional** `10^4 C_E(z)/W`. Keep **realized inventory-risk diagnostics separate** from actual shortfall: the risk term in (4) is an *ex ante preference/objective*, not an expense booked to an actual fill. Also give objective including preference risk for optimizer-comparison diagnostics, but label it accordingly.

The `P_i,k` realized after episode start and any post-start actual volume enter only the **scorer**, never the schedule or cap. In the primary specification, `Vhat^E` in the temporary scenario is frozen at episode start; an alternate *ex post* evaluator can use **realized** market volume solely to score sensitivity, visibly tagged **ex post evaluator, unavailable to policies**. Execution must not be declared feasible merely because ex-post realized volume happened to be large: hard caps are on identical ex-ante forecasts; additionally report actual realized participation `z_i,k / V_i,k` as a risk diagnostic, and how often it exceeds 10%.

Funding enters only according to actual position outstanding at a **recorded funding settlement**, consistently across strategies; do not insert an arbitrary forecast rate or retrospectively change scheduling because of realized funding.

### 10.3 Predeclared evaluation environments, deliberately not just the optimized model

| Evaluator | Construction | What it tells us |
|---|---|---|
| **E0 — optimizer's own fitted kernel** | Score each policy using the same `G` that T4 assumed, holding other terms common. | **Smoke-test / mechanical upper bound only**. Always mark *circular/in-model* and **exclude from primary success claim**. |
| **E1 — separate past-fitted response evaluator** | Refit a **separate** constrained kernel on a **180-day historical block ending at least 30 days before the test month** (strictly disjoint from the evaluated test month, though possibly overlapping the optimizer’s earlier training history); use a fixed `(5,30)` min decay and separately selected development-only regularization, without copying T4's rolling-year estimates. Freeze it for that month. | Sensitivity to estimation sample, not truly causal independence. If necessary historical records are unavailable, fall back to **the fixed pre-test development-fitted model** and mark the limitation. |
| **E2 — diagonal/no-cross benchmark world** | Set cross entries of the E1 model to zero; keep independently fitted self curves and all nonimpact assumptions identical. | Detects fragility or cost **harm** when cross-impact is not real. Important null world, not secondary to the full-matrix world. |
| **E3 — misspecified/stressed impact and liquidity worlds** | Before test, define multipliers `0.5, 1, 2` on *each entire PSD matrix component*, decay constants `0.5×/2×`, and temporary cost `κ ∈ {0.0005,0.001,0.005}`. For cross-effect stress, interpolate `(1-ρ)diag(C)+ρ C`, `ρ ∈ {0,0.5,1}`, which preserves PSD; also consider a separately PSD-certified opposite-sign off-diagonal counterfactual. | Ranges over reasonable assumptions; full matrix should not win *only* at precisely its optimized parameter point. |
| **E4 — optional same-venue depth benchmark** | Using only matched OKX historical trades/books, select snapshots at the scheduled timestamps and compute contemporaneous mechanical market-order book-walking costs, where available and time-aligned. No invented Binance books. | Real observed liquidity snapshots but still no counterfactual price adjustment or actual fill simulation; **separate venue vignette**, not an apples-to-apples extension of E1. |

**E1 temporal feasibility detail:** In January 2026, a separate example block is **2025-06-01 to 2025-11-27**, ending more than 30 days before month start; recompute similarly for later months, without touching their outcome days. `180` is a target number of calendar days, require explicit gap >=30d and no overlap with the month being evaluated. Use **identical E1** for every strategy within the same month, with no model-specific evaluation advantages. E1 may overlap T4's earlier training history (they are alternative estimates from the same historical economy); it is **not independently randomized causal evidence**. An E1 covariance kernel fit from aggregate public flow is, like B, a reduced-form *scenario parameterization*.

Under the diagonal E2 evaluator, T4 may rationally lose to simpler strategies. **Do not exclude it**. Report the fraction of evaluators, episodes and stress levels in which T4 underperforms T3, and the **maximum regret** versus the best policy in each specified evaluator.

### 10.4 Required cost and risk reports per policy

For each held-out episode and evaluator, store at least: `arrival UTC`, train/refit cutoff, starting quantities, forecast volume/caps, chosen policy, trade schedule, model/version, feasibility/solver status, **path cost**, **kernel cost**, **temporary cost**, **spread**, **fee**, **funding** if applicable, total shortfall USDT and bps, realized maximum per-minute volume participation, realized residual inventory (should be zero in model units), and pre-trade inventory risk score. Every missing metric must have an explicit reason; no manufactured fill prices or silent zero imputation.

Produce four minimum summaries: (i) all months pooled; (ii) month-by-month; (iii) weekends versus weekdays; (iv) liquidity/volatility terciles whose thresholds are determined from **lagged 28-day information** (not the future evaluation window). Report net and **fee-excluded** changes to expose whether a constant-fee component is merely cosmetic.

## 11. Hypotheses, statistical inference and interpretation

### 11.1 Prespecified primary contrasts

The two core contrasts are deliberately different types of evidence:

- **H1, observed conditional fit (scientific primary):** On 2026-01 through 2026-06 held-out data, the full *admissible* model B has lower **paired monthly standardized response MSE** than otherwise matched diagonal A. Define
  \[
  \delta_{\mathrm{fit}}=\frac{\mathrm{MSE}_A-\mathrm{MSE}_B}{\mathrm{MSE}_A},
  \]
  with a predefined **nontrivial practical threshold of 0.5%**, not automatic statistical significance. Report both BTC and ETH, weighted aggregate and any negative months. Separate model B's improvement over **N0**.
- **H2, conditional execution robustness (decision primary):** Evaluate the **same causally generated** test policies T4 and T3 under the **same independent/stress evaluators E1–E3**, and compare shortfall. Define
  \[
  \Delta_E=10^4\frac{C_E(T3)-C_E(T4)}{W}\quad\mathrm{bps}.
  \]
  Positive `Δ_E` favors the cross-impact-aware schedule. Report the full scenario matrix and its minimum, median, 25th/75th percentiles, paired monthly effects and **bad-case losses**, without selecting only favorable evaluators. A project-specific practical-interest target is **≥0.1 bp improvement** under E1 together with non-catastrophic E2/E3 losses; neither number is a guarantee or proof of causal savings.

**Do not demand H1/H2 be true to declare project completion.** A rigorously documented H1 failure, H2 reversal under E2, or unstable off-diagonal kernel may be the most interesting result. The above thresholds are **precommitted presentation/gating heuristics**, not arbitrary rejections after inspecting the held-out period.

### 11.2 Uncertainty estimation

- Paired inference unit for execution: **calendar day** (four within-day windows are correlated); resample **seven-day contiguous blocks**, with replacement, 500 bootstrap draws. Compute **95% percentile confidence intervals** for the pooled **paired bps difference** and relative cost reduction. Prefer interval width/effect size over isolated p-values. For six monthly fit differences, report the **six actual monthly points** and a supplementary block-bootstrap uncertainty summary based on time blocks of prediction errors, not a naive six-point normal approximation.
- Keep the test period **fully frozen** after development selection. If testing optional models C/D, call the findings **secondary** even if striking; if many comparisons are performed, transparently list all and consider a simple **Benjamini–Hochberg 10% FDR** table for exploratory fit questions only. Do not report bootstrap pseudo-replications as independent trading days.
- Estimate calibration confidence separately from cost-evaluation uncertainty: use §6.6's at least 50 past-only block refits for off-diagonal coefficients. Report possible sign reversals and how often PSD constraints bind.
- For response MSE use a time-series-aware **daily paired loss** and block bootstrap. Do not use independent Gaussian errors or 500,000 one-minute rows as if independent samples.

### 11.3 Success, partial success and negative-result standards

**Scientific result hierarchy:** (1) sound data and unit tests, (2) admissible interpretable fit and evidence about cross-coupling, (3) numerically correct solver and matched policies, (4) independent scenario stress, and only then (5) conditional model-based economic benefit. A numerical execution optimizer that is elegant but underperforms robustly is still a complete project **if the limitations and causes are analyzed**.

Never claim “market impact is causally identified,” “0.7 bp execution saving in live trading,” “new general Volterra theorem,” or “first ever crypto multi-asset impact” unless independently supported by evidence that this project currently does not possess.

## 12. Ablations and sensitivities — bounded, not an endless search

The following is the **minimum** robustness matrix, with core mandatory items first. Preselect full factorial combinations **only where explicitly noted**; otherwise use one-factor-at-a-time sweeps around the locked primary configuration, to control laptop run time and multiple testing.

| Dimension | Mandatory comparisons | Priority |
|---|---|---|
| Off-diagonal matrix | A vs B response fit, T3 vs T4 execution, off-diagonal set to 0 in E2, report C12 sign/magnitude | Core |
| Model calibration | Constrained B vs U diagnostic; B vs N0; rolling 365d vs frozen pre-test B | Core |
| Decay | `K=1` vs `K=2`; candidates `τ=2/5/10/30/60`, at most 2 selected; show typical fitted curves | Core |
| Risk preference | `θ=0,1,2` using the **same** TWAP-normalized risk definition | Core |
| Inventory and caps | nominal size `0.5%,2%,5%`; caps `5%,10%,20%`; **skip infeasible** combinations rather than repair with future volume | Core |
| Temporary liquidity proxy | `κ=0.0005,0.001,0.005` in evaluator and, if computationally cheap, reoptimize in separate prespecified scenario runs | Core |
| Price timing | next bar close versus open/OHLC proxy, labeled recorded-price reference not matched BBO | Core |
| Regime | low/high lagged liquidity and volatility, month/weekend cuts | Core |
| Horizon | 30/60/120 minute episodes (recompute ex-ante starting sizes and forecasts) | Secondary |
| Spread / fee | half spread `0/1/2` bps, taker fee `2/5/10` bps; show constant-fee cancellation | Secondary |
| Stationarity | B versus deterministic C with `η=0/0.5/1` after §7.4 gate | Conditional |
| Alpha | D versus same B risk/caps when genuine past-only validation skill exists | Conditional |
| Market depth | matched OKX dates or clean Binance band proxies; no claim of structural intervention | Conditional |
| SOL / spot-perp / L4 | Only after core is accepted | Extension |

**Compute budget rule:** Prefer **one** default joint fit per monthly test refit and a limited development grid; cache lag-basis designs/normalizers and **small fitted summaries**, not duplicate full raw datasets. If the expanded decay grid requires impractical repeated SDP optimization, use first-stage unconstrained ridge/ranking on development training/validation to shortlist a **small fixed set**, then refit **every shortlisted candidate under the PSD constraint** before comparing results. A cheap unconstrained screen is not the final model. Do not prune candidates using the final test period.

## 13. Concrete phases, decision gates and stopping rules

These are scientific dependencies to guide later execution, **not a day-by-day Codex action plan**. The project can terminate successfully at an informative negative result.

| Gate | Minimum artifact / test | Continue / adjust / stop decision |
|---|---|---|
| **G0 — data feasible** | Two validated monthly 1m archive pilots, correct kline schema and buyer-flow sign; quote units and timestamps verified; extrapolated full-core disk under chosen budget | If one venue blocked, see §3 fallbacks; if signed notional unavailable, **do not fabricate it**. |
| **G1 — sample accepted** | Complete/core QC report for BTC/ETH 2024-01–2026-06 and fixed chronological split; no unreported fills, known data gaps masked | If missing spans affect selected months, apply preregistered exclusion rules and report lost rows/days. |
| **G2 — estimator trustworthy** | Synthetic recovery on known PSD kernels; diagnostic U/A/B comparison, bounded condition numbers/eigenvalues; low-rank/zero-cross null tested; no endogeneity overclaim | If B's cross coefficients are indistinguishable/unstable, **keep the null result**, execute B only as a robustness case; do not add features to force significance. |
| **G3 — solver correct** | AJNT restricted two-asset replication (§8.3 V1); constrained QP V2; self/cross, diagonal, inventory, grid convergence and no-manipulation tests (§8.4) | Fix solver and units before any cost claims; if V1 cannot be faithfully reproduced, document exact discrepancy and restrict theorem-implementation claims. |
| **G4 — OOS core complete** | Predeclared six-month final test, T0–T4, E1–E3, block intervals, relative/month/regime tables and stress losses | The project is **CV-complete** even if T4 is not better. Write results as supported, not hypothesis-driven conclusions. |
| **G5 — optional sophistication** | C passes ≥0.5% dev validation fit improvement **or** D has genuine dev predictive skill **or** same-venue depth gives useful validation | Undertake only the individual promising extension and do not displace the core report with speculative architecture work. |

**Scope discipline:** The first 3 gates should be completable on CPU with two assets and compressed/partitioned public bars. If solver theory reproduces but the public-flow estimator cannot identify a stable off-diagonal component, the main paper's meaningful conclusion can instead be **“conditional public-flow evidence does not reliably support structural cross-impact-aware crypto execution under the examined data and admissibility assumptions.”** Do not claim a live execution experiment took place.

## 14. Final artifacts, figures, tables and minimum reproducibility

### 14.1 Scientific output

One well-structured **research report** (Markdown + optional rendered PDF, but the `.md` report is sufficient to be editable), about **12–20 substantive pages excluding appendix**, containing abstract, question/hypotheses, reviewed mathematics, archive provenance and limitations, estimator and constrained optimal control, chronology, model-comparison results, independent execution scenarios, uncertainty, negative findings and references. A focused CV project should prioritize a defensible complete report over an unbounded software framework.

**Six priority figures:**

1. Data timeline, missingness/QC and BTC/ETH signed-flow summary.
2. Estimated self- and cross-impact curves versus lag, with past-data coefficient uncertainty bands.
3. Monthly off-diagonal strength and PSD eigenvalue diagnostics.
4. Held-out response fit A vs B (plus N0), monthly and pooled.
5. A representative day of paired BTC/ETH liquidation schedules (T0/T1/T2/T3/T4), including cap and inventory trajectories.
6. Distribution/scenario heat map of **T4–T3 independent evaluation shortfall** including adverse/diagonal worlds and uncertainty, not just the in-model E0 estimate.

**Four minimum tables:** dataset/date/rows/QC; calibrated kernel selection and estimator accuracy; matched policy cost decomposition and risk; stress/negative findings with uncertainty and failure counts. Provide numerical configuration, chosen hyperparameters, sample size and unit in every table.

### 14.2 Source and result artifacts (lightweight, not enterprise engineering)

- A single declared environment (`requirements.txt` or `pyproject.toml` with versions), Python 3.11+ and a normal local virtual environment; recommended packages: `numpy`, `pandas`, `pyarrow`, `scipy`, `cvxpy`, **one free SDP-capable solver**, `osqp` (QP), `statsmodels` when useful, `matplotlib`, `pytest` (short targeted tests). **Check selected solvers' installed capability** rather than assuming OSQP handles semidefinite fitting.
- One human-readable `configs/core.yaml` or comparable single configuration file encoding §2, train/val/test dates, fees/cost grids and seed (default `20261027`). Keep optional experiments in a separate small override, not duplicated project folders.
- Minimal module boundaries: `data` (archive + QC), `features`, `kernel_fit`, `impact_cost`, `execution`, `evaluate`, `figures`; a short top-level runner/CLI is sufficient. Repo README states exactly how to obtain free raw data, run a small pilot, and regenerate core tables/plots.
- **Small verifiable tests** for signs, causality/lag cutoffs, PSD and cost nonnegativity, analytic special cases, inventory/caps, scaling, archive parsing, evaluation independence, and train/test leakage. Store an automatically produced `run_manifest.json` containing code Git commit, config hash, data file manifests, train cutoffs, seed, installed package versions, and result directory. These are **reproducibility essentials**, not a need for CI/CD services.
- Data stays under **one canonical `data/raw/` or external cache**, one cleaned partition set, `results/`, `figures/`; large source archives, credentials and generated caches excluded from Git. Do **not** copy multi-GB arrays for each model. A fresh laptop should reproduce the **pilot** in a reasonable run; full-core reproduction may use streamed partitions and CPU batching.
- Do **not** build cloud orchestration, live exchange trading, dashboards, Kafka/database pipelines, REST services, Kubernetes, automated daily retraining, paid-data integration, exhaustive CI, or GPU ML **solely for this CV study**. The later `AGENTS.md` can cover narrow programming conventions; this document defines **science and experiment**.

### 14.3 Result audit trail

A single compact `results/experiment_index.csv` with columns `run_id, UTC_run_time, data_cutoff, config_hash, Git_commit, model, evaluator, sample_period, status, key_metric_path` suffices. A failure should appear in the results rather than be thrown away. Once final-test metrics are calculated, subsequent changes are marked **exploratory**, or a new untouched test window is reserved. No fabricated performance metrics, retrospective performance-based filtering, or unstated hand-selected episodes.

## 15. Contribution criteria and accurate CV language

The CV can credibly emphasize **advanced mathematical modeling and CPU-scale research implementation**, even if no new theorem is proved. Strong accomplishments (once *actually done*) include:

- Adapted a published **matrix-valued transient propagator** to BTC/ETH USDT-margined perpetual-futures data, with symmetric-PSD/no-manipulation constrained estimation and a validated discrete optimal-execution solver.
- Estimated the degree, temporal stability and uncertainty of **reduced-form cross-flow price response** with strict 2024–2026 chronological evaluation; separated contemporaneous explanatory effects from alpha.
- Benchmarked coupled liquidation against TWAP, ex-ante VWAP, independently optimized assets and a joint no-cross baseline under matched risk, participation and fees, using **separate stress evaluators** rather than self-scored fitted impact.
- Quantified where off-diagonal terms improved, failed or reversed under **independent assumption perturbations**, and documented causal identification limits of free public data.

**CV-ready *format* after results (fill numbers only after genuine tests):** “Implemented and validated a two-asset matrix-Volterra cross-impact execution framework on free BTC/ETH perpetual-futures data; calibrated admissible transient kernels and compared joint vs independent liquidation under walk-forward and misspecification stress, finding [honest measured result and uncertainty].” **Do not copy this as a completed claim while implementation and tests remain undone.**

**Thresholds for higher claims:**

- “Improved return/flow explanatory accuracy” requires held-out H1 measurements with uncertainty and predeclared controls.
- “Reduced modeled execution costs” requires explicitly named independent scenarios and risk/fee assumptions, with effect sizes and adverse cases.
- “Reduced realized market costs” requires actual recorded orders/fills or a defensible causal intervention study—not merely public price/book histories.
- “Novel theoretical guarantee” requires a precisely stated proved theorem and direct comparison with [R01–R13] and relevant subsequent research. No such theorem is part of this initial specification.
- “First crypto implementation” requires a much more exhaustive priority search; the earlier handoff establishes only **not identified in prior search**.

## 16. Bounded extensions and decisions intentionally left flexible

The following decisions are **not** necessary to finish the core and should not be interpreted as automatic scope expansion:

1. **SOL third asset:** Add `SOLUSDT` only after two-asset unit tests, stable fitting and independent evaluation. A 3×3 PSD kernel is mathematically straightforward but increases conditioning and data/interpretation burden; same normalized units and matched test dates required.
2. **Spot–perpetual joint execution:** Distinct potential research question involving BTC/ETH spot and perps, basis risk, funding, venue liquidity and collateral. It needs a **separate cashflow and cross-venue unit model**; cannot assume trading a spot unit is identical to trading a perp notional or count funding as pure price impact. Specify fresh before coding.
3. **Real L2 and parent-order proxies:** OKX conditional days or selected Hyperliquid L4 order lifecycle, if permissions/resources allow. Genuine intervention-response validation remains difficult, but a small related study may improve understanding of confounded reduced-form kernels.
4. **Robust control/theory:** Covariance-aware uncertainty set, perturbation-to-execution-value bound, or structure-preserving discretization if a *specific unproved, non-overlapping proposition* emerges. Relevant offline-learning, statistical-estimation and robust-control literature [R06,R07,R13,R20–R23] must be re-audited first; do not invent novelty on the basis of the framework's complexity.
5. **Nonlinear impact:** Already an active field [R20]; treat a nonlinear EBM or symbolic function as a separate scientific question requiring compatible no-manipulation/convexity guarantees, not an unvalidated drop-in to B.

Core numerical defaults may be changed for **documented feasibility or development evidence before looking at the final test**. Fixed requirements are public/free data, no unearned structural claims, correct admissibility, same information/constraints across comparisons and independent scenario sensitivity. The final model can be **simpler** than this specification when actual data show complexity is unjustified.

## 17. Papers and books: annotated reference catalog

**Reading priority:** `★` essential to read at least relevant definitions and methods; `†` important overlap / caution; `◇` background or extension. Linked paper titles are the **primary references** wherever available; peer-reviewed publications are distinguished from preprints. Some less-central summaries rely on abstracts plus the supplied handoff; **inspect the full texts before using precise unverified theorem claims**.

| ID | Paper, permanent link / status as at 2026-10-27 | Precise role and overlap |
|---|---|---|
| **R01 ★** | **Abi Jaber, Neuman & Tuschmann (2026), “Optimal Portfolio Choice With Cross-Impact Propagators.”** *Mathematical Finance*. [Publisher DOI](https://doi.org/10.1111/mafi.70025), [free arXiv HTML](https://arxiv.org/html/2403.10273), [preprint](https://arxiv.org/abs/2403.10273). | **Primary math and solver**. General deterministic matrix Volterra kernels, stochastic strategies/signals, Theorem 2.8 Fredholm/resolvent; Cor. 2.9 deterministic case; Theorem 2.15/Cor. 2.18 admissible convolution classes; §3 simulations and Nyström. Synthetic experiments **already two and three assets**. |
| **R02 ★** | **Alfonsi, Klöck & Schied (2016), “Multivariate Transient Price Impact and Matrix-Valued Positive Definite Functions.”** *Mathematics of Operations Research* 41(3), 914–934. [DOI](https://doi.org/10.1287/moor.2015.0761), [arXiv](https://arxiv.org/abs/1310.4471). | Direct predecessor on **matrix-valued transient impact** and admissibility: forbids a claim that multivariate kernels were introduced in 2026. |
| **R03 ★** | **Schneider & Lillo (2019 journal; 2016 preprint), “Cross-impact and no-dynamic-arbitrage.”** *Quantitative Finance* 19(1), 137–154. [arXiv:1612.07742](https://arxiv.org/abs/1612.07742). | Cross-impact restrictions, dynamic arbitrage and reciprocity; compare the meaning of no-manipulation conditions. |
| **R04 ★** | **Mastromatteo et al. (2017), “Trading Lightly: Cross-impact and Optimal Portfolio Execution.”** [arXiv:1702.03838](https://arxiv.org/abs/1702.03838). | Earlier **empirical multivariate cross-impact plus optimization**, principally equities; important limitation on novelty claims. |
| **R05 ★** | **Naviglio, Bormetti, Campigli, Rodikov & Lillo (2026), “Why Is the Estimation of Metaorder Impact With Public Market Data So Challenging?”** *Quantitative Finance* 26(4), 505–523. [DOI](https://doi.org/10.1080/14697688.2026.2628221), [arXiv](https://arxiv.org/abs/2501.17096). | **Methodological anchor**. Public-flow statistical response can qualitatively differ from real metaorder impact; undercuts naive causal backtesting. |
| **R06 ★** | **Hey, Neuman & Tuschmann (2025 preprint), “Nonparametric Estimation of Self- and Cross-Impact.”** [arXiv:2510.06879](https://arxiv.org/abs/2510.06879). | Already estimates multi-asset propagators and confidence intervals using proprietary metaorders plus public equity flow; our **simple constrained estimation is application work, not new estimation theory**. |
| **R07 †** | **Neuman, Stockinger & Zhang (2023 preprint), “An Offline Learning Approach to Propagator Models.”** [arXiv:2309.02994](https://arxiv.org/abs/2309.02994). | Offline estimation and robust/uncertainty-aware execution precedent; constrain robust-control novelty. |
| **R08 ★** | **Trivedi (2026 working paper), “Separating Flow-Driven From Information-Driven Price Impact Across Asset Markets.”** [SSRN:6450561](https://ssrn.com/abstract=6450561). | **Very close crypto estimation overlap**, with Binance public trade illustrations and structurally constrained matrix response; separate what this document adds and note its depth-validation caveat. **Working paper, not treated as journal result.** |
| **R09 †** | **Thumm & Chen (October 2026 preprint), “Market Impact Estimation via Causal Foundation Models.”** [arXiv:2610.12537](https://arxiv.org/abs/2610.12537). | Recent causal simulation/impact estimation approach and distinctions between predicted and intervention-conditional outcomes. Proof of concept; not evidence of market-cost identification by our protocol. |
| **R10 †** | **Rosenbaum & Tomas (2022), “A Characterisation of Cross-Impact Kernels.”** *Frontiers of Mathematical Finance*. [DOI](https://doi.org/10.3934/fmf.2022005). | Independent admissibility reference; verify paper's exact notation and assumptions if extending kernel family. |
| **R11 ◇** | **Almgren & Chriss (2000 manuscript / 2001 journal), “Optimal Execution of Portfolio Transactions.”** *Journal of Risk*. [DOI](https://doi.org/10.21314/JOR.2001.041). | Canonical risk–impact liquidation benchmark and motivation. |
| **R12 †** | **Gatheral (2010), “No-Dynamic-Arbitrage and Market Impact.”** *Quantitative Finance* 10(7), 749–759. [DOI](https://doi.org/10.1080/14697680903373692). | Why price-impact shape and decay cannot be selected independently under no-arbitrage principles. |
| **R13 †** | **Ackermann, Kruse & Urusov (2026), “Multi-Asset Optimal Trade Execution With Stochastic Cross-Effects: An Obizhaeva–Wang-Type Framework.”** *Mathematics and Financial Economics*. [DOI](https://doi.org/10.1007/s11579-026-00416-7), [preprint](https://arxiv.org/abs/2503.05594). | **Different** modern stochastic matrix cross-impact/resilience framework; weakens broad “first stochastic multi-asset” novelty claims. |
| **R14 †** | **Ramirez & Sanchez (2023), “Optimal Liquidation With Temporary and Permanent Price Impact, an Application to Cryptocurrencies.”** [arXiv:2303.10043](https://arxiv.org/abs/2303.10043). | Prior crypto price-impact calibration and optimal liquidation. Do not claim the general combination “crypto + execution” is new. |
| **R15 †** | **Bundi, Wei & Khashanah (2024), “Optimal Trade Execution in Cryptocurrency Markets.”** *Digital Finance* 6, 283–318. [DOI](https://doi.org/10.1007/s42521-023-00103-y). | Crypto market-vs-limit execution and fee effects; baseline / implementation-cost grounding. |
| **R16 †** | **Albers, Cucuringu, Howison & Shestopaloff (2026), “An Open Book: Level 4 Order Book Data from the Hyperliquid Exchange.”** [Zenodo DOI](https://doi.org/10.5281/zenodo.18184441). | Free order lifecycle/book research archive, large 195.3GB; prospective detailed-data extension. |
| **R17 ◇** | **Cont, Kukanov & Stoikov (2014), “The Price Impact of Order Book Events.”** *Journal of Financial Econometrics*. [DOI](https://doi.org/10.1093/jjfinec/nbt003). | Order-book event OFI and depth-dependent impact baseline; explicitly **not** the same as taker-volume imbalance in 1m klines. |
| **R18 ◇** | **Anastasopoulos et al. (2026), “Order Flow and Cryptocurrency Returns.”** *Journal of Financial Markets*. [DOI](https://doi.org/10.1016/j.finmar.2026.101047). | Crypto return-prediction overlap; distinguish statistical signals from execution impact. |
| **R19 ◇** | **Doan & Vo (2025), “The Interconnection Between Net Buying Pressures in Derivatives and Spot Markets.”** [DOI](https://doi.org/10.1016/j.bar.2025.101702). | Spot/perpetual signed-flow transmission already studied; prospective basis/funding extension requires a new question. |
| **R20 †** | **Abi Jaber, Bondi, De Carvalho, Neuman & Tuschmann (2025 preprint), “Fredholm Approach to Nonlinear Propagator Models.”** [arXiv:2503.04323](https://arxiv.org/abs/2503.04323). | Prior theory for nonlinear impact existence/numerics. Not part of linear core. |
| **R21 †** | **Abi Jaber, De Carvalho & Pham (2024 preprint), “Trading With Propagators and Constraints: Applications to Optimal Execution and Battery Storage.”** [arXiv:2409.12098](https://arxiv.org/abs/2409.12098). | Constraints / stochastic Fredholm formulations are established; applied QP constraints are **not an automatically new theorem**. |
| **R22 ◇** | **Neuman & Zhang (2023 preprint), “Statistical Learning With Sublinear Regret of Propagator Models.”** [arXiv:2301.05157](https://arxiv.org/abs/2301.05157). | Learning regret literature; theory stretch must check for overlap. |
| **R23 ◇** | **Muhle-Karbe & Tuschmann (2026 working paper), “Trading With Uncertainty About Signals and Price Impact.”** [SSRN:6275479](https://ssrn.com/abstract=6275479). | Robust optimal trading under uncertain signals/impact; review before proposing uncertainty-based theory. |
| **R24 ◇** | **Albers, Cucuringu, Howison & Shestopaloff (2022), “Fragmentation, Price Formation and Cross-Impact in Bitcoin Markets.”** [DOI](https://doi.org/10.1080/1350486X.2022.2080083). | Crypto cross-venue effects—not evidence of own **cross-asset** execution impact. |
| **R25 †** | **Hoch / Talos (2025), “An Empirical Model of Market Impact in Cryptocurrency Trading.”** [Talos report](https://www.talos.com/insights/an-empirical-model-of-market-impact-in-cryptocurrency-trading). | Private **parent-order** evidence and practical crypto impact scale; raw execution dataset **not available for free**. |
| **R26 ◇** | **Zheng, He & Yang (2023 preprint), “Optimal Execution Using Reinforcement Learning.”** [arXiv:2306.17178](https://arxiv.org/abs/2306.17178). | Existing crypto/cross-exchange execution approach, but not core optimizer. |

**Novelty audit rule:** Before writing an abstract/paper introduction, check **R01, R04, R06, R08, R09, R13–R16, R20–R23** again for revisions and overlapping released code, then characterize novelty narrowly. This document is not a warranty of publication eligibility or priority.

## 18. Data documentation and exact acquisition references

| ID | Documentation/source | Use |
|---|---|---|
| **D01 ★** | [Binance Public Data official GitHub/README](https://github.com/binance/binance-public-data), [archive browser](https://data.binance.vision/). | **Required**: canonical futures kline/aggTrades schemas, UTC timestamp units, directory structure, daily/monthly release timing and published checksums. |
| **D02 †** | [Binance bookDepth folder (BTC)](https://data.binance.vision/?prefix=data/futures/um/daily/bookDepth/BTCUSDT/), [issue #431](https://github.com/binance/binance-public-data/issues/431), [issue #496](https://github.com/binance/binance-public-data/issues/496), [issue #512](https://github.com/binance/binance-public-data/issues/512). | Optional depth-band file path, plus concrete **corruption/staleness/incompleteness warning**; checksum validity is insufficient. |
| **D03 ★** | [OKX official historical-data landing page](https://www.okx.com/en-us/historical-data), [official API docs changelog](https://www.okx.com/docs-v5/log_en/). | Conditional tick plus L2 history since 2023, public historical-download entry and scope. |
| **D04 †** | [OKX API historical download parameter reference (client documentation)](https://github.com/burakoner/OKX.Api/blob/master/docs/reference/public.md). | Parameters `module`, `instFamilyList`, UTC/UTC+8 distinctions and 10-inclusive-day API bound; **reconfirm against current official API immediately before download**. |
| **D05 ★** | [Binance USD-M Futures REST API / historical funding-rate documentation](https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data). | Optional recorded funding times/rates, pagination and venue semantics. |
| **D06 †** | [Hyperliquid research archive (Zenodo, DOI 10.5281/zenodo.18184441)](https://zenodo.org/records/18184441). | Exact file-size/schema metadata, potential L4 extension; 195.3GB **not minimum-project data**. |
| **D07 †** | [Binance fee structure explanatory page](https://www.binance.com/en-NG/support/faq/detail/360033544231). | Illustrative tier/fee assumptions; cannot establish this researcher's historical fee tier. |
| **D08 ◇** | [Bybit public dataset](https://public.bybit.com/), [CryptoHFTData](https://www.cryptohftdata.com/). | Additional leads only; no unsupported claim of free historical full L2. |

**Concrete minimum download manifest:** `BTCUSDT, ETHUSDT` × **30 monthly files each** for `2024-01, 2024-02, …, 2026-06` from the futures/um 1m kline template in §3.1: **60 ZIPs total**, plus their `.CHECKSUM` files if provided. **Optional pilots**: `2 symbols × 7 selected days = 14 aggTrades ZIPs` and up to 14 days of initial depth files in a week-long two-symbol pilot, and **six OKX instrument-day L2 files plus same-venue trades** conditional on actual endpoint metadata. No existing project dataset or downloaded market files are assumed.

## 19. Freeze checklist for the eventual first full run

- [ ] The `2024-01 → 2026-06` dataset, vendor terms and actual free access checked; quote-volume and taker sign verified against sample raw prints.
- [ ] Test dates/episodes **not inspected** while tuning hyperparameters or evaluating preliminary improvements; prior period used only for development.
- [ ] Data timestamps / fields validated, gaps masked, no future-volume leakage, one raw and one canonical cleaned dataset.
- [ ] Per-asset USDT normalization and return-response formula confirmed; PSD requirement applies to the correctly scaled kernel.
- [ ] A/B use matched nuisance variables/hyperparameter budget; lagged control collinearity excluded; own/cross flow identification limitations acknowledged.
- [ ] Published AJNT restricted benchmark reproduced separately from the applied constrained QP, with correct terminal inventory convention.
- [ ] Every baseline has the same inventory, constraints, covariance risk accounting and information cutoff; E1/E2/E3 definitions fixed before test.
- [ ] The **difference between E0 in-model optimism and E1–E3 stress evidence** appears prominently in results.
- [ ] All reported costs specify units, fees, spread assumptions, evaluation kernel and what was actually observed; no fabricated live fills.
- [ ] Negative coefficients, PSD binding, failed solver runs and adverse regimes are reported, not silently removed.
- [ ] Results contain figures, source links, month/regime tables, block CIs and limitations; only verified achievements appear on CV.

**End of specification v1.0.** Initial scope and parameters are research choices for implementation, not completed experimental findings. A separate `AGENTS.md` and execution plan may be prepared later; neither is supplied by this document.
