# Stage 2 kernel estimation session

**UTC:** 2026-10-27; final verification 23:38 onward. **G2 implementation: PASS.**
**Development-only scientific verdict: SUPPORTS_HYPOTHESIS** for conditional
cross-flow association; structural/causal execution impact remains unidentified.
Final 2026 H1/H2 have not been evaluated. No Stage 3 solver was begun.

## Authority, starting state and preservation

Read AGENTS.md, specification v1.0, Stage 1 code/config/reports/manifests, and the
actual longer-named Stage 2 prompt under `prompts/`. The requested short filename
was absent. The supplied paper was `references/2403.10273v2.pdf`; inspected
definitions/equation (2.7), Theorem 2.15 and Corollary 2.18, including rendered
pp.11–12. No new paper or market data was downloaded.

Git remained `main` at `6d5639af60649a80b9dccffeaf63d99a49d4b780`. Initial state
contained all prior Stage 1 code/data documentation and the user-added prompt/PDF
as untracked work. Preserved them. Final state remains uncommitted/untracked,
with Stage 2 source/config/tests/reports/figures and SPEC_CHANGELOG added;
README and requirements updated. No commits, pushes, branches or destructive
cleanup. Tracked AGENTS/spec/`gitignore`, active `.gitignore`, Stage 1 source,
canonical data, manifests and reports were not changed. Core config, spec and
Stage 1 manifest fingerprints match the prior run. Full working-code hashes
match across selected models, tests and `run_all.json`.

Installed missing free packages in the existing Python 3.14.6 `.venv`: CVXPY
1.9.3, CLARABEL 0.11.1, SCS 3.3.1 and dependencies, plus local PDF readers.
Scipy 1.18.1 supplies filtering. OSQP arrived transitively; it was not used as an
SDP or execution solver. Exact resolved versions remain in the single pinned
requirements.txt. SDP/import smoke and `pip check` passed.

## Work completed and actual results

Added `configs/stage02_kernel.yaml`, `src/cryptocrossimpact/kernel/` feature,
sufficient-statistic fit/prediction, admissibility, diagnostic and reporting
modules; `scripts/stage02.py`; and `tests/test_stage02_kernel.py`. Compact
outputs are in `reports/research/stage02_artifacts/`, selected figures in
`figures/stage02/`, and ignored small sufficient-statistic caches in
`results/kernel_development/`. No second feature dataset or rowwise predictions
were saved. Source/code/config/package IDs and cutoffs are bound in run/model
manifests. Implementation clarifications are recorded in SPEC_CHANGELOG.md.

Read **48 development symbol-months only**, January 2024–December 2025. The I/O
guard rejects 2026 partitions before opening them. Primary common sample:
**786,239 train / 264,960 validation targets**; initial history attrition 1,441
minutes. Recorded zero-volume/stale bars remain. L is the training median
positive quote turnover; y is already `1e4 sqrt(L) log-return`. Nuisances use
prior completed bars; same-bar flow is explanatory, never an earlier signal.
PSD is imposed on economic C, not heterogeneously standardized/raw coordinates.

All **276 candidates converged**: N0 six penalties; U/A/B each 15 decay families
× six penalties. No screening or failed candidate was hidden. Selected A, B and
U: **K=1, tau=60 minutes, lambda=1**; N0 lambda=1. Tie rule: within 0.1% relative
MSE, prefer fewer components, then stronger ridge. Fixed June-end models give:

| Model | BTC validation standardized MSE | ETH | Pooled |
|---|---:|---:|---:|
| N0 | 0.587852 | 0.876093 | 0.731973 |
| U | 0.377338 | 0.493184 | 0.435261 |
| A | 0.411840 | 0.518842 | 0.465341 |
| B | 0.375526 | 0.493292 | 0.434409 |

B improves pooled conditional MSE by **6.647%** over A. Minimum component
eigenvalues: A **1.835563**, B **0.770884**; B cross ratio **0.583768**;
neither selected constraint binds. Standardized design condition number is
323.685; constraint residuals are zero to reported precision. U is asymmetric,
diagnostic-only and blocked from admissible-kernel export.

Completed synthetic zero/positive/negative-cross recovery, independent direct
design/SDP checks, all-candidate eigenvalue and synthetic round-trip checks,
two train-half fits, six **development-only** past-365-day refits, monthly losses
and validation weekend/past-liquidity cuts. Cross sign persists, but magnitude
drifts. **50 seven-day bootstrap refits** give instantaneous C12 interval
**[1.017872, 1.206249]**, zero sign reversals and no binding replicates. This
conditions on selected settings/preprocessing; it is not causal uncertainty.

**50 fixed whole-day cross-only shifts** preserve own flow/return alignment.
On the 783,239-row common null mask, observed training gain is 9.163%; null gains
are near zero and shifted C12 ranges [-0.006655, 0.004238]. The 1/51 diagnostic
tail fraction is not final-test inference. Block features precede resampling,
so no fabricated block-boundary adjacency enters estimation.

Lag-only fits lose the explanatory gain; future-flow placebo fits still explain
some returns. This reinforces confounding/feedback concerns. H=30/120,
no-return-control and October 28–30 source-flag sensitivities preserve the
qualitative A/B comparison. **Caveat:** selected tau is at the grid upper limit;
G(60) retains 36.8% of G(0). Primary H=60 and its omitted H+1 boundary convention
are unchanged. Stage 1's tick aggregation audit remains QUALIFIED. Optional
forward 1-/5-minute prediction was NOT RUN, as allowed by the prompt; no alpha
claim is made. No mandatory G2 diagnostic remains incomplete.

## Executed checks and reproduction

Executed Stage 2 `prepare`, `fit`, `metrics`, `diagnostics`, `synthetic`, and a
successful full `all` run, including report/figures. **Full run: 274.2 seconds**.
Final applicable pytest command: **41 passed, 0 failed, 2 deselected**, four
existing Stage 1 parser deprecation warnings. The two deselected Stage 1
integration tests would open 2026 pilots. Stage 2's real-source checks use
training data only. One initial near-noiseless SSE assertion differed by
2.2e-15 due to sufficient-statistic cancellation; a justified 1e-12 absolute
tolerance fixed the assertion, with the estimator unchanged.

Four diagnostic figures were rendered and visually inspected; source tables,
units, development periods and the lead-placebo warning are explicit.

```sh
.venv/bin/python -m pytest tests/test_stage01.py tests/test_stage02_kernel.py -m 'not integration' -q
.venv/bin/python scripts/stage02.py synthetic
.venv/bin/python scripts/stage02.py all
```

Safe checkpoint: Stage 2 complete. Stage 3 can load `model_A.json`/`model_B.json`
through `kernel.fit.level_kernel`; units, L, coefficients, transforms and source
IDs are included. It must independently verify its cell-integrated cash Hessian,
half-cell factors, AJNT V1 and constrained V2 solver. The estimation-only pretest
lock explicitly leaves the full policy/evaluator freeze to later stages.

## Resources and final handoff

Full-run measured peak RSS **3,168,518,144 bytes** (3.17 GB), under the 8 GB target.
Project retained storage approximately **1.00 GB**, about **0.18 GB additional**
over Stage 1/user-added inputs, mainly dependencies; caches about 28 MiB.
Incremental peak is conservatively below 0.25 GB including installation/temp
overhead; this disk peak is an estimate, not a continuous measurement. No budget
or paid/access hold arose. No source data were downloaded or removed.

Handoff: `reports/research/stage02_kernel_estimation.md`, compact model/diagnostic
artifacts and estimation lock beside it, four figures, this session report and
`run_all.json`. **No decision is required to close Stage 2.** Scientific limits
remain explicitly unresolved; no causal savings or final-test success is claimed.
