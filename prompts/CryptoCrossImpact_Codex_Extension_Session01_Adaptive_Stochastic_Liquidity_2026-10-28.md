# Codex Research Extension — Session 1: Adaptive Execution and Scenario-Based Stochastic Liquidity

**Project:** `CryptoCrossImpact`  
**Prompt version/date:** X1.0 / 2026-10-28  
**Status:** Authorized implementation prompt for the **first extension session**; not a research result.  
**Scope:** Improve 1-minute liquidity forecasting, introduce modest forecast-distribution scenarios, and implement **state-correct receding-horizon execution** on BTC/ETH perpetual futures. **Development-only evaluation.**  
**Explicitly excluded:** Robust/minimax optimization (reserved for **Session 2**); randomly evolving Volterra impact kernels and full stochastic path-dependent optimal control (saved as **future Option 2**); new alpha, nonlinear impact, new markets, live trading, and final held-out confirmation.

> **Paste this entire prompt into Codex from the repository root.** Read `AGENTS.md` before changing anything. Carry out the authorized work without routine approval requests, but obey the research gates and stop conditions below. Do not interpret a passing test as a demonstrated trading improvement.

## 0. Authority, inputs, and preservation

Before implementing:

1. Inspect `git status --short`, current branch, the existing folder structure, source code, configs, available data, and relevant test/report paths. Preserve all existing dirty changes. Do **not** commit or push unless separately instructed.
2. Read the root `CryptoCrossImpact_Research_Specification_v1_2026-10-27.md`, `SPEC_CHANGELOG.md`, and existing Stage 3/4/5 reports, especially:
   - Stage 3 exact-cell, cash-consistent kernel Hessian and constrained QP.
   - Stage 4 causal episode engine, 28-day forecasts, immutable as-of model loading, and policies T0/T1/T2/T3/T3B/T4.
   - Stage 5 **v2 funding-excluded** evaluation protocol, ready-lock lineage, finalized 2026-H1 results and limitations. **Do not modify or reinterpret those historical results.**
   - The already saved Stage 2 fitted A/B models and as-of monthly-refit interfaces. The PDF `references/2403.10273v2.pdf` is the source for AJNT mathematics.
3. If `CryptoCrossImpact_Research_Extensions_Literature_Survey_v1_2026-10-28.md` is present in the repository, read its Sections 3 and 7. It is **background**, not a substitute for this executable prompt. **Do not block** on its absence; all X1 implementation choices needed for this task are specified here.
4. Run the smallest relevant existing tests and inspect available development inputs before editing. Use the existing `.venv` and dependency declaration. Add only a truly necessary small package, if any.
5. Create a **new extension-specific config, protocol and results namespace**; do not overwrite Stage 1–5 data, frozen models, scores, hashes, or pretest documents. Keep all scientific deviations versioned and dated. Prior original H1/H2 findings remain the original historical study.

**Historical motivation (not an X1 finding):** Stage 5 showed a 7.55% reduction in *contemporaneous explanatory* MSE for the full PSD model, but a +0.02081 bp E1 modeled shortfall advantage with CI crossing zero. Original 60-minute hour-of-week forecasts were constant within the hour (T0=T1), while some realized participation exceeded 100% of minute turnover. We are testing whether better *past-only liquidity information and feedback* change decisions and **scenario-conditional**, funding-excluded costs. Do not call the Stage 2 public-flow coefficients causal own-trade impact.

## 1. Scientific question and success criteria

**Question X1:** Does **intrahour liquidity forecasting plus a state-correct adaptive liquidation policy** improve *development-period* liquidity predictability, realized-participation diagnostics, and matched model-based execution outcomes relative to the original open-loop policy, without clairvoyance or relaxed constraints?

Separate the contributions:

- **Forecast improvement:** V0 versus intrahour V1 versus past-activity V2, and interval/scenario calibration.
- **Adaptation improvement:** static versus receding-horizon with the **same** impact kernel and forecast input.
- **Cross-impact interaction:** full matrix B versus diagonal/no-cross controls under **matched** forecasts, risk, parent inventory, evaluator and observation latency.
- **Practical feasibility:** how often realized per-minute participation exceeds 10%, 20%, or 100%, and whether any policy violates its **ex-ante** caps or terminal inventory. Do not equate forecast-cap feasibility with real fills.

Negative, mixed and inconclusive findings are allowed; do not change sample boundaries or forecasting rules after viewing favorable/adverse execution scores just to improve rankings.

**Evidence status:** All X1 development analyses are **exploratory/post-original-model-selection**. Our earlier 2026-01–2026-06 results have already been inspected. **No newly independent OOS confirmation is produced by this session.** A later extension session may precommit to a fresh 2026-07–2026-09 holdout if its outcomes have genuinely not been inspected. **Do not open those new months in this session.**

## 2. Data and time protocol (strict)

- Reuse existing **validated** Binance Vision USD-M `BTCUSDT` and `ETHUSDT` 1-minute futures klines and 2024–2025 canonical partitions. No new purchase, API credentials or bulk download. All timestamps UTC; bar `b` opens at `b` and becomes available **at `b + 1 minute`**, never earlier.
- **Training/calibration:** 2024-01-01 through 2025-06-30 UTC, for small volume-model choices and scenario-residual calibration. **Development evaluation:** 2025-07-01 through 2025-12-31, four episodes/day at 00:00, 06:00, 12:00, 18:00 UTC; 60 minutes per episode. Reuse the Stage 4 eligible 736-episode definition, unless independently logged *predeclared structural* QC rules require exclusions. Keep a common paired episode universe.
- At an episode start `t0`, the last known market bar opens at `t0-1 min`. For a replan issued at `t0+5 min`, the latest available bar opens at `t0+4 min`; **the bar beginning at `t0+5` is future information**. Similar checks apply at all updates.
- **Original parent inventories are fixed at `t0`**, e.g. `X0_i = 0.02 * sum_{k=0}^{59} V0_i,k(t0)` USDT, with the original baseline V0 and original constraints. In particular, a superior updated forecast cannot change the parent-order size retrospectively. Keep both legs sell-only, hard terminal 60-minute target, no round trips or intra-experiment position additions.
- Preserve Stage 4 initial 10%-of-forecast per-bin cap and reference risk scaling for the **primary matched study**. Hold the *initial cap vector* `cap_i,k^0 = 0.10 V0_i,k(t0)` fixed across all policies and replans. This prevents the cap definition itself from changing between competitors or becoming infeasible solely because a forecast was revised. Updated liquidity affects the **objective and diagnostic forecasts** rather than quietly redefining hard limits. A clearly separate optional experiment with conservative updated caps is allowed only if fully feasible and predeclared; never label it the same matched experiment.
- Freeze the Stage 4 starting covariance `Sigma_per_minute`, common normalized risk coefficient `beta`, arrival/reference prices, kernel fit provenance, fee/spread assumptions, and `theta=1` at `t0` in the main factorial comparisons. **The primary X1 variation is forecast and decision updating, not changing all model inputs simultaneously.** Preserve `kappa=0.001`, fee=5 bp/side, half-spread=1 bp, zero alpha and *funding-excluded* cash accounting. A return signal is neither trained nor injected.
- **Outcome firewall:** For policy construction, read only the permitted `as_of` history. In particular, no future realized price, volume or flow can affect an order. Completed bars revealed during the 60-minute window can affect **later** replan decisions. Future market prices/volumes are allowed **only for scoring or ex-post feasibility diagnostics**, after each order was committed. Do not leak a future-bar-existence/validity check into policy selection.

## 3. Small, frozen liquidity-model family

Predict **one-minute quote-notional turnover in USDT**, not base-coin volume, realized spread or L2 queue depth. Keep positive finite forecasts. Use a **small** family, not LSTM/deep-learning hyperparameter search.

### V0 — original baseline (must exactly reproduce prior code)

The existing past-28-calendar-day hour-of-week (with documented fallbacks/floor) median volume estimate. At 00/06/12/18, it is constant over the 60-minute hour. **Do not edit V0's previously established algorithm**. Add compatibility tests establishing equality to the existing Stage 4 forecasts for sample development episodes.

### V1 — minute-of-hour seasonal profile

For each asset, form a past-only minute-of-hour profile from trailing **28 complete days**. To make it identifiable with reasonable sample size, pool all 24 hours of those days and estimate a ratio of each minute's observed volume to that historical hour's within-hour positive reference turnover. A natural simple recipe is:

1. For every completed historical hour, calculate a nonzero robust **within-hour reference** from its 60 validated one-minute turnovers; use that hour solely after it is completed, and exclude invalid/missing hours by a declared fixed mask.
2. For minute `m=0,…,59`, estimate the median of verified nonnegative normalized ratios (including genuine zero-volume minutes) over the preceding 28 days, **shrink toward 1** with fixed weight `n/(n+50)` (where `n` is the eligible historical count) and renormalize the **60 profile factors to mean 1**. No information from the hour currently being forecast is used until those minutes have actually closed.
3. Multiply the original V0 hour-of-week level by these 60 intrahour factors. Apply the same documented positive forecast floor as V0 and log each use.

For forecasts extending into a future hour, use the appropriate past-known hourly V0 baseline plus the same learned intrahour factors. Predeclare a small harmless sensitivity of profile lookback 56 days **only if** development forecast metrics warrant it; do not expand the feature family after inspecting execution-cost outcomes. Record the exact implemented treatment for insufficient full historical hours.

### V2 — small activity-conditioned forecast (gated addition)

Use V1 plus an ex-ante update derived from trailing **completed** turnover, such as:

\[
 d_{i,t}=\operatorname{clip}\left[\log\frac{\mathrm{EWMA}_{5,\,i}(t)+\epsilon}{\mathrm{EWMA}_{60,\,i}(t)+\epsilon},-\log 2,\log2\right],\quad
 \widehat V^{V2}_{i,t+k\mid t}=\widehat V^{V1}_{i,t+k\mid t}\exp\{d_{i,t}\exp[-(k-1)/\tau_a]\}.
\]

Both EWMAs use only completed bars, and `epsilon` must be set from a strictly past-known positive-volume floor. Use `tau_a=15 minutes` as the initial setting; a **development-only** fixed grid `{5,15,30}` may be compared by forecast loss **before** looking at policy shortfall. The activity multiplier should return gradually toward 1, not assume all 60 future minutes retain today's shock. If observed volume is zero, use a documented well-defined floor, not invented trades.

The simple EWMA specification is preferred to training a sophisticated volume network. If a codebase already has a small ridge activity model, one equivalent low-dimensional comparator may be used **only if** it obeys the same information cutoff; do not add a new ML project or dozens of features.

### S1 — coarse liquidity distributions/scenarios (mandatory light-weight component)

A stochastic-liquidity **approximation**, not a stochastic kernel theorem:

- From **training-period** forecast errors of V2 (or V1 if V2 fails its forecast gate), after the necessary 28-day warmup, collect realized-to-predicted *log-volume ratios* at predeclared historical forecast origins, after labels mature. Calibrate empirical **10th/50th/90th percentile residual factors**, at most in horizon buckets **1–5**, **6–15**, **16–60** future minutes, by asset. Use exact documented times and positive floors. Pool buckets if sample size is inadequate, recording it in advance. Do not use July–December 2025 labels to calibrate its own quantiles.
- At each decision time, form `V_low`, `V_mid`, `V_high` by applying frozen training-calibrated multiplicative residual factors to the current past-only point forecast. Require `0 < low <= mid <= high` and finite values. Bands are marginal approximations and do **not** model serial dependence or guarantee joint path coverage.
- Report development **quantile coverage** (10/50/90), quantile/pinball loss and empirical misspecification by horizon bucket; do not advertise calibrated probabilistic forecasts without checking.
- Scenario-aware deterministic **temporary-cost** policy may use an explicitly declared three-point scenario-weighted inverse-volume curvature `kappa * sum z² * [0.25/V_low + 0.50/V_mid + 0.25/V_high]`, while keeping the primary fixed cap vector `cap^0`. This is a **transparent stress/expectation proxy**, not the exact expectation under a full stochastic process and not random `G`.
- Preserve a **point-forecast** temporary-cost policy `kappa * sum z² / V_mid` as the matched control so we can isolate any advantage of liquidity uncertainty modeling. Keep transient kernel A/B deterministic and admissible.

**Gate before economic comparison:** Verify V1/V2 volume forecasts are nontrivially different from V0, compare timestamp-aligned **MAE/median APE or RMSLE** on July–December development, and report zero-volume/coverage behavior. If V2 adds no credible volume-model value, retain it as a *negative result* and use V1 for the primary MPC rather than opportunistically tweaking it. Scenario bands must pass training-only construction and development calibration checks; if not, label the scenario policy QUALIFIED/NOT_RUN and continue the valid V1/MPC branch.

## 4. State-correct receding-horizon optimizer (the critical mathematics)

**Primary cadence:** Re-optimize at `t0`, then every **5 completed minutes** (`t0+5, +10, ... +55`), submitting a **frozen 5-minute trade prefix** from the current optimizer between updates. This is a practical CPU-friendly MPC policy. First trade of each prefix occurs only after its inputs are available. An optional 1- or 10-minute cadence is a secondary sensitivity **only after correct primary implementation**.

### 4.1 Preserve both inventory and transient impact history

Let `z_p` denote child sale notionals already executed in earlier bins and `z_f` the not-yet-executed sales. Given Stage 3's full-horizon symmetrized, exact-cell impact-cash Hessian `H_G` (in USDT units), partition it into past/future blocks. The **future-dependent** part of total path impact cost is

\[
 C_{G,\mathrm{future}}(z_f\mid z_p)
 =\tfrac12 z_f^\top H_{ff}z_f+z_f^\top H_{fp}z_p,
\]

up to a past-only constant. **Do not drop** the cross-term `H_fp*z_p`. It carries the residual self- and cross-impact generated by prior simulated trades. Equivalently, maintain the exact exponential historical state, but prove its equivalence to the block-Hessian method on small fixtures. Preserve the same `tau`, per-asset `L`, cash normalization `10^-4`, and exact-cell convention across past and future.

The optimization for the remaining bins uses:

- Actual **remaining simulated reference-USDT inventory** `X_remaining = X0 - sum(z_p)` (not reset to X0).
- Terminal equality `sum(z_f)=X_remaining` asset by asset, `z_f>=0` and **original fixed per-bin** cap `z_f<=cap^0_future`.
- Temporary cost using **current as-of revised** future point or scenario volumes (positive), with units `kappa*z²/V`; do not charge twice for already executed sales.
- The same Stage 4 full-covariance risk `Sigma_per_minute` and **unchanged** episode-start `beta`; compute future pretrade inventories from `X_remaining` and remaining sale variables, not from original unliquidated X0. Past risk is a constant irrelevant to remaining decisions. Linear fees/spread on remaining sales stay schedule-invariant when all liquidate.
- No drift/alpha and no future cash-path information.

**Mathematical tests:** Explicitly evaluate the full-horizon cost `0.5*[z_p,z_f]^T H_G*[z_p,z_f]` and compare its future-dependent difference with the conditional formula above. Check the gradient and each block's transpose/factor-of-two, signed cross-impact, cache/array ordering, and correct handling at `k=0`, `k=5`, `k=55`, final one-bin case and zero inventories. Verify eigenvalue/PSD conditions and solver KKT/inventory/cap feasibility exactly as Stage 3. A replan with unchanged forecasts and an otherwise unchanged full deterministic quadratic problem should reproduce the **tail of the initial optimum** (within numerical tolerance); failure indicates an incorrect state or risk continuation. This is an important nonnegotiable regression test.

### 4.2 Online replay / policy construction

At each `t`:

1. Load only canonical observations with `available_at <= t` and allowed historical context. A strict slicing/as-of reader should enforce this; don't load future outcome columns into a shared policy object.
2. Update V1/V2's *forecast* for remaining bins from completed bars, retaining fixed training-calibrated seasonal/scenario factors.
3. Rebuild only the future QP with remaining inventory and carried-forward impact state; solve, validate constraints/units, commit the next five sale amounts, and append their immutable decision records.
4. Continue until minute 60, then verify total liquidation and replay aggregate objective/cost from **the entire realized schedule once**. Never sum local QP objective values across replans; these have different conditioning/constant terms and would double-count risk/impact.

You may use existing OSQP/CVXPY and the Stage 3 solver; keep additions small. A simple stored full-horizon Hessian per episode/model is fine for `2 assets × 60 bins`. Do not implement a general stochastic dynamic program or Fredholm-conditional-expectation solver. **The optimization is deterministic conditional on the observed history and a frozen forecast at each replan.**

## 5. Small matched policy matrix

Use the **same** 2025 development episode starts, parent inventory, initial fixed caps, model as-of dates, fee/spread, covariance, risk normalization, solver tolerances and scorer across compared policies. Reuse Stage 4 A/B kernel objects; no outcome-driven re-estimation.

| ID | Kernel | Volume assumption | Re-optimization | Interpretation |
|---|---|---|---|---|
| `X1-P0` | Full B | Original V0 | Never | **Exact reproduction of Stage 4 T4** (essential smoke comparator) |
| `X1-P1` | Full B | V1 point forecast | Never | Isolates intrahour forecast change, no feedback |
| `X1-P2` | Full B | V1 point forecast | Every 5 minutes | Isolates feedback versus P1 |
| `X1-P3` | Full B | V2 point forecast | Every 5 minutes | Adds current activity signal; **gated** by volume forecast evidence |
| `X1-P4` | Full B | S1 low/mid/high liquidity scenarios | Every 5 minutes | Adds uncertainty-aware *liquidity* cost, **not** robust impact control |
| `X1-D0` | Diagonal A (or T3B if exact self-matching is desired, predeclare choice) | V1 point forecast | Never | Matched no-cross open-loop control |
| `X1-D1` | Same diagonal as D0 | V1 point forecast | Every 5 minutes | Matched no-cross adaptive control |

Also calculate **forecast-TWAP/VWAP** from the same V1 at episode start for diagnostic comparison, ensuring they differ when the intrahour profile varies. Do not run all possible combinations of A/B/V0/V1/V2/S1/update cadences. If runtime is high, first test a predeclared tiny set of development days, then the full 736 episodes for the feasible subset. **Never select specific episodes using their observed returns or favorable costs**. Any failures, skipped variants and their reasons remain visible; do not invent costs or mark fail as zero.

**Cross-term isolation:** Preserve the Stage 4 distinction between `T3` (separately fitted diagonal A) and `T3B` (diagonal of B with B self terms/L). If useful and feasible, use **T3B** as `D0/D1` to isolate the off-diagonal effect; if so, do not call it A. Compare adaptive B to adaptive same-self T3B using identical forecasts and initial risk. Do not mix different `L` scalings or use an unverified matrix by copying raw elements between fits.

## 6. Development evaluation and diagnostics — no new held-out claims

Use the original Stage 5 **funding-excluded** cash cost definition, as an **exploratory 2025 development replay**:

- Recorded price-path arrival shortfall from next-bar closes, using the original scoring convention; alternate open/OHLC price proxies optional, clearly sensitivity-only.
- Full executed-schedule exact-cell transient cost under a **single common evaluator kernel** per episode/world, not the varying optimizer QP values. Prefer a **separate past-fitted E1-style** evaluator (180-day history ending 30 days before each development month), with a diagonal/no-cross E2 counterpart, computed using only earlier data. If the frozen Stage 5 v2 E1 factory cannot be applied causally to 2025 development, implement a minimal validated development-only version rather than substitute the optimizer's own B. The optimizer's own kernel is labeled **E0/in-model smoke only**.
- Temporary liquidity under the same **common** evaluation assumptions for all policies, with the baseline frozen forecast and a clearly marked alternate **ex-post realized-volume scorer** if useful. Realized volume affects **scoring/diagnostics only**, never the cap or an earlier decision.
- Fees/spread as fixed illustrative assumptions, **funding omitted**; no claiming all-in perpetual returns or verified executions. Ex-ante risk preference is shown separately from cash shortfall.
- Primary exploratory contrasts: `P2-P1` adaptation holding V1 fixed; `P1-P0` intrahour volume assumption; gated `P3-P2` and `P4-P3` if both use V2; **if V2 fails**, omit P3 and compare V1-based P4 directly with P2; and `D1-D0` vs `P2-P1`. Define the sign of every bps contrast explicitly (e.g. cost(control) minus cost(new), positive favors new). Do not compare heterogeneous own-model objective values as realized performance.
- **Liquidity and feasibility:** For all policies, report actual observed turnover participation `z_i,k/V_realized_i,k`, with zero-volume bins marked undefined (or infeasible, explicitly), proportion of positive-volume bins **>10%, >20%, >100%**, max and upper percentiles, concentration of misses across episodes, violations of **frozen forecast caps**, any terminal residual, and fraction of episodes requiring repairs (none should silently occur). An actual 100%+ volume fraction is strong evidence of simulator infeasibility; do not report it as an executable order.
- Statistical summaries: paired by calendar day (four episodes/day), 7-day moving-block bootstrap **500 draws**, fixed seed `20261027` if existing code supports it. Report mean/median bps differences, 95% descriptive intervals, month-by-month signs, adverse episodes, sensitivity to lower/liquidity regimes and negative results. These intervals are **development/post-search diagnostics**, not a new confirmatory significance test. Forecast losses need their own time-aware daily/block diagnostics.

**Do not access July–September 2026**, add SOL, download L2, repeat the original Stage 5 2026-H1 test as purported new evidence, or revise the existing Stage 5 result. Leave fresh OOS evaluation and robust impact optimization for later authorized sessions.

## 7. Lightweight verification requirements (high priority)

Implement the following **focused** tests; reuse existing helpers rather than building redundant infrastructure.

1. **Causality/as-of tests:** mutate every current/future bar while preserving all completed bars; an issued policy prefix at its decision time must remain byte-identical. After an update time, changing an *already completed* volume bar may change later prefixes but must never rewrite earlier decisions. Include boundary cases across UTC hour/day/month transitions.
2. **Baseline reproduction:** V0 and static X1-P0 match prior Stage 4 T4 forecasts, inventories, constraints and schedules on representative development episodes to numerical tolerance. No modification to prior Stage 4/5 files is needed.
3. **Profile/scenario math:** only past data calibrate minute-of-hour factors and scenario quantiles; profile positive, mean normalized, bands monotone; zero volume/partial history handled without inventing trading. V1 should not be constant across the hour unless the data truly imply a flat profile.
4. **Persistent impact state:** cross-term Hessian hand examples, exact-cell cost identity, gradient finite differences, dynamic-programming time consistency of an unchanged future-input QP, no-reset negative control, positive/negative *admissible* cross terms, zero-kernel and zero-inventory cases.
5. **Risk and feasibility:** same beta/Sigma/caps/initial inventory for matched arms; remaining-inventory terminal equality, no buys, no negative child trades, KKT and objective decomposition, no silent clipping/repair, no double-counted impact or risk.
6. **Evaluation independence:** same E1/E2 evaluator for all arms on each episode; perturb optimizer kernels without changing fixed evaluator parameters; altering future prices changes scores but cannot change earlier decisions; altered future volume changes ex-post diagnostics but not earlier schedules.
7. **Reproducibility/preservation:** rerun a small deterministic pilot twice and compare schedules/metrics; prior Stage 1–5 reports/models are unchanged; no 2026 canonical data are opened by X1. Run impacted old tests, and state any tests *not run*.

Use a small predeclared pilot with at least one weekday/weekend and at least one UTC month boundary, then run the matched 2025 development sample if the pilot passes. No manual schedule editing or outcome-driven episode exclusions.

## 8. Deliverables / expected file layout

Adapt existing structure; **do not build a new repo or heavyweight pipeline**. Suggested names are not mandatory if an existing naming convention is better:

```text
configs/extension_x1_adaptive_liquidity.yaml

docs/extensions/x1_adaptive_liquidity_protocol_v1.md   # chosen defaults, pre-outcome decisions, data/time/claims
src/cryptocrossimpact/liquidity/               # V1, V2, frozen quantile residual calibration
src/cryptocrossimpact/execution/              # minimal state-correct MPC changes, not a rewritten solver
scripts/extension_x1.py                       # pilot / forecasts / replay / report CLI

tests/test_extension_x1.py
reports/research/extension_x1_adaptive_liquidity.md
reports/research/extension_x1_artifacts/        # small CSV/JSON tables; no raw-data duplication
figures/extension_x1/                         # only meaningful compact figures
reports/sessions/YYYYMMDD_HHMM_X1_adaptive_liquidity_session.md
results/extension_x1/                         # ignored local schedules/cache, if needed
```

**Minimum scientific output:**

- **Forecast table:** V0/V1/V2 MAE, RMSLE or comparable volume error, pinball and 10/50/90 empirical interval coverage, grouped by minute-of-hour/horizon; include zero-volume cases and units.
- **Policy table:** static and MPC objective feasibility, all matched outcomes under E1 and E2, paired bp effects/intervals, rolling decision runtime, negative/outlier episodes and exact policy statuses.
- **Participation table:** ex-ante cap violations (must be zero or explicitly failed), realized >10/20/100% percentages and maximum ratios per policy.
- **Diagnostic figures:** 60-minute V0/V1/V2 forecast curves versus subsequently observed volume on **predeclared** development episodes; one BTC/ETH inventory/schedule update trace with prior-impact state; paired E1/E2 contrasts and participation-risk distribution. Distinguish **as-of plots** from posthoc evaluation overlays.
- **Research report:** concise methodology, source citations, mathematical derivation of carried impact and the scenario-weighted temporary term, development results, failures, interpretability, assumptions, no-lookahead evidence, limits and next-session handoff. Maintain existing work's citation/figure conventions.
- **Session report per `AGENTS.md`:** what changed, tests actually run, data periods actually read, result paths, versions/hashes, resource/disk effects, and exact next safe action. Add a `run_manifest.json` binding config/source/code/models/clock/frozen training-only quantile calibration. No full verbose log dumps.

### Completion gates

- **X1-G0 — implementation validity:** causal cuts, baseline reproduction, persistent impact, feasibility and common-evaluator tests all pass.
- **X1-G1 — forecast assessment:** genuine minute variation and training-only scenarios; quantify whether forecasts outperform V0, without forcing a positive effect.
- **X1-G2 — exploratory development policy evidence:** completed matched analysis, fee/funding labels, liquidity failure diagnostics, negative findings retained.

Classify separately (i) implementation `PASS / QUALIFIED / BLOCKED / INVALID` and (ii) scientific `SUPPORTS_HYPOTHESIS / DOES_NOT_SUPPORT / INCONCLUSIVE`. Even an economically negative study can be a completed X1 research extension if technically valid.

## 9. Strict exclusions and future work (preserve these decisions)

**Do not start Session 2 robust optimization in this task.** In a later session we intend to test uncertainty sets over **PSD self-/cross-impact kernels** and potentially adverse liquidity worlds (without optimistic same-model scoring), using the X1 machinery if valid. Do not pre-emptively implement it now.

**Save future Option 2:** *Full stochastic Volterra optimal control with genuinely evolving random liquidity/impact kernels `G(t,s;ω)` or stochastic temporary costs, and an adapted policy optimized over future market-state paths.* This would require new stochastic-control mathematics and could fall outside the hypotheses of the original AJNT deterministic-kernel theorem. **Do not implement, claim, or silently approximate this as a theorem in X1.** We will revisit it only after the bounded empirical extension is complete.

Likewise, do **not** add speculative alpha, full time-inhomogeneous kernel re-calibration, nonlinear causal-impact claims, deep volume forecasting, OKX/Hyperliquid datasets, a new paper theorem, or fresh 2026-Q3 outcome access. If useful, list them as future research options in the session report only.

## 10. Suggested starting command / user-visible handoff

Implement an idempotent CLI, preferably of the form:

```sh
.venv/bin/python scripts/extension_x1.py pilot
.venv/bin/python scripts/extension_x1.py forecasts
.venv/bin/python scripts/extension_x1.py development
.venv/bin/python scripts/extension_x1.py report
.venv/bin/python -m pytest tests/test_extension_x1.py -q
```

The exact names can follow established repository patterns; write them in `README.md` or the new research report. **Run the full scope of this session now**, subject to actual data/resource gates. If a branch is genuinely blocked, preserve its valid counterparts and produce a clear, specific blocker instead of manufacturing output or entering approval loops.

At the end of your Codex reply, state concisely: **(1)** completed X1 gates, **(2)** whether volume predictions and scenario coverage improved, **(3)** whether adaptive execution actually improved development modeled costs and realized participation—and uncertainty/limitations, **(4)** tests and any failures, **(5)** file/session-report paths and exact next-step recommendation. **Stop before Session 2 and any new final-test access.**

---

## Sources and positioning (reference guide, not extra required input files)

- **Abi Jaber, Neuman & Tuschmann (2026)**, *Optimal Portfolio Choice With Cross-Impact Propagators*, *Mathematical Finance*, https://doi.org/10.1111/mafi.70025 — existing base Volterra mathematical benchmark; deterministic kernel in the theorem's stated setting.
- **Bechler & Ludkovski (2015)**, *Optimal Execution with Dynamic Order Flow Imbalance*, *SIAM Journal on Financial Mathematics*, https://doi.org/10.1137/140992254 — dynamic information and adaptive execution background.
- **Cartea & Jaimungal (2016)**, *Incorporating Order-Flow into Optimal Execution*, *Mathematics and Financial Economics*, https://doi.org/10.1007/s11579-016-0162-z — conditional-flow execution motivation, not an exact model identity.
- **Cartea & Jaimungal (2016)**, *A Closed-Form Execution Strategy to Target Volume Weighted Average Price*, *SIAM Journal on Financial Mathematics*, https://doi.org/10.1137/16M1058406 — forecast-aware VWAP motivation.
- **Frei & Westray (2015)**, *Optimal Execution of a VWAP Order: A Stochastic Control Approach*, *Mathematical Finance*, https://doi.org/10.1111/mafi.12048 — uncertain relative-volume framework; X1 is an approximation, not their full solution.
- **Muhle-Karbe, Wang & Webster (2024)**, *Stochastic Liquidity as a Proxy for Nonlinear Price Impact*, *Operations Research*, https://doi.org/10.1287/opre.2022.0627 — stochastic liquidity motivation, not a justification for random `G` under AJNT without new analysis.
- **Naviglio et al. (2026)**, *Why Is the Estimation of Metaorder Impact With Public Market Data So Challenging?*, *Quantitative Finance*, https://doi.org/10.1080/14697688.2026.2628221 — warning about public-flow confounding and causal execution claims.

**End of Codex Session 1 prompt (X1.0).**
