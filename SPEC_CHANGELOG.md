# Implementation clarifications and scientific change log

## 2026-10-27 — Stage 2, before final-test research inspection

- **Common-return factor:** the specification's lagged equally weighted factor
  would equal half the sum of included BTC/ETH lag-one returns. The Stage 2
  prompt explicitly requires omitting an exactly redundant factor. Omitted it
  for every model; no nuisance direction or sample advantage is given to B.
  This is a rank clarification, not a new statistical target.
- **Cross-flow permutation:** the Stage 2 execution prompt clarifies that a
  whole-day-shifted stream enters only the opposite asset's cross-flow slot.
  Each own-flow/own-return alignment and all nuisance controls remain intact.
  This resolves the ambiguity of specification §6.6's stream-shift wording and
  isolates cross synchronization. Fifty fixed offsets were recorded in config
  before the diagnostic fits; the common null eligibility mask is structural.
- **Numerical/feature conventions:** unsigned activity is log1p(mean USDT
  turnover), volume deviation uses log1p and a trailing median, volatility is
  prior-return population RMS; nuisance/flow effects receive the same standardized
  ridge penalty with unpenalized intercepts. Both assets' training-only loss
  standard deviations are saved, while PSD is enforced on economic matrices.
- **Sensitivity only:** the previously flagged October 28, 2024 source interval
  is excluded with two following calendar days in one declared sensitivity,
  covering feature history. The primary sample is unchanged. H=30/120,
  lag-only, lead-flow and no-return-control fits are separate diagnostics and
  cannot replace the primary selected H=60 model.

No instrument, sample date, hypothesis, primary equation, grid, scoring target,
or admissibility condition was changed. January–June 2026 research rows have not
been opened by Stage 2; no final-test outcome was inspected. A complete policy/
evaluator freeze still belongs to the later stages before test scoring.

## 2026-10-28 UTC — Stage 3 exponential-cell numerical convention

- **Old setting:** specification equation (2)'s initial half same-cell G(0)
  plus sampled positive-lag kernel.
- **New production discretization:** exact uniform-rate exponential cell
  integrals, including the causal same-cell triangle once. This is expressly
  preferred by the approved Stage 3 prompt after verification. Scalar factors
  agree with independent quadrature; cash Hessians and signed round trips pass
  PSD/unit checks. The half-cell/sample-lag version remains a controlled
  comparison and agrees as grid duration tends to zero.
- **Comparability:** C, tau, L, the Stage 2 return-regression equation/memory,
  instruments, sample, hypotheses, fees and risk preference are unchanged. Exact
  exponential level kernels are not forcibly cut off at the regression H=60.
  Objective construction and reporting use the same declared exact convention.
  This refines numerical integration, not the economic hypothesis or causal claim.
- **Test firewall:** no January–June 2026 outcome rows were opened. All Stage 3
  capacities/covariances are explicit synthetic inputs; existing research
  artifacts and source/canonical datasets are preserved.
- **Reference numbering:** local AJNT v2 has terminal penalty in Remark 2.10,
  equation (2.15), and an unnumbered §3.4 matrix scheme/Table 1 on pp.20–21. The
  prompt/spec's other equation numbers are not used to substitute another paper.

## 2026-10-28 UTC — Stage 4 matched-policy interpretation and time-safe protocol

- **T3 preserved:** joint model A, with full past return covariance. The original
  table's description of T4–T3 as isolating cross-impact is qualified: A and B
  have independently estimated self terms. Added **T3B**, diagonal of every B
  component with B's exact tau/L, as the secondary pure cross-term ablation, as
  explicitly instructed by the Stage 4 prompt. H2's primary contrast is unchanged.
- **Shared risk scale:** the verified QP now accepts an optional nonnegative
  externally determined beta. T2's two own-variance decisions retain the same
  full-covariance capped-TWAP beta as T3/T3B/T4. Default Stage 3 behavior is
  unchanged and its original source is preserved under ignored provenance.
- **Forecast/quality clarification:** the prompt's explicit [t0−28d,t0) completed
  minute window controls at all UTC arrival hours. Complete valid paired history
  is required; no imputation or jump/stale/verified-zero exclusion. Fine/coarse
  class minimum120, positive 1st-percentile floor, covariance ddof1 using two
  closes inside the window (40319 returns; minimum40000). At hourly arrivals and
  a60min horizon, hour-of-week forecasts are constant within each episode and
  T0/T1 coincide. This behavior was retained without economic tuning.
- **As-of fits:** reuse six existing B fits and create six missing A fits via
  the Stage 2 fixed-family 365-day API, preserving each fit's own L. Main
  development diagnostics use monthly refits; fixed June fits are sensitivity
  on the first UTC Monday's four arrivals per month. No source/model artifact
  from Stages 1–3 is rewritten.
- **Pretest freeze:** fixed E1(5,30) regularization is selected separately within
  that family from the existing Stage 2 development candidate losses, using its
  0.1% stronger-ridge tie rule. E1's exact180d window ends30d before month start;
  E3 stresses use the specification's one-factor-at-a-time convention, with
  PSD-certified opposite-sign counterfactual. Frozen development terciles and
  inference definitions are in protocol v1. Actual funding and E1 implementation
  preflights remain explicit Stage 5 holds; this is **PRETEST_LOCK_PENDING**.
- **Final-test status:** no January–June2026 market observations were opened;
  no historical future-price cost/evaluator or H1/H2 result was computed. No
  scientific target, test dates, main policy baseline, or causal interpretation
  was changed. Stage 5 was not begun.

## 2026-10-28 UTC — explicitly approved Stage 5 v2 ex-funding amendment

- User approved excluding funding from the primary modeled execution-shortfall
  estimand before any 2026 canonical outcomes were opened. Funding cashflow
  is unobserved/omitted, never filled as zero; all-in cost is unestimated.
- No funding-event exclusions or further funding collection. All other dates,
  models, policies, E1/E2/E3, metrics, inference and constraints remain frozen.
- v1 lock and the original funding HOLD remain unchanged. Exact predecessor
  changelog bytes are preserved in docs/stage05_v1_preserved/. The amended
  protocol is docs/stage05_pretest_policy_evaluator_lock_v2.md. Independent E1
  and remaining pretest checks must pass before PRETEST_READY_v2/data access.
- This approved accounting-scope deviation limits comparability with an all-in
  funding-inclusive experiment; it does not identify causal execution savings.
