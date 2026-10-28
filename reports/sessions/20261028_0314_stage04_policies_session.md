# Stage 4 development episodes and matched policies — session

**UTC:** 2026-10-28; final audit from 03:14. **Implementation PASS; stage
QUALIFIED / PRETEST_LOCK_PENDING. G4 OOS NOT RUN.** No economic hypothesis was
evaluated; no historical shortfall or savings comparison was conducted.
**Stage 5 was not begun; January–June 2026 canonical observations never opened.**

## Authority and preservation

Read local AGENTS.md, specification v1.0, its changelog, the exact Stage 4 prompt,
Stage 1–3 research/session reports, configs, source/model/lock/run artifacts and
relevant numerical interfaces/tests. Specification hash begins `bc5d9686`;
Stage 4 config `stage04-policies-v1` hash begins `5d936afc`; exact fingerprints
are bound in run manifests and the versioned pretest lock.

Git remains `main` at `6d5639af60649a80b9dccffeaf63d99a49d4b780`. Initial worktree
contained the prior untracked research tree; final worktree retains it and adds
Stage 4 files/docs. No tracked diff, commit, push, branch change or deletion.
All **148 protected prior files** and **60 canonical size/mtime snapshots** match.
Only previous-source change: optional `risk_multiplier_override` in the verified
QP, explicitly authorized by the Stage 4 prompt to preserve common T2 beta.
Default solver behavior is unchanged and all prior tests pass. Original source
is preserved in ignored `results/stage04_development/provenance/` with matching
initial hash. README updated; SPEC_CHANGELOG appended; original spec, Stage 2
models/lock, Stage 3 results/benchmark, source manifests and data are unchanged.

## Implementation and outputs

Created `configs/stage04_policies.yaml`, `episodes.py`, `execution/policies.py`,
`stage04.py`, `stage04_reporting.py`, thin `scripts/stage04.py`, focused tests,
research report/tables, three figures and protocol v1 under `docs/` and
`configs/stage05_pretest_lock.yaml` (SHA-256 companion). Reused the existing
Python 3.14.6 `.venv`; no dependency or market-data downloads.

Episode t0 uses the completed bar opening t0−1min, excludes current/future bars,
and freezes the open-loop schedule. Require complete valid paired 28-day UTC
history, retain diagnostic jumps/stale/verified zeros, no imputation. Forecasts
are hour-of-week medians with declared hour/day/overall fallbacks, past-positive
1st-percentile floor. Covariance is ddof1 of 40319 consecutive internal log
returns per 40320-bar window, in fractional variance per minute. Arrival P0 is
stored for later use only. Vhat is USDT/bin; X0=2% forecast total, cap=10% Vhat.
No future volume or prices enter any decision.

Main models: existing six B monthly refits reused unchanged; six missing A fits
generated through the tested fixed-family `refit_historical` API. All use exact
365-calendar-day prior targets (525600 rows), tau60/ridge1, and their own fitted
L/C. The fixed June-end A/B sensitivity covers 24 first-Monday arrivals.

T0 capped closest-uniform TWAP; T1 forecast VWAP; T2 separate A/own-variance QPs;
T3 joint A/full covariance; T4 joint B/full covariance; T3B B self terms with
each cross component zeroed. All share full-covariance reference beta, inventories,
forecasts, caps and fee/spread/kappa/theta assumptions. T4–T3 is an estimated-family
comparison; T4–T3B isolates the cross term. No baseline was relabeled. Own-model
objectives are numerical QA only; all policies report common full-covariance risk.

## What actually ran and QA results

Executed direct model preparation, Stage 4 `smoke`, `build`, `policies`, `all`,
`report`, `lock`, pytest, dependency and preservation/hash/ignore checks. The
two-day July smoke completed **8 episodes / 48 schedules**. Full July–December
2025: **736 nominal / 736 eligible / 736 complete episodes**, **4416 schedules**,
**3680 primary scalar/joint QP solves**, **zero policy failures/exclusions**.
Policy history loading reused 14 June–December development partitions (616320
source rows); A refits also read their earlier development liquidity windows
and existing sufficient statistics. No 2026 Parquet file was opened, even for
preservation checks, which used stat metadata only.

All 88320 forecast asset-bins use the fine seasonal class (minimum240 historical
observations); no fallback/floor activation. All primary horizons occupy one
UTC hour, so the prescribed forecast is constant within episodes and **T0=T1**
by construction. Retained this behavior without performance tuning. Median
initial inventories: BTC 6.895m / ETH 8.415m USDT. Jump flags occur in 112
overlapping input windows; none excluded. No policy input window has stale flags.

Maximum terminal residual **5.96e-8 USDT**, normalized physical residual
**3.01e-15**, QP stationarity **2.45e-15**, decomposition residual **1.39e-15**.
No forecast cap binds and no T0 projection adjustment is needed on this primary
sample; active-cap/infeasible cases are tested synthetically. T4–T3 mean rate L2
distance is **7.55%**; T4–T3B **8.30%**. These are schedule geometry, not savings.
All six policies share exact input hashes/beta within every episode.

Two complete numerical policy runs give identical SHA-256
`c22faff167c787d01d5ad99e385a155e0376e870f94f19d7166ad61210ddcb95`.
**116 tests passed, 0 failed, 2 integration tests deselected**, 8.64 seconds:
30 Stage 4 cases plus 86 prior-stage cases. Covers future mutation/appending,
UTC/month boundary, pre-I/O test/model rejection, common beta, diagonal/isolation
limits, fees, permutation/units, forecasting/zeros/fallbacks, constraints and
real development source smoke. The deselected tests would open 2026 source
pilots. Four existing Stage 1 parser deprecation warnings remain. No numerical
test or policy failed. `pip check` passed. Three figures were rendered and
visually inspected; source tables are retained.

## Lock, resources and recovery

Protocol v1 freezes policies, exact-cell costs, E1 separate180d/gap30d/(5,30)
family, E2 diagonal, E3 PSD stresses, contrasts, development terciles and paired
seven-day/500-replicate inference. E1 ridge1 was independently selected within
that fixed family using existing Stage 2 development losses, not copied from
T4's matrices. No E0–E4 cost scorer ran. Lock bindings and its report SHA are
verified; this is not a G4 OOS result or causal execution evidence.

**Pending before any test opening:** verify actual funding settlements/rates
or verified timestamp-only common exclusions, and validate/freeze the exact E1
implementation on development data. Then generate strict-as-of E1 fits before
each monthly scoring; later windows may contain elapsed 2026 history, so all
six artifacts are not required before January opens. No invented eight-hour
schedule or unverified funding zero is assumed. These are Stage 5 preflights,
which were not begun. No user decision is needed to close authorized Stage 4.

Full `all` run: **119.40s**, measured peak RSS **386088960 bytes** (~386MB).
This is the resumed runner using saved refits; initial A-refit peak was not
instrumented. Project storage ~1.024GB; retained Stage 4 addition **~16.6MB**,
including ~13.5MB ignored inputs/schedules. Peak additional disk estimated below
30MB; no storage ceiling approached or duplicate raw dataset retained.

Handoff: `reports/research/stage04_episode_policies.md`, compact
`stage04_artifacts/`, `figures/stage04/`, ignored `results/stage04_development/`,
and `docs/stage05_pretest_policy_evaluator_lock_v1.md` with its hashed YAML.

```sh
.venv/bin/python -m pytest tests/test_stage04_policies.py tests/test_stage03_execution.py tests/test_stage02_kernel.py tests/test_stage01.py -m 'not integration' -q
.venv/bin/python scripts/stage04.py all
```

Next safe action is separately authorized Stage 5 preflight under the pending
lock. **Stop here: final-test outcomes unopened; no historical backtest.**
