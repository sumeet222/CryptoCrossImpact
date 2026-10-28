# Codex Stage 5 Recovery — Approved Funding-Excluded Evaluation Amendment and Full OOS Completion

**Project:** `CryptoCrossImpact`  
**Task:** Resume the interrupted Stage 5; amend the pretest protocol, complete its remaining preflight, then execute the entire locked January–June 2026 out-of-sample study  
**Prompt version:** Recovery v1, prepared October 27, 2026 (US/Eastern); predecessor preflight report dated October 28, 2026 UTC  
**Execution:** Local Codex CLI in the existing repository and `.venv`  
**Scope:** **Stage 5 only. Do not begin Stage 6, new scientific extensions, or live trading.**

> **START HERE — USER APPROVAL AND REQUIRED ACTION.** The user expressly approves a *narrow, pre-outcome scientific protocol amendment*: remove perpetual-futures funding from the **primary modeled execution-shortfall estimand**. Report results as **execution shortfall excluding funding**, not as all-in cash cost, actual exchange fills, or realized/live savings. Funding cash flows are **unobserved/omitted**, never assumed zero; do **not** exclude episodes using guessed funding timestamps or choose cases by funding rates. Preserve the original frozen Stage 4 lock and the funding-HOLD evidence unchanged; write a **new versioned amended pretest protocol** referencing those files. Finish independent evaluator E1 development validation **before any 2026 canonical market outcomes can be opened**; once that gate passes, generate a hash-linked new `PRETEST_READY` record and **proceed autonomously through all of Stage 5**, including H1/H2, E1–E3, confidence intervals, bounded sensitivities, and reports. Do not require another user approval for this already-authorized amendment. If any *other* scientific pretest gate fails, hold the affected work honestly and do not bypass it.

---

## 0. Read, inspect, preserve, and resolve precedence

1. Start with `git status --short`, current branch/commit, worktree inventory, existing files and available disk. **Never overwrite or erase existing research artifacts, uncommitted work, old locks, manifests, or HOLD evidence.** No unrequested commits, pushes, destructive Git commands or another repository's data.
2. Read the actual repo files (their exact paths may differ; discover them):
   - `AGENTS.md`, `CryptoCrossImpact_Research_Specification_v1_2026-10-27.md`, `SPEC_CHANGELOG.md`, `configs/core.yaml`, relevant Stage 2–4 configs and scientific/session reports.
   - `docs/stage05_pretest_policy_evaluator_lock_v1.md`, `configs/stage05_pretest_lock.yaml`, and their bound/hash manifests. The Stage 4 handoff recorded lock SHA-256 **`a691a3db76a776d4f8e31b43f6c68663145891e1974e2bf6dc0f061130192e31`** and 47 bound files. Verify these against actual repository data; do not blindly assert verification.
   - The **original** `prompts/CryptoCrossImpact_Codex_Stage05_OOS_Evaluation_and_Robustness_Prompt_2026-10-27.md` (or its actual existing name), including its definitions of E1/E2/E3, H1/H2, scoring, tests and reports.
   - The interrupted Stage 5 pretest HOLD report, session report and evidence under `reports/research/stage05_artifacts/` (or actual folder). Read the current `scripts/stage05.py`, `src/cryptocrossimpact/evaluation/preflight.py`, tests, and established Stage 2/3/4 APIs.
3. Confirm the actual predecessor status: a **development-only** BTC funding archive and checksum were inspected, the Binance REST endpoint returned **HTTP 451** (restricted location), `calc_time` could **not** be verified as the REST settlement `fundingTime`, neither F1 nor F2 was admitted, E1 was **NOT_RUN**, no `PRETEST_READY` was created and **no 2026 canonical outcomes were opened**. This is a *reported state to verify*, not permission to assume a later run cannot have changed anything. Stop if evidence indicates outcomes have already been opened or a conflicting, more recent lock exists; reconcile and disclose before proceeding.
4. **Authority for this one change:** the user's current explicit approval of funding-excluded evaluation and this recovery instruction govern **only the funding amendment**. All unrelated scientific definitions in the approved specification, the original Stage 4 lock and the original Stage 5 prompt remain binding. The new versioned amended lock records exactly which predecessor clauses it supersedes. Do **not** rewrite v1 or silently modify the core research specification.
5. Keep the existing Python environment, selected Stage 2 models `(tau=60 min, ridge=1)`, Stage 3 exact exponential-cell cash solver, Stage 4 causal episode and policy implementations. Avoid package/tooling changes unless genuinely necessary. No fresh papers, new paid data, funding API access or market-data downloads are required for this approved recovery; reuse the complete 2024–2026 canonical bars already obtained.

### Reconcile the frozen protocol before doing work

Original Stage 4 status `PRETEST_LOCK_PENDING` stays historically true. The previous Stage 5 `PRETEST_FUNDING_HOLD` remains an archived factual outcome; **do not relabel it as a successful funding audit**. Create a new *amended* protocol, e.g.:

- `docs/stage05_pretest_amendment_v2_funding_excluded.md` — rationale, user approval, precise protocol delta, original lock paths/hashes, pre-outcome status, retained caveats.
- `docs/stage05_pretest_policy_evaluator_lock_v2.md` — complete, readable frozen scientific protocol with the v1 unchanged clauses incorporated by reference where unambiguous.
- `configs/stage05_pretest_lock_v2.yaml` — machine-readable experimental settings and evaluator identity, bound inputs, intended estimand, source hash links.
- A separate **new** `reports/research/stage05_artifacts/pretest_ready_v2.json` (or `docs/` if existing practice requires) **only after all remaining gates pass**. Readiness is a verified, machine-checkable state, **not an editable Boolean supplied by the operator**.

These are suggested names; follow existing repo conventions, but **never overwrite** the original lock or earlier HOLD/QA reports. Add a short dated entry to `SPEC_CHANGELOG.md` identifying this as an **approved pre-2026-outcome deviation**. Record the SHA-256 of the predecessor lock and actual SHA-256 of the new protocol/config, plus the original Stage 5 prompt and recovery prompt. A future reviewer must be able to reconstruct exactly why v1 stopped and what v2 changed.

---

## 1. Exact approved amendment: funding is omitted, not zero

The amended **primary estimand** for each episode, policy and evaluator world `E` is:

```
C_ex_funding,E(z) = C_path(z)
                    + C_transient,E(z)
                    + C_temporary,E(z)
                    + C_fee(z)
                    + C_spread(z)

C_path(z)        = sum_{i,k} z[i,k] * (1 - P[i,k] / P0[i])
C_transient,E(z) = 0.5 * vec(z)' H_G(E) vec(z)      [USDT]
C_temporary,E(z) = kappa_E * sum_{i,k} z[i,k]^2 / Vhat[i,k] [USDT]
C_fee(z)         = fee_bps / 10000 * sum_{i,k} z[i,k]
C_spread(z)      = halfspread_bps / 10000 * sum_{i,k} z[i,k]

shortfall_ex_funding_bps = 10000 * C_ex_funding,E / W
W = sum_i X0[i] > 0
```

**No `C_funding` term is computed, filled as zero, or included in the sum.** Prefer explicit output fields:

- `cost_scope="modeled_execution_shortfall_excluding_funding"`
- `funding_included=false`; `funding_observed=false`; `funding_cashflow_usdt=null` / missing by design
- `shortfall_ex_funding_usdt`, `shortfall_ex_funding_bps`
- `all_in_cash_cost_usdt=null` / **not estimated**

If a legacy schema has a required `funding_usdt` column, introduce an unambiguous nullable/not-estimated status, or use a separate explicitly named **mathematical contribution omitted** marker. **Never turn an omitted component into `0.0` in the reported total** and never label the number `total_realized_cost`, `all_in_shortfall`, `funding_free`, or actual exchange P&L.

**Episode treatment:** Retain the *original* Jan–Jun 2026 calendar grid and the **same** 00:00/06:00/12:00/18:00 UTC arrivals, 60-minute horizon, 1-minute bins, last completed price at arrival, two positive inventories, ex-ante forecasts, caps, fixed fees/spreads, risk convention and policies. **Do not exclude any episode for funding events**: neither event times nor event status are established. Apply only the **already frozen structural input-eligibility and evaluation-bar QC rules** common to all policies, not event/price/return/volatility-driven exclusions. Episodes may cross real funding settlements; **their funding-related cash flow is simply outside the scope of the estimand**. Report this explicit limitation even when the window is short.

**Unchanged:** All strategies retain the zero-alpha, sell-only, full-liquidation, 60-minute Stage 4 objective and its original no-funding decision assumptions. This amendment changes the **evaluation accounting scope and the former funding prerequisite**, not the decisions, refit family, scientific hypotheses, evaluation kernels, test dates, metrics, or model optimization parameters. It does not change the fact that public flow-based cross-impact kernels are *reduced-form observational response estimates* used as hypothetical structural scenarios.

**No further funding work is requested or necessary:** Keep the HTTP 451 and checksum/archive evidence as originally recorded. Do not request a proxy, bypass a location restriction, infer an eight-hour funding calendar, fetch 2026 funding rates, or block Stage 5 again solely because `calc_time` remains undocumented. If future research incorporates funding, it needs a **separately authorized and independently validated extension**, not an overwrite of this analysis.

### Code-contract amendment tests (mandatory, pre-outcome)

- A synthetic episode crossing an *arbitrary hypothetical funding event* has the **same eligibility and computed ex-funding cost** as the otherwise identical synthetic episode without it. It is **not** described as having no real funding costs.
- Any output `all_in_cash_cost` is null/unestimated, and no code path uses funding-rate sign/time to select episodes or adjust schedules.
- A policy with the same sold total has identical fixed linear fee and spread, irrespective of scheduling.
- Existing v1 HOLD manifests/tests still explain the old result; v2 preflight's funding condition is **`NOT_APPLICABLE_BY_APPROVED_SCOPE_AMENDMENT`**, not falsely `F1_PASS` or `F2_PASS`.

---

## 2. Phase 5A — complete every *remaining* pretest gate on 2025 data only

**All of this section must finish successfully before opening any 2026 canonical file, even for a preliminary plot or exploratory H1 check.** Keep a strict dataset-read barrier enforced *before file I/O*. An external/user-editable `ready` flag cannot unlock it. Maintain protection of historical 2026 Parquet paths, any function that can load them, and source-linked outcome features.

### 2.1 Implement the independent E1 evaluator exactly as frozen

For evaluation month beginning at UTC `m`:

- E1 training targets cover **exactly 180 complete UTC calendar days** `[m−210 days, m−30 days)`, ending with a **30-day gap** before the evaluated month. Context for features may precede that window, but **targets, fit normalizers and `L`** must come only from eligible rows within its 180 calendar days. No evaluated-month observation may enter.
- Both BTCUSDT and ETHUSDT, Binance USD-M, must share the Stage 2 synchronized source mask, price-flow response equation, nuisance definitions and correct asset/notional units. Preserve independent estimator time origins, standardized-feature transforms and allowed source hashes.
- Fix the **two-component symmetric-PSD matrix exponential family** at `tau_minutes=(5,30)` — not the optimizer's single `(60)` kernel. Estimate each component from the **E1 window**, never reuse model B's C matrices, `L`, frozen June-2025 coefficients or time transforms. Reuse *estimator code*, not fitted parameters.
- Select the E1 ridge **once from Stage 2's development-only** `reports/research/stage02_artifacts/candidate_selection.csv`: full B model, *exact* `(5,30)` family, original 2025 validation loss and the locked **0.1%-near-best / stronger-ridge** tie rule. Record the candidate rows and selection calculation. **No search of 2026 labels or evaluator/policy outcomes.** No monthly retuning of ridge.
- Save each E1 fit with source window, as-of cutoff, model/asset identity, lag family, selected ridge, two fitted PSD matrices, separate `L`, full preprocessing metadata, covariance/Hessian checks, optimizer status and content hash. Require numerical fit tolerances and reject invalid/wrong-market/U model exports.
- An inability to fit a required window is a **real E1 hold**, not a reason to substitute T4's own matrix or select a better evaluator after seeing costs. A fallback is allowed **only if** it is already expressly in the original Stage 4 lock and is frozen **before test access**, separately labeled `QUALIFIED`.

**Mandatory pretest proof using 2025-only data:** Independently fit and inspect at least **two representative 2025 as-of months** with correct 180d/30d windows, PSD constraints and normalizers. Check source earliest/latest labels, exact embargo, status, reproducibility, distinctness from optimizer-B fits, synthetic planted-kernel recovery, and exact-cell cash Hessian/PSD on synthetic schedules. Reject deliberately wrong as-of windows, swapped BTC/ETH order, non-PSD C and illegal 2026 accesses. Perform synthetic tests of sign/unit consistency, stability and tests that E1's parameters and `L` are not secretly copied from B. Development-only execution sanity is permitted; **do not select E1 or change its settings based on development execution gains**.

### 2.2 Implement and freeze evaluator worlds — before test

Use a single common evaluator interface for all policies. All matrices remain symmetric PSD; exact exponential double-cell cash integrals from Stage 3 are binding, including correct `10^-4` and `sqrt(L)` conversion.

| World | Locked definition | Claims allowed |
|---|---|---|
| `E0` | Same Stage 4 B optimizer kernel for **all** policies (fixed per episode); common base costs | Circular in-model diagnostic **only**; not evidence of independent advantage |
| `E1` | Independently fitted **180d/30d** two-decay full PSD kernel; `kappa=.001`, fee `5 bps`, halfspread `1 bp` | Primary alternative model-based evaluation assumption; **not causal independence** |
| `E2` | Each E1 PSD matrix diagonalized, preserving its self diagonals, tau, `L` and other costs | Mandatory adverse/null-cross world |
| `E3` | One-factor-at-a-time about E1: multiply **every complete** matrix component together by 0.5 or 2 (plus base 1); multiply decay constants by 0.5 or 2; `kappa` 0.0005/0.001/0.005; for each C interpolate `(1-rho)diag(C)+rho C`, `rho=0/0.5/1`; separately `D C D`, `D=diag(1,-1)` opposite-sign PSD counterfactual; deduplicate identical base scenarios | Full predeclared uncertainty and adverse-world matrix; do not cherry-pick |

Preserve exactly the Stage 4 lock's scenario IDs/definitions where available. Do not add optional E4, C/D stochastic/nonstationary models, SOL, same-venue L2, a new impact model or post-test scenario values. Recompute exact cash matrices after a stressed `tau`, check Hessian PSD, preserve evaluator-specific `L`, and score **the same USDT schedules** under every world. Wrong-world, cross-coordinate, non-PSD and scenario-identity tests must fail decisively.

### 2.3 Finish all other pretest freeze items

Before opening outcomes, bind **one exact** version of: Stage 4 causal policy definitions T0/T1/T2/T3/T3B/T4, monthly fixed 365-day optimizer fits, episode labels, hard caps and inventories, 28-day forecasting and covariance, zero-alpha, the exact price-path arrival/next-minute-close proxy, E1–E3 and E0 diagnostic, eligible-row rules, **ex-funding score**, primary/secondary H1/H2 comparisons, 7-day bootstrap with 500 draws and seed 20261027, development-defined state/regime terciles, exact planned stress/sensitivity families, output fields and software/source hashes. Precompute regime cutoffs from **July–December 2025 episode inputs only**. Keep T0=forecast-VWAP T1 equality under flat within-hour forecasts if still true; never retune forecasts to force baseline separation.

Check that all the Stage 1–4 model/source/data identities, pre-2026 locks and known notes are internally consistent. Existing Stage 5 HOLD code/test logic should support **two separately identified protocol versions**: v1 remains correctly blocked by funding; v2 is eligible for readiness *only after* E1 and all remaining scientific checks are verified. Do **not** simply bypass/patch an `if HOLD` or write a permissive ready flag without verifying the underlying conditions.

### 2.4 Issue `PRETEST_READY_v2` only if every applicable gate passes

Produce the new v2 lock, config and a hash-linked readiness manifest recording, at minimum:

- `previous_lock_sha256`, `amended_lock_sha256`, `config_sha256`, current specification/code/package/source manifest hashes and original Stage 5 hold evidence path/hash;
- approval basis: **user-authorized funding-excluded cost-scope amendment; 2026 outcome unopened at amendment**;
- `funding_status="NOT_APPLICABLE_BY_APPROVED_SCOPE_AMENDMENT"` and `cost_scope="modeled_execution_shortfall_excluding_funding"`;
- independent E1 implementation tests, E1 development fit IDs and PSD/embargo checks, frozen ridge choice; E2/E3 and scorer synthetic tests;
- locked episode/policy/evaluator IDs and baselines, frozen stats/seed/cutoffs, allowed chronological as-of source permissions;
- status **`PRETEST_READY_v2`** and timestamp **only if all applicable pretest evidence passes**.

Use hashes and signed-by-code checks, not a user-editable marker. Verify on disk that the v1 lock, v1 YAML, original funding hold and previous reports/models are **unchanged**. If anything else fails, write an accurate `PRETEST_HOLD_v2` plus concise exact resumption action. Do not open test.

---

## 3. Phase 5B — only after `PRETEST_READY_v2`: execute locked 2026 OOS once

**Now continue autonomously; do not stop merely because the previous funding HOLD existed.** Execute the original Stage 5 experiment with only the explicitly amended shortfall definition. The requested period is **2026-01-01 through 2026-06-30 inclusive** (end-exclusive 2026-07-01 UTC). Nominal calendar starts: four per UTC day, **724 potential episode labels** before the original structural QC. Never filter based on costs or outcome severity.

### 3.1 Chronological as-of fitting and policies

For each test month, processed **in order** from January to June:

1. Fit optimizer A and B (and N0 as applicable for H1) using the **previous 365 complete days** `[m−365d,m)`, with Stage 2 fixed decay `(60)` minutes, ridge `1`, past-only `L` and normalizers. Freeze per month. Use historical lag context legally but not future labels.
2. Fit the **separate** E1 `(5,30)` PSD evaluator on `[m−210d,m−30d)` with its development-locked ridge and independent coordinates. Freeze it for that month. Later months **may** use previous 2026 observations already elapsed by the refit cutoff, as preauthorized by Stage 4. Never fit on or peek at the month being evaluated. Verify as-of timestamps and source IDs and persist fit hashes.
3. Build precisely the Stage 4 full 28-day history forecasts, 60-bin common volumes/covariance/risk multiplier and inventory/caps for each 00/06/12/18 arrival. The **completed bar opening `t0−1 minute` is available at `t0`**; the bar opening `t0` and all later data are unavailable to the decision. Generate all six policies under the same input/hash: capped T0, causal T1 forecast-VWAP, T2 independent A, T3 joint A/full covariance, T3B joint using B with every off-diagonal set zero, T4 joint full B. No alpha, no purchases, no short, hard terminal equality and forecast participation caps.
4. **Persist policy decisions and hashes before reading the post-arrival evaluation bars**. Reject a wrong-month refit, stale/invalid model ID, incomplete input history or failed solver. Preserve failures/omissions with reasons. **No backward in-time revisions** after viewing any 2026 outcomes.
5. Only then load the required 60 subsequent minutes to **score** those immutable decisions. Use the fixed last completed P0, next-bar close as recorded-price proxy, and exact Stage 3 cash cost under each common E1/E2/E3 world. E0 is optional diagnostic only. Later whole-month or whole-test plots must not implicitly change historical decisions.

**Important guard:** If implementation efficiency necessitates loading a whole monthly Parquet file into memory, enforce a tested logical availability firewall and strict ordering of reads/decisions within it. Prefer streaming/chunking or decision/scoring separation if feasible. Merely having the entire month accessible in memory and trusting programmer discipline without a verified as-of test is insufficient.

### 3.2 Score the same policies under the same evaluator assumptions

- For each episode/policy/world compute the exact **five ex-funding cash components** in §1, the USDT amount and basis points of total starting notional. Do **not** include inventory-risk preference in cash shortfall; report raw inventory risk and the risk penalty separately.
- `P0` is the most recent **completed** 1-minute close; each `P_k` is the close of the bar beginning `t0+k minutes`. This **historical price-path term** is a *counterfactual reference-price proxy*, not an executable actual fill or trader-induced market response.
- Realized volume is allowed only in **ex-post participation diagnostics** (and any explicitly predeclared scoring stress), never in X0, forecast-cap or schedule creation. Zero realized volume yields flagged undefined/infinite participation, not a fabricated denominator.
- Same **E1** for all policies; E2 and every predeclared E3 world similarly shared. `E0` never forms primary claims. Do not compare T3's own-model objective with T4's own-model objective as if they were measured costs.
- Record adverse and negative outcomes, failures, calendar/QC exclusions, unmatched episodes and every scenario. Fixed 5-bp fee and 1-bp halfspread are scenario assumptions and schedule-invariant for equal notional; **do not cite them as drivers of a scheduling advantage**.

### 3.3 H1 — observed conditional response, not a tradable alpha

Report monthly and pooled paired **January–June 2026** N0/A/B standardized 1-minute response MSE on identical source-valid target rows; BTC and ETH MAE/RMSE in bps and contemporaneous explanatory `R²`. Retain the fixed 0.5%-MSE practical threshold, loss differences, negative months and a time-aware daily block uncertainty. Refit once per month as-of; *same-minute* aggressor flow enters only after the bar closes, so this is **descriptive conditional fit, not prediction or causal impact**. No new hyperparameter searches.

### 3.4 H2 — predeclared model-based ex-funding decision contrasts

Primary, for every episode `e` and common evaluator `E`:

```
Delta_ex_funding[E,e] = 10000 * (
  C_ex_funding,E(T3,e) - C_ex_funding,E(T4,e)
) / W[e]
```

Secondary **cross-term isolation**:

```
Delta_cross_ex_funding[E,e] = 10000 * (
  C_ex_funding,E(T3B,e) - C_ex_funding,E(T4,e)
) / W[e]
```

Positive favors T4. T4–T3 compares **different independently fitted A/B kernels including different self terms**; T4–T3B isolates off-diagonal effects of B at common self coefficients. Preserve both distinctions. E1 is the primary *alternative evaluator*; E2 and E3 include unfavorable/null worlds. Preserve the Stage 4 **0.1 bp E1 practical-interest** threshold, without inventing a significance result or treating this threshold as a model-selection target. All H2 results must be labeled **modeled scenario shortfall excluding funding**; not all-in, live, causal or actual savings.

---

## 4. Phase 5C — frozen inference, robustness and reports; NO retuning

Carry out the **original Stage 5 prompt Sections 5–8**, subject only to the new funding-excluded cost definition:

- **Uncertainty:** Paired **7-consecutive-calendar-day moving-block bootstrap**, **500 draws**, `seed=20261027`, 95% percentile interval, resampling complete calendar days and preserving all four within-day episodes, all common policy/world pairs and exclusion statuses. Do not treat 724 episodes or 260,640 minute rows as IID. Report all months separately, pooled effects and the actual CI width; handle zero/negative average denominator for relative cost changes without silently displaying misleading ratios.
- **Complete adverse results:** E1/E2/E3 full prespecified matrix, mean/median/quantiles, positive/negative share, maximum regret and fractions of evaluator worlds/episodes where T4 loses; failure counts and outlier diagnostics. Include primary T4–T3 and secondary T4–T3B consistently.
- **Regime views:** UTC month, weekday/weekend, historical 28-day liquidity/volatility terciles with **2025-only locked thresholds**. Report signed results and uncertainty where practical; do not select regimes on future data.
- **Bounded sensitivities, one-factor-at-a-time:** `theta=0/1/2`; starting forecast participation `.005/.01/.02/.05`; caps `.05/.10/.20`; alternate price proxies (next-bar open and OHLC arithmetic mean); secondary 30/120-minute horizons with recomputed past-only forecast totals; permitted fixed $100k/leg vignette; fee 2/5/10 bps and halfspread 0/1/2 bps; fixed pre-test June-2025 versus rolling calibration as a *labeled* sensitivity. Preserve infeasibility counts. Do not run a huge Cartesian product or change main parameters to make a model win.
- **Outputs:** One clear Stage 5 research report with **H1 and H2 separately labeled**, data/date coverage, QC, selection/lock lineage, numerical model/kernel summaries, cost decomposition and units, common-world comparisons, CIs, adverse/negative findings, methodological limitations and suitable CV-level conclusions. Save modest, legible figures and small underlying figure-data tables; store full results only once under an ignored `results/` location; keep compact research summaries trackable.
- **Session report:** Follow `AGENTS.md` with precise created/modified/unchanged paths, hashes, commands actually run, test outcomes, runtime/storage and resumption instructions. Never say a test passed unless executed.

**Minimum report language:**

> We evaluate hypothetical, sell-only BTC/ETH perpetual-futures liquidation schedules using recorded Binance prices and **model-based** transient/temporary market-impact assumptions. All reported shortfalls **exclude funding payments** because verified historical settlement-event/cashflow reconstruction was unavailable through accessible sources. These amounts are not actual fills, live execution savings, causal price effects, or all-in perpetual-futures P&L. This explicit ex-funding scope was approved and frozen before the January–June 2026 test was opened.

Avoid deploying code, trading APIs, paid-data integration, full depth simulation, Kubernetes, databases, dashboards, CI infrastructure or a new kernel-search project. This is a focused **CV research project**, not a production execution engine.

---

## 5. Mandatory tests, quality gates and failure behavior

**Before readiness and before accessing test outcomes:**

1. Original v1 files/47 bindings (where verified) unchanged; v2 amendment traceable, hash-linked, accurate, version-validated; original funding HOLD preserved and correctly classified.
2. Funding-excluded scope: no funding-driven episode exclusion, no fake zero funding, no funding field in reported ex-funding sum, no implied all-in cost, synthetic equality across hypothetical funding-event labels.
3. E1 `(5,30)` 180d/30d fit on two **2025** months and synthetic recovery; independent `L`, PSD, lag/nuisance convention, embargo exact; candidate ridge chosen only from 2025 selection table.
4. E2/E3 matrix PSD, joint-amplitude and cross-interpolation rules, exact-cell stressed tau, scenario IDs and common USDT schedule scoring verified on hand-computed fixtures.
5. Causal forecasts/decisions, Stage 4 policy identities, solver/asset order, 2025 regime thresholds, expected 2026 episode **calendar** counts, outcome-I/O barrier tests; a manual ready flag or edited config cannot bypass a failed gate.
6. Evaluate 2025-only mock/scorer inputs (artificial prices/volumes where helpful); check path cash sign, `10^-4`, fee/spread invariance, negative shortfall, null/infinite realized participation, numerical decomposition and stored provenance. Re-run focused Stage 1–4 tests that **do not** read 2026 outcomes.

**Then close `PRETEST_READY_v2`; only then** permit monthly chronological 2026 reads. Continue with post-ready tests, fully logged run and final reports. If the code discovers a **material scientific error**, stop the affected branch, record precisely what was opened and what failed, preserve all original outputs and report whether the test was contaminated. Do not repair based on favorable/negative 2026 results; unresolved outcome-driven changes require exploratory labeling or a truly unused new period. If a peripheral optional sensitivity fails, do not hold valid primary outcomes; mark the missing branch qualified.

### End-state acceptance

**`G4 OOS COMPLETE`** requires all of: a validated v2 amendment and `PRETEST_READY_v2`; E1 implementation/2025 tests; frozen A/B/N0 H1 scores on 2026; 2026 policies T0/T1/T2/T3/T3B/T4 with common eligibility; E1/E2/E3 matrix scoring in ex-funding units; primary/secondary H2 contrasts with block CIs and adverse cases; core robustness/report figures; comprehensive QA and concise session report. It does **not** require positive research results. If any critical part is unavailable, report `STAGE5_PARTIAL` or `PRETEST_HOLD_v2` accurately rather than claiming completion.

No implementation of model C/D, SOL, spot/perp, L2/L4, new theorem, live data feed or **Stage 6**. No re-download of validated Binance bars, no duplication of monthly Parquet, no speculative search of later data. Favor existing reusable code and a short critical-test suite over overengineering.

---

## 6. Final Codex handoff format

After running the work, respond briefly with:

- **Stage verdict:** `G4 OOS COMPLETE` / `PRETEST_HOLD_v2` / `STAGE5_PARTIAL`, plus separate H1/H2 scientific outcomes or `NOT_RUN`.
- **Protocol:** path/hash of new funding-excluded v2 lock and `PRETEST_READY_v2`; show original v1 remained unchanged.
- **Data/evaluation:** test months, eligible/scored episodes, evaluators, policies, results and tests actually run. State **excludes funding** prominently.
- **Key effect sizes:** H1 actual MSE A/B and H2 E1/E2/E3 signed bps including adverse results, and paired intervals, **only if computed**.
- **Artifacts:** research report, compact result tables/figures, run manifest, session report and exact restart command; time/disk usage, any unresolved blockers. Do not start Stage 6.

**Execution reminder:** Resume from the pretest HOLD and perform the entire remaining Stage 5 under the one explicitly approved scope amendment. Preserve unfavorable evidence. Scientific and numerical accuracy matter more than a favorable CV headline.
