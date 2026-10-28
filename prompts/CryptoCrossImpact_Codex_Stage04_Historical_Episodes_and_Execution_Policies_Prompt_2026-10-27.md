# Codex Stage 4 — Historical Episode Construction, Causal Inputs, and Matched Execution Policies

**Project:** `CryptoCrossImpact`  
**Stage:** 4 of 6 — build the development-period episode engine and policy suite; finalize the pretest protocol  
**Prepared:** 2026-10-27  
**Execution:** Run **locally in the existing repository root** with its current `.venv`. Execute autonomously under the repository's *actual* `AGENTS.md`. Stop after Stage 4; do not conduct the final OOS test or Stage 5 cost comparisons.

> **STARTING INSTRUCTION FOR CODEX:** Read `AGENTS.md`, the complete research specification, its changelog, the Stage 1–3 reports and session reports, and the existing code/artifacts before changing anything. Implement and execute **Stage 4 completely**: (i) time-safe historical execution episodes and 28-day, past-only liquidity/risk estimates; (ii) all core, exactly matched liquidation policies T0–T4 using the verified Stage 3 QP and Stage 2 kernels; (iii) diagnostic cross-term isolation and development-only feasibility/schedule analysis; (iv) a **versioned, explicit pretest policy/evaluator lock** for Stage 5. Run focused tests, produce compact figures and research/session reports, and stop. **Do not open or score January–June 2026 market observations; do not conduct historical implementation-shortfall or hypothetical savings comparisons at Stage 4.** Avoid production engineering; this is a CV research study.

---

## 0. Authority, current checkpoints, permitted scope

### 0.1 Read and inspect first

1. Capture `git status --short`, branch/commit, pre-existing untracked work and disk footprint. Never reset, overwrite, delete, commit, push, or reorganize unrelated user files without authorization. **Do not copy or reuse the sample EBM project's AGENTS.md**; the local CryptoCrossImpact `AGENTS.md` is authoritative for general conventions.
2. Read `CryptoCrossImpact_Research_Specification_v1_2026-10-27.md` in full, emphasizing **§§0, 2, 4, 5.2–5.5, 6.4, 7, 8–13, 14, 19**; `SPEC_CHANGELOG.md` and the current `configs/core.yaml`, `configs/stage02_kernel.yaml` and any Stage 3 configuration. The research spec controls scientific definitions. This prompt operationalizes Stage 4, and records a clarification where the original baseline table does not perfectly isolate the cross term.
3. Read `reports/data/stage01_data_quality.md`, the actual Stage 2 research report and `reports/research/stage02_artifacts/{selection.json,model_A.json,model_B.json}`, and the actual Stage 3 research report, run manifest, figures, tests, and session report(s). Locate paths from the live repo rather than assuming all filenames exactly match these examples.
4. Inspect source interfaces, particularly `src/cryptocrossimpact/data/`, `src/cryptocrossimpact/kernel/`, `src/cryptocrossimpact/execution/`, and `scripts/stage03.py`. **Reuse** `execution.impact_cost.load_stage02(root, 'A'/'B')`, `execution.solver.solve_execution(...)` and the verified cash/Hessian functions when present. Confirm signatures from code. Reuse canonical partitions, manifests, tested historical-refit functionality and source-time conventions rather than creating duplicate loaders.
5. Verify `.venv/bin/python`, `requirements.txt` and solver availability. Add only minor free dependencies if truly necessary; no new environment, paid data, L2 bulk download, cloud, trading API, dashboard or complicated orchestration.
6. Optional primary reference `references/2403.10273v2.pdf` is already present. No new paper PDF is required for Stage 4. The published AJNT unconstrained/terminal-penalty benchmark and our hard-terminal, sell-only applied QP remain **different** problems.

**Reported checkpoints — confirm against actual files:** Stage 1 G0/G1 `PASS` (60/60 Binance USD-M futures 1-minute monthly archives validated, 2024-01 through 2026-06). Stage 2 G2 `PASS`, development A/B selected `tau=60` minutes and `ridge=1` (conditional response, **not identified intervention impact**), 2025 validation pooled MSE A≈0.465341, B≈0.434409. Stage 3 G3 `PASS`: AJNT zero/exponential V1 reproduced; fractional endpoint match qualified; V2 integrated Volterra impact cash costs, feasible constrained OSQP QP verified by CLARABEL, 45 focused tests passed. Treat these as reported results, **not a reason to skip code/interface checks**.

### 0.2 Hard data and outcome firewall

- **Stage 4 may read only 2024-01-01 through 2025-12-31 market observations**, with a first emphasis on **2025-07-01 through 2025-12-31 development-validation episodes**. The development part may be inspected for engineering, forecasting and schedule plausibility. The final 2026-01-01–2026-06-30 test is still locked. No Stage 4 script, test, plot, hidden diagnostic or fallback may deserialize/open 2026 Parquet market data or report 2026 economic outcomes.
- Historical **as-of data** may be used to *form* 2025 policies and characterize schedules/forecast quality, but do not implement or run a historical price-path implementation-shortfall backtest, retrospective book-fill simulator, **E0–E4 cost evaluator**, or H1/H2 2026 hypothesis scoring. Stage 5 owns those operations.
- The Stage 3 verified **synthetic** calculations may be rerun when needed; do not refit Stage 2 hyperparameters or change the research target to chase an attractive schedule.
- Do not modify the 60 canonical monthly source partitions, source manifests, Stage 2 model JSONs, Stage 2 estimation lock or Stage 3 benchmark implementation except for an independently justified, tested critical bug fix, with an explicit changelog and non-destructive preservation of prior output.
- Public same-bar signed flow is **not** a real-time forecast of own future price impact. Stage 4 policies receive only known fitted kernels, ex-ante turnover forecasts, past covariance and declared scenario parameters. **No alpha** in the core (`m=0`).

---

## 1. Deliverables and acceptance standard

Produce an end-to-end, **development-only** episode-to-policy pipeline that:

1. Creates each eligible UTC `BTCUSDT`/`ETHUSDT` perpetual-futures liquidation episode using **only data available by its arrival instant**; records source/clock provenance, forecast coverage and exclusion reasons.
2. Implements/preserves **T0 capped TWAP, T1 causal forecast-VWAP, T2 independent optimizers, T3 joint zero-cross (fitted model A), T4 joint full cross (fitted model B)** with identical inventories, forecast caps, risk accounting conventions and available information. Add **T3B** (or an unambiguous diagnostic name) using **B's exact self-impact matrices with B's off-diagonal set to zero**, for a controlled isolation of *the cross term*. Do not silently relabel T3.
3. Exercises the suite on July–December 2025 **development validation only**, beginning with a very small smoke sample and then processing the full eligible development episode set. Produces schedule, inventory, cap and validity diagnostics; **no observed future-price cost/P&L results**.
4. Creates a definitive versioned **Stage 5 policy/evaluation pretest lock** specifying protocols, assumptions, evaluator E1–E3, change/hold rules and a machine-checkable hash (including any explicitly unresolved data items). It must state what is *ready* vs *pending* before January 2026 outcomes can ever be opened.
5. Adds focused tests, a compact Stage 4 research report and a new session report, with `G4_PRETEST_READY` or a clearly qualified/blocked status. **Do not claim Stage 5's G4 OOS gate has passed**: that requires the actual final evaluation.

Follow the minimum credible CV-project workflow; do not add a database, event-driven fill engine, order simulator, deployment service or excessive bookkeeping.

---

## 2. Episodes, time semantics, and data identity

### 2.1 Universe, horizon and episode grid

- Exchange/data: **Binance Vision futures/um 1-minute** `BTCUSDT`, `ETHUSDT` USDT-margined perpetual trade-price OHLC and quote turnover, using existing **Stage 1 canonical** Parquet. Never substitute Binance spot, mark/index candles or cross-venue books.
- Develop on **2025-07-01 00:00 UTC through 2025-12-31 23:59 UTC**. Horizon **60 minutes**, with `delta=1` minute (60 sale bins); episode arrivals **00:00, 06:00, 12:00, 18:00 UTC** every calendar day. These give **736 nominal development-validation episodes** (184 days × 4), before any objective predeclared quality exclusion. Start times are specified by the calendar; do not select or drop episodes based on future prices, profitability, solver preference or volatility realized during the episode.
- At arrival `t0`, the last permissible market bar is `[t0−1min,t0)`, whose close is known at exactly `t0` under the source's bar-completion convention. Store the last valid close as **arrival reference** `P0` for *later* scoring; do not use any 2025 after-`t0` price to choose policy schedules. A flow/bar with open time `t0` is **not** available when the initial schedule is formed.
- Primary decision is a **single frozen/open-loop 60-minute schedule**, determined at `t0` from only past information. No post-arrival schedule revision or realized future-volume adaptive cap. A receding-horizon version requires separate authorization and a new fair baseline design.
- Require both instruments present and valid for all *historical input windows*. For Stage 4, whether the **future 60-minute realized bars exist** is relevant only to a mechanically predetermined eligibility/missing-data audit on development data; it may never select episodes based on future values. Record exclusions precisely. Do not forward-fill lost data, synthesize volume, replace source anomalies or change the Stage 1 quality flags.
- If a selected episode has a flagged price jump or zero-turnover/stale history, keep it unless the **predeclared input-quality rule** says it is unusable, and report sensitivity/flags instead of cherry-picking days. Use Stage 1 flagged calendar facts for auditing, not to build future-regime signals.

### 2.2 One episode record: provenance and information set

Every episode must carry at minimum:

`episode_id`, `t0_utc`, venue/market/symbol order, arrival `P0`, data ID/source hashes, model IDs and **as-of fit cutoffs**, forecast construction cutoff/lookback, forecast positive-floor/fallback usage, `Vhat[bins,assets]` in **USDT per bin**, initial inventory `X0[assets]` in **reference USDT notional**, cap `pmax*Vhat`, `Sigma_per_minute[2,2]` of **log returns per minute**, `T`, `delta`, risk/temporary/fee/spread assumptions, QC status, policy status and `test_outcomes_unopened=true`. Preserve physical units.

Use one well-defined causal information cutoff for all methods; a different method must not benefit from a later revised bar or realized future trading volume. Store compact provenance as part of episode metadata (or in shared run metadata), not duplicate all raw market fields into each policy file.

### 2.3 Historical models / rolling refits

- Primary Stage 4 preview: **Stage 2's already selected fixed-family A/B model artifacts trained through 2025-06-30**, so July–December 2025 are out-of-fit observations for policy construction. Use their stored liquidity normalizers `L`, asset ordering, time units, calibration provenance and `C` as exported by the tested loader.
- Also implement and **exercise** the **monthly 365-complete-calendar-day as-of refit interface** needed for Stage 5: for each 2025 development month July–December, either reuse an existing verified Stage 2 `model_development_refit_YYYY-MM.json` with exact matching cutoff or invoke the tested `refit_historical` routine restricted to data before that month. Ensure the fit has no month-internal leakage. Record the exact 365-day window and its own `L`; do **not** map a normalized `C` to another `L` without the correct cash-consistent transformation.
- Choose *one* main Stage 4 policy-generation/refit convention for the development diagnostic tables—**prefer the monthly as-of refits** because Stage 5 will use them—while retaining the fixed June-2025 model as a clear sensitivity/check. The selected kernel family/penalty are frozen by Stage 2; **do not reselect using any 2026 information or retrofit the test period**.
- If a development monthly refit artifact lacks a needed field or does not match the Stage 2 API, repair the interface in a tested, minimal way; do not silently re-estimate or use a fitted model trained after the episode's arrival.

---

## 3. Ex-ante forecast turnover, risk and inventory definitions

### 3.1 One past-only turnover forecast for all policies

At every arrival `t0`, use only previous **28 full UTC calendar days / completed minute bars before `t0`** to create a forecast vector `Vhat[i,k]` for `k=0,...,59` for the intended future clock times. The specification prioritizes trailing-median quote-turnover seasonality by hour-of-week, with shrinkage/fallback. Concrete bounded default here:

1. Select historical 1-minute **USDT quote volume** observations matching each future bin's UTC **hour-of-week**, over `[t0−28d,t0)`; forecast **median minute turnover** of valid completed bars in that class. Require at least **120** valid minute observations for this fine class; otherwise use a trailing **hour-of-day** median (minimum 120) and then the overall trailing 28-day median. Use calendar semantics; crypto trades 24/7 (no NYSE session clock or DST adjustment).
2. Use a strictly positive **forecast floor** determined at `t0` from the trailing window's positive data, initially the **1st percentile of positive minute quote turnover** for that asset (bounded below by a tiny numerical epsilon, documented); record all fallbacks and clipping. Do not use future realized volume, current unfinished minute, test-wide normalization or validation-global lookups.
3. Use deterministic historical handling of legitimate verified zero-volume bars; they are observed zero activity, not missing rows. If a median/floor cannot be estimated from a clean history, **mark the episode unavailable**; never fill from future bars.
4. Forecast at minute granularity, but no neural network / complex volume prediction. Do not tune the forecast to improve T4's apparent performance. A simple trailing overall median may be a documented robustness comparator, not a concealed replacement.

Use exact UTC bar availability—verify that the most recent included bar opened before `t0` and has `available_at_utc <= t0`. Implement shared forecasts once, then pass the **same exact `Vhat` array** to every baseline, constraint and optimizer. Save a compact development-only forecast diagnostic (coverage, seasonal/fallback frequencies and, optionally, development-only forecast-versus-realized aggregate error, **not** trading-cost performance).

### 3.2 Inventory and caps

For both assets, primary initial sale inventory is:

`X0_i = 0.02 * sum_{k=0}^{59} Vhat_{i,k}` in **USDT reference notional**.

Set per-bin sell cap `cap_i,k = 0.10 * Vhat_i,k`. All strategies share **exactly the same** X0, 60-bin horizon and caps. Nonnegative sales, hard terminal equality, no buy/short/round trip. The starting inventory is sized **ex ante**, never from realized future turnover. Check `sum(cap_i,k) >= X0_i` analytically, and fail/flag if numerical rounding or data quality makes a case infeasible. Never change the denominator retrospectively.

Primary `pmax=10%`, initial target `2%`; do not require all `0.5%,1%,5%`, cap `5%,20%` and horizon `30/120` sensitivity grids now. Implement straightforward parameterization for Stage 5; a one-episode smoke for alternate horizons/caps is sufficient.

### 3.3 Past-only covariance and shared risk normalization

- Estimate per-minute 2×2 return covariance `Sigma_per_minute` from clean, consecutive **1-minute close-to-close log returns** within trailing `[t0−28d,t0)` available at `t0`. Require a clear minimum coverage, record valid counts, and use a modest **PSD-aware numerical convention** (e.g. symmetric sample covariance; reject if materially indefinite, clip only negligible negative floating-point roundoff with disclosure). Never include returns from after arrival.
- Stage 3's solver accepts `Sigma_per_minute` and internally applies `delta` once. Do not multiply by 60 or by bin length a second time; do not confuse covariance of price returns with covariance of USDT positions.
- Define *one reference risk multiplier per episode* using the **full past-only covariance** and the common, cap-constrained closest-uniform TWAP reference schedule: `beta = theta*(W/10000)/R_raw(TWAP)` with `theta=1` primary, `W=sum X0`, and **pretrade** inventory risk. All policies use the *same global beta/risk preference scale* for fairness, and report the actual full-covariance risk diagnostic regardless of what a baseline optimized. If `R_raw` is effectively zero, use the documented Stage 3 theta-zero fallback with a warning.
- **T2 independent** optimization may omit off-diagonal risk *inside its own decision objective* per specification, but must retain that same externally determined global `beta`; **do not** renormalize risk separately by asset and inadvertently change the comparison. If Stage 3's API recomputes beta by default when Sigma changes, add a small tested optional parameter or equivalent controlled implementation—not a new solver.

### 3.4 Locked objective and assumptions

Use Stage 3's **verified exact-cell Volterra cash cost** with the model's own `C`, `tau`, `L`, actual `delta`; **not** the naive half-point kernel, a rewritten raw-price response, or AJNT's unconstrained signed solution. Set primary `kappa=0.001`, `theta=1`, `fee=5bps/side`, `halfspread=1bp`, `m=0` (no alpha); keep all costs in USDT with objective decomposition as in Stage 3. Fee and spread are **illustrative schedule-constant all-taker assumptions** under equal-total sell-only programs, not historical fills or a source of schedule advantage.

---

## 4. Baseline policies and fairness rules

Implement the following **named, traceable policies**, with identical data/episode IDs and no future inputs:

| ID | Policy | Exact decision rule | Interpretive role |
|---|---|---|---|
| **T0** | **Capped TWAP** | Equal `X0_i/60` USDT notional per minute, projected to the nearest feasible schedule under per-bin caps and exact sum if necessary: minimize `sum_k (z_i,k−X0_i/60)^2` subject to `0<=z<=cap` and `sum z=X0_i`. Use deterministic, documented projection; preserve raw target and adjustment counts. | Timing-uniform baseline, not a kernel optimizer. |
| **T1** | **Forecast VWAP** | For each asset `z_i,k = X0_i Vhat_i,k / sum_j Vhat_i,j`, with deterministic minimal cap-repair if the chosen parameter setting requires it. **Forecast-only**; never hindsight realized VWAP. | Causal liquidity-aware baseline. |
| **T2** | **Independent single-asset execution** | Optimize each asset with fitted model A's own kernel, temporary cost/caps, own variance term and the **shared global beta** defined above; no cross-impact or cross-risk interaction inside the decisions. | Operational independent baseline. |
| **T3** | **Joint risk-aware / diagonal impact A** | Solve the joint Stage 3 QP with **model A's fitted self-impact kernels** and the **full return covariance**, shared beta/constraints. | Specified primary no-cross strategy for comparison to T4; note that A's fitted self coefficients differ from B's. |
| **T4** | **Joint full matrix B** | Solve joint QP with **model B's full PSD matrix** and full covariance, same inputs. | Cross-impact-aware candidate; no structural/causal claims. |
| **T3B** | **B self-impact, zero cross (diagnostic)** | Construct `diag(C_B,a)` for **each component a** from B, preserve B's `tau`/`L`/all else, retain full covariance. Check PSD, solve joint QP. | **Critical isolation:** T4 vs T3B changes **only off-diagonal impact**; T4 vs T3 (A) also reflects re-estimated self coefficients. |

**Interpretation clarification (record in `SPEC_CHANGELOG.md`):** The initial spec's T4–T3 comparison is scientifically valid as a **full-estimated-model versus independently fitted diagonal-model** comparison, but it is *not* a pure off-diagonal coefficient ablation because `diag(C_A) != diag(C_B)`. Keep **T3** unchanged as the prespecified comparison and add **T3B** as a diagnostic/secondary comparison. Do not revise H2 after seeing test outcomes; specify both contrasts in the lock and later reports.

All six policy paths must:

- Use **identical `t0`, `X0`, `Vhat`, caps, horizon, return covariance, common beta and fee/spread assumptions**, apart from the clearly disclosed independent T2 decision restriction.
- Produce `z[60,2]` USDT reference notional, pre/post-inventory arrays, exact terminal inventory, solver diagnostics/KKT for QPs, and per-policy identifiers/model hashes. Use deterministic tie/rounding rules; no invented maker fills, order-book slippage or unannounced residual repair.
- Pass physical feasibility with a **unit-aware** tolerance (e.g. terminal residual `<= max(1e-6*X0_i, quoted quantization tolerance)`), no negative sales and cap consistency, without silently clipping solver outputs. Disclose any numerical failures and remove/flag **the same episode for all compared policies** under a prespecified complete-case rule; do not let a complex strategy drop its bad days.
- Distinguish **objective under each strategy's model** (may differ across strategies and is *not directly comparable*) from later **cross-scored common-evaluator** cost. Stage 4 may log own-model solver objective solely to verify optimization; **do not rank policies using heterogeneous fitted objectives** or say T4 is cheaper from those numbers.

**Optional policies C/D are NOT required**: do not introduce nonstationary G or forecast alpha while Stage 4 is establishing fair core baselines. Preserve simple extensible hooks, not speculative code.

---

## 5. Development-only run protocol, diagnostics and bounded workload

### 5.1 Work sequence

1. Add tiny **synthetic** manual episodes and tests first to verify time alignments, policy formulas, fee invariance, common beta, half-cell/exact-cell compatibility and every cap/equality constraint.
2. Run **a 2-day development smoke** (up to eight scheduled arrivals) in July 2025. Print/record compact status and forecast sample values, check no test files read.
3. Run all eligible **736 nominal** July–December 2025 episodes, using one common episode set. At most a modest number of 120-variable QPs each; this is CPU MacBook research scale. Do **not** rerun 276 Stage 2 hyperparameter fits, download new raw data, create duplicated 2025 market datasets or re-run all Stage 1 integration tests.
4. Use **monthly as-of** existing model refits for primary development schedule diagnostics, and record a small fixed-model comparison on a representative predeclared subset (e.g. first UTC Monday of each month) if affordable. Do not train on the month being simulated.
5. Evaluate only **policy construction, forecast reliability and ex-ante diagnostic properties**: number of episodes accepted/flagged, forecast fallback/floor rates, cap binding/adjustment frequencies, solver numerical failures, inventory residuals, QP iterations/timing, average rate/inventory curves, T3/T4/T3B schedule distance and risk *ex ante*. **No historically realized future-price shortfall, impact-reduction bps, P&L, strategy winner or E1–E3 scenario cost matrix yet.** Do not compute a causal-impact claim from signed-flow responses.

### 5.2 Required lightweight figures/tables

Create a single Stage 4 research report, e.g. `reports/research/stage04_episode_policies.md`, with at least:

- A count/coverage table by month: 736 scheduled arrivals expected, accepted, excluded (by reason), source/model cutoff checks and fallbacks.
- Forecast and risk QA: representative trailing 28d volume profile, positive-floor frequency, input units and non-leakage validation.
- A **representative, predetermined** development episode showing BTC/ETH sales and remaining inventories for T0, T1, T2, T3, T3B, T4 against caps, and a second compact aggregate schedule summary. Choose the representative episode **by fixed date rule**, not by impressive strategy differences.
- A policy fairness/solver table: caps/terminal residual maxima, common-beta verification, number of solver failures, how often TWAP projection is needed, and schedule-difference measures (not an economic-performance table).
- A clear **stage verdict** (`G4_PRETEST_READY / QUALIFIED / BLOCKED`), open decisions, scientific limits and status of final test lock.

Keep selected human-readable figures under `figures/stage04/` or `reports/research/stage04_artifacts/`, compact table CSV/JSON under `reports/research/stage04_artifacts/`, and bulk per-episode schedule arrays under **ignored** `results/stage04_development/` (prefer a single partitioned Parquet/table plus small manifest, not one JSON per minute or per episode). Ensure figures are rendered and inspected for labels/units. Use relative Markdown links; do not duplicate raw data.

### 5.3 Avoiding unnecessary runtime overhead

One small config file, a few reusable module functions, a thin script CLI, concise structured manifests and focused tests are enough. Reuse actual Stage 3 solver and Stage 2 API. Do not create an event-driven OMS, market depth reconstruction, parallel job queue, database, CI framework or dozens of tuning knobs. Preserve the existing project's resource budget; document extra/peak bytes and avoid keeping ZIP/Parquet duplicates. Seed any random smoke if used, although primary policies should be deterministic.

---

## 6. Freeze the Stage 5 policy and evaluator protocol **before** opening test data

**This is a material Stage 4 deliverable, not a promise that test evaluation is done.** Create a versioned Markdown lock plus a small machine-readable manifest, suggested:

- `docs/stage05_pretest_policy_evaluator_lock_v1.md`
- `configs/stage05_pretest_lock.yaml` (or JSON) with a SHA-256 recorded in the Stage 4 report.

If `docs/` is not already present, create only this small directory. Include:

1. **Immutable primary sample specification:** two contracts, UTC bar-open/end convention, data provenance, 2026-01-01 through 2026-06-30 test dates (labels only, **not read**), 00/06/12/18 arrivals, 60 × 1m grid, 28d forecasts/covariance, 2% inventory and 10% cap, complete-case criteria, fee/spread/kappa/theta values, locked Stage 2 model selection and exact Stage 3 cell integration.
2. **Historical as-of refits:** first UTC day of each **test month**, use strictly earlier 365 complete calendar days and frozen family/penalty, with separate model A and B, their own `L` and provenance. Explicitly state handling of first/last available bars and lag context; no in-month future labels. No new selection of `tau`/`lambda` from test results.
3. **Policy definitions:** T0–T4 as §4 above, with **T3B as secondary cross-term isolation**, identical forecasts/constraints, common risk normalization and complete-case policy comparisons. T4–T3 is an estimated-family comparison; T4–T3B isolates cross term; do not conflate them.
4. **Scoring/evaluator definitions** from specification §10: common recorded unaffected **price path** component `C_path` using a declared primary next-bin close proxy; pre-existing Stage 3 `C_G` integrated exact cells; `kappa*z²/Vhat`, fee/spread, funding handling, cash USDT and bps; **ex-ante risk preference kept separate** from cash implementation shortfall. No historical trade fills or counterfactual reactions are asserted. Declare `E0` in-model diagnostic only, **E1** separate pre-month historical-window fitted evaluator, **E2** its diagonal/no-cross counterfactual, **E3** preannounced matrix/decay/liquidity stress worlds (see exact §10.3 multiplier/interpolation grid), common to every policy. `E4` optional only with separately matched same-venue L2 data; do not imply it exists.
5. **Critical evaluator independence:** E1 must fit a **180-day historical block ending at least 30 days before the evaluated month** (fitted separately with fixed `(5,30)` decay family and development-only regularization) or use the spec's explicitly labeled fallback if the entire block cannot be established. E1 is *alternative past-data parameterization*, **not independent causal treatment identification**. No evaluator may be tailored to T4 test success. E2=diagonal of E1 (PSD); E3 includes total-matrix `0.5/1/2` amplitude, decay `0.5×/2×`, `kappa` `{0.0005,0.001,0.005}`, and PSD-preserving interpolation of cross term `rho={0,0.5,1}`, without multiplying non-PSD matrices separately. Report scenario failures rather than discarding adverse worlds.
6. **Statistical/inference contract:** 2026 per-month A/B conditional-fit H1 (response MSE) and paired policy H2 using the same episode set and evaluators, primary T4 vs T3 plus secondary T4 vs T3B; daily-clustered seven-day moving-block bootstrap with 500 replicates for paired shortfall; per-asset and monthly breakdowns; lagged only and contemporaneous explanatory labels; adverse evaluator/regime results. Do **not** reopen thresholds after seeing test data. Explain H1 observational fit ≠ causal impact, and scenario savings ≠ realized exchange fills.
7. **Funding/data availability rules:** funding is **not** in the required Stage 1 one-minute kline archive. Before test opening in Stage 5, either obtain actual historical funding settlement timestamps/rates from a verified free source and specify inventory-weighted settlement treatment, **or** enforce the spec's fixed **timestamp-only** exclusion of windows overlapping actual settlements with documented verification. Do not invent an 8-hour funding schedule or silently set an unverified cash flow to zero. This data preflight must be finalized **before** any test-outcome scoring. Fee/spread remain stated assumptions unless externally verified.
8. **Lock process:** Save hashes for specification/changelog, config, code revision, model schema, eligible source manifest, Stage 4 development QA, evaluator protocol and a pretest `test_unopened` assertion. A later scientific change motivated by test observations requires a new untouched future period or must be openly labeled exploratory. If a critical evaluator input remains unresolved, mark `PRETEST_LOCK_PENDING` with an exact remedy, **not** a fabricated `READY`.

Stage 5 will implement and actually score evaluators and open the test **only after** the lock is complete. Stage 4 may write evaluator mathematical definitions or unexecuted test stubs but **must not run them against historical future prices**, even on 2025, unless indispensable to verifying a synthetic identity. Keep Stage 4 focused.

---

## 7. Mandatory focused tests and acceptance gates

Add `tests/test_stage04_policies.py` (and one small additional file only if necessary). Test actual code rather than self-declared statuses:

**Causality/time tests**

- Given an arrival `2025-07-01T00:00Z`, last input bar must be the one opened `2025-06-30T23:59Z`, available by `t0`; never include `2025-07-01T00:00Z` or later. Verify close/open month boundaries, UTC 24/7 calendar and time unit identity.
- **Future mutation test:** change or append all market data with `available_at > t0` (including current bar) and check `Vhat`, covariance, X0 and all six schedules remain bitwise/within deterministic solver tolerance **unchanged**.
- **Train/test firewall:** explicit attempts to access `2026-01` canonical partitions, to load a post-arrival fitted model, or to use realized target-period turnover as forecast/cap should fail before file I/O. A stage CLI with a test start date must error, not quietly use those records.
- Covariance input excludes current/after-arrival returns and is symmetric PSD up to declared numerical tolerance; model L/refit window must predate arrival.

**Policy and fairness tests**

- T0 exactly constant if no caps bind; otherwise solves closest feasible capped projection (compare with independent small analytic/water-fill solution). T1 follows known past forecast proportions, totals exactly X0 and never uses future VWAP. Under X0=`2%*sum(Vhat)` and cap 10%, T1 must be feasible by construction.
- All policies have identical positive inventories and upper caps, no buys/shorts, matching asset order, exact end inventory, meaningful solver/KKT statuses, common inputs/covariance/risk reporting. Fee/spread constants cancel from schedule timing for fully liquidated all-taker policies (within solver precision).
- T2 joint versus separate decomposition **with diagonal covariance and a fixed common beta**; T3 uses full covariance and A diagonals. Reject inadvertent normalization of T2's risk by separate per-leg denominators.
- T3B and T4 share **exact B diagonal, tau and L** and differ only in off-diagonal components. A synthetic zero-cross B must make T3B=T4 within numerical tolerance. With the same synthetic full diagonal model, other baselines reduce as expected. All PSD checks before optimization.
- Verify that Stage 3 quadratic decomposition equals evaluation of the same strategy's *own-model objective*, but **do not interpret heterogeneous own-model objectives as a policy ranking**.
- Run a tiny example with a cap-infeasible initial notional and confirm explicit failure, no silent cap relaxation or leftover inventory. Verify asset permutation and scaling of reference USDT unit where applicable.

**Historical development sample gates**

- Nominal 736 arrivals, explain any exclusions objectively and symmetrically for all policies. At least a two-day smoke and an end-to-end 2025 development run with deterministic rerun identity and run manifest. Report resource usage, number of successful policy solves and any failures.
- No existing Stage 1–3 tests regressed; run focused Stage 4 suite and relevant **non-test-opening** regression tests. Do not run 2026 Stage 1 integration QC or Stage 5 tests that intentionally inspect 2026 outcomes.
- No output may claim actual savings/profitability, independent empirical execution advantage or 2026 H1/H2 results at this stage.

**G4_PRETEST_READY means:** time-safe development episodes built, all six named policies generated, causal forecasts and common constraints tested, Stage 3 interfaces reused, development coverage/figures/research report complete, and an evaluator-policy lock written with no essential unaddressed methodological contradictions. `G4_PRETEST_READY` does **not** mean the Stage 5 research hypotheses succeeded. If funding coverage or E1 exact implementation still needs a Stage 5 preflight, report `QUALIFIED`/`PRETEST_LOCK_PENDING` as appropriate; do not falsely certify the lock.

---

## 8. Repository structure, commands, reporting, and stopping point

Expected small additions (adapt to current project conventions):

```text
configs/stage04_policies.yaml
src/cryptocrossimpact/episodes.py                  # or episodes/{...}
src/cryptocrossimpact/execution/policies.py
scripts/stage04.py                                 # smoke | build | policies | report | lock | all
reports/research/stage04_episode_policies.md
reports/research/stage04_artifacts/                # compact tables and provenance
figures/stage04/                                   # selected plotted development episodes
results/stage04_development/                       # ignored bulk schedules/episode outputs
docs/stage05_pretest_policy_evaluator_lock_v1.md
configs/stage05_pretest_lock.yaml                  # definitions/lock; no test reads
tests/test_stage04_policies.py
reports/sessions/YYYYMMDD_HHMM_stage04_policies_session.md
```

Only make files/directories that are genuinely needed; preserve `.gitignore` and document any justified new patterns. Reuse the preexisting Stage 3 solver and Stage 2 model APIs. Avoid one market-data duplicate per strategy, per seed or per episode; store schedules once with identifiers.

At completion:

1. Generate the **new Stage 4 session report** required by `AGENTS.md`: UTC time, starting/ending Git status and paths changed, data/model cutoffs, manifest/config hashes, exact commands and versions, tests run and true pass/fail counts, coverage, forecast QC, policy solver failures, source anomalies, resource delta/peak, deviations/holds and exact next action. Do not claim tests ran unless executed.
2. Produce a **readable Stage 4 research report** with a compact methods/QA summary, schedule plots, fairness tests, what is frozen for Stage 5, and scientific limitations. Use development-only labels. Save figure source data/metadata in small tables where useful.
3. Provide a concise Codex terminal summary: **stage verdict**, nominal/eligible/solved 2025 episodes, implementation and lock file paths, tests, blockers, resources, and whether January–June 2026 files were never opened. If the lock is pending, say what exactly remains.
4. **Stop.** Do not begin Stage 5, compute independent scenario/P&L/backtest shortfalls, open final-test market observations, download optional books or pursue optional C/D extensions.

**Completion principle:** Stage 4 succeeds by creating **causal and fair execution decisions on development history**, not by producing a favorable backtest. Stage 5 will independently score their costs under predeclared models and the locked final period. The reduced-form flow-response kernel remains an explicit scenario assumption, not an identified market intervention.
