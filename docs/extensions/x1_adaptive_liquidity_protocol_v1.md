# X1 protocol v1 — 2026-10-28, exploratory development only

Authority: original specification plus the explicitly authorized X1.0 prompt.
No Stage 1–5 artifact is edited. Original H1/H2 remain historical findings.
No 2026 canonical partition may be read. No robust/minimax optimization,
random impact kernel, alpha, new market, download or fresh confirmation.

Before policy costs: freeze this config, forecast gate and training quantiles.
Origins are 00/06/12/18 UTC; training Jan29 2024–Jun30 2025 (28d warmup),
development Jul1–Dec31 2025, all 736 original eligible Stage 4 episodes.
Pilot: Jul5 00:00 (weekend), Jul31 18:00, Aug1 00:00 (weekday/month boundary).
Figure examples are those pilot origins; trace is Aug1 00:00. No cost-based selection.

V0 calls the original Stage 4 construction at arrival and reproduces its exact
28d hour-of-week medians/fallback/floor. At replans the same volume-only recipe
uses [t−28d,t); covariance and inventories are never recomputed. V1 profile uses
28 complete UTC days ending at decision-day midnight, pools only full valid
60-minute hours, divides by each hour's median positive turnover, includes zero
ratios, shrinks n/(n+50) toward one and renormalizes mean to one. An hour with no
positive turnover or invalid/missing bins is excluded; fewer than 24 full hours
per asset causes a recorded flat-profile fallback. Zero factors receive machine
epsilon before renormalization; forecast floor remains V0's past positive p1.
No 56d sensitivity or tau grid is used. V2 uses adjust=False EWMA spans5/60
on the same past28d valid turnover; ratio clipped [1/2,2], epsilon=past floor,
multiplier exp(d*exp(−k/15)), k=0 for the next bar.

Primary V2 gate: lower95% seven-day/500-draw paired daily interval for V1 minus
V2 log1p-volume squared error >0, pooled assets, with neither asset RMSLE >1%
worse. Gate uses only forecast labels, before execution scores. Failure leaves
V2 as a negative result and P3 NOT_RUN. Forecast report covers arrival horizons,
not all overlapping five-minute replan origins. Training S1 calibration uses
these same four origins/day; residual=log(max(actual,past floor)/forecast).
10/50/90 empirical factors by asset and horizon1–5/6–15/16–60; pool within asset
only if fewer1000 matured valid labels in any bucket. Calibration never uses
July–December labels. Construction checks and absolute development coverage
error<=5 percentage points at every asset/bucket/quantile are the S1 gate;
otherwise bands remain diagnostics and scenario policies NOT_RUN/QUALIFIED.

P0=original full B/V0 static, P1=B/V1 static, P2=B/V1 five-minute MPC;
P3=B/V2 MPC only if gate passes. P4=three-point inverse-volume weighted MPC
using the gated base forecast; **P4M** is its mandatory matched median-only MPC
control, isolating uncertainty curvature from median recalibration. P4−P3/P2
is a combined scenario/recalibration contrast; P4−P4M isolates weighting.
D0/D1 use diagonal of every B component, same B tau/L, V1 static/MPC.
Diagnostic TWAP uses the original fixed caps; VWAP allocates V1 proportionally,
checks fixed caps, fails explicitly rather than repairing. All arms share
original X0, cap0=.1V0, Sigma, beta, P0, monthly B, theta1, kappa.001, zero alpha,
fee5bp, halfspread1bp. No updated-cap sensitivity.

At t, only bar opens<t (available_at<=t) may enter. A filtered as-of reader
provides completed history only; policy callbacks receive volumes and validity,
never future prices/flow. Every prefix is fixed at its issue time. All decisions
are saved before score-only future reads. Fixed kernel H is time-major USDT.
Future cost=.5zf'Hff zf+zf'Hfp zp. Risk continuation uses remaining inventory,
fixed Sigma/beta. Do not sum local objectives. Full schedule cost/risk is scored
once. No clipping, cap relaxations or inventory repair. Direct OSQP uses the
original scaled objective, eps_abs/rel1e-9, polishing, max_iter100000; independent
KKT, constraints and objective checks apply. Past trades are never reset.

E1: existing frozen-family factory, exact180d window ending month−30d,
tau(5,30), ridge1, own-window L/standardization, saved only under X1.
E2=diagonal E1. Common baseline V0 temporary scorer; next-bin close path,
exact full-schedule impact, fee/spread assumptions; funding unobserved/omitted,
risk separate. No ex-post-volume cost variant is needed; realized volume is
used only for participation diagnostics after commitment. Zero-volume ratios
are undefined, positive trades in them explicitly infeasible, never filled.
Positive delta=cost(control)−cost(new), bp of original total X0. Contrasts
P1/P0, P2/P1, D1/D0, P2/D1, P1/D0, gated P3/P2, P4/base and P4/P4M;
interaction=(P1−P2)−(D0−D1). All/month/weekend/past-liquidity-tercile
summaries retain negative cases. Bootstrap calendar days, paired four episodes,
seven-day moving blocks,500 draws,seed20261027; descriptive post-search only.
Forecast losses have separate daily block intervals. Record all failures.

Public-flow coefficients are observational; modeled costs are scenario assumptions,
not fills, causal savings or an AJNT stochastic theorem. Bands are marginal,
not joint path laws. Session 2 and full random Volterra control remain future work.
