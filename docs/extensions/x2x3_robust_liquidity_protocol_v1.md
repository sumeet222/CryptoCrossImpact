# X2+X3 protocol v1 — 2026-10-28 UTC

Authority: user-approved combined X2+X3/1.0 prompt; original specification,
funding-excluded amendment and all original/X1 findings remain unchanged.
New hypotheses are H-L (overload), H-G (robust tails), H-GL (combined versus L),
and H-cross (GL-D versus GL). No random Volterra theorem/control, alpha, new
market, live fill or causal identification. Development Jul–Dec2025 is exploratory;
Jul–Sep2026 is a separate conditional untouched holdout,368 nominal episodes.

## Predeclared math and construction, before new development costs

All six primary policies share X0=.02sum(V0), fixed cap0=.1V0, full covariance
from28d completed returns/ddof1, common arrival beta from capped-TWAP risk,
P0, kappa.001, theta1, fee5bp/halfspread1bp assumptions, zero alpha and60min.
V1 is exactly X1's predictor, updated only from completed bars at0/5/…/55.
No further V2 selection. A new time-authorized adapter preserves X1 mathematics;
original guards/sources are untouched. No policy sees future price/flow/volume.
Every five-minute prefix is persisted before the next reveal. A filtered reader
or strict causal tape API supplies only samples open<decision clock.

Ambiguity: nominal monthly B; diagonal B; .5B+.5diag(B); DBD with D=(1,−1);
frozen June2025 B (a distinct existing past-history fit). Five alternatives,
no family tuning. Frozen June B was fitted before every experiment episode;
it retains its own L/tau. It is an optimizer ambiguity point, not E1. E1 remains
separate180d/gap30,tau5/30,ridge1, own fitted L/normalization; E2 diagonal E1.
All Stage5 E3 amplitude/decay/kappa/cross/opposite worlds remain secondary.
No evaluator is copied into the optimizer set. Each exact-cell cash Hessian is
verified PSD in physical USDT coordinates. Duplicate Hessians are recorded and
deduplicated. Report global PSD and elementwise/nonnegative-sale dominance,
active scenario and dual weights; do not search alternatives to avoid dominance.
GL-D diagonalizes each of these five scenarios, preserving its own self/tau/L.

At replan k, per scenario remaining impact is .5zf'Hff_g zf+zf'Hfp_g zp.
Past-only .5zp'Hpp_g zp is excluded from epigraph ordering. Risk uses remaining
inventory and fixed beta/Sigma. CVXPY+CLARABEL solves the convex QCQP, scaled
by original per-asset X0 and W/10000. Never use OSQP for quadratic constraints.
N and D call the unchanged X1 QP. Singleton/zero-penalty conic parity is tested.
Solver tol1e-8, max300; relative feasibility1e-7, stationarity/complementarity/
epigraph tolerances2e-5, scaled to economic magnitude. No clipping/PSD repair.
Independent decomposition, dual feasibility and objective checks required.

Joint path bank: previous28 COMPLETE UTC days, matching episode hour-of-day;
full60-minute paired BTC/ETH hours, valid finite nonnegative turnover only.
All-zero and partly zero valid hours remain eligible. Rank days by SHA256 of
seed|episode UTC date|arrival hour|historical date, take12 with equal weights;
minimum12, otherwise explicit support HOLD. Identities remain fixed within an
episode. For each minute/asset divide each historical volume by the positive
median across eligible historical matching-hour samples; multiply these ratios
by the current past-known V1 prediction. A missing positive reference is a
support failure. No independence across assets/minutes, no artificial zeros or
positive replacement of observed zero capacity. No joint calibration guarantee.
Keep timestamps/cutoff/support and marginal10/50/90 coverage diagnostics.

Liquidity penalty: e_s=sum_future(max(z−.1V_s,0))/W with ORIGINAL W each replan.
CVaR90=min_a a+sum(max(e_s−a,0))/(.1S), equal scenario weights. Preference in
USDT=(W/10000)*lambda*CVaR, not paid cash or firm liquidity. L adds this to B;
GL adds to worst-case impact; GL-D uses diagonalized ambiguity; G has lambda0.
No revised caps/parents/risk, and no past overload cost in future preference.

Selection uses L25 and L100 ONLY, all736 development episodes, choosing the
smallest nonzero lambda with>=10% relative mean observed overload reduction
against N and E1 mean shortfall increase<=.10bp. Mean criteria select, intervals
are descriptive. No GL-specific tuning. After selection, run G,L,GL,GL-D,D,N
on all736. If neither lambda qualifies, selected candidate=N, retain lambda25
L/GL/GL-D as negative fixed ablations (L100 table also retained). If it qualifies,
one selected holdout candidate=L; GL/G/GL-D/D remain fixed ablations. This
simplicity decision avoids selecting combined robustness from favored-world P&L.
No expanded grids, scenario deletions or post-holdout changes.

## Scoring, inference and stop/go

Overload O=sum_all(max(z−.1Vreal,0))/W, including zero Vreal, only after commitment.
Participation denominators exclude zero cells but positive sales there are
explicitly infeasible. Report incidents>10/20/100%, finite maxima and zeros.
All policies share common E1/E2/E3; next-bar close recorded path + exact-cell
transient + frozen V0 temporary + assumed fee/spread, FUNDING EXCLUDED and
unobserved; risk/CVaR preference separate. Score whole schedules once, never
sum local objectives. No optional incomplete-fill evaluator in this assignment.

Paired seven-calendar-day moving blocks,500draws,seed20261027; carry four
intraday policy/world tuples together. Report pooled/month/weekend/development
past-liquidity-tercile contrasts and relative-overload intervals, flag near-zero
baseline. Tail measures: independent worst-world costs, p95 disadvantage,
mean/max ex-post regret, loss share. Positive delta=control−new for both cost
and overload. H-GL compares GL with L, H-cross compares GL with GL-D. Hurdle
>=10% overload reduction with<=.10bp E1 mean cost increase is a heuristic.
No positive result is required. Keep all adverse/outlier/zero episodes.

Before acquisition or value read of six official Jul–Sep2026 monthly archives:
verify eligibility using affirmative prior-run scopes, not filename absence;
finish development, synthetic/real parity/causal/KKT/as-of/scorer/holdout-gate
checks; freeze exact code/config/protocol/selection/tests/source identities in
PRETEST_READY_X2X3. Readiness validates underlying evidence/hash bindings, not a
manual flag. Acquisition is gated too; verify terms, SHA256, CRC/schema/ms UTC,
coverage/pairing/Stage1 quality without changing its QC rules. New source manifest
is separate, original canonical corpus/registry unchanged; one physical new
partition per symbol-month. Inaccessible archive/uncertain eligibility means
OOS_HOLD; never substitute Jan–Jun2026 or another period.

Monthly B refits trailing365 complete days, fixed tau60/ridge1. E1 exact180d
ending30d before month. Already inspected Jan–Jun2026 is disclosed elapsed
calibration history only. July/August can enter later fits only after the closed
month's immutable decisions/scores exist under frozen code. No outcome-driven
refit choice. Initial and every later replan obey open+1min availability. Source
QC can occur after freeze; outcome-dependent economic exclusions cannot.

Attribution: Binance Vision, recorded CC BY-NC-SA noncommercial terms; raw inputs
not redistributed. Original source/endogeneity and hypothetical-fill limitations
remain. Robust-control literature motivates this finite-set applied model, not
an inherited theorem guarantee. Future full stochastic Volterra work is excluded.

## Pre-economic numerical preflight clarification

Real-input pilot conditioning exposed CLARABEL `optimal_inaccurate` despite
passing small synthetic cases. Add the mathematically redundant a>=0 CVaR
constraint (e_s>=0 guarantees a nonnegative optimal VaR). Use a bounded,
deterministic CLARABEL max-step retry sequence .99,.95,.90, all with the same
tol1e-8/max300 and same objective/constraints; accept only optimal plus verified
KKT/duals/decomposition. Log every attempt. No tolerance/cap/risk relaxation,
no economic-results-based choice. This resolves numerical degeneracy, not model
selection. Failed pilots remain in their versioned artifact namespaces.

If the same conic problem still misses status/KKT acceptance, numerical
refinement tightens all solver tolerances successively to1e-9 and1e-10, using
the same bounded step sequence. At most nine CLARABEL attempts; acceptance
thresholds and science stay unchanged, and all retries are recorded. This is
pre-economic numerical precision refinement, not a policy/tuning grid.

## Equivalent numerical reduction before full development

A singleton epigraph is folded into the quadratic objective. If one complete
cash Hessian elementwise dominates every other, nonnegative zp/zf prove that
its conditional remaining cost dominates for all feasible sales. In that case
only redundant epigraph inequalities are removed computationally; the declared
family and full per-scenario cost audit remain unchanged. The certified
singleton lambda0 problem may use the verified X1 OSQP QP; nonsingleton QCQPs
use CLARABEL. Tests compare reduced and unreduced epigraph optima, including
carried history. This is algebraic presolve, not outcome-selected scenario deletion.
