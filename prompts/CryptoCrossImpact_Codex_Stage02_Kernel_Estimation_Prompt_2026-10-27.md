# Codex Stage 2 Prompt — Admissible Crypto Cross-Impact Kernel Estimation

**Project:** `CryptoCrossImpact`  
**Stage:** 2 of 6 — feature construction, response-model estimation, PSD-constrained propagators, development-validation selection, and G2 scientific diagnostics  
**Date:** 2026-10-27  
**Execution mode:** local Codex CLI/Desktop, from the existing repository root  
**Authorization:** execute **Stage 2 only**, end to end. **Do not run Stage 3's execution solver, Stage 4's liquidation strategies, or Stage 5's final OOS evaluation.**

## 0. Starting instruction and governing documents

You are the implementation and research agent. Read, in this order:

1. `AGENTS.md` (repository-wide operating rules).
2. `CryptoCrossImpact_Research_Specification_v1_2026-10-27.md` (the **authoritative scientific protocol**, especially §§0–2, 4–7, 11–13 and 14).
3. `references/AJNT_Optimal_Portfolio_Cross_Impact.pdf` (user-added **Abi Jaber–Neuman–Tuschmann** primary paper; review the relevant model, nonnegative-definite kernel and convolution-admissibility definitions; detailed paper numerical reproduction is **Stage 3**).
4. Existing Stage 1 code/config/`README.md`, `reports/data/stage01_data_quality.md`, `data/registry/source_manifest.json`, `data/registry/run_manifest.json`, `data/registry/qc_anomalies.csv`, trade-audit summaries, latest Stage 1 session report, and any existing `SPEC_CHANGELOG.md`.

If paths differ, locate the actual files rather than assuming they are absent. Check `git status --short`, branch and commit first. Preserve all existing work, including uncommitted changes, raw/canonical data and Stage 1 outputs. **Do not rewrite the research specification** or replace it with this prompt. Where this prompt is less specific than the specification, follow the specification; record genuine conflicts or necessary deviations.

**Known Stage 1 handoff (verify against actual local artifacts):** G0/G1 reported PASS; 60/60 official Binance `futures/um` BTCUSDT/ETHUSDT 1m archive partitions for 2024-01–2026-06 validated; 2,626,560 total symbol-bars, no missing minute keys/invalid bars, with one missing initial return from unavailable predecessor. Stage 1 retained flagged zero-volume/shared-stale intervals in October 2024 and completed a **QUALIFIED**, not perfectly matching, 14-symbol-day aggTrades signed-flow audit. No kernel fit or test outcome analysis was performed. The local repository and its data manifests, **not this handoff paragraph**, are the evidence of completed work.

**Do not re-download** the 60 months; use the single canonical Stage 1 dataset. The existing `.venv` should have Stage 1 dependencies; inspect it and **install only missing Stage 2 free packages** (for example `cvxpy` and an installed **SDP-capable** backend such as SCS or CLARABEL, plus plotting/statistical dependencies as needed). Keep a single reproducible dependency declaration and record selected solver versions. A QP-only solver such as OSQP is **not sufficient for the PSD-constrained estimator**. Choose small, robust, portable code rather than new infrastructure.

## 1. Scope and nonnegotiable research firewall

Implement the **observational conditional flow-to-price-response study** of specification §§4–6. The desired outputs are calibrated and validated *reduced-form* transient kernel families that Stage 3 can later use **as structural assumptions for scenario analysis**. These estimates **do not causally identify the price impact of our hypothetical trades**.

- **Instruments:** Binance USDT-margined USDⓈ-M **perpetual** `BTCUSDT`, `ETHUSDT` only; UTC one-minute last-trade closes and **USDT taker quote-notional flow**. Do not silently substitute spot, mark/index prices, base units, L2 OFI, parent orders or another exchange.
- **Train:** 2024-01-01 through 2025-06-30 UTC. **Validation:** 2025-07-01 through 2025-12-31. **Locked test:** 2026-01-01 through 2026-06-30. Make all choices based on **train/validation only**.
- **Test firewall:** **Do not read, fit, chart, rank, print, or analyze 2026 outcome rows** (returns, flows, kernel coefficients, conditional response error, predictive performance or trading-related effects). Stage 1's pre-existing test **integrity counts** may be read to confirm data identity; do not use those summaries to choose model settings or exclusions. **Do not perform rolling 2026 refits**; those belong to Stage 5 **after model/evaluation rules have been frozen**.
- **No schedules/backtests:** no optimal liquidation, TWAP/VWAP policy, execution P&L, simulator, scenario-cost comparison or test-period inference. Simple synthetic nonnegative-definiteness checks on a cost kernel are allowed as **model validity checks**, not Stage 3 execution experiments.
- **No new data or papers required.** The PDF above is sufficient primary mathematics for this stage. Do not download optional Binance `bookDepth`, OKX L2, Hyperliquid L4, SOL or spot data.
- **Conservative claims:** any empirical explanatory gain is *conditional* on observed contemporaneous trade flow; it is **not** an implementable return forecast or causal evidence. A zero/unstable off-diagonal is valid and must be reported, not repaired into a positive finding.

## 2. Stage 2 target: four matched conditional-response models

Implement and compare **N0**, **U**, **A**, and **B** from specification §6:

| ID | Specification | How to use |
|---|---|---|
| `N0` | Past-only nuisance controls, no contemporaneous/propagator flow | Descriptive control benchmark; same target and eligible rows as A/B |
| `U` | Unconstrained (possibly asymmetric) `2×2` transient flow-response coefficients on the same low-dimensional basis | **Diagnostic only**; compare empirical fit lost when imposing economic admissibility; **never export as an execution kernel** |
| `A` | Diagonal, stationary, matrix exponential propagator, all component diagonals nonnegative | Main no-cross-impact constrained benchmark |
| `B` | Full **symmetric positive-semidefinite** `2×2` component matrices, stationary exponential propagator | Main cross-impact constrained model; can have *negative off-diagonal entries* while PSD |

All four use the **same synchronized eligible train/validation rows**, target, past-only nuisance controls and metrics. Models A/B get the **same candidate decay/regularization search budget**. N0 must not lose rows just because it has no flow regressors. Keep separate *per-asset* nuisance coefficients, but fit the economically coupled matrix parameters **jointly** (do not fit BTC and ETH independently and then average directional coefficients into a supposedly PSD matrix).

### 2.1 Correct cash-consistent normalization

For each fitted training window, set `L_i` to the **median positive one-minute USDT quote volume** for asset `i`, computed from that window only. For fitting at this stage, calculate `L_i` from **development train**, and hold it fixed for all validation predictions. Define

```text
q_i,t = 2*taker_buy_quote_volume_i,t - quote_volume_i,t       [USDT]
f_i,t = q_i,t / sqrt(L_i)                                    [sqrt(USDT)]
r_i,t = log(close_i,t) - log(close_i,t-1)                    [fraction]
y_i,t = 10000 * sqrt(L_i) * r_i,t                            [bps*sqrt(USDT)]
```

`y` is **already a one-minute log return**, not a price level. **Never difference `y` again.** No symmetric/PSD requirement is imposed on the raw, heterogeneously scaled `bps/USDT` mapping; the restriction is on the `C_a` matrices that map scaled `f` to `y`.

Track the exact `L_i`, its sample cutoff, and its usage in every trained model. Keep all economic transformations reversible for later Stage 3 cash-cost conversion. Verify by tiny hand-calculated tests that a trade in quote notional is mapped to small log-price displacement using the specification's `10^-4` and `sqrt(L_i)` factors.

### 2.2 Level propagator versus *return* regression — crucial

For `K=1` or `K=2`, define `G(ell)=sum_a C_a exp(-ell/tau_a)` at nonnegative integer **minute** lags, each `C_a` constant across time. The model of **one-minute scaled returns** is the specification's equation (1):

```text
y_t = sum_a C_a [ f_t + sum_{ell=1}^{H}
                      (exp(-ell/tau_a)-exp(-(ell-1)/tau_a)) f_{t-ell} ]
      + B * x_{t-1} + epsilon_t,
```

with `H = 60` minutes initially, and the **same 1-minute UTC close-to-close time convention** as Stage 1. For each exponential, efficiently form a 2-vector **flow basis** from current flow and the specified lag differences, then fit small matrices `C_a` against these bases. Note especially that the coefficients at positive lags are typically **negative due to decay** even though `C_a` is PSD; don't impose nonnegative coefficients on *return* lags. This is not a regression of returns directly on the undifferenced `G(ell)` level weights.

**Boundary/truncation clarity:** the primary equation deliberately truncates at `H=60` and approximates the unmodeled older displacement tail. If checking exact differencing of a *truncated level* kernel, a boundary term at `H+1` appears; do **not silently add or remove it** from the prespecified primary regression. Document its size and assess `H=30/120` **on development data only** if tail diagnostics warrant it. Ensure monthly feature calculation includes necessary historical lookback so month boundaries are not mistaken for new data starts.

Each same-bar `f_t` becomes available **only after** the bar closes; therefore this is **same-bar explanatory/nowcast modeling**. The contemporaneous observation can be used in the regression but cannot be presented as an earlier trading decision's signal.

### 2.3 Nuisance variables and their availability

Implement the parsimonious controls from specification §6.2 with an explicit metadata table of **source fields, units, transformations, maximum lookback and availability cutoff**:

- BTC/ETH **past-only** log-return lags `1, 2, 5, 15` minutes.
- BTC/ETH **past-only unsigned quote-turnover activity** over `5, 15, 60`-minute windows; define and report the transformation/scale (e.g. stable training-only log / standardization). These are **not lagged signed-flow sums**.
- Lagged current/previous completed-bar volume deviation from a **trailing past-only one-day median**; handle genuine zero volumes without inf/nan fabrication.
- Trailing realized volatility over **60 and 1,440 completed minutes**; use strictly pre-target information, with a documented population/sample convention.
- Simple cyclical UTC time-of-day/day-of-week terms; these are calendar-known.
- A lagged equally-weighted BTC/ETH return factor **only if it is not an exact linear combination of already included return lags**. Diagnose design rank/collinearity first. If it is redundant, document its omission rather than retaining an unidentified nuisance direction; a no-common-factor sensitivity is permitted.

**Do not add lagged signed-flow sums as nuisance covariates**: they can duplicate the impact-basis design and destroy interpretability. Flow history is represented through the specified exponential response basis. Don't add contemporaneous other-asset returns as explanatory controls, use future values in scaling, or perform high-dimensional indicator mining. Any feature at `t-1` must have been fully available at the close of `t-1` under Stage 1's recorded `available_at_utc` semantics. Verify multi-month boundaries, training/validation handoff, and no dependence on 2026 rows.

## 3. Efficient estimation and model selection

### 3.1 Valid observations, anomalies and standardization

Use Stage 1's **source-defined valid flags** and synced BTC/ETH minutes. Exclude only rows whose target, lag window, or past-only nuisance window is genuinely unavailable; count exactly how many and why, by split/asset. Preserve the genuine October 2024 shared zero-volume/flat-price flags as recorded; **do not invent missing bars or silently remove them**. If source anomalies materially distort the development fit, report a **separately labeled, predeclared flag-mask sensitivity**, not an outcome-selected rewrite of the main sample. Show counts for the October plateau and the aggregate-trade audit caveat. Stage 1's qualified audit does **not** justify changing `q` to reconstructed tick flow.

Use **training-only** centering/scales for numeric nuisance predictors and for any numerical loss weighting. For comparable fit, standardize the scaled target **by its per-asset training standard deviation** in the regression objective / reported standardized MSE; save the transformations. Preserve `C_a` in the **original economic `f→y` coordinates** and impose PSD in those coordinates. If numerically reparameterizing the optimizer, explicitly derive and test the inverse mapping to valid economic matrices. Intercepts may be per asset; don't penalize them unintentionally. Detect exact/near collinearity and log chosen rank remedy consistently across A/B.

### 3.2 Parameterization, solvers, and computational discipline

For fixed positive `tau_a`, the mapped response is **linear in each `C_a` and the nuisance coefficients**, so use **joint, weighted, ridge-penalized least squares**, with matrix PSD constraints for B (`C_a == C_a.T`, `C_a >> 0`) and nonnegative diagonals for A. Use `cvxpy` with **an SDP-capable solver**, verify solver status and residuals, and reject invalid `C_a` rather than silently projecting the estimator to a different model. For `U`, allow fully asymmetric free matrix components with comparable regularization. In `2×2`, a nonlinear product inequality written naively is not necessarily CVXPY-DCP compliant; use a valid PSD or equivalent SOC constraint.

To stay within MacBook CPU and memory limits, process the existing monthly Parquet partitions **sequentially** and accumulate appropriately weighted `X'X`, `X'y` and `y'y` **sufficient statistics** for each candidate basis. These are small: avoid building/caching a 2.6-million-row dense design or duplicating the canonical dataset per candidate/model. Verify the accumulated-statistic objective/predictions against direct design-matrix fitting on a tiny synthetic and one small real **train-only** subset. Preserve precision (typically float64) and check conditioning. It is fine to stream small transient batches in memory. Reuse the Stage 1 `.venv` and code patterns; don't introduce Spark, distributed compute, a database or a research platform.

### 3.3 Prespecified development hyperparameter search

Start with specification's baseline candidates `K=1, tau=(5)` and `K=2, tau=(5,30)` (all numbers are **decay time constants in minutes, not half-lives**). Complete a **bounded** development search using at most two distinct ordered members of `{2,5,10,30,60}` minutes, and ridge `lambda in {0,1e-4,1e-3,1e-2,1e-1,1}` on a clearly defined **training-standardized** coefficient scale. Match A/B's search budget and valid rows; the more complex model may not receive extra unseen optimization trials. If full grid is computationally excessive, use the specification §12's **development-only inexpensive screening** to shortlist a fixed number of candidates and then **refit under correct PSD constraints** before final development comparison. Document exact tested and skipped candidates, numerical failures, and comparison fairness.

- **Fit** on 2024-01 through 2025-06 only.
- **Select and compare** using 2025-07 through 2025-12 only.
- **Selection metric:** average per-asset *training-standardized* one-minute response MSE, also report each asset separately and `MAE`/`R^2` as diagnostic. Do **not** call same-minute explanatory `R²` a forecast `R²`.
- **Tie rule:** improvements **less than 0.1% relative MSE** favor fewer exponentials/simpler kernel/stronger regularization.
- Keep `N0` as past-only baseline and `U` as unconstrained diagnostic on **identical target times**. Compare `A` vs `B` to isolate admissible cross coupling; compare `N0` with A/B to measure explanatory value of current + past flow; compare `U` vs `B` to expose the fit cost of reciprocity/admissibility.
- Select/report a frozen development configuration for later stages but **do not apply it to 2026 test rows yet**. The later 365-day monthly rolling historical refits with locked settings and OOS scoring belong to **Stage 5**.

Retain enough **compact model parameters and metadata**, not rowwise prediction copies, for Stage 3 to instantiate `G_A` and `G_B` from saved `C_a`, `tau_a`, liquidity units, training cutoff and normalization metadata. For Stage 5, provide a reusable function/API to refit a model using a requested historical cutoff/365-day window *without invoking it for test months now*. Make explicit that admissibility survives only the validated representation and unit conversion.

## 4. Required G2 scientific checks — small, meaningful, not performative

Complete these on **synthetic data and development train/validation only**:

1. **Known-kernel synthetic recovery:** Generate paired signed flows and returns from a known symmetric-PSD one- and two-exponential `2×2` model using the *actual return-response equation*. Verify recovered matrices/decays within a defensible sample-noise tolerance. Include `C12=0`, a valid *negative* `C12`, and nuisance-correlated flow. If strong confounding prevents exact recovery, diagnose correctly instead of falsely passing.
2. **PSD and cash units:** Numerically inspect eigenvalues of **every** estimated component `C_a`. Test valid positive/negative cross terms, reject matrices with materially negative eigenvalues; separately check a small finite-grid symmetrized transient impact quadratic form for nonnegative cost under random signed trades/round trips (with consistent same-cell convention). Stage 3 owns the production discretization and QP, but a Stage 2 kernel must already be admissible.
3. **Timing and transformations:** Hand-verified toy cases for `q`, `L`, `f`, `r`, `y`, time constants, lagged response signs, lookbacks, prior-bar availability, first bar of month/validation, zero volume and no double-differencing. Assert that all development code refuses to use a 2026 target/flow observation for fitting or selection.
4. **Comparability and nulls:** A fitted `B` with off-diagonal forced to zero must coincide with `A` for the same decay/penalty conditions; asset-label swapping must map matrices/predictions consistently. Check `U` allows directional asymmetry and is not accidentally exported as an admissible kernel. Evaluate identical-row and identical-control assertions.
5. **Fit quality, stability:** Training/validation standardized MSE, raw return-bps error and MAE, `N0/U/A/B` per asset and pooled; report residual cross-correlation, eigenvalues, `C12 / sqrt(C11*C22)` where defined, degree of PSD-binding, condition numbers and the actual self/cross level curves at lags `0,1,5,15,30,60`. Don't show raw `C12` without contextual self coefficients/units.
6. **Time stability:** Split the **training period** into two calendar subperiods and compare signs/magnitudes; show development-period monthly validation response loss and a meaningful past-only liquidity/weekend stability cut. Use predictable rather than hindsight regime thresholds where interpreting a regime as information known for decisions. Clearly label any monthly refit as development-only.
7. **Confounding/placebos:** (a) lag-only version excluding contemporaneous flows; (b) diagnostic **lead-flow placebo**, explicitly marked **uses future data for a falsification only, NEVER a predictor or final model**; (c) at least **50** prespecified whole-day, nonzero-offset shifts/permutations in the **training period**. Preserve each asset's **own** flow/return alignment; shift a flow series **only in the opposite asset's cross-flow predictors** to break cross-asset synchronization. Don't accidentally wreck both own-flow equations and claim the resulting decline isolates cross-impact. Refit the corresponding chosen model for each placebo where feasible and report the full null distribution, not just a selected example.
8. **Past-only coefficient uncertainty:** At least **50** seven-day training-block resampling/refit replicates for the chosen kernel, reporting off-diagonal spread, sign reversals and binding PSD constraints. Handle block boundaries correctly: lag/rolling features must be calculated on the **original contiguous time series before block selection**, without introducing fictitious adjacency across resampled blocks; cluster/resample corresponding return-feature rows consistently. Mark uncertainty as **observational estimator variability**, not causal-impact uncertainty or final-test inference.
9. **Restricted sensitivity:** `H=30/120` if a truncated tail problem is material; one anomalous-development-interval exclusion sensitivity if necessary. Always report original `H=60` and main full-sample results alongside any sensitivity. No test-driven change.

Compute budget: don't explode the placebo/bootstrap design into the entire hyperparameter grid. First select a small main model on train/validation, then run the required **50 + 50** refits at that selected *fixed* candidate, with efficient small sufficient-statistic calculations and recorded seeds. If numerical/compute issues prevent a mandatory check, save a precise `QUALIFIED` G2 status, its scientific implication and a reproducible resume command; don't fabricate completion. Keep memory **under ~8 GB** and incremental storage well under the **30 GB** AGENTS.md ceiling.

## 5. Optional small predictive diagnostic (not execution alpha)

If the core plus G2 checks finish successfully, the specification §6.5 asks for a **clearly separated** simple next-bar / 5-minute response diagnostic using **past completed** flows and returns only. You may run a **small fixed linear/ridge baseline** on development train/validation and compare against a zero-return predictor. Label target alignment, overlapping-horizon inference and score accurately. **Never incorporate current target-bar flow into a claimed predictive forecast.** This diagnostic does **not** authorize Stage 4/5 alpha-aware trading, stochastic Fredholm control, extensive signal mining or exploration of 2026 outcomes. If time is constrained, prioritize the G2 kernel work and label this additional diagnostic `NOT RUN` with an honest reason.

## 6. Expected code, configuration and outputs

Adapt to the existing Stage 1 layout; create only what is needed. Recommended minimal structure, relative to project root:

```text
configs/
  core.yaml                       # existing Stage 1 scientific/data contract; preserve
  stage02_kernel.yaml             # bounded Stage 2 candidate grid, seed, feature conventions
src/cryptocrossimpact/
  kernel/                         # feature/lag basis, estimators, PSD and prediction APIs
scripts/
  stage02.py                      # small stage-specific CLI (or existing CLI subcommands)
tests/
  test_stage02_*.py               # focused synthetic/real-train/timing/PSD tests
results/
  kernel_development/             # compact coefficients, metrics, diagnostics, plots
reports/
  research/stage02_kernel_estimation.md
  sessions/YYYYMMDD_HHMM_stage02_kernel_session.md
```

*Use the existing package name/layout if different; don't rename a working Stage 1 project.* Keep data under the **existing** `data/canonical/` and `data/registry/`; **no second feature dataset or per-split duplicates**. Tracked compact outputs: config, code, unit tests, JSON/CSV metrics/model parameter tables, the Markdown report, and selected small figures. Store large ephemeral intermediates in Git-ignored paths; do not export giant rowwise predictions or raw financial data to Git. Keep the Stage 1 `.gitignore` intact unless a necessary omission is discovered.

Mandatory deliverables:

1. **Reproducible commands** to inspect input/G1, run quick synthetic tests, build/evaluate the development basis, fit/select N0/U/A/B, rerun G2 diagnostics and reproduce the report. Prefer a single CLI with documented subcommands, deterministic seed `20261027` by default, and reuse of existing `.venv`.
2. **Model artifact** for each winning A and B development fit: exact `C_a` matrices with ordered asset names, decay `tau_a` in **minutes**, `L_i`, normalization means/scales, nuisance coefficients/intercepts, training and validation cutoffs, source/config/code identifiers, `H`, PSD/solver validation and prediction code. Also save N0/U summaries and U coefficients with an explicit **`diagnostic_only=true` / non-executable flag**.
3. **Development selection table** of all candidates actually attempted, their convergence statuses, sample sizes, objective values, train/validation MSE and selection rationale; failures remain visible. Preserve complete fit comparison (N0, U, A, B) by asset and pooled.
4. **Development diagnostics** including matrix/eigenvalue table, lag curves, time-stability plot/table, placebo and bootstrap summaries, observed flow-response caveat, and clear train/validation-only labels. Save small underlying plot tables when useful and inspect rendered figures for legibility.
5. **`reports/research/stage02_kernel_estimation.md`** with mathematical derivation/normalization, exact data/split/feature definitions, candidate/selection rules, useful tables/figures, limitations, G2 verdict and the complete route to reproduce. Include precise citations to AJNT and the research specification; don't invent paper results.
6. **Latest `reports/sessions/..._stage02_..._session.md`**, as prescribed by `AGENTS.md`, with files changed, commands and tests **actually executed**, observed metrics, qualified branches, Git status, approximate disk footprint and a precise restart point. Update a compact experiment index/manifest if already used in the repo.
7. **A short Stage 3 handoff** within the research report: where a downstream solver obtains a validated `G_A/G_B`, its units, half-cell/lag convention **to be verified in Stage 3**, and exactly what remains unresolved. Do **not** implement that solver now.

The command names above are suggestions; preserve any working repo conventions. If there is no pinned requirements file, add the smallest reproducible dependency declaration. A user with a fresh checkout plus Stage 1 data should be able to rerun a **small synthetic check** cheaply and the full development fit without manual intervention beyond environment/data availability.

## 7. G2 completion requirements and autonomous decision rules

Treat **G2 as an implementation/scientific-validity gate**, *not* a requirement to produce a positive off-diagonal result:

- **`PASS`:** all N0/U/A/B development estimators run on correctly scaled matched train/validation data; selected A/B satisfy PSD and numeric checks; real-data output is reproducible; model-selection chronology and G2 synthetic/timing/placebo/uncertainty checks passed; reports, artifacts and session log exist. If cross effect is weak or zero, state **`DOES_NOT_SUPPORT`** or `INCONCLUSIVE` separately while G2 may still be `PASS`.
- **`QUALIFIED`:** a usable scientifically bounded fit exists, but a mandatory diagnostic, source definition or solver issue is incomplete or materially uncertain. Identify exactly what's valid, which results are quarantined, and the smallest safe repair.
- **`BLOCKED`:** a critical dependency (correct data semantics, canonical read, numerical PSD fitting, etc.) is genuinely unavailable and no defensible permitted alternative works. Do not invent values or shrink the sample silently.
- **`INVALID`:** results relied on future information, incorrect scaling, an invalid return-kernel equation, unsatisfied constraints or nonconverged fitting but were treated as valid. Repair or quarantine before claim/hand-off.

**Scientific verdict (separate from gate):** `SUPPORTS_HYPOTHESIS`, `DOES_NOT_SUPPORT`, or `INCONCLUSIVE` based on **development-period** diagnostics only. Main six-month 2026 H1/H2 tests **have not occurred** and must not be claimed. Once the development choices are fixed, save a short **pre-test lock manifest** enumerating selected decay family/penalties, common sample masks, normalization procedure, future monthly rolling refit protocol, core metrics, and any scientific deviations. This is a preparation for Stage 5, **not permission to score the final test early**. A complete, well-diagnosed *negative* result is acceptable; don't tune until the answer turns positive.

Autonomously resolve routine API/solver or numerical issues, record changes, and continue other legitimate diagnostic branches. Stop only the affected activity if it would require paid data, deleting previous user work, >30 GB storage, a change to the frozen test/scope/estimand, or knowingly abandoning PSD validity. Do not initiate Git commits/pushes, destructive resets or background jobs without authorization.

## 8. Final Codex chat response format

Be **brief but substantive**. Report:

- G2 **implementation** status and distinct **development-only** scientific evidence (including whether cross-impact is stable/weak/unstable, not a claim about final test).
- Models fitted and selected `K/tau/lambda`, comparison of N0/U/A/B **validation** performance by asset and pooled, PSD minimum eigenvalues, and any uncertainty or placebo caveat.
- **Tests actually run**, numerical failures/qualified items, affected data flags and whether the 2026 test firewall was preserved.
- Key code/config/model/report paths, exact reproduction command(s), session report location, incremental disk/RAM observations, and Git status.
- What Stage 3 can safely use **without rerunning Stage 1**, and **the precise unresolved issue**, if any.

**Final required sentence in substance:** “Stage 2 only was executed. No January–June 2026 research outcomes, liquidation policies, execution-cost backtests, or Stage 3 solver were evaluated.” If that is not true, explain the deviation transparently instead of claiming compliance.

---

**Research principle:** *Correct conditional return-response specification, cash-consistent PSD kernels, matched development comparison and honest confounding diagnostics matter much more than matching an attractive coefficient or building an elaborate codebase.*
