# CryptoCrossImpact — Codex Stage A: Liquidity-Dependent Transient Cross-Impact

**Version:** A1.0 · **Prepared:** 2026-10-28  
**Task status:** Authorized new *empirical extension*, **not** authorization for the future theoretical stochastic-Volterra project (Option 2).  
**Execution style:** One substantial, autonomous Codex session with internal checkpoints; truthful partial completion if any scientific gate fails.  
**Project level:** CV / applied mathematical-finance research. Keep engineering lean; mathematical fidelity, causal timing and honest comparisons are more important than new infrastructure.

## 0. Research question and prior outcome

**Question:** Does an *ex-ante liquidity-dependent, admissible matrix-valued transient-impact kernel* explain BTC/ETH public-flow responses and/or improve the existing adaptive **liquidity-CVaR execution policy**, beyond the improvement already obtained from liquidity-risk control alone?

What is already established (do **not** recompute, overwrite, or relabel as new):

- AJNT deterministic benchmark and exact-cell cash-consistent BTC/ETH execution QP passed mathematical tests (Stages 2–3).
- Full PSD BTC/ETH stationary kernel B improved contemporaneous conditional return-response MSE by **7.55%** versus diagonal A on the already examined January–June 2026 test. This is *observational response*, not causal own-order impact.
- Initial stationary cross-impact scheduling yielded **no reliable economically meaningful** execution-cost advantage.
- X1 completed five-minute adaptive MPC and past-only V1 liquidity forecasts. Adaptive-cost effects were small/uncertain.
- X2+X3 completed robust-impact and liquidity-CVaR (CVaR90) extensions. In its **already opened** July–September 2026 holdout (368 episodes), L (liquidity-CVaR, `lambda_liq=25`) reduced mean observed overload versus N by about **42.0%** (95% block interval 37.1%–47.4%); modeled cost difference remained uncertain. Joint GL offered little incremental benefit, and its impact ambiguity was dominated by one fixed kernel. **TWAP had even lower mean overload**; do not omit this comparison.
- Realized participation could still exceed 100% of recorded market turnover; the study does not reconstruct actual fills. Funding remains **excluded**, not assumed zero.

**Core scientific distinction:** Does changing the *transient impact kernel itself* with liquidity add information/economic value, **holding the successful L liquidity-tail preference and everything else fixed**? Do not confuse this with forecasting more volume, applying liquidity CVaR again, or merely using additional tuning capacity.

## 1. Instructions, source priority and file safety

1. From the repository root, inspect `git status --short`, branch, local data coverage, original research specification, provenance, dependency environment, existing modules and last X2+X3 session reports. Respect `AGENTS.md` regarding autonomy, Git, tests, file safety, permissions, memory/storage, reports and negative findings. **No unrequested commit/push, force, reset, deletion, or overwriting old numerical artifacts.**
2. Read:
   - `AGENTS.md`; `CryptoCrossImpact_Research_Specification_v1_2026-10-27.md`; `SPEC_CHANGELOG.md`.
   - `references/2403.10273v2.pdf` (or discover the actual local AJNT paper) and existing Stage 2 fitted-kernel/response code, Stage 3 exact-cell impact and constrained QP, Stage 4 historical episode maker, Stage 5 v2 ex-funding scorer.
   - X1 (`docs/extensions/x1_adaptive_liquidity_protocol_v1.md`, `configs/extension_x1_adaptive_liquidity.yaml`, existing X1 source/report); X2+X3 (`docs/extensions/x2x3_robust_liquidity_protocol_v1.md`, `configs/extension_x2x3.yaml`, latest **development and July–September 2026 holdout** reports, code/config/tests/selection/lock). **Discover actual paths instead of assuming report names.**
   - If available, `CryptoCrossImpact_Research_Extensions_Literature_Survey_v1_2026-10-28.md` (particularly the liquidity-dependent Volterra section). No other paper PDF is mandatory.
3. Primary research references (consult actual text/abstract for scope; don't attribute our equation to the authors):
   - **Abi Jaber, Neuman & Tuschmann (2026)**, *Optimal Portfolio Choice With Cross-Impact Propagators*, *Mathematical Finance*, DOI: https://doi.org/10.1111/mafi.70025 , https://arxiv.org/abs/2403.10273 — general **deterministic** matrix Volterra kernels and nonnegative-definite cost; original stochastic theorem is **not** automatically valid for a random impact kernel.
   - **Muhle-Karbe, Wang & Webster (2024)**, *Stochastic Liquidity as a Proxy for Nonlinear Price Impact*, *Operations Research* 72(2), 444–458, DOI: https://doi.org/10.1287/opre.2022.0627 — published stochastic-liquidity/concave-impact approximation; *not* a proof that our inverse-volume scaling is correct.
   - **Muhle-Karbe & Tracy (2024)**, *Stochastic Liquidity as a Proxy for Concave Multi-Asset Propagator Models*, SSRN working paper: https://ssrn.com/abstract=4885733 — closely relevant multi-asset precedent; working-paper status and its assumptions must be preserved.
   - **Alfonsi, Klöck & Schied (2016)**, *Multivariate Transient Price Impact and Matrix-Valued Positive Definite Functions*, https://doi.org/10.1287/moor.2015.0761 — pre-existing multivariate admissibility theory.
   - **Naviglio et al. (2026)**, *Why Is the Estimation of Metaorder Impact With Public Market Data So Challenging?*, https://arxiv.org/abs/2501.17096 — observational flow coefficients need not be own-trade intervention kernels.
4. Create only Stage-A namespaced files, e.g. `docs/extensions/a_liquidity_impact_protocol_v1.md`, `configs/extension_a_liquidity_impact.yaml`, `src/cryptocrossimpact/extensions/` if existing structure supports it, `scripts/extension_a.py`, `tests/test_extension_a.py`, `reports/research/extension_a_liquidity_impact.md`, `reports/research/extension_a_artifacts/`, `results/extension_a/` (large, ignored), `figures/extension_a/`, and a **new** `reports/sessions/` record. Adapt exact locations to repository conventions. Avoid a duplicate dataset, new environment, service, database, cloud/GPU or elaborate experiment tracker.
5. For any actual scientific change to this prompt, **version the local protocol, explain the change and pre/post outcome access**. Prior reports, v1/v2 original locks, previous outcomes and previous change logs remain untouched. Preserve previous test baselines.

## 2. Scope and chronology — critical

**Core A1 study:** BTCUSDT and ETHUSDT Binance USD-M perpetual **1-minute** data, sell-only 60-minute two-asset execution, four episode starts/day (00/06/12/18 UTC), five-minute MPC, same initial 2% forecast-volume parent order, original `10%` V0 participation caps, same covariance/risk, fee/spread proxies, CVaR90 lambda **25**, same funding exclusion. Keep the X2+X3 selected **L** policy as the default benchmark, not the weaker N or the more complex GL. Maintain context TWAP and nominal N; use same-self diagonal comparison to isolate cross-impact.

**For development and scientific selection:** only **2024-01 through 2025-12** canonical source values; train through **2025-06-30**, validate and simulate July–December 2025 (736 predefined episodes) using genuine past-only monthly refits for each month. Model-selection candidate set is deliberately tiny. The original Stage 2/5 and X2+X3 prior outcomes (January–September 2026) are **already inspected**, and can be cited as historical background but **cannot** become fresh confirmation of this newly motivated extension. Avoid opening them during selection unless a nonoutcome manifest is strictly necessary.

**Optional fresh, small chronological confirmation**, ONLY if every pretest gate passes: 2026-10-01 through **2026-10-25 inclusive**, four predefined episodes/day (up to 100). This is intentionally a **limited October mini-holdout**; do **not** call it an adequately powered three-month replication. Use official `data/futures/um/daily/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM-DD}.zip` (and checksums if available) for the two symbols, solely after the model, policy, evaluator, QC, inference and selection rules are frozen. The monthly October archive should **not** be assumed available on 2026-10-28. October source availability, data permissions and actual noninspection must be established first. September data may enter **past lookbacks** for October decisions/calibration; the corresponding historical data were previously studied, which is not itself leakage into October outcomes.

If October source data are unavailable/incomplete, already inspected for Stage A, would require unauthorized access, or fail strict leakage/QC gates: **do not substitute July–September as an “independent” test**. Complete development work, issue `CONFIRMATION_HOLD` and preserve October (or a future November/December period) for a separately authorized genuinely untouched confirmation. Do not change dates or hypotheses to obtain a favorable result.

**IMPORTANT:** When data from October are used for source QC, do not read performance/return/flow outcomes until the lock permits it. Source metadata probes and precommitted structural validity checks are allowed; separate first outcome access receipt. No leakage via plotting or exploratory metrics.

## 3. Hypothesis and admissible state-dependent kernel

Let `i,j ∈ {BTC, ETH}`; in previously established **cash-consistent liquidity coordinates**, `C_a = C_a^T ⪰ 0` and `tau_a>0` denote PSD kernel components. The existing fitted stationary model is

\[
G_0(t,s)=\mathbf 1_{s\le t}\sum_a C_a e^{-(t-s)/\tau_a}.
\]

Construct a *restricted* nonconvolution, **conditionally deterministic** kernel for a **frozen forecast path** at each optimization time `r`:

\[
G^{(r)}_\eta(t,s)=\mathbf 1_{s\le t}\,A^{(r)}_\eta(t)
\Big(\sum_a C_{a,\eta}e^{-(t-s)/\tau_a}\Big)A^{(r)}_\eta(s),
\qquad
A^{(r)}_\eta(t)=\operatorname{diag}(a_{i,\eta}^{(r)}(t)),
\]
\[
a_{i,\eta}^{(r)}(t)=\operatorname{clip}_{[0.5,2]}
\left(\frac{V_{i,\mathrm{ref}}^{(r)}}{\widehat V_i(t\mid\mathcal F_r)}\right)^{\eta/2},
\qquad \eta\in\{0,0.5,1\}.
\]

Here `Vhat` is the existing **V1 past-only minute-level** quote-volume forecast available at replan time `r`; `V_ref` is a **past-only** reference median-positive 1-minute USDT turnover (fixed at the start of each month or equivalent as-of fit), defined consistently in training and testing. Clip `Vhat` by the already approved *forecast* denominator floor before taking ratios; do **not** floor realized source zero volumes. Keep asset ordering, common `L` and `C` per fitted model, USDT units, and one-minute time constants explicit. No fitted hidden future liquidity, no random `G` inserted into AJNT Theorem 2.8.

**Mathematical invariant:** For any fixed bounded deterministic diagonal `A(t)`, the quadratic impact form for `G_eta` equals the stationary PSD form applied to the transformed trading rate `A(t)u(t)`. Therefore the **pathwise frozen-path cost** is nonnegative. Prove this elementary congruence argument in the protocol and verify the **actual exact-cell discrete Hessian**. Do **not** claim this establishes full dynamic no-manipulation or optimality of a feedback strategy with a stochastic, endogenous future `A` process; that is deferred **Option 2**.

### 3.1 Coherent use of realized *past* liquidity state in MPC

**Do not reset or re-evaluate past trades with a new future forecast.** At each executed minute `k`, record the liquidity multiplier `a_k` **as it was fixed before that minute's sale**. Once a trade is committed, its multiplier is immutable in the impact-state ledger. At replan `r`, construct a single composite path:

- past cells: actual *previously committed ex-ante* multipliers `A_0,...,A_{r-1}` and already executed trades `z_p`;
- future cells: one deterministic forecasted multiplier schedule `A^{(r)}_r,...,A^{(r)}_{T-1}` based only on information through `r`;
- next replan: append the actually committed prefix multipliers, *update only future multiplier forecasts*, and repeat.

For each such composite path, build **one complete exact-cell, cash-consistent Hessian** with blockwise state congruence. Conditional future impact is

\[
C_G^{\mathrm{remain}}(z_f\mid z_p)=\tfrac12 z_f^\top H_{ff} z_f+z_f^\top H_{fp}z_p.
\]

**Retain `H_fp z_p`** and all cross-asset terms, even where past and future multipliers differ. If liquidity evolves during a physical minute, our one-minute piecewise-constant approximation is explicit. Verify the exact-cell exponential factors (`a0, a_m`) from Stage 3 **without** introducing a spurious extra time-step factor. Test triangle/symmetrization identities, PSD, units and the actual committed-path cash accounting. `eta=0` must exactly reproduce existing stationary exact-cell cash impact and original X2/X3 L policy, to tight numerical tolerance.

If the current code cannot guarantee state-consistent impact history, **stop the empirical comparison for this variant**, report `INVALID`, fix mathematics and tests; never silently reset transient state or rewrite earlier fills. `V1` is a public-volume forecast treated as exogenous to our hypothetical orders: endogenous reaction to our trades is **not modeled**.

## 4. Calibrate the conditional response model properly

**Do not take the old Stage 2 stationary matrices and simply label them “liquidity-calibrated.”** Implement two clearly distinguished choices:

1. **Fixed-C scaling diagnostic (`S_fixed`):** old rolling stationary B coefficients with the `A` factors applied, no refit. Cheap unit/mechanism diagnostic, NOT the primary claim about explanatory improvement.
2. **Re-estimated conditional kernel (`S_fit`):** for each *fixed candidate* `eta`, re-estimate symmetric PSD `C_{a,eta}` using the **same** training dates, y, nuisance controls, economic scaling, constrained loss formulation and ridge `lambda=1` as the stationary A/B comparison. Keep the selected time constant **60 minutes**, one exponential; do not reopen a broad search over decay/ridge/eta. Select only eta on development validation, then use the selected frozen eta in monthly strictly past-only as-of refits.

The return-response design must account for the *change in the entire liquidity-scaled displacement*, not the shortcut `A_t × stationary return regressors`. For candidate `eta`, define the finite-lag **return design** at target minute `t` using a time-varying level-response difference:

\[
Z^{\eta}_{ij,t} = a_{i,t}\sum_{\ell=0}^{H}\phi(\ell)a_{j,t-\ell}f_{j,t-\ell}
  -a_{i,t-1}\sum_{\ell=0}^{H-1}\phi(\ell)a_{j,t-1-\ell}f_{j,t-1-\ell},
\qquad \phi(\ell)=e^{-\ell/60},\ H=60,
\]
\[
y_{i,t}\simeq\sum_j C_{ij,\eta}Z^{\eta}_{ij,t}+\beta_i^\top x_{t-1}+\varepsilon_{i,t},
\quad y_{i,t}=10^4\sqrt{L_i}\,\Delta\log C_{i,t}.
\]

**Finite-lag convention:** This uses `H` taps for the current level and `H-1` for the previous level to **match Stage 2's originally declared truncated return-response basis exactly when `eta=0`** (no artificial `H+1` tail term). It is a finite-lag approximation to the full infinite exponential level process, NOT the exact difference of two equally truncated level processes. Record the tail approximation, and carry out one cheap tail/sensitivity check (`H=120` or exact infinite-exponential recursion) on development data. **Do not mistake a changed tail convention for an eta benefit.** The execution cost itself uses the **untruncated continuous exponential** integrated over the finite execution horizon, as in Stage 3.

In `Z^eta`, `a_{i,t}` is computed from information strictly **before bar `t`**, not from that bar's realized volume. Contemporaneous signed flow `f_{j,t}` can enter **descriptive response estimation**, as in Stage 2, but cannot become a trade-time alpha. All rolling seasonal profiles, feature scaling, `L`, price/flow quality masks and estimators are fit causally; do not use target-bar return as an RHS feature, current-bar volume in a same-bar multiplier, cross-asset future flow, or a predictor normalized by the validation period.

**Computational method:** With `eta` and `tau` fixed, the model remains linear in entries of PSD `C`; accumulate small sufficient statistics by monthly chunks or use vectorized/recursive precomputed causal convolution. Do not persist full duplicated million-row feature panels. For `eta=0`, match existing Stage 2 B's fitted response/loss on the same data and same finite-lag convention, to precision consistent with numerical solvers. If there is a reproducibility mismatch, diagnose and fix it before interpreting any conditional-kernel advantage. Use the same asset observation rows, nuisance features, loss weights and regularization budget for eta candidates, and compare with the same stationary baseline `B0`.

**Primary model-selection gate (development only):** Pick the simplest eta within 0.1% of minimum validation standardized response MSE. Promote nonzero eta as the main model **only if** it improves relative pooled validation MSE over eta=0 by **at least 0.5%**, yields positive PSD components and reasonable stable state-response diagnostics, and passes all equivalence/timing tests. Otherwise select **eta=0** for the primary baseline and report eta=.5/1 as prespecified *failed/secondary* experiments. Do not tune eta to modeled execution shortfall, extreme tail episodes or future holdout performance. Report per-asset, monthly/low-high past-liquidity, and no-lookahead diagnostics. Response `R²` is contemporaneous explanatory, **not predictive**.

### 4.1 Optional cheaper fallback, if full re-estimation is too expensive

If all `S_fit` calculations materially exceed the MacBook resource/time budget or cannot be completed correctly, do the smaller `S_fixed` eta=.5 sensitivity with validated math/tests, label it **mechanistic sensitivity only**, and do **not** assert `S_fit` calibration success or open the optional confirmation. Record a bounded next action. Do not silently replace an invalid fit with the convenient fixed-C variant.

## 5. Matched execution policies (same information, identical L risk preference)

On the **same predefined development episodes**, with exactly the same parent `X0`, original V0 caps, V1 forecast, halfspread/fee assumptions, risk covariance, risk multiplier, 60-minute terminal condition, five-minute MPC, cost definitions and CVaR90 liquidity-scenario bank from X2+X3, construct:

| ID | Policy | What it identifies |
|---|---|---|
| **A0 / L0** | Original X2+X3 selected **L25**: stationary B, V1 adaptive MPC + CVaR90 liquidity penalty | **Critical strongest-existing baseline**; reproduce exactly, do not refit it by a new rule. |
| **A1 / L_eta** | Same as L0 except **liquidity-dependent transient kernel**, using selected eta and properly re-estimated `C_eta`; update only future predicted multipliers at each replan | Primary marginal effect of state-dependent *impact* beyond liquidity CVaR. |
| **A2 / L_eta_diag** | Same as A1, but each `C_eta` component diagonalized, preserving its own self-impact, L, scaling and remaining state | Isolate whether conditional *cross* impact contributes anything. |
| **A3 / L_eta_frozen** | At arrival, freeze predicted **future** multiplier path until termination (but retain committed past multipliers), keep CVaR/MPC liquidity updates otherwise | Secondary effect of *refreshing* impact-state forecasts versus having liquidity-conditioned impact at arrival. |
| **Context** | N (X1 adaptive, no CVaR), unchanged TWAP, and optionally X2+X3 GL | Guard against an overly weak comparator and show trade-offs. GL is contextual, not a new model to retune. |

When eta=0, all A1/A2/A3 formulae should reduce to the appropriate stationary model (A1/A3 exactly L0; A2 same-self diagonal L) aside from numerical tolerances. The only *intended* differences A0→A1 are the estimated liquidity-conditioned kernel and its pathwise state, **not** a changed CVaR bank, volume forecast, inventory target, caps or risk penalty. Note A1 vs A0 therefore combines scale response and constrained matrix re-estimation; provide the **fixed-C state-scaling diagnostic** to distinguish these two ingredients.

**If development selection chooses eta=0:** still report the nonzero-eta ablation outcomes, but do not promote the complex policy or search for another eta to recover a positive answer. Optional October test, if used, should focus on the frozen selected eta=0 null and predeclared eta=.5 ablation, not pretend the failed variant was selected prospectively.

**No new** cross-asset alpha, directionally signed unconstrained round trips, random nonlinear propagator, GL uncertainty-set redesign, forced maker fills, or spot/SOL/L2 integration in Stage A.

## 6. Evaluate actual evidence, not the optimizer's own assumptions

### 6.1 First priority: observed-data conditional-response comparison

On development validation (and on the optional untouched mini-holdout if admitted), report B0 vs `S_fit` eta candidates: pooled/per-asset standardized response MSE, MAE in bps, relative gain, time-block uncertainty and monthly/language-neutral past-liquidity regimes; off-diagonal coefficients, eigenvalues, state-scale distributions, marginal impact curves at low/reference/high forecast liquidity, partial model drift and computational cost. Keep same-minute fitted flow **descriptive**. Do not claim structural identification, tradable return forecasting, new theorem or performance improvement from a better nowcast alone.

### 6.2 Second priority: matched hypothetical execution comparisons

For A0/A1/A2/A3, score **common full schedules** under each of the following *precommitted* evaluator families, all ex-funding and matched across policies:

- **E_stationary:** Original X2+X3 independent **E1** past-only matrix kernel (180-day block ending >=30 days before the evaluated month; fixed tau=(5,30), ridge=1). This is a **null stationary world**, and is not the optimizer's own fitted B.
- **E_conditional:** An **independently fitted, past-only, PSD liquidity-conditioned** matrix evaluator using the same 180-day E1 sample gap and the frozen selected eta. Its fit, scaling and state path are separate from A1's 365-day optimization refits. The evaluator must use one coherent convention for the realized as-of past multiplier ledger and **only information revealed before the corresponding future cell**. This is a *scenario evaluator*, not a causal truth; independently estimate or justify it prior to outcome inspection.
- **E_conditional_diag:** Remove E_conditional's cross terms while preserving its self, normalization and liquidity state. This is a critical adverse/null check.
- **Limited predeclared stress:** whole-PSD-component amplitude ×0.5 and ×2, and a state-scaling strength perturbation eta→0 (stationary). Include no favorable-only scenario selection. No new huge E3 grid.

If no nonzero eta passes the validation gate, the conditional evaluator for eta=0 is identical in **state mechanism** to stationary; do not manufacture distinct information. Deduplicate exact alias worlds and label them. The E_conditional valuation depends on an assumed impact law learned from observational flow; comparing it with E_stationary avoids self-scoring a complex optimizer as its only evidence.

For each policy/evaluator/episode, report **recorded-path shortfall proxy + exact-cell transient impact assumption + unchanged temporary-cost proxy + constant assumed fees/spread**, in USDT and bp of original W, with funding omitted. Compute risk and CVaR *preference* separately, not as paid cash. Include paired A0–A1 and A2–A1 deltas, monthly/weekday/weekend and *past-defined* liquidity regimes, 7-day calendar-block bootstrap (500 draws, fixed seed `20261027`), tails, negative cases, worst-day effects and runtime.

### 6.3 Liquidity realism as a co-primary risk diagnostic

**Do not lose the genuinely useful X2+X3 result.** Compute the existing observed-overload measure

\[
O(z)=\frac{1}{W}\sum_{i,k}\max(z_{i,k}-0.10V^{\mathrm{real}}_{i,k},0),
\]

and provide mean/p90/p95/worst-day, positive-volume participation proportions over 10%, 20%, 100%, positive sales with recorded zero turnover, maximum finite ratio and the TWAP benchmark. Zero-volume positive sales are explicitly *non-executable*, not ratios. Do not remove them from averages or impute missing fills. Any improvement in modeled mean shortfall accompanied by worse overload/tail cost is a **trade-off**, not a win.

**Primary scientific claims to test (not assume):** (H-A1) improved conditional-response fit; (H-A2) liquidity-state-aware impact generates *incremental* execution improvements versus L25 in independently specified scenarios; (H-A3) the improvement does not meaningfully worsen liquidity overload or adverse costs. The threshold for a practically interesting modeled shortfall difference is **0.1 bp**, but report uncertainty, failure cases and alternative scenarios; the test may be null/negative.

**Diagnostic plots (small set):** (1) low/median/high liquidity multiplier and kernel curves, (2) monthly response fit & parameter stability, (3) representative matched cumulative inventories plus realized overload, (4) evaluator-by-policy cash differences and 95% intervals, (5) adverse cases/participation tails. Save small table-behind-plot CSVs; visually inspect figures.

## 7. Ordered implementation and pretest gates

**A-G0 — Inventory and protocol**

- Record existing result/lock hashes, branch/status, resource usage and exact existing L25 baseline source ID; read all relevant old data contracts. Write `a_liquidity_impact_protocol_v1.md` and small YAML config with model formula, causal information schedule, all dates, eta grid, selection rule, policies/evaluators, overload/cost definitions, inference and seed. Keep prior locks immutable.

**A-G1 — Mathematical tests before any new historical outcomes**

- Hand-check 1- and 2-cell exact-cell cross-time blocks under nonconstant A; congruence PSD under positive/negative admissible cross coefficients and random signed vectors; `eta=0` exact parity; asset permutation; cash/bps/L units; A1 `H_fp z_p` and committed past multipliers; conditional finite-difference gradients; time-consistent replans at 0/5/55/59; no clipping/constraint repair; original stationary L25 reproduction on 2–3 development episodes.
- Essential **negative test**: replacing past `a_s` by newly forecast `a_s` must change the test outcome and be rejected. Essential **future mutation test**: altering all price/flow/volume inputs after decision cutoff must not change the committed policy prefix.
- Run focused tests on CPU only; exact tests and small synthetic seeded fixtures should be sufficient. Do not rerun all old massive experiments or inspect Oct before the lock.

**A-G2 — Development fitting and identification checks**

- Build causal V1 multiplier features for 2024–2025; verify same split/rows/nuisance and `eta=0` Stage 2 parity; fit eta=(0,.5,1) PSD models on development training; evaluate July–Dec 2025 response and choose eta **once** using §4. Diagnose the finite-lag tail convention and stability. If `S_fit` impossible/invalid, stop that branch honestly.

**A-G3 — Development policy evaluation and scope selection**

- Apply properly selected/fitted kernels to all eligible fixed 736 episodes. Reuse X2+X3 L25 and other policy inputs; rerun matched L25 schedules to establish parity; then compare A1/A2/A3 and common E_stationary/E_conditional/diagonal/stress worlds. Report primary and adverse outcomes, overload and uncertainty. All development findings are **exploratory/post-search**.
- **Do not optimize the model family to achieve a better execution-cost result after looking at it.** If the nonzero eta fails the response gate, do not add new candidates. Still deliver scientific negative results.

**A-G4 — Optional October mini-holdout pretest (do not force this)**

- Confirm official October daily Binance kline archives legally/publicly accessible, schema/CRC/checksum, availability clock and strict October sample completeness; confirm no Stage-A outcome has been seen. No reliance on suspected-corrupt October `bookDepth`; **only validated futures 1-minute klines**.
- Before reading October economic values, freeze all code hashes/config/protocol/eta/model-selection decision/evaluators/episode timestamps/selection masks/uncertainty methods/outputs; record `PRETEST_READY_A` with evidence, tests, and a first-outcome-access receipt. A manually written flag must not suffice for the reader; implement a simple fail-closed bound check, not production security machinery.
- If ready, independently score only predeclared October 1–25 episodes, in chronological month with 365-day optimizer and 180-day E1 evaluator past-only fits; *October outcomes may not enter those refits*. Use old September only as already occurred historical input. Record total eligible episodes and exact loss/QC reasons. **Label this limited 25-day sample a mini-holdout, not a full confirmation of an economic effect.** Report scientific uncertainty and that the result remains underpowered.
- If not ready or no valid October source, leave ready flag absent, return `CONFIRMATION_HOLD` without changing the sample or broadening the experiment. Development results still stand.

**A-G5 — Report and close**

- Generate one standalone research report with model, citations, estimator/evaluator details, exact findings including negative ones, sample/units, provenance, chronological gates, numerical tests, CV value and limitations. Summarize in the Codex reply: (i) which gates passed, (ii) eta selected/failed, (iii) response improvement, (iv) shortfall/overload contrast and intervals, (v) October holdout status, (vi) tests/resources/paths, (vii) the exact next scientific decision.
- Write the mandatory concise *new* session report. Keep output figures/CSVs small and raw data/cache ignored. Never label a scenario-based result as achieved real savings or proven structural causal impact.

## 8. Stop / approval boundaries and resource management

Proceed autonomously on implementation, tiny configs, necessary tests, and permitted existing data. Stop *only the affected branch* for paid/restricted data, access-control bypass, an incompatible source license, >30 GB incremental storage without approval, destructive changes to pre-existing work, scientifically undefined units/clock, invalid PSD/cash, or contaminated holdout. Continue other valid branches and report exact blocker. **No new exchange connections, real trades, live execution, API keys, L2 history, large L4 downloads or neural model training.** Keep CPU/RAM and cache usage proportional; reuse `.venv`/dependencies; keep only one canonical market data representation.

**Theoretical Option 2 stays deferred:** this Stage A does **not** establish optimal adapted control for random stochastic matrix Volterra kernels, stochastic Riccati–Volterra equations, a new full stochastic feedback theorem or stochastic performance-regret bound. If observations motivate such a theorem, list the precise mathematical question as a *future research candidate* only; do not start the proof program in this assignment.

## 9. Definition of done / acceptable negative result

A **complete Stage A development study** needs: verified reproducible eta=0 nested case; correct state-dependent exact-cell impact and past-impact ledger; development-only PSD kernel fit and honest choice of eta; matched L25 versus conditional kernel comparisons; independent scenario/response tests; uncertainty + liquidity-realism diagnostics; final report and session report. **No nonzero-eta gain is required.** An inconclusive or negative finding is a complete CV research extension if the experiment is correct.

An **October confirmation** is a separate, conditional gate; it does not block completion of scientifically valid development work if the actual data/noninspection preconditions fail.

**Final operating rule:** Improve the model only where out-of-sample evidence and economic plausibility support it. Preserve the original finding that liquidity-tail protection worked better than additional kernel robustness; do not erase or over-interpret it. All results remain observational or model/scenario-based, not actual fills, identified causal impact or all-in perpetual-futures P&L.
