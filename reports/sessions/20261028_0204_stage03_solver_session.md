# Stage 3 mathematical execution-solver session

**UTC:** 2026-10-28; preservation checkpoint 01:27:48, final verification after
02:04. **G3 PASS. V1 required zero/exponential deterministic cases REPRODUCED;
optional fractional pointwise figure agreement QUALIFIED. V2 PASS.** No new
empirical/economic hypothesis was evaluated. Stage 4 was not begun.

## Authority, Git and preserved inputs

Read AGENTS.md, specification v1.0, the exact Stage 3 prompt, Stage 1/2 reports,
configs, changelog, model/selection/lock artifacts and relevant kernel code/tests.
Inspected the supplied AJNT v2 PDF, including rendered reference figures and
pp.9/20/21. Its actual terminal-penalty reference is Remark 2.10 **(2.15)**; the
prompt's other equation numbers do not match this local version. The matrix
scheme/Table 1 and original parameters were used without substituting a paper.

Branch/HEAD remained `main` / `6d5639af60649a80b9dccffeaf63d99a49d4b780`.
Initial/final worktree is untracked research work from prior sessions plus new
Stage 3 files. No commit, push, branch or destructive operation. Preserved all
**105 fingerprinted prior research files**, including source, models/locks,
manifests, configs, reports/figures, requirements and PDF. All **60 canonical
partitions** retain initial size/mtime; this check used stat metadata only and
read no outcome bytes. README was updated and SPEC_CHANGELOG appended with the
authorized numerical clarification. The research specification is unchanged.

Used the existing Python 3.14.6 `.venv`; no dependency install was needed.
NumPy 2.5.4, SciPy 1.18.1, CVXPY 1.9.3, OSQP 1.1.3 and CLARABEL 0.11.1 are
bound in run manifests; `pip check` passed.

## Files and mathematical implementation

Created `configs/stage03_execution.yaml`, `src/cryptocrossimpact/execution/`,
`scripts/stage03.py`, `tests/test_stage03_execution.py`, the Stage 3 research
report/artifacts, four selected figures and this report. The execution package
separates `ajnt_benchmark` (V1), `impact_cost` (immutable adapter/exact cells),
`solver` (V2), and numerical verification/reporting. No calibration code or data
were changed, and no new market data were downloaded.

V1 uses paper-unit signed rates `dX=u dt`, **T=10, X0=(10,0), varrho=4,
Pi=I, gamma=0, Lambda=0.03 I**, and exact C matrices diag(0.06,0.06) /
[[0.06,0.05],[0.05,0.06]]. Reconstructed Table 1 `D_n u_n=g_n` at
**n=100/200/400**, solved without forming an inverse. Independent exact-cell
Galerkin and continuous exponential Fredholm/ODE solutions provide checks.

V2 uses frozen Stage 2 A/B JSON only, with exact schema/hash/unit/order/cutoff
validation and U rejection. For total sale notional z and w=z/sqrt(L), exact
uniform-bin exponential integrals give `C_G=1e-4 sum_{k>=j} w_k'K_kj w_j` and
`H_G=T_cash+T_cash'`, so `0.5 z'H_G z=C_G`. Same-cell integration counts the
causal triangle once. The half-cell/sample-lag convention remains a controlled
comparison; C/L/tau and regression H=60 were not changed or physically truncated.

The constrained QP uses sell-only bounds, forecast caps and hard terminal
equality; temporary proxy, full covariance risk preference, fee/spread and frozen
drift are returned separately. Per-minute covariance is multiplied by bin
duration once. A capped closest-uniform reference defines common risk scaling;
zero reference risk explicitly falls back to theta=0. Inventory and objective
scaling are reversed for reporting, with primal/KKT/Hessian checks. No clipping,
PSD projection, diagonal repair or cap relaxation is applied.

## Actual verification and results

- **45 pytest tests passed, 0 failed**, in 2.86 s. Coverage includes original
  paper forcing/signs/endpoints, independent quadrature/analytic/Galerkin checks,
  one-/two-cell cash factors, signed PSD/round trips, tiny indefinite rejection,
  null/diagonal/permutation limits, active caps/infeasibility/zero-inventory legs,
  fee invariance/drift/risk units, second solver and schema/firewall rejection.
- All 18 paper grid cases solved; maximum relative Fredholm residual below
  **3e-15**. At n=400, exponential inventory errors versus the continuous
  solution are **0.006351 shares diagonal / 0.004951 cross**, below 0.064% of
  initial inventory. Cross C produces short/buy/sell behavior in asset 2;
  diagonal C produces none. Finite terminal inventories were retained.
- Fractional cell/residual/inventory convergence checks pass, but terminal
  pointwise plot fidelity is **QUALIFIED**. The raw left-cell scheme has endpoint
  rate asymmetry 0.1844→0.1043→0.05719 at 100/200/400 cells, unlike symmetric
  Galerkin rates. `u(T)` is not another traded bin. No endpoint/parameter tuning
  or invented digitized reference points were used. Required V1 and V2 remain valid.
- Six Hessian families × 100 signed synthetic round trips pass. Cash Hessian
  min eigenvalues: **A 8.197e-14 / B 4.079e-14**; norms, relative tolerances and
  direct triangular identities are reported. Maximum cell-quadrature error is
  **5.22e-15**. No negative material impact cost occurred.
- Synthetic A/B/same-self diagonal cases have maximum terminal residual
  **4.66e-10 USDT**, KKT stationarity about **1e-15**, and decomposition residual
  below **4e-16**. OSQP/CLARABEL maximum schedule difference divided by inventory
  is **1.31e-11**; objective agreement is at floating-point precision.
- Fixed continuous-input 2/1/0.5-minute grids have inventory sup errors
  **0.8789% / 0.3607% / 0.1185%** against the synthetic 0.25-minute reference.
  Turnover/covariance rates and initial inventories are held fixed. Half-cell
  impact discrepancies shrink 0.12065→0.03061→0.00770 USDT.
- A/B toy rate L2 difference is modest (**2.35%**); removing B cross terms while
  holding self terms fixed gives **3.03%**. These are geometry diagnostics, not
  savings. The four rendered figures were visually inspected.

## Commands, resources and restart

Actually ran `paper`, `synthetic`, `models-smoke`, successful `all` runs, focused
pytest, dependency and Git checks. The last complete numerical/report run took
**8.88 s**, with measured peak RSS **279,019,520 bytes** (~279 MB). No numerical
solver/test failures or V2 blockers remain. The optional fractional figure
qualification and public-flow causal/upper-grid parameter uncertainties remain
explicit; stochastic Theorem 2.8 and historical policy/economic tests were not run.

```sh
.venv/bin/python -m pytest tests/test_stage03_execution.py -q
.venv/bin/python scripts/stage03.py all
```

Current project storage is about **1.01 GB**; Stage 3 adds roughly **3 MB** including
temporary reference renders (about 1.93 MB measured after reference inspection).
No large matrices or duplicate datasets were retained. Storage/RAM limits were
not approached. `run_all.json` binds prompt/spec/config/PDF/model/code hashes,
Git/dirty status, packages, conventions and resource measurements.

Handoff: `reports/research/stage03_mathematical_solver.md`,
`reports/research/stage03_artifacts/`, and `figures/stage03/`. Stage 4 can use
`load_stage02`, `solve_execution`, `build_problem` and `triangular_cash`; the
caller must supply genuinely past-known forecasts/covariance. Next safe action
is Stage 4 after G3 acceptance/separate authorization. No decision is needed to
close Stage 3; optional pointwise fractional fidelity remains isolated.

**The 2026 final-test outcomes were not inspected, and no historical execution
backtest or Stage 4 work was performed.**
