# Codex Stage 3 — AJNT Mathematical Benchmark and Verified Volterra Execution Solver

**Project:** `CryptoCrossImpact`  
**Stage:** 3 of 6 — published mathematical benchmark, impact-to-cash discretization, constrained liquidation optimization, and G3 verification  
**Prepared:** 2026-10-27  
**Execution:** Run with Codex CLI **locally from the existing repository root**. Complete this stage autonomously, consistent with `AGENTS.md`. **Do not start Stages 4–6.**

> **STARTING INSTRUCTION FOR CODEX:** Read the authority documents and existing Stage 1–2 code/artifacts listed in §0. Then **implement and execute Stage 3 completely**: (V1) reproduce a representative deterministic AJNT paper liquidation experiment using the paper's actual equations and parameters, and (V2) construct a dimensionally consistent, PSD-checked **two-asset, hard-terminal, sell-only Volterra liquidation QP** using Stage 2's fixed admissible kernels. Run rigorous, compact synthetic/numerical tests, write the Stage 3 mathematical research report and required session report, and stop. This is a CV research project; **do not overengineer**. Do not inspect January–June 2026 test outcomes, run historical liquidation episodes, compare trading policies, or claim causal execution savings.

---

## 0. Context, mandatory reading, and authority

At session start:

1. Inspect `git status --short`, current branch/commit, project tree, existing `.venv`, dependency manifest, and the current specifications/configs. **Preserve all existing tracked and untracked work; no destructive cleanup, unsolicited commits or pushes.**
2. Read `AGENTS.md` in full, then **`CryptoCrossImpact_Research_Specification_v1_2026-10-27.md`**, especially §§0, 1.3, 2, 4.2, 5, 7.1–7.2, **8**, 9.1–9.3, 10.1, 13–14. The **scientific specification governs**, and this prompt operationalizes *only* G3. Read `SPEC_CHANGELOG.md` for authorized Stage 2 clarifications.
3. Read **the actual local reference** `references/2403.10273v2.pdf` (or locate the user's existing AJNT PDF under `references/`); use the supplied paper as the definitive source of notation, terminal penalty, objective, and numerical benchmark. Relevant exact places in arXiv v2: §2.1 equations (2.3)–(2.9) and (2.16), Corollary 2.9, Remark 2.10 equations (2.35)–(2.37), Theorem 2.15/Corollary 2.18, §3.1 equations (3.1)–(3.5), and **§3.4 equations (3.16)–(3.21), Table 1 and the `D_n u_n=g_n` numerical scheme**. Read the exact PDF, **not a memory of the formulas**. Primary link: <https://arxiv.org/abs/2403.10273>.
4. Read Stage 1 data-quality report and Stage 2 research report, latest session reports, `configs/core.yaml`, `configs/stage02_kernel.yaml`, `reports/research/stage02_artifacts/selection.json`, `model_A.json`, `model_B.json`, and `src/cryptocrossimpact/kernel/fit.py`/`diagnostics.py` plus their tests. Locate actual paths instead of assuming a naming convention. **Reuse the tested Stage 2 APIs and actual model schema; do not reimplement calibration or edit source data.**
5. Confirm the installed `.venv` and `requirements.txt`. Stage 2 has `numpy`, `scipy`, `cvxpy`, `clarabel`, `osqp`, `matplotlib`, `pytest`, and other free packages. **Install only what is missing**, record substantive versions; no fresh environment, paid package, GPU/cloud infrastructure, or bulk downloads.

**Known, reported Stage 2 checkpoint (verify against local artifacts, not this summary):** G2 implementation `PASS`. Development validation (July–December 2025) has pooled standardized MSE `A=0.4653407827`, `B=0.4344090465`, about **6.65%** lower for B. Selected both A and B use one exponential with **`tau=60` minutes, `ridge=1`**. Stage 2 calibration matrices, in economic scaled coordinates and asset order `[BTCUSDT, ETHUSDT]`:

```text
C_A ≈ [[1.83556335, 0],          [0, 2.46221365]]
C_B ≈ [[1.65715185, 1.09542690], [1.09542690, 2.12483219]]
L   ≈ [6,233,267.0166, 3,488,186.03573] USDT median 1m turnover
```

Values above are **orientation checks only**; always load the real JSON, verify schema/version/hash/asset order, and fail on mismatch. `U` is **diagnostic-only and not exportable as an execution kernel**. The positive observed cross-response, its bootstrap interval, and development selection **do not establish a structural intervention kernel or a tradable signal**. Both `tau=60` and `lambda=1` sit at the respective development grid's upper boundary; flag tail/regularization uncertainty as a Stage 4–5 sensitivity, **not a reason to retune using the test set**.

### 0.1 Stage 3 firewall and permitted inputs

- **Allowed:** the AJNT PDF; existing verified Stage 2 model JSON and develop-only metadata/configuration; entirely synthetic benchmark arrays; strictly development-only small snippets for a loader smoke test if necessary. Read source-data *metadata*, not outcome data, when avoidable.
- **Forbidden:** loading/scanning/charting any 2026-01 through 2026-06 BTC/ETH outcome rows; OOS refits, test performance, real historical episode schedules, policy comparisons T0–T4, evaluation E0–E4, market-impact backtests, forecast optimization using realized future volume; optional external L2 downloads.
- **Scope:** implement a **generic deterministic execution solver and verification harness**. Stage 4 will define the actual timestamped episode builder, capacity forecasts, strategies and schedules. Stage 5 will unlock the final-test outcomes only after the complete policy/evaluator protocol is frozen.
- **Claims:** label the paper replica **`AJNT_DETERMINISTIC_BENCHMARK`** and the project solver **`CONSTRAINED_SCENARIO_QP`** separately. The latter is not literally the AJNT stochastic Theorem 2.8 optimizer. Correct solver + observational kernel ≠ real savings or identified causal market impact.

---

## 1. Required deliverables and acceptance goals

**V1 — published mathematics:** reproduce the **deterministic-signal/zero-signal two-asset AJNT numerical example** from §3.1 with §3.4's operator/Nyström-type method or an algebraically equivalent discretized Fredholm first-order system. Verify the **paper's terminal-penalty objective and unrestricted signed controls**. Produce comparison figures/diagnostics for diagonal and cross-impact, and a precise verdict (`REPRODUCED`, `QUALIFIED`, `NOT_REPRODUCED`) with numerical evidence. Do not fabricate pointwise comparisons with paper figures for which no digitized data are available.

**V2 — applied constrained solver:** implement a well-tested CPU `2×60`-variable convex QP for two positive starting **USDT-notional inventories** sold in one-minute slices with nonnegative sells, forecast participation caps and exact full liquidation. Its transient **cash cost must be derived consistently** from Stage 2's normalized `C`, liquidity units `L`, one-minute kernel time constants and within-cell integration. Include temporary/liquidity cost, ex-ante inventory risk and optional *preknown* drift; fee/spread constants only when explicitly supplied as assumptions. Return a decomposition with *units*, inventory/cap residuals, optimization status, PSD diagnostics and numerical check results.

**G3:** numerical/scientific validity gates, reproducible runner, focused tests, a mathematical report, a fresh Codex session report, no historical execution conclusions. Prefer robust, readable math code and a few meaningful figures over a large framework.

---

## 2. V1 — exact-paper deterministic numerical benchmark

### 2.1 Use paper's actual experiment, without crypto re-scaling

First target: AJNT **§3.1, Figures 1–2** with **no alpha signal**, `T=10` (paper's dimensionless time), `X0=(10,0)^T`, terminal penalty `varrho=4`, `Pi=I_2`, `gamma=0`, `Lambda=diag(0.03,0.03)`, and two alternative matrices:

```text
C_diagonal = [[0.06, 0.00], [0.00, 0.06]]
C_cross    = [[0.06, 0.05], [0.05, 0.06]]
```

Follow §3.1's `G(t,s)=1_{s<t} C phi(t-s)` and the actual reference settings: `phi_zero=0`, `phi_exp(lag)=exp(-0.5*lag)` and, when numerically well-defined, `phi_frac(lag)=lag^(-0.25)` (integrate its singularity, **do not evaluate at zero**). Paper §3.4 gives cell integrals. **At minimum** reproduce the zero and exponential cases for both matrices. The fractional case is a desirable compact extension of the replica; record `QUALIFIED` if technical fidelity cannot be established economically, rather than blocking V2.

**Important:** The paper's asset 2 begins at zero and can **short/buy/round-trip** in an *unconstrained* terminal-penalty problem. Do **not** impose the project's sell-only constraint or force exactly zero terminal inventories in V1. The paper's penalty is finite, not a hard equality. Inspect PDF for the precise sign convention `dX=u dt`, first-order system and `g` used for liquidation; the initial inventory appears in the source term. `P` martingale/no alpha means deterministic expected price variation is zero, **not** a license to drop terminal-penalty forcing.

### 2.2 Reference mathematical implementation

Implement the prescribed deterministic case (Corollary 2.9 with Remark 2.10), preferably reconstructing `D_n` and `g_n` from §3.4's precise triangular matrices and table. Solve a **linear system** (`scipy.linalg.solve`), **do not explicitly form a numerical inverse**. Choose a reasonable sequence of grid resolutions (e.g. `n=100, 200, 400`, subject to CPU/RAM), and compare inventory/trading-speed curves, terminal residual, condition number and objective. A direct independently discretized quadratic-cost first-order condition is encouraged as an analytic check where time permits.

Report **reference checks**: with `C` diagonal, asset-2 trade/inventory remains approximately zero (up to grid error); the cross matrix can induce **signed asset-2 round trips** in the unconstrained problem, as illustrated in the paper; asset-1 solution differs between diagonal and cross cases; refining the grid improves stability. Show at least the no-signal exponential case against the **qualitative structure** of Figure 2. Reproduce approximate curves without claiming exact pixel equality; account transparently for paper's integration/quadrature conventions and potential terminal endpoint treatment.

Do not substitute the project's `tau=60 minutes`, `L` scaling, USDT amounts, or constraints into V1. Do **not** claim to have implemented AJNT's **general stochastic Theorem 2.8 conditional-expectation solution**; V1 verifies only a deterministic specialization / paper's §3.4 scheme.

---

## 3. V2 — kernel-to-execution dimensional contract

### 3.1 Immutable stage-2 model input

Load **A and B** from `reports/research/stage02_artifacts/model_{A,B}.json` via a safe tested adapter. Verify:

- `asset_order == ["BTCUSDT", "ETHUSDT"]`; positive `liquidity_usdt=L_i`; `tau_a>0` in **minutes**; `C_a=C_a^T` and `eigmin(C_a) >= -specified_scale_aware_tolerance`; fit status/`execution_kernel_export_allowed=true`; stage provenance and cutoff through **2025-12-31 at latest**; never substitute model U.
- `G(lag)=sum_a C_a exp(-lag/tau_a)` in the same coordinates as Stage 2's reported **level kernel**; `H=60` is Stage 2's **return regression lag truncation**, **not** automatically a decree that the fitted level kernel becomes exactly zero for execution lags greater than 60. In primary `T=60`, simply use the declared exponential up to horizon; state and test any alternative truncation convention. Never take the already differenced return-lag basis coefficients as impact levels.
- `q` and hypothetical execution flow are in **USDT quote notional**, buys positive/sells negative. For a signed notional vector `u`, transformed flow is `D_L^{-1/2}u` with `D_L=diag(L_i)`. A first-order change in asset `i` log price is `10^-4/sqrt(L_i)` times the scaled `G` response to transformed flow. Accordingly the quadratic modeled trading cost in **USDT** has factor `10^-4` times the square of transformed USDT notional. No extra `10^-4`, price, USD-to-coin, or minutes multiplier can be inserted without derivation.
- Unit normalization is a **small log-price/constant-reference-notional approximation**; do not claim exact execution in contract quantity or use contemporaneous future mid prices. Externally supplied reference prices are only needed in later execution scoring / rounding extensions.

### 3.2 Correct discrete transient cash cost — derive, test, record conventions

Write a short derivation in source docstrings **and** the research report from the continuous-time form (specification §5.3/§8.1):

```text
C_G(u) = 10^-4 * integral_0^T [u(t)/sqrt(L)]^T
                 * integral_0^t G(t,s)[u(s)/sqrt(L)] ds dt
```

Take one-minute or general-duration bins `I_k`; let `z_k` be **total positive notional sold during bin k**, `w_k=D_L^{-1/2}z_k`, with an assumed uniform rate `w_k/delta_k` during that bin. Then exact cell integrals define

```text
C_G = 10^-4 * sum_{k,j<=k} w_k^T K_(k,j) w_j ,
K_(k,j) = 1/(delta_k delta_j) * integral_(t in I_k)
            integral_(s in I_j, s<=t) G(t,s) ds dt .
```

For a single scalar exponential component with equal bin width `d` and time constant `tau`, independent checks for the scalar integral factors are:

```text
k > j:  a_(k-j) = (tau/d)^2 * exp(-(k-j-1)*d/tau) * (1-exp(-d/tau))^2
k = j:  a_0     = (tau/d) - (tau/d)^2 * (1-exp(-d/tau))
```

Multiply these by **each** matrix `C_a`, then sum components. These exact factors approach the familiar lag-sampled kernel and `a_0 -> 1/2` when `d/tau -> 0`. Implement numerically stably using `expm1`/series near zero; compare with independent numerical integration for tiny examples. **Do not count the same-bin quadratic cost twice.**

**Reconcile with specification equation (2):** it uses a **half same-cell instantaneous kernel** as its stated initial uniform-bin convention. The *exact integrated exponential diagonal* above is a modest, more accurate cell convention that may differ slightly from `0.5*G(0)`. Make the choice **explicit**; compute a half-cell/sample-lag baseline and show its `d -> 0` agreement, with a short, dated `SPEC_CHANGELOG.md` note **if the production convention changes**. Do not silently replace the specification or use one convention in objective and another in reporting. For the **primary exponential kernel**, prefer the exact cell integral if verified; keep the half-cell discrete approximation as a controlled comparison. This is a numerical clarification, **not** a new economic hypothesis.

Form a **symmetric** QP block Hessian `H_G` such that `0.5*z^T H_G*z == C_G(z)`. In particular, off-diagonal time blocks must not receive an erroneous factor of two and each same-bin block must account for the correct half-triangle integral. Explicitly verify this identity for hand-computed one- and two-bin scalar and two-asset examples. `H_G` should be PSD (within justified floating-point tolerance) for the admissible fitted exponential PSD components, including **signed round-trip** vectors. **Do not silently PSD-project an indefinite empirical Hessian**; diagnose math/unit/discretization first.

If implementing a power-law or general `G(t,s)` utility, keep it tightly scoped to synthetic V1 needs and integrate singular cells; **do not** invent uncalibrated crypto power-law models or optimize them in Stage 3.

---

## 4. V2 — hard-terminal sell-only convex quadratic program

### 4.1 Inputs and constraints (synthetic or explicit development-only smoke inputs)

The solver accepts these **as provided**, without loading future market data:

```text
assets                    = (BTCUSDT, ETHUSDT), in that order
start_inventory_usdt       = X0 in R^2_+; >0 on both legs for main use
forecast_turnover_usdt     = Vhat[n,2] positive, explicitly ex-ante
risk_cov_per_minute        = Sigma[2,2], symmetric PSD, historical/past-only if empirical
model                     = validated Stage 2 A or B
horizon_minutes            = n * delta, default 60 and delta=1 minute
cap_fraction               = 0.10 primary (tests 0.05, 0.20)
kappa                     = 0.001 primary (tests .0005, .005)
theta                     = 1 primary (tests 0, 2)
fee_bps                   = 5 illustrative, half_spread_bps=1 illustrative
expected_price_change     = zero default (optional **frozen** future-interval expectations)
```

Sell variables `z[k,i] >= 0` are **USDT notional per interval**. Remaining **pre-trade** inventory `h[k] = X0 - sum_{j<k} z[j]`; terminal equality `sum_k z[k,i] == X0[i]` for each `i`; upper cap `z[k,i] <= pmax * Vhat[k,i]`. In the main project, never allow negative sells, short positions, or round trips; **that is different from V1**. Use a deterministic feasible synthetic example, e.g. `Vhat` positive fixed arrays and `X0_i=0.02*sum_k Vhat[k,i]` (specification §8). Cap feasibility is analytical: require `X0_i <= pmax*sum_k Vhat[k,i]`, with a scale-aware tolerance. If infeasible, **report infeasible**, do not use future actual volume or silently relax caps/terminal equality. Keep any possible quantity/lot-size rounding as an explicit future extension; Stage 3 continuous notional constraints are the mathematical core.

### 4.2 Objective components, exact units and objective decomposition

Use **one** objective with the same conventions throughout (specification §8):

1. **Transient modeled cash cost** `C_G(z)` from §3 above, in USDT, based on chosen `G_A` or `G_B`. Model A has diagonal components; B full PSD, but both share the same volume, risk and constraints.
2. **Temporary liquidity proxy**, `C_tmp = kappa * sum_(k,i) z[k,i]^2 / Vhat[k,i]` in USDT. This uses only **forecast** turnover, not next-minute realized volume; it is a scenario parameter, **not measured historical bookwalking**. Positive `kappa` ensures useful regularity even if an impact matrix is singular.
3. **Pretrade inventory risk** `R_raw = sum_k h[k]^T Sigma h[k]` where `Sigma` is ex-ante **one-minute log-return covariance**. Use the full covariance for the joint optimizer, even with diagonal `G_A`. Set **`C_risk = theta * (W/10000) * R_raw/R_raw(z_TWAP)`**, `W=sum_i X0_i`, `theta=1` primary, and a deliberately chosen **reference uniform-cap-feasible TWAP schedule** `z_TWAP` as defined in the specification. If naive uniform TWAP is infeasible under forecasts, the common reference must be the uniquely defined **capped closest-feasible uniform schedule** (Stage 3 may implement this mathematical projection for normalization; this is not the Stage 4 policy comparison). If risk-reference denominator effectively zero, record a `theta=0` fallback, never divide by zero silently.
4. **All-taker linear cost**, `C_linear = 10^-4 * (fee_bps+half_spread_bps) * sum_(k,i) z[k,i]`, where illustrative bps inputs are **assumptions**, not venue-observed BBO or historical fee tiers. For identical sell-only full liquidation it is schedule-constant; assert invariance numerically. Don't misattribute strategy ranking to it.
5. **Optional drift term** `C_drift = - sum_(k,i) z[k,i] * m[k,i]`, where `m[k,i]` is a fractional **forecast** change from arrival; core `m=0`. No realized future returns, same-bar order flow or hindsight alpha allowed.

Minimize `C_G+C_tmp+C_risk+C_linear+C_drift` under the constraints. Return all components **separately**, including the raw risk diagnostic (distinct from booked shortfall), and prove via small tests that their sum equals the reported objective. Scaling by a positive constant for optimization conditioning is fine if **undone** in reports and verified.

Potential nuance: `C_G` is an impact **model**, `C_tmp`, spread and fees are **assumed** costs, and `C_risk` is a **preference penalty rather than realized execution expense**. Never report the sum as historical realized implementation shortfall. The paper's temporary impact convention has its own `1/2 * Lambda` trade-price factor; V1 must follow it, while V2 follows this specification's **separate `kappa` proxy**. Do not conflate the two.

### 4.3 Solve and validate

- Use `cvxpy` + **QP solver** (`OSQP` or `CLARABEL`, whichever satisfies small robust tests) for V2. Verify actual solver availability. At default horizon there are only **120 notional sell variables**. Verify returned status, primal feasibility, objective residual, cap slack, KKT or stationarity diagnostics where feasible, and Hessian eigenvalue/conditioning. Test a second solver or direct analytic solution on small instances; don't rely solely on a CVXPY `optimal` flag.
- The solver should accept any valid **symmetric PSD** `2×2` market covariance and economically admissible kernel, including zero and diagonal limits. Add small numerical tolerance to condition checks, **not arbitrarily large diagonal repairs** that secretly redefine impact. If conditioning forces reasonable numerical scaling/reformulation, record it.
- API should return immutable or clean result structure with the 2D schedule, `h_before`, `h_after`, exact starting/ending inventory, caps used, total/individual cash-cost terms, objective, status and diagnostics. Ensure shape/unit assertions; reject negative or zero `Vhat`, non-finite `C/L/Sigma`, asset-order swaps, an invalid B matrix, a diagnostic-only U export, time-unit mistakes and unidentified schema revisions.
- Provide one **standalone synthetic** A-vs-B *solver sanity example*, optionally plotting both schedules to show the impact of cross terms **under the model's assumed objective only**. This is **not** a real-data strategy or policy-performance comparison, and no claim of cost savings should be drawn from it. Stage 4 will implement and compare the actual T0–T4 policies on time-aligned episodes.

---

## 5. G3 mathematical tests — minimum mandatory coverage

Write focused pytest fixtures with tiny hand-checkable arrays and a few medium cases. These are the acceptance conditions, not merely optional suggestions:

| Area | Mandatory check |
|---|---|
| **AJNT V1** | Reference parameter fidelity and **unrestricted signed** controls; `C` diagonal gives no asset-2 trading (zero signal); cross term induces qualitative round-trip behavior in asset 2; `n` refinement and numerical first-order residual. A mismatch must be diagnosed/reported, never tuned away by changing the paper. |
| **Time/units** | One- and two-cell exact exponential integrations versus independent quadrature; scalar/two-asset cash hand calculations; `tau` minutes vs grid duration; `10^-4` and sqrt(`L`) applied once; `H=60` return truncation not applied as an undeclared physical 60-minute execution cutoff. |
| **Hessian/admissibility** | `0.5*z^T H_G z` equals direct triangular cost for arbitrary vectors, including **signed** ones; full Hessian PSD for A/B and several PSD synthetic kernels (relative tolerance); zero/off-diagonal negative-but-PSD synthetic examples; reject indefinite matrices. |
| **Limits** | `G=0`, `theta=0`, `kappa>0`: exact optimal `z[k,i]` proportional to forecast volume (subject to feasible caps); constant `Vhat` returns uniform TWAP; diagonal `G`, diagonal `Sigma` ⇒ joint solution equals two independent 1D solves; identical asset relabeling permutes output. |
| **Feasibility** | Full terminal inventory to numerical tolerance, nonnegative child orders, participation caps, monotone remaining inventory, no purchases/round trips; `X0=0` permitted for a synthetic leg but with zero sales; explicit infeasible caps fail cleanly. |
| **Cost accounting** | Scalar sign and factors of two, same-bin vs across-bin, quadratic scaling of impact when doubling trading size with no active caps, correct units for temporary/risk/fees, fee invariance, objective equals sum of breakdown. |
| **Convergence/independent check** | Compare `delta=2,1,0.5` minute grids on **purely synthetic continuous inputs** (`0.5`-minute data is **not** claimed to be an observed market series). Hold the **continuous-time** horizon, initial notional, forecast turnover *rate*, and covariance *rate* fixed: convert forecast turnover and return covariance to each slice consistently (e.g. under a constant synthetic diffusion, `Vhat_delta = rate*d` and `Sigma_delta = Sigma_per_min*d`). Compare **trading rates/cumulative inventory**, not raw per-bin notional at different widths; show cost/trajectory convergence and compare an independent numerical formulation or second solver. |
| **Model firewall** | `model_A.json` and `model_B.json` accepted in correct coordinates, model `U` rejected, unverified market/asset order rejected, 2026 data read blocked by Stage 3 CLI; Stage 1/2 artifacts and canonical partitions unchanged. |

Use **scale-aware** numerical tolerances; a target inventory residual is `≤ max(1e-6 * X0_i, physically justified numerical tolerance)`, with tighter synthetic tolerances when practical. Document solver residuals and negative eigenvalue tolerances **relative to matrix norms**. If exact V1 benchmark has a genuine convention discrepancy, mark its result `QUALIFIED` and continue V2 if mathematically independent. No fake all-tests-passed declaration.

---

## 6. Efficient code organization, commands and provenance

Adapt existing modules, do not create a second independent package or oversized scaffolding. Suggested minimal additions:

```text
src/cryptocrossimpact/execution/
    ajnt_benchmark.py       # paper-specific V1, equations and grid integration
    impact_cost.py          # normalized kernel adapter, exact cell blocks, cash Hessian
    solver.py               # constrained V2 QP + diagnostics
scripts/stage03.py          # thin CLI: paper, synthetic, models-smoke, all, report
tests/test_stage03_execution.py
configs/stage03_execution.yaml        # small numeric defaults; NO test dates or new data path
reports/research/stage03_mathematical_solver.md
reports/research/stage03_artifacts/   # small tables, reference comparison, plots/metadata
reports/sessions/YYYYMMDD_HHMM_stage03_solver_session.md
```

Keep code functions small, dimensioned, well-commented for nonobvious math, using `pathlib` and one dependency file. Minimal CLI examples (adapt to working local structure):

```bash
.venv/bin/python -m pytest tests/test_stage03_execution.py -q
.venv/bin/python scripts/stage03.py paper
.venv/bin/python scripts/stage03.py synthetic
.venv/bin/python scripts/stage03.py models-smoke
.venv/bin/python scripts/stage03.py all
```

The **model smoke** should load and validate model JSON only; **no** historical test observations. If a sample real feature is required for a developer sanity check, use *development only* and disclose exact cutoff. Prefer entirely synthetic capacity/return-covariance inputs for V2 in Stage 3. No additional exchange data acquisition. Avoid duplicate multi-GB datasets, notebook snapshots, large run dumps or detached background processes; stay within `AGENTS.md` disk/RAM limits. Persist compact machine-readable numerical diagnostics, figures and inputs, not huge matrices or hundreds of output plots.

**Minimal run manifest**: prompt/spec/config hashes, Git revision **and dirty status**, AJNT PDF path/hash/version, Stage 2 A/B file hashes, accepted asset order, source data identity, solver/library versions, seed, paper grid size, synthetic grid size, component conventions, result paths and valid/failed statuses. Preserve Stage 1 and 2 manifests; never call a new implementation an exact paper reproduction just because a QP solved.

**Documentation/report output** in `reports/research/stage03_mathematical_solver.md` should include:

1. **V1 paper specification and exact source citations** (§/equations), derivation/definition of `D_n`, zero/exponential (and optional fractional) curves of signed trading speed and inventory, convergence/first-order residuals and honest reproduction status.
2. **V2 derivation** from level `G` and scaled quote notional to **USDT cash cost**, fully worked one- and two-cell factor-of-two tests, exact-vs-half-cell comparison and PSD eigen diagnostics.
3. **Applied QP** objective, fixed input units, feasibility/constraints, sample synthetic A/B schedules, component costs and full test summary. State that all outputs are **synthetic/model-based**, not measured crypto execution results.
4. **Caveats and decisions:** observational public-flow `C` as structural **scenario assumption**; tau/regularization upper-grid selections, tail sensitivity; any numerical discrepancy; spec change log if exact-cell quadrature changes the declared convention; no test data accessed.
5. **Stage 4 interface:** names/functions and small input/output schemas for A/B model, ex-ante turnover forecast, covariance, inventories, cap, cost assumptions and optimizer result. Recommend next steps and identify any essential blocker. Avoid an extensive developer manual.

Generate a **new**, concise session report per `AGENTS.md` containing file change inventory, tests/commands actually run, evidence/verdict, disk impact, key model/solver functions, any failed branches and exact restart. At the end of Codex's final reply, give paths, **V1 and V2 statuses separately**, G3 PASS/QUALIFIED/BLOCKED/INVALID, number of tests passed/failed, and next handoff to Stage 4.

---

## 7. Decision gates and scope stopping rules

- **V1 paper:** If the reference numerical scheme cannot be reconstructed with convincing first-order/grid evidence, classify `QUALIFIED` or `NOT_REPRODUCED`, state *precisely* why, and independently complete V2 when possible. Do not quietly fall back to a different constrained QP while still claiming exact AJNT replication.
- **V2 impact/Hessian:** Any unresolved major unit inconsistency, signed round-trip **negative impact cost** for the verified PSD family, objective decomposition error, or material constraint violation is a **G3 BLOCKER**; fix these before Stage 4.
- **V2 no-cross/null:** If the calibrated cross term changes synthetic schedules only weakly, **report it**. No mandatory positive gain or artificially chosen high cross weights. Negative scientific/economic results are acceptable.
- **Stage completion:** G3 may be called `PASS` only after the central unit, PSD, solver and inventory tests succeed and the paper replica verdict is presented honestly. A `QUALIFIED` paper numerical match can coexist with a valid V2 solver if the exact discrepancy and label are explicit.
- **No scope creep:** Do **not** implement historical episode enumeration, VWAP forecasting, TWAP/VWAP/T2/T3/T4 policy comparisons, E1–E3 score worlds, monthly 2026 refits, actual P&L, funding/fees from APIs, OKX depth, model C/D, SOL, or the general stochastic Theorem 2.8 solver. Those are later stages/conditional extensions.

**Do not ask for routine confirmations.** Proceed within project permissions, resolve implementation details via the local paper and specification, document modest deviations, stop only the affected branch on scientific/legal/resource gates, and finish every independently valid task.

---

## 8. Final response required from Codex

After execution, report concisely:

- **V1** AJNT deterministic reproduction status with actual paper parameters, numerical comparison and figures.
- **V2** constrained solver status with exact cash-factor convention, PSD/feasibility tests, synthetic A/B examples and objective checks.
- G3 overall verdict, significant tests run and any not run, files created/changed, session-report location, incremental disk usage and next safe action.
- Explicit statement: **the 2026 final-test period was not inspected and no historical execution backtest was performed**.

**Stop after Stage 3. Next authorized stage, after G3 acceptance: Stage 4 (episode forecasts, matched policy construction and development-only dry runs).**
