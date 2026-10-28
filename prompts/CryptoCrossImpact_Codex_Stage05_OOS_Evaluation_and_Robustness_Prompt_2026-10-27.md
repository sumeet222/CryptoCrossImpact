# Codex Stage 5 — Locked Out-of-Sample Evaluation, Independent Scenarios, and Robustness

**Project:** `CryptoCrossImpact`  
**Stage:** 5 of 6 — complete the pretest authorization checks, then evaluate the frozen BTC/ETH execution study  
**Prepared:** 2026-10-27 (based on Stage 4 handoff generated 2026-10-28 UTC)  
**Execution mode:** Local repository, existing `.venv`, CPU-only. **Execute autonomously within `AGENTS.md` and the scientific stop gates below.**  
**Required final status:** Either `G4 OOS COMPLETE` (with separate scientific verdicts), or an honest `PRETEST HOLD` / `QUALIFIED` identifying unfinished gates. **Do not begin Stage 6.**

> **STARTING INSTRUCTION FOR CODEX:** Read `AGENTS.md`, the approved research specification, `SPEC_CHANGELOG.md`, the Stage 1–4 research and session reports, and especially `docs/stage05_pretest_policy_evaluator_lock_v1.md` together with `configs/stage05_pretest_lock.yaml`. Implement and run Stage 5 completely **only after** the two outstanding pretest checks are resolved: (1) actual historical funding-settlement treatment, and (2) independent evaluator E1 implementation plus development-only validation. Verify and close the pretest lock *before opening any January–June 2026 canonical market outcomes*. Then run the prespecified monthly walk-forward A/B/N0 response tests and matched T0/T1/T2/T3/T3B/T4 policy evaluation under common E0–E3 environments; calculate all costs, block confidence intervals, adverse regimes and bounded robustness analyses; produce a compact research report, tables/figures and session report. **Never choose methods, exclusion rules, scenarios, or metrics after seeing 2026 results. Do not implement optional models C/D, SOL, L2/L4, live execution, or Stage 6.**

---

## 0. Scientific authority, scope, and checkpoints

### 0.1 Authority and files to read before execution

1. Record `git status --short`, branch/commit, existing uncommitted and untracked files, and incremental storage use. Preserve user work; no unrequested commit, push, destructive cleanup, history rewrite or cross-repository modification.
2. Read **the actual repository** `AGENTS.md`; `CryptoCrossImpact_Research_Specification_v1_2026-10-27.md`, particularly §§0, 2, 4, 5, 6.4–6.6, 8–15 and 19; `SPEC_CHANGELOG.md`; `configs/core.yaml`; the Stage 2–4 configs; the actual Stage 1–4 research reports and latest session logs.
3. **Binding pretest source**: `docs/stage05_pretest_policy_evaluator_lock_v1.md` and `configs/stage05_pretest_lock.yaml` **as actually generated in Stage 4**, not the text of this prompt where a value differs. Verify recorded file hashes, the `PRETEST_LOCK_PENDING` status and the Stage 4 handoff's cited lock SHA. If inconsistent, resolve against the frozen, pre-outcome artifacts and document the discrepancy **before** accessing 2026 canonical outcomes. A missing or contradictory pretest protocol is a HOLD, not permission to invent one.
4. Inspect and reuse working APIs in `src/cryptocrossimpact/data/`, `kernel/` and `execution/`, plus `scripts/stage02.py`, `scripts/stage03.py`, `scripts/stage04.py`; inspect the actual file layout instead of assuming path names. Prefer the verified Stage 2 `refit_historical`, Stage 3 exact-cell `triangular_cash` / `build_problem` / `solve_execution`, and Stage 4 episode/forecast/policy functions. Keep existing compatible interfaces.
5. Reuse existing `.venv` and `requirements.txt`. A small free package addition is allowed if essential; do not install a separate toolchain or use external compute. No new paper is needed: `references/2403.10273v2.pdf` and the specification bibliography are already available. Only **the free official funding history**, if used, is potentially new data.

**Previously reported, to verify from source rather than blindly assume:** Stage 1 60/60 Binance USD-M BTC/ETH monthly kline partitions valid; Stage 2 `N0/U/A/B` PSD-constrained development selection, `tau=60` min and `ridge=1`, observational B-over-A validation MSE gain ~6.65%; Stage 3 mathematical AJNT V1 and constrained V2 `PASS`; Stage 4 736/736 development episodes, 4,416 schedules for T0/T1/T2/T3/T3B/T4, 116 tests passing, **`PRETEST_LOCK_PENDING`**. Stage 4 performed **no** historical path-cost comparison and **never opened** 2026 canonical observations. The Stage 2 A/B coefficients reflect **public contemporaneous flow associations, not identified causal own-trade impact**.

### 0.2 Stage 5 deliverables and scientific order

**Phase 5A — no 2026 outcome opening:** Inspect/fix the pretest protocol; verify funding events and lock the handling method; implement and validate the independent E1 estimator and E2/E3 generators using pre-2026 data; finish performance/metric/eligibility tests; produce a signed/hash-linked `PRETEST_READY` manifest.

**Phase 5B — only after 5A passes:** Execute chronological January–June 2026 test once under the frozen protocol. At each month start, fit only permitted past data, build causal episodes and policies, score all against shared E1–E3 worlds and optional diagnostic E0, and save complete paired results. Also score the prespecified monthly **contemporaneous explanatory** N0/A/B response fit (H1); do not confuse H1 with alpha.

**Phase 5C — no retuning:** Perform the fixed bootstrap and robustness matrix, generate concise primary tables/figures and scientific conclusions including negative results, then stop for the Stage 6 final report. Complete a new `AGENTS.md`-format Codex session report even if blocked.

**No-go boundaries:** Do not start Phase 5B if either Phase 5A gate is unresolved, the recorded lock cannot be reconciled, an estimator identity or solver has a scientific invalidity, or expected 2026 data access violates terms. If only a secondary stress/sensitivity fails, finish valid primary branches and report that stress as `QUALIFIED` or `BLOCKED`; never hide unfavorable results.

---

## 1. Phase 5A, gate 1: funding settlement verification and treatment — BEFORE ANY 2026 price/flow access

The required Binance Vision **trade-price** 1-minute klines do **not** establish historical funding settlement times or realized rates. Stage 4 explicitly left this unresolved. Prefer the **simplest scientifically defensible completed branch**; this is a CV project, not a derivatives-accounting platform.

### 1.1 Permitted data and source verification

- Primary candidate: official Binance USD-M perpetual historical funding-rate endpoint, per instrument:
  `GET https://fapi.binance.com/fapi/v1/fundingRate?symbol={BTCUSDT|ETHUSDT}&startTime={UTC_ms}&endTime={UTC_ms}&limit=1000`.
  This is **not** evidence that the endpoint is accessible in the user's region; probe access/terms/response schema/rate limits and paginate without missing events. Official source and semantics are in specification §3.6 / D05. An equivalent **verified official free archive** is acceptable with precise provenance; no guessed calendar from an 8-hour convention.
- Verify actual settlement timestamp coverage, sorted uniqueness, instrument identity and whether any known irregular interval or missing rate exists for **2025 development and 2026 test dates**, including adjacent boundary dates. Run an initial validation on development-only sample records. **Before lock closure, do not inspect, aggregate or use 2026 funding-rate signs/magnitudes for economic decisions**: only coverage and event timestamps may be audited as factual calendar metadata. Rates are permitted later solely if the funding-cash branch was chosen *before* test scoring.
- Do not bypass access restrictions, invent a zero rate, reinterpret perpetual funding as price impact or use a different venue's event dates as interchangeable. Keep downloaded records in one ignored local data source with a compact provenance/coverage manifest; no public raw archive redistribution.

### 1.2 Choose and freeze exactly one of two authorized methods

**F1 — explicit realized funding cashflows (if the source supports it cleanly).** Document the sign convention against official documentation (e.g., positive perpetual funding generally means longs pay). For each funding event, calculate an *inventory-weighted, sign-correct* cost for a **long inventory being progressively sold**; include any event exactly at episode arrival (initial exposure) and declare consistent endpoint/bin conventions, with the outstanding quantity and the source's reported mark/reference price where legitimately available. If the score uses an approximated reference notional instead of true mark notional, label and test that approximation. Only realized rates used **by the scorer after policy scheduling**; no post-arrival rate may affect scheduled trades. Apply identically to every policy, preserving the recorded schedule and end inventory. Audit simple positive/negative/zero funding and event-in-bin hand examples. Do not assume settlement is always every 8 hours. Funding can be negative cash *cost* (receipt).

**F2 — verified timestamp-only common exclusion (often simplest for this project).** When accurate settlement times can be established but cashflow modeling is disproportionate or rates are not available, freeze a **calendar/event-time-only** exclusion: drop every episode whose **closed or boundary-inclusive** holding interval `[t0,t0+T]` intersects **either instrument's actual verified funding event** (including an arrival event). Do not use the realized rate sign, market direction, future return or policy-specific scheduling to decide. Declare boundary convention, compute and report coverage by month, and apply identical episode removal to all policies. No unverified `funding=0` claim; state that eligible episodes are **funding-event-free under the verified schedule**. All selected policies remain identical to the Stage 4 model outside these predetermined exclusions.

**Fail-closed:** If neither actual event timestamps nor a reliable funding method can be verified for the entire required range, mark `PRETEST_FUNDING_HOLD` and **do not open 2026 canonical outcomes**. Diagnose the actual access blocker; do not substitute undocumented 8-hour UTC times. If F1 has incomplete rate coverage, do **not** automatically switch to F2 after seeing outcomes: choose the switch during Phase 5A, document it and freeze before test.

---

## 2. Phase 5A, gate 2: E1 independent evaluator implementation — DEVELOPMENT ONLY

The pretest lock requires a **distinct past-estimated evaluator**, not another name for T4's fitting kernel. Implement and test it before opening the final test. E1 is **alternative observational parameterization**, *not* causal intervention identification.

### 2.1 Exact E1 definition from the Stage 4 pretest lock

For test month start `m` (UTC), fit E1 on **exactly 180 complete UTC calendar days**:

`[m - 210 calendar days, m - 30 calendar days)`.

- Include both BTCUSDT/ETHUSDT canonical data with the **same 1m signed quote-flow definition**, return basis, source identity and suitably fixed Stage 2 nuisance features. All targets, time-varying fit normalizers and each `L` must be learned **only on the E1 block**; context bars may precede its start to form lags, but may not enter E1 targets/normalizers. No evaluated-month label enters fitting. Check final target available time and 30-day embargo precisely.
- Constrain each symmetric **2×2** component matrix PSD, with **exactly two exponential time constants `(5,30)` minutes**, same admissible statistical framework and appropriate solver. **Do not reuse optimizer B's `(60)` time constant, `C`, `L` or standardization** as E1 parameters. Reuse the *estimator code* and source QC to avoid methodological bugs.
- Choose E1 ridge **once before test** from the existing Stage 2 **development** `candidate_selection.csv`, specifically the *full B* candidates with `(5,30)` and the stated 0.1%-near-minimum/stronger-ridge rule; record rows, chosen value, script/hash and rationale. **Do not tune E1 ridge on 2026 response errors or policy results**, and do not per-month re-search it.
- An E1 candidate must report its own matrix components/eigenvalues, lag family, source/fit cutoff, L, normalization identities, PSD diagnostic, numerical convergence, full 180-day completeness and a distinct evaluator ID/hash. It can overlap T4's historical observations but may **never** use any outcome from the month being evaluated. This is not a randomized independent experiment.
- If an E1 block is truly unavailable or source-invalid, the specification's **frozen pretest development-B fallback** may be used **only if this fallback is finalized in Phase 5A**, with the exact failure reason and `QUALIFIED` label. No silent switch to T4's current fitted parameters or a validation/test-error-driven choice. A different estimator family is an unapproved protocol change.

### 2.2 E1 development test (mandatory)

Using **2025-only development calendar months**, perform a genuine small-scale historical test of E1: verify two representative as-of 180-day/gap windows, target rows, normalizers, PSD matrices and reproducible fit; compare E1 matrices/curves against B's optimizer kernel to confirm they are **not copies**. Test its parameter recovery on small synthetic data and evaluate analytic cash-cost identities/PSD for a known artificial schedule. Test a deliberately wrong date window and a wrong model/kernel/market identity; both must fail. The E1 development test is an **implementation check**, not a reason to select a favorable evaluator based on execution performance. Keep 2026 canonical Parquet from being opened by any preflight test, including an accidental fallback.

### 2.3 Freeze the E2/E3 evaluator world constructors on development inputs

Implement identical evaluator interfaces that can score **every** policy on **the same** kernel/scenario input. Require PSD of all generated matrix components and of the exact-cell symmetric cash Hessian (with a scale-aware relative tolerance). No silent eigenvalue repair.

| Evaluator | Frozen construction and allowed scientific interpretation |
|---|---|
| **E0** | All policies scored under the **same** optimizer-B kernel and base temporary/spread/fee assumptions. Mechanical, *circular in-model* diagnostic **only**; exclude from primary claims. |
| **E1** | Separate full PSD kernel from the predeclared 180-day, 30-day-gap window above; base `κ=0.001`, fee `5` bp, halfspread `1` bp. **Main alternate evaluation world**. |
| **E2** | Diagonalize *each E1 component matrix*, preserving its diagonal, decay times, liquidity scaling and other assumptions. **Null cross-impact world** (can penalize T4). |
| **E3** | Prespecified **one-factor-at-a-time** stresses centered on E1: *all matrix components jointly* multiplied by `{0.5,1,2}`; all decay constants multiplied by `{0.5,2}`; `κ ∈ {0.0005,0.001,0.005}`; cross interpolation `(1−ρ)diag(C)+ρ C` with `ρ∈{0,0.5,1}` on **each** PSD matrix; plus opposite-sign cross via `D C D`, `D=diag(1,-1)`, as a separate adverse PSD world. Deduplicate identical base scenarios and label each ID unambiguously. No stress should change only an isolated off-diagonal entry in a way that violates PSD. |

No E4 (same-venue order-book) without a separately authorized and sourced extension. Do not add scenarios after reviewing 2026 outcomes. In a scenario where `τ` is stressed, regenerate the **exact continuous-cell-integrated** cash matrix at the stressed decay, not an ad-hoc multiplication of existing discrete lag entries. When `L` differs between A/B/E1, convert each into **the same actual USDT sale schedule** before scoring; never compare or sum incompatible scaled coordinates.

### 2.4 Close the pretest lock explicitly

Before any 2026 canonical read:

1. Verify the actual Stage 4 lock and YAML agree with this source, check their recorded hashes and preserve both originals as immutable predecessor artifacts (do not overwrite lock v1 silently).
2. Freeze F1/F2 funding method, E1 fit implementation/validation and chosen development-only ridge, evaluator IDs, parameter grids, exact-price proxy, fixed policy names, train/refit cuts, H1/H2 metrics and units, exclusion/timing rules, regime thresholds computed from **2025 development episode inputs only**, bootstrap design/seed and bounded sensitivities. Verify all required software/data sources/constraints first. Finalize a **new, versioned ready manifest/lock v1a or v2** plus hashes and a dated changelog entry saying **`2026 outcomes not yet opened`**; scientific settings may not change after this point except as declared exploratory or with a genuinely untouched new test window.
3. Run a **preflight test barrier**: attempts to open a 2026 canonical Parquet *before this ready flag exists* must fail **before I/O**. Check barrier on the actual CLI/data loading path. The barrier can open 2026 only after (i) verified funding method, (ii) E1 development validation, (iii) pretest lock hash consistency, (iv) all prerequisite scientific tests passing and (v) saved `PRETEST_READY` file with UTC time/config/code hashes. A mere human-readable status line is not enough.
4. If any requirement remains open, produce a `PRETEST HOLD` report and stop final scoring. Do not implement around it by setting an unsafe default.

*Chronological nuance:* The **per-month** as-of E1 fit for later 2026 months may include **elapsed earlier 2026 data**. Therefore **do not attempt to materialize all six 2026 E1 fits before any 2026 reads**; instead freeze its algorithm and verify it on 2025 first, then fit each month's as-of E1 **before that month's outcomes are scored**, using only the time-eligible history. The same applies to optimizer A/B/N0 monthly refits.

---

## 3. Phase 5B: immutable test universe and strictly chronological execution

### 3.1 Test calendar and source identity

- Final **2026-01-01 00:00 UTC through 2026-06-30 23:59 UTC** (inclusive), Binance Vision **USD-M futures/um** perpetual `BTCUSDT`/`ETHUSDT`, **1m**. This is not spot, mark/index, or cross-exchange data.
- Scheduled 60-minute, 1-minute-slice arrival episodes at **00:00, 06:00, 12:00, 18:00 UTC every eligible day** (**724 nominal episodes** across 181 calendar days, before predetermined exclusions). Both initially long inventories are sold to hard zero; no buys, shorts or round trips.
- Arrival at `t0` observes the last completed bar with open `t0−1min`, available exactly at `t0`, but **never** the current or future bar. Only complete, valid paired 28-day past histories may form decisions. Do not change Stage 4 missing/invalid/zero-volume/jump rules after seeing outcomes.
- **Exclusion hierarchy**: (a) past-input QC checked at arrival, (b) if F2, verified funding-event **timestamp-only** exclusion, (c) future evaluation window **structural integrity** (missing/invalid paired required bars) checked **only after** a policy set was generated, symmetrically for all strategies. Never exclude for bad returns, high execution cost, realized liquidity, unprofitable strategies, unusual volatility or optimizer failure; such issues must appear as outcomes/failure counts. Report nominal/excluded/eligible counts and reasons by month and policy.
- Preserve existing Stage 1 raw/canonical partitions and Stage 2–4 frozen models/results. Do not copy the full market dataset per strategy or per refit; existing monthly canonical partitions and small reports suffice.

### 3.2 Month-by-month as-of order of operations

Process test months **sequentially** `2026-01` ... `2026-06`; for each month `m`:

1. Before scoring any episode in month `m`, generate A/B/N0 as-of **optimizer/conditional-response** models using the **immediately preceding 365 complete UTC days** `[m−365d,m)`, exactly as frozen in the specification/Stage 4 lock. Fixed selected A/B `tau=(60)` minutes, `ridge=1` (N0 uses its preselected development penalty); independent per-fit `L` and training transforms. No within-month refit, no test-result hyperparameter update. End target must be available by start of `m` and the lag context must not leak an in-month target. Validate each model's cutoff, PSD, L and provenance; reject U as an execution kernel.
2. Generate E1 from `[m−210d,m−30d)` with its fixed `(5,30)` family/ridge and distinct normalization, then E2/E3. Save **all** month-specific optimizer/evaluator artifacts, hashes, cutoff assertions **before scoring that month's outcomes**. Prior 2026 months may legitimately be part of the next month’s available past. The algorithm and settings were locked in Phase 5A; this is causal walk-forward refitting, **not re-selection**.
3. From each arrival's preceding full paired 28-day history, compute Stage 4's **hour-of-week/other fallback** predicted 60-bin quote turnover `Vhat`, trailing covariance `Sigma_per_minute` (`ddof=1`), initial `X0=0.02 sum_k Vhat_i,k`, and per-bin cap `0.10 Vhat_i,k`; `κ=0.001`, `θ=1`, five-bp taker fee, one-bp halfspread, `m=0`. All predictors/features and model IDs must be **available as of that episode**. 28-day forecast/lookback and risk multiplier conventions must be identical across policies. The 60-minute within-hour forecast may be constant; preserve the documented **T0≈T1 degeneracy** rather than tune the forecast to separate their performance.
4. Generate **all six** Stage 4 policies **T0** capped closest-TWAP, **T1** causal forecast-VWAP, **T2** independently optimized single-asset A, **T3** joint A with full risk covariance, **T3B** joint B-diagonal retaining exactly B's own-impact components/scale, and **T4** joint full B with full covariance. T2 must use the **same global TWAP risk multiplier** as the others even when optimizing the own-variance contribution. Exact-cell USDT cash and cap inventory constraints are inherited from Stage 3. Do not reoptimize policies under E1/E2/E3 or in response to realized future prices. Record per-schedule solver/KKT/residual failures and their causes; do not hide them by dropping the entire episode from the sample.
5. Store a compact **read-only decisions snapshot** (episode IDs, data-availability cutoff, model/evaluator inputs and parameter hashes, forecasts, caps, inventories, and schedules) before any policy scoring uses the post-arrival price path. Then load price/volume evaluation bars to compute the frozen scenario outcomes. Enforce this as a real programmatic interface separation, not a comments-only promise. Re-running policy generation on its already available past after seeing results is for deterministic verification only; do not alter science based on it.
6. Save month-level results and a checkpoint **without looking at results to decide upcoming settings**. Every later month uses exactly the same locked algorithm and predeclared evaluators. A later test month may contribute historical data to a future refit by causal availability; it must not contribute to **research design selection**.

### 3.3 Core policy and evaluator fairness invariants

- One episode carries **identical `X0`, `Vhat`, caps, horizon, fee/spread, risk covariance, reference P0, ex-ante risk-normalization coefficient and source identity** across all six policies. Only the policy's allowed impact assumption changes.
- **T4 vs T3** is the primary prespecified comparison of fitted full-B against independently estimated diagonal-A strategies (both different estimated self coefficients and cross terms). **T4 vs T3B** is the secondary controlled *cross-only* comparison with identical B self-impact. Do not confuse them or silently substitute one as primary when an effect is attractive.
- On every evaluator and episode, score *every* valid policy using exactly the **same evaluator `G_E`, `κ_E`, price-path proxy, fee/spread, and funding/eligibility rule**. Never score T3 under A and T4 under B to claim cross-strategy savings. The optimizer's preferred own-model objective is not a fair cost ranking.
- Stage 2's observational kernel is **not structurally identified**. Even a positive E1 result is **scenario-conditional modeled shortfall**, not measured live savings.

---

## 4. Outcome scoring: precise definitions and units

### 4.1 Price-path component and cash shortfall

For each asset `i` at episode `t0`, let `P0_i` be the **last pre-arrival completed 1m close**. Sale `z_{i,k}` denotes reference **USDT notional**, corresponding to approximate base quantity `z_{i,k}/P0_i` throughout the episode. Primary realized reference price `P_{i,k}` is the **close of the minute beginning at `t0+k min`**. Define:

`C_path(z) = sum_{i,k} z_{i,k} * (1 - P_{i,k}/P0_i)`  (USDT).

This is a **recorded unaffected-price-path proxy**. It can be negative; never clip negative shortfall into profit-free zero. It is not an observed exchange fill. Prespecified timing sensitivities: next interval **open** and arithmetic mean of its OHLC, explicitly labeled non-executable price proxies. All policies share exactly the same reference rule.

### 4.2 Exact-cell modeled impact, temporary cost, fees, funding

For each evaluator `E` and immutable cash-notional sale schedule `z`:

```
C_transient,E(z) = 0.5 * vec(z)^T * H_G(E) * vec(z)   [USDT]
C_temporary,E(z) = kappa_E * sum_{i,k} z[i,k]^2 / Vhat[i,k] [USDT]
C_fee(z)         = (fee_bps/10000) * sum_{i,k} z[i,k]  [USDT]
C_spread(z)      = (halfspread_bps/10000) * sum_{i,k} z[i,k] [USDT]
C_funding,E(z)   = signed F1 cash cost if chosen; otherwise 0 only for
                   verified F2 funding-event-free eligible episodes [USDT]
C_shortfall,E    = C_path + C_transient,E + C_temporary,E
                    + C_fee + C_spread + C_funding,E
bps_E           = 10000 * C_shortfall,E / W, W=sum_i X0_i > 0
```

- Construct `H_G(E)` by Stage 3's validated **exact exponential cell integrals** with E1/E2/E3 `C_a, τ_a, L`. The returns-to-cash factor `10^-4` and each `sqrt(L)` appear **exactly once** in the code. Do not use the Stage 2 **return regression lag-difference coefficients** in place of **level kernels**. For different fitted normalizers L, the underlying real sale schedule `z` remains unchanged; evaluator-specific `L` enters only the cash conversion.
- `Vhat` is **ex ante** and shared in primary temporary-cost scoring; any alternative `Vreal` denominator uses true **post-arrival observed quote volume only in a clearly tagged ex-post stress evaluator**, and not for policy sizes/caps. Report realized per-bin participation `z/Vreal` and incidence above 10% without retroactively invalidating schedules. Handle verified zero volume explicitly (infinite/undefined realized participation), **never** replace it with a fabricated volume.
- Risk objective term from Stage 3 is **not actual cash cost**. Report `C_risk_preference` and raw inventory-variance proxy separately, and an optional total *objective including risk* explicitly labeled non-cash. It is wrong to add a risk preference to realized implementation shortfall as though it was paid to an exchange.
- Fixed all-taker linear fee and constant spread are **schedule-invariant for fully sold equal-notional inventories**; verify this numerically. Show cost breakdown; do not falsely attribute the policy advantage to a constant fee component. Report USD/USDT distinction and model approximation: all calculations in **USDT reference notional**.
- If using F1: cash flows are based on actual verified timestamps/rates and the predeclared outstanding-position convention, common to policies; data may enter scoring after schedules are frozen. If F2: no event intersects the predeclared inclusive holding interval; report the common eligibility removal rather than assuming universal zero funding.

### 4.3 Evaluator output matrix

Score all policies under **E1**, **E2**, and **every frozen E3 world**; E0 is extra diagnostic and is never used to substantiate the main H2 claim. Save *the whole episode × policy × evaluator/scenario matrix*, not just positive or pooled differences. E1 and stress parameter IDs must be stored with each row. Include adverse worlds where T4 loses. An infeasible or failed policy is a disclosed failure with diagnostic, **not** an omitted poor return.

Every row must carry at least: `episode_id`, UTC arrival and refit cutoff, month, asset/inventory sizes, model/policy ID, evaluator/scenario ID, source/canonical IDs, spec/pretest-lock/config/code hashes, decision snapshot hash, solver/pass status, common exclusion/QC reason where relevant, path/transient/temporary/fee/spread/funding cash components, **total shortfall USDT and bps**, risk preference/raw inventory risk, max realized participation and diagnostic invalid counts. Store month summaries separately from compact long-form results; no per-policy duplicate full market data or individual 1m price files.

---

## 5. Prespecified inference and scientific hypotheses

### 5.1 H1: response-fit test, NOT an actionable return forecast

Perform the **monthly as-of A/B/N0** matched test against actual 2026 recorded signed flow and contemporaneous minute return, using locked nuisance features and time normalizations. H1's primary paired monthly standardized MSE A versus B, with per-asset MAE/RMSE and explanatory conditional `R²`, is an **observational conditional-response** comparison. Report:

- Pooled and six monthly paired standardized MSE for A/B/N0, same eligible target sample for each; `delta_fit=(MSE_A-MSE_B)/MSE_A`, with the predeclared **0.5% practical threshold**, negative months, per-asset results and daily paired loss statistics.
- Time-series-aware block interval for paired loss differences (not 260,000 independent minute draws). Label the same-minute flow as **observed after its bar**, not available to earlier decisions. The lag-only 2025 diagnostic showed essentially no forecast skill; **do not reinterpret H1 as a tradable return prediction**.
- No test-period decay/ridge/feature searches or target revisions; later-month refits are with fixed family/hyperparameters.

### 5.2 H2: matched scenario shortfall, the central decision result

For each common episode `e` and evaluator `E` define:

`Delta_E,e = 10000 * ( C_E(T3,e) - C_E(T4,e) ) / W_e`  (bps; **positive favors T4**).

Secondary cross-isolation:

`Delta_cross,E,e = 10000 * ( C_E(T3B,e) - C_E(T4,e) ) / W_e`.

Report paired pooled and monthly means/medians, both USDT and bps, **positive/negative share**, 25th/75th percentiles, 95% intervals, evaluator-by-evaluator adverse effects, worst periods, **maximum regret** against the best strategy *within each world* and failed-schedule counts. E1 is the main alternate world; E2 and every E3 stress must be shown prominently even if they reverse the ranking. A project-specific **0.1 bp** E1 practical target is *not* a significance test or a reason to tune the simulator. If H2 is negative, preserve and explain the negative finding.

The **T3B comparison is scientifically important**, because Stage 4 showed that T4/T3 also differ in their fitted diagonal coefficients. Keep both comparisons, with the primary/secondary labels fixed.

### 5.3 Correct paired uncertainty: block on calendar days

- For execution results, the basic dependent units are **calendar days** with up to four correlated episodes per day, not individual minutes or independently sampled strategy rows. Use **seven-consecutive-calendar-day moving-block bootstrap**, **500 draws**, `seed=20261027`, 95% percentile interval, as in Stage 4 lock.
- Draw complete contiguous 7-day blocks with replacement from the **full calendar-day index**, concatenate/truncate to the test span. Carry every paired policy/evaluator observation, original exclusion/missing status and episode-day grouping together; **do not resample independently by policy or world**. An eligible-day-only list that collapses over removed calendar days would break the declared block design.
- Calculate pooled episode-weighted mean bps contrast from the resampled days (or clearly document the frozen weighting if the lock specifies a different one); retain calendar-day clusters and disclose zero-eligible bootstrap replicates rather than force an outcome. For relative cost reduction, define the denominator and give a missing/unstable flag if the baseline mean is zero or crosses zero; do not turn negative-cost denominators into wins.
- H1 block uncertainty must use **paired daily loss aggregates** under a time-series-aware block design, not a 500,000-row IID standard error. The six monthly results are reported individually; do not claim six months are independent Gaussian observations.
- Do not calculate a test p-value for each of dozens of post-selected worlds. If an exploratory FDR table is added, label it exploratory; exact primary comparisons are locked.

### 5.4 Required regime and risk views

Compute month-by-month; weekday/weekend; **past-information-defined** low/middle/high liquidity and volatility states with tercile boundaries frozen using **July–December 2025 episode inputs only**; 2026 state at arrival cannot see future realized volume/volatility. Report both cost and ex-ante risk exposure. If high/low groups overlap in time or have small samples, say so; don't infer regime invariance from one favorable subgroup. Include how often realized participation exceeds 10%, the most adverse full-matrix regimes, and the fraction of E1/E2/E3 worlds where T4 underperforms T3/T3B.

---

## 6. Bounded sensitivities, no adaptive search

After **all primary H1/H2 results are frozen and indexed**, run the limited prespecified secondary work. This is **diagnostic robustness**, never a second hyperparameter search on the test outcomes:

| Dimension | Frozen set / action | Interpretation |
|---|---|---|
| Cross effects | T4 versus T3 (primary), T4 versus T3B (secondary), E2 and E3 `rho` cross removal | Coupled execution versus diagonal null; isolate cross term |
| Impact world | E1 versus all E3 amplitude/decay/sign scenarios | Identified weakness under model misspecification, not new structural estimates |
| Temporary liquidity | E3 `κ=0.0005,0.001,0.005` | Sensitivity to assumed mechanical execution cost |
| Optimizer risk | `theta=0,1,2` only | Reoptimize each strategy from same past inputs and matched caps, with common risk-convention reference |
| Inventory size | initial target fractions `.005, .01, .02, .05` of forecast 60m turnover | Recompute quantities from the same **past** forecast; show infeasible size/cap combinations honestly |
| Participation caps | `.05,.10,.20` | Identical forecast caps, skip/report infeasible combos without future-volume repairs |
| Reference price | next-bar close primary; next-bar open and OHLC arithmetic-average score sensitivities | Historical price reference convention, not actual exchange fills |
| Horizons | 30 and 120 minutes secondary | Recompute past-only horizon-specific forecast totals, sizes and caps; preserve four arrivals per day and non-overlap |
| Fixed notional | $100,000 per leg **only where ex-ante caps permit** | Economic-size illustration, not eligibility conditioning on realized liquidity |
| Fees/spread | fee 2/5/10 bp; halfspread 0/1/2 bp | Illustrative fixed linear costs, typically policy-rank invariant |
| Refitting stability | Frozen June-2025 parameters vs monthly rolling 365-day models as a separately labeled sensitivity | Drift/estimation risk; **not** grounds for changing the chosen primary refit |

**Compute discipline:** One-factor-at-a-time around the locked primary settings; **do not perform the full Cartesian product** of scenario × horizon × size × risk × fee. Prioritize core E1–E3 and H1/H2, then complete cheap authorized sensitivities. If compute/disk becomes problematic, reduce only secondary optional work with a clearly documented `QUALIFIED` status, never silently omit an adverse base scenario or change test sample. No L2, SOL, spot–perp, stochastic-signal Fredholm, or nonlinear ML extension in Stage 5.

---

## 7. Verification tests and scientifically meaningful failure handling

Add focused `tests/test_stage05_evaluation.py` (and a small helper test file only if needed). Before opening the final test, **run the relevant new synthetic/2025 tests**; after lock closure, run regressions without revising outcomes. At minimum test:

1. **Barrier and timing:** before `PRETEST_READY`, any 2026 canonical dataset read fails **before I/O**; after ready, an as-of month optimizer cannot access its own-month future for refit, E1 has exactly 180 whole days with a 30-day gap, and episode decisions never use the bar beginning `t0` or any later bar. Perturbing after-arrival data changes **scores only**, not X0/caps/forecasts/schedules.
2. **E1 independence:** matrix/lag parameters not copied from T4; E1 training normals/L and PSD all source-specific; fixed `(5,30)` family and development-selected ridge; negative test rejects use of future model as evaluator and rejects U/non-PSD/wrong asset order.
3. **Funding:** positive/negative cashflow sign, zero-event windows, arrivals exactly at events, internal settlement events, event at horizon endpoint under declared convention; F2 common exclusions independent of rate signs or prices; failures on missing source calendar.
4. **Cash decomposition:** independent hand one/two-bin price-path and impact examples; exact Stage 3 triangular-vs-Hessian identities under E1/E2/E3 and different L; no double count of within-bin impact or extra 60-minute factor; all policies evaluated under one world; constant fee cancels from paired equal-notional comparisons.
5. **Evaluator worlds:** all E3 matrix/decay/interpolation/opposite-sign variants PSD; diagonal E2 zero cross at *each component*; stressed decay recomputes exact-cell coefficients; reject invalid/negative impact Hessian instead of project-to-PSD; E0 marked `IN_MODEL_ONLY`.
6. **Policy matching:** same forecasts/caps/risk/cutoffs at arrival; T4−T3B isolates B off-diagonals, T4−T3 includes both estimated self/cross; no schedule changes after evaluator variation; capital/terminal inventory/sell-only checks and failures preserved.
7. **Bootstrap:** toy 14/21-day time-series with known paired effects, seven-day contiguous resampling and reproducible seed; keep entire policy/world rows paired and preserve excluded calendar days; check no IID per-minute/per-episode bootstrap; one bootstrap check with zero/negative baseline cost.
8. **QC and mutation:** predeclared structural future-bar gap excludes commonly with a logged reason; a severe **valid** price jump or adverse policy outcome must remain; a failed policy solve is not silently mapped to a cost of zero or removed as a market-data error. Negative implementation shortfall is preserved. Realized next-minute turnover cannot affect participation caps.
9. **No test-driven selection:** assert frozen config/lock hashes and fixed scenario lists throughout full scoring. Verify 2026 path is never opened in any pretest command; after opening, every result's model and scenario IDs trace to the fixed settings.
10. **Regression and determinism:** rerun key Stage 2/3/4 focused tests; on a small **test-free** fixture verify score sums, evaluator identities and exact rerun equality. Avoid rerunning expensive Stage 1 downloads just for reporting. Where a full experiment run fails, checkpoint valid months and resume idempotently without double-counting or replacing past results.

**Numerical integrity:** No silent clipping of negative costs, PSD eigenvalues, risk terms, ratios, nonconverged solvers, residual inventories, missing funding, missing market data or empty bootstrap samples. Keep failures and qualifications visible. Tolerance scales should reflect USDT-notional numerical conditioning and inherited solver checks, not an arbitrary absolute “1e-8 USD” across all magnitudes.

---

## 8. Lightweight implementation artifacts and reproducibility

Adapt existing folder conventions. Recommended, **not mandatory**, small additions:

```text
configs/stage05_evaluation.yaml                    # pretest-bound run config; no unapproved changes
src/cryptocrossimpact/evaluation/                 # concise scorer, funding, scenarios, inference
scripts/stage05.py                               # preflight | freeze | test | summarize | robustness | all
reports/research/stage05_oos_evaluation.md       # research findings, not full Stage 6 manuscript
reports/research/stage05_artifacts/               # selected small CSV/JSON tables, locks, figure-data
figures/stage05/                                # meaningful compact PNGs
results/stage05_oos/                             # ignored bulk paired schedules/scores, checkpointed
results/experiment_index.csv                     # small run index, track if permitted
reports/sessions/YYYYMMDD_HHMM_stage05_oos_session.md
tests/test_stage05_evaluation.py
```

- Preserve the pretest v1 source and its SHA; save a separately versioned **ready** lock/manifest after passing funding+E1 gates. Record all original and new hashes. In `SPEC_CHANGELOG.md`, document only actual scientific clarifications/deviations; don't rewrite the core specification to make unexpected results look predetermined.
- Commands can be adapted to the existing CLI; recommend `stage05.py preflight`, `stage05.py freeze`, `stage05.py test`, `stage05.py summarize`, `stage05.py robustness`, `stage05.py all`. An `all` entry point must enforce the pretest barrier; it must never silently skip a failed gate. A `preflight` command must never read 2026 canonical price/flow outcomes.
- Record per-run Python/package versions, Git starting/ending state, spec/pretest lock/config/code/source hashes, seed, as-of model cutoffs, funding verification/source, versioned evaluator IDs and cheap restart commands. Use **one copy** of canonical market data; write only new compact paired results and figures. No databases, cloud deployment, unnecessary parallel computation, APIs, trading systems, dashboards, or enterprise logging.
- A result plot must state which **evaluator world**, policy, window, cost units, and uncertainty unit produced it. Save small data-behind-figure tables, inspect actual PNGs for mislabels/clipping, and reference them relatively in Markdown. A CV-grade readable science report matters more than exhaustive instrumentation.

**Minimum required figures:**

1. 2026 data/episode timeline with excluded cases and the funding rule applied.
2. Monthly A/B/N0 *conditional explanatory* fit, BTC/ETH separately and pooled (H1).
3. As-of estimated self and off-diagonal impact kernel drift over the six months, with PSD status.
4. Paired T4−T3 and T4−T3B **E1** bps shortfall contrasts with 95% day-block intervals, monthly and overall.
5. Scenario/evaluator heatmap (E1/E2/E3) including **adverse/worst** contrasts (not just in-model E0).
6. Cash-cost decomposition and representative inventory/schedule comparisons, indicating fee invariance and modeled-vs-recorded terms.

**Minimum tables:** (i) sample/eligibility/funding/QC; (ii) H1 per-asset/month; (iii) policy score decomposition and raw risk under E1; (iv) full scenario stress matrix with T4 underperformance fraction and maximum regret; (v) bootstrap effects and stated limitations. Additional figures only for distinct scientific questions. Do not generate a massive PDF or polished CV claims yet; Stage 6 will synthesize.

---

## 9. Acceptance gates, report, and handoff to Stage 6

### Phase 5A readiness verdict (must be explicit)

`PRETEST_READY` requires **all**: verified funding plan F1 or F2 for the entire sample; E1 estimator developed/tested using 2025-only data and its development-selected ridge fixed; E2/E3 PSD; 2026 I/O firewall and exact time boundaries tested; preserved Stage 4 lock and consistent new versioned lock hashes; correct primary contrasts/inference settings; tests passed and a UTC before-test ready manifest created. Anything else is `PRETEST HOLD`; do not pretend 2026 outcomes were safely opened.

### G4 full OOS verdict (after 2026 results)

`G4 OOS COMPLETE` means the frozen January–June 2026 sample was actually evaluated for **H1** (matched, time-aware explanatory response) and **H2** (matched decisions under E1/E2/E3), with all common exclusions/failures, model/refit timestamps, cash/risk decomposition, paired block confidence intervals, months/regimes/adverse worlds and tested source provenance. **It does not require H1/H2 to be favorable.** The distinct scientific conclusion is `SUPPORTS_HYPOTHESIS`, `DOES_NOT_SUPPORT`, or `INCONCLUSIVE` per H1 and H2; implementation `PASS/QUALIFIED/BLOCKED/INVALID` is independent.

**When reporting:** Make the causal boundary explicit. Public same-bar order-flow association does not identify the price effect of our orders, and no kline-based hypothetical backtest observes actual fills, queue response or participant adaptation. Say **“modeled/scenario-based execution shortfall”**, not **“realized live savings”**. Compare E0 in-model optimism with E1/E2/E3 adverse outcomes; negative evidence can be the central research finding.

**Required Codex closing outputs:**

1. `reports/research/stage05_oos_evaluation.md`: a compact, precise research evaluation with primary tables/figures, H1/H2 effect sizes and uncertainty, negative months/scenarios, any holds, source limitations, and actual tested findings. Use links relative to file location.
2. Small `stage05_artifacts` with versioned pretest ready manifest, funding provenance, as-of model/evaluator registry, per-month coverage, primary contrasts, bootstrap CI summary and stress matrix; save any larger paired schedule table in ignored `results/` with a portable re-run command.
3. `reports/sessions/YYYYMMDD_HHMM_stage05_oos_session.md`: follow `AGENTS.md` (exact files changed, run order, verified test counts, status, hashes/versions, storage/RAM, failures/deviations and next action). If 5A blocks, report the blocker and **confirm 2026 canonical outcomes were not opened**.
4. Concise final Codex reply: **stage verdict**, pretest-lock status, nominal/eligible/scored episodes, H1/H2 direction and confidence or explicit `NOT_RUN`, E1/E2/E3 adverse result summary, test count, scientific limitations, paths and resource delta. No fabricated success, and no new Stage 6 work.

**STOP after Stage 5.** Do not refit model families to test results, reinterpret observational flow as a causal kernel, launch optional signal/spot–perp/L2 investigations, draft CV bullets as completed live trading performance, or begin the final Stage 6 project manuscript. The next authorized stage is the synthesis/report **once the whole OOS result, including unfavorable cases, has been documented**.

---

## 10. Start command to paste in Codex

```text
Read AGENTS.md, CryptoCrossImpact_Research_Specification_v1_2026-10-27.md,
SPEC_CHANGELOG.md, docs/stage05_pretest_policy_evaluator_lock_v1.md,
configs/stage05_pretest_lock.yaml, and
prompts/CryptoCrossImpact_Codex_Stage05_OOS_Evaluation_and_Robustness_Prompt_2026-10-27.md.

Execute Stage 5 completely. Before accessing any 2026 canonical market outcomes,
verify actual funding-settlement treatment and implement/validate E1 on 2025-only
history, then close and hash the pretest lock. If either fails, report a HOLD
and do not open test outcomes. Otherwise run the locked six-month walk-forward
H1/H2 evaluation, E1/E2/E3 stress scenarios, predeclared sensitivity and paired
block-bootstrap inference. Produce the research and session reports, preserve
prior artifacts, and stop before Stage 6.
```

**End of Stage 5 prompt.**
