# Stage 5 policy/evaluator protocol v2 — funding excluded

The [approved amendment](stage05_pretest_amendment_v2_funding_excluded.md) is part
of this protocol. The unchanged clauses of [v1](stage05_pretest_policy_evaluator_lock_v1.md)
are incorporated by reference. No ready status is asserted by this document.
The machine lock and readiness receipt are created only after pretest evidence.

Primary sample: Binance USD-M perpetual BTCUSDT/ETHUSDT last-trade 1m, UTC,
2026-01-01 inclusive to 2026-07-01 exclusive; four arrivals/day 00/06/12/18,
724 nominal labels. Past-input and structural evaluation-bar QC only; diagnostic
jumps/stale/verified zeros retained. There are no funding-based exclusions.

T0/T1/T2/T3/T3B/T4 and numerical defaults come from the immutable Stage 4 config
and tested policy function. Monthly A/B/N0 targets are the preceding365 days;
own fit L/transforms, fixed tau60/ridge1. E1 targets [month−210d,month−30d),
two full PSD components tau5/30, independently fitted L/transforms and separately
development-selected ridge. E2 diagonalizes every E1 component. E3 jointly
scales all whole components .5/2, all tau .5/2, kappa .0005/.005, interpolates
cross rho.5, and uses DCD with D=diag(1,−1). rho0 is E2; rho1 and base repetitions
are E1 aliases, explicitly recorded rather than silently dropped. E0 is the
common optimizer-B in-model diagnostic. Every policy faces each same world.

Shortfall_ex_funding = sum z(1−Pclose/P0) + .5 vec(z)'H_G vec(z)
+ kappa sum z²/Vhat + 1e-4(fee+halfspread)sum z. P0 is last completed close;
Pclose is close of the minute beginning at t0+k. Risk preference is reported
separately, never added to cash shortfall. Report USDT and 1e4 shortfall/W bps.
Funding cashflow and all-in cash cost are null, with explicit scope flags.
Per-asset impact allocation .5 z_i(H z)_i is bookkeeping, not causal attribution.

Policies are persisted with content hashes before any post-arrival scoring
read. Filtered Parquet reads enforce explicit purpose/start/end availability;
no current-month target enters its optimizer/E1 refit. Source checksums may
read source bytes after readiness for integrity but do not expose future values
to policy code. Future-value mutation must leave decisions unchanged.

H1 compares standardized paired A/B/N0 errors on matched monthly targets, with
per-asset bps errors/R² and daily loss aggregates. H2 uses 1e4(C(T3)−C(T4))/W,
secondary T3B in place of T3; positive favors T4. Practical thresholds remain
0.5% H1 and 0.1bp E1 H2, not automatic significance or tuning criteria.
Keep all adverse worlds/months. Bootstrap:500 shared draws of seven consecutive
full-calendar-day blocks, seed20261027, 95% percentile intervals, episode-weighted
means; exclusions and all within-day/world pairs travel together. Monthly CIs
use within-month full calendars. Relative reductions are undefined when baseline
mean is nonpositive or its 95% bootstrap interval crosses zero. No negative cash
shortfall is clipped. Development terciles are inherited unchanged from v1.

After indexing primary results, run one-factor decision sensitivities theta0/2,
size.005/.01/.05, cap.05/.20, horizon30/120, fixed100k and fixedJune calibration.
Each is scored under E1/E2, avoiding the full scenario×sensitivity Cartesian
product. Close/open/OHLC and fee2/5/10,halfspread0/1/2 are separate score-only
sensitivities. All primary E1/E2/E3 worlds remain mandatory. Infeasibility and
solver failures are preserved and paired results report missing pairs explicitly.

No test-driven selection, funding collection, C/D, L2/L4, SOL, live execution
or Stage 6 work is authorized. Code/config/lineage/evidence hashes are checked
at readiness and throughout the chronological run; a marker alone cannot open
the data. Scientific failures after opening must disclose what was inspected.
