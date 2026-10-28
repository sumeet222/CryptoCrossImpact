# Stage A liquidity-dependent impact protocol v1 — 2026-10-28

Authorized Stage A A1.0, nested applied extension of the original specification.
Prior code, reports, change logs and locks remain immutable. All selection and
execution development uses only2024–2025 canonical values. January–September2026
is inspected historical background, never fresh confirmation. October1–25 is an
optional separately gated mini-holdout, not required for development completion.

## Mathematics and information

For fixed forecast path, G(t,s)=A(t)sum C exp(-(t-s)/tau)A(s), C PSD in q/sqrt(L)
to1e4 sqrt(L) log-return coordinates. a=clip((Vref/max(V1,floor))^(eta/2),.5,2),
eta in0,.5,1. Vref is positive turnover median over the28 COMPLETE days before
month start, fixed throughout month and used identically for estimation,
optimizer and independent evaluator. It is distinct from each fitted model's L.
V1 is unchanged X1, forecast bar t using only opens<t, daily complete-day
seasonal profile and rolling28d hour-of-week median, fallback/floor unchanged.
For January2024 no preceding full28d month-start reference exists: set A=I
through January, count this identity warmup, retaining EXACT Stage2 rows for
all candidates. No future reference or validation normalization. February onward
has full support. This explicit startup convention avoids silently shortening
the stationary training sample or leaking a future reference into January.

Let D=blockdiag(A_k), H0 the verified exact-cell stationary cash Hessian.
H_A=D H0 D, so z'H_A z=(Dz)'H0(Dz)>=0 for every signed vector. Continuous
proof substitutes A(t)u(t) in the stationary nonnegative quadratic form. Same-cell
causal triangle and off-cell a_m are unchanged; no extra minute factor. This is
frozen-path admissibility only, not dynamic no-manipulation or stochastic optimality.
At replan concatenate IMMUTABLE committed past multipliers and newly forecast
future multipliers. Include H_fp z_p, exclude past-only constants. Never reset
state or reevaluate old multipliers. Record prefix multipliers before reveal.

Response Z_ij,t=a_i,t sum(l=0..H) exp(-l/tau)a_j,t-l f_j,t-l
 -a_i,t-1 sum(l=0..H-1) exp(-l/tau)a_j,t-1-l f_j,t-1-l.
This matches Stage2 truncated return basis at eta0: no artificial H+1 boundary.
It is not the exact difference of equally truncated levels. A H120 sensitivity
is reported separately; execution uses untruncated continuous exponential cells.
The coefficient model is linear in symmetric PSD C. Same joint standardized
loss, unpenalized intercept, ridge1 nonintercept effects, nuisance/features/rows
and own-window L as Stage2; tau60 only, no new grids. Receiver-specific design
scales are restored when constraining C. Nuisance estimates and target scales
come only from the fit window. Same-minute flow is descriptive, not an alpha.

## Selection, policies and scoring (declared before Stage A outcomes)

Fit eta0/.5/1 on Jan2024–Jun2025, validate Jul–Dec2025. Choose smallest eta
within0.1% of best pooled standardized MSE; nonzero promotion additionally needs
>=.5% gain versus eta0, valid PSD/state stability and all equivalence/timing tests.
No execution-cost selection. If failure select0, retain .5 AND1 secondary
ablations; no replacement candidates. Fixed-C eta.5/1 diagnostics distinguish
scaling from re-estimation. All monthly optimizer refits use365 preceding days,
fixed tau60/ridge1; Econditional uses180d ending30d before month, tau5/30/ridge1.

A0=EXACT existing selected L25; A1=selected fitted eta; A2=same-self diagonal;
A3=arrival-frozen future impact multipliers but CVaR/V1 still adapt. Nonzero .5/1
A1/A2/A3 remain reported ablations if not selected. Include fixed-C .5/1, N and
TWAP context. Original X0=.02sum(V0), cap=.1V0, beta/full Sigma, model L, reference
price,60min,four/day and5min cadence fixed. Same12 joint historical paths,
CVaR90 lambda25, temporary kappa.001, assumed fee5bp and halfspread1bp.

Common independent worlds: old E1 stationary; independently re-estimated
conditional selected eta; conditional diagonal; conditional PSD amplitude.5/2;
eta0 stationary-strength stress retaining conditional model C. Exact aliases
are deduplicated and labeled. Also score fixed .5 and1 conditional worlds for
prespecified failed/secondary ablations, separately labeled, without tuning.
Evaluator state is one common per-minute ledger: V1 known BEFORE each minute,
monthly Vref, separate fit C/L. It is not any policy's changing forecast ledger.
Full schedules scored once with recorded next closes, exact transient quadratic,
frozen V0 temporary, assumed fees/spread; funding omitted. Risk/CVaR preferences
separate. Never sum local objectives; no real fill or causal improvement claim.

736 original Jul–Dec2025 episodes, no economic exclusions. Report all worlds,
paired A0-A1 and A2-A1 plus A3-A1, month/weekend and predeclared X2 development
past-liquidity terciles. Seven-calendar-day moving blocks500draws seed20261027,
paired whole-day tuples; response errors similarly resample calendar days.
Practical modeled cost hurdle.1bp; overload/tail deterioration is a tradeoff.
Overload includes true zero turnover; ratios exclude zeros but positive sales
there explicitly non-executable. Retain finite maxima,10/20/100% incidents,TWAP.

## Gates, optional confirmation and literature

Before new empirical fitting: seeded signed PSD/cell/unit/gradient/ledger tests,
future mutation, negative past-multiplier rewrite, eta0 stationary L25 parity.
Before October values: complete development/selection/outputs/tests and immutable
hash evidence; metadata/source rights/noninspection/completeness must be established.
No automatic permission from a text flag. If optional branch is not established,
leave PRETEST_READY_A absent, CONFIRMATION_HOLD, no October values accessed.
A complete negative development experiment is an acceptable closeout.

AJNT https://arxiv.org/abs/2403.10273 supplies deterministic Volterra scope;
Alfonsi–Klöck–Schied https://arxiv.org/abs/1310.4471 supplies earlier matrix theory.
Muhle-Karbe–Wang–Webster https://doi.org/10.1287/opre.2022.0627 motivates liquidity
as reduced-form concavity proxy, NOT our inverse-volume law. Muhle-Karbe–Tracy
https://ssrn.com/abstract=4885733 is a2024 working-paper multi-asset precedent;
abstract consulted, full PDF access403, no detailed theorem borrowed.
Naviglio https://arxiv.org/abs/2501.17096 explains public-flow identification limits.
Our restricted formula and empirical state law are hypotheses, not their theorems.
No Option2 proofs/control directions, new alpha, markets, L2 or live system.
