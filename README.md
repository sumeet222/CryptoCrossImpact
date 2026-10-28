# CryptoCrossImpact

A noncommercial academic/CV study of cryptocurrency cross-impact and joint optimal
execution. The governing experiment is
[research specification v1.0](CryptoCrossImpact_Research_Specification_v1_2026-10-27.md).
**Stages 1–5** implement data QC, development-only conditional kernel estimation,
the AJNT deterministic benchmark, a verified constrained solver, and past-only
development episodes with six matched policies, and locked January–June 2026
evaluation of modeled execution shortfall **excluding funding**. The approved
v2 protocol preserves the original funding-HOLD evidence. Stage 6 is not begun.

## Environment

Use the existing Python 3.11+ virtual environment. This run tested Python 3.14.6 on
an 8 GiB Apple Silicon Mac; exact dependencies are pinned in `requirements.txt`.
No system Python packages or optimization/ML services are needed for this stage.

```sh
.venv/bin/python --version
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python -m pytest -q
```

## Reproduce Stage 1

Run from the repository root, with direct internet access to the official public
archive and GitHub documentation. No exchange account or credentials are used.

```sh
.venv/bin/python scripts/stage01.py preflight
.venv/bin/python scripts/stage01.py pilot
.venv/bin/python -m pytest -q -m integration -k real_vendor
.venv/bin/python scripts/stage01.py acquire
.venv/bin/python scripts/stage01.py audit
.venv/bin/python scripts/stage01.py qc
.venv/bin/python -m pytest -q
```

The pilot is May 2024, October 2025 and May 2026, both symbols. Full acquisition is
30 months × 2 assets. `qc` verifies every source against canonical numeric values
and reconciles first-row returns when isolated pilot partitions gain their prior
month context. Run it after acquisition and audit to refresh the quality report.
Integration tests require actual local archives; an absent vendor corpus is
reported as skipped, never as real-source verification. A partial corpus fails the
full-inventory integration test.

Successful partitions resume from their manifest and fresh published checksums.
Changed upstream sources or modified canonical files halt the affected partition
for review. Requests retry at most three times; access restrictions and rate
limits are explicit holds. Missing/corrupt monthly files use official same-market
daily archives. Missing observations are never filled.

Resources are bounded at 25 GB warning / 30 GB stop for incremental project storage,
including installed dependencies. The six-pilot extrapolation is about 0.38 GB
canonical data plus about 0.15 GB compressed monthly sources. Processing is one
month or 200,000 tick rows at a time; the 14-day supporting audit deletes only its
own verified temporary tick archives after saving durable audit summaries.

## Data and outputs

- `configs/core.yaml`: fixed source/symbol/date/split contract and QC rules.
- `src/cryptocrossimpact/data/`: source verification, parser, canonical data, QC,
  trade-sign audit and CLI implementation.
- `data/canonical/{BTCUSDT,ETHUSDT}/YYYY-MM.parquet`: one physical corpus, ignored.
- `data/raw/`: compressed monthly sources, checksums and accessed schema/terms,
  ignored; no extracted CSV copies.
- `data/registry/`: small trackable source/run manifests and QC/audit summaries.
- [Stage 1 quality report](reports/data/stage01_data_quality.md): actual coverage,
  quality exclusions and stage verdicts.
- `reports/sessions/`: session checkpoint, test evidence and resource accounting.

Train: January 2024–June 2025; validation: July–December 2025; locked final test:
January–June 2026. Stage 1 inspects test **source integrity only**. Fields are
available at bar completion, not bar open. Stage 2 estimates liquidity units and
conditional flow/return response on development data only; no 2026 research
outcomes or trading performance are evaluated.

## Reproduce Stage 2

Stage 1 data are reused unchanged. The data reader refuses 2026 partitions before
opening them. CVXPY with CLARABEL fits economic PSD matrices; SCS provides an
independent estimator check. OSQP is a transitive package and is not used for
semidefinite estimation or an execution solver in this stage.

```sh
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
.venv/bin/python -m pytest tests/test_stage01.py tests/test_stage02_kernel.py -m 'not integration' -q
.venv/bin/python scripts/stage02.py synthetic
.venv/bin/python scripts/stage02.py all
```

The single full command runs monthly feature/statistic construction, the complete
276-candidate N0/U/A/B development comparison, validation metrics, 50 training
block refits, 50 cross-only whole-day shift refits, time/lag/lead/memory/source-QC
diagnostics and the report. Individual restart subcommands are `prepare`, `fit`,
`metrics`, `diagnostics`, `report`. No Stage 1 re-download is needed.

Do not rerun the Stage 1 integration tests during Stage 2: those open 2026 source
pilots. The command above runs the Stage 1 synthetic tests and Stage 2 synthetic
and real-**training** checks while preserving the current firewall.

- `configs/stage02_kernel.yaml`: fixed grid, features, seed and diagnostics.
- `src/cryptocrossimpact/kernel/`: causal feature timing, joint estimators,
  predictions, admissible level-kernel export and G2 checks.
- [Stage 2 research report](reports/research/stage02_kernel_estimation.md): actual
  results, mathematical conventions, limitations and Stage 3 handoff.
- `reports/research/stage02_artifacts/`: compact models, selection table, metrics,
  uncertainty/placebos, source/code provenance and estimation-only pretest lock.
- `figures/stage02/`: development-only diagnostics; underlying tables are saved.
- `results/kernel_development/`: ignored small sufficient statistics, not a
  second feature dataset or per-model source-data copy.

Selected A/B artifacts are conditional observational kernels. Their use as causal
execution kernels would be an additional structural assumption. Stage 3 independently
verifies its mathematical discretization and solver; see the report below.
Development policy construction is documented below.

## Reproduce Stage 3

All new execution inputs are synthetic. Only the supplied AJNT PDF, frozen
Stage 2 model JSON and source metadata are read; no canonical market rows, new
exchange data, kernel refits or historical episodes are needed.

```sh
.venv/bin/python -m pytest tests/test_stage03_execution.py -q
.venv/bin/python scripts/stage03.py paper
.venv/bin/python scripts/stage03.py synthetic
.venv/bin/python scripts/stage03.py models-smoke
.venv/bin/python scripts/stage03.py all
```

- `configs/stage03_execution.yaml`: original paper parameters, synthetic inputs,
  integration convention, solver and numerical grids.
- `src/cryptocrossimpact/execution/`: separate paper benchmark, immutable model
  adapter, exact exponential cash Hessian, constrained QP and verification.
- [Stage 3 mathematical report](reports/research/stage03_mathematical_solver.md):
  actual results and Stage 4 interface.
- `reports/research/stage03_artifacts/`: convergence, cash/KKT/PSD diagnostics,
  preservation checks, test evidence and run provenance.
- `figures/stage03/`: paper reproductions and clearly labeled synthetic figures.

The required zero/exponential deterministic paper cases are reproduced. Optional
fractional terminal-point figure agreement is qualified; raw collocation values
are retained. V2 uses verified exact exponential cell integration with a controlled
half-cell comparison; the convention is recorded in SPEC_CHANGELOG.md.
Paper controls are unrestricted signed rates with a finite terminal penalty;
V2 sales are nonnegative with hard liquidation and forecast caps. No stochastic
Theorem 2.8 solver or historical execution-performance claim is made.

## Reproduce Stage 4

Stage 4 reads only development observations through December 2025. It constructs
28-day past-only forecasts/covariance, monthly 365-day as-of A/B kernels and
T0/T1/T2/T3/T3B/T4 frozen sell-only policies. T3B retains B's exact self terms
and isolates its cross terms; T3 retains the separately fitted model A.

```sh
.venv/bin/python -m pytest tests/test_stage01.py tests/test_stage02_kernel.py tests/test_stage03_execution.py tests/test_stage04_policies.py -m 'not integration' -q
.venv/bin/python scripts/stage04.py smoke
.venv/bin/python scripts/stage04.py all
.venv/bin/python scripts/stage04.py policies
```

The final command verifies deterministic numerical replay against the saved
schedule hash. Restart commands are `build`, `policies`, `report`, `lock`; keep
the tested configuration and model registry together. No new dependencies or
market downloads are needed. Do not run Stage 1 integration tests during this
stage, since they inspect final-test source pilots.

- [Stage 4 report](reports/research/stage04_episode_policies.md): development
  coverage, forecast/risk QA, schedule geometry and solver/fairness diagnostics.
- `src/cryptocrossimpact/episodes.py` and `execution/policies.py`: causal episode
  inputs and six policy definitions; Stage 3 QP reused with a shared-beta option.
- `reports/research/stage04_artifacts/`, `figures/stage04/`: compact QA and plots.
- `results/stage04_development/`: ignored inputs/schedules, one common corpus.
- [Pretest protocol v1](docs/stage05_pretest_policy_evaluator_lock_v1.md) and
  `configs/stage05_pretest_lock.yaml`: hashed policy/evaluator definitions.

Implementation passes separately from the **PRETEST_LOCK_PENDING** status:
Stage 5 must verify actual funding settlement data/timestamp exclusions and
the separate E1 monthly estimator preflight before test opening/scoring.
No E0–E4 evaluator, historical shortfall/P&L comparison, or January–June 2026
outcome inspection was performed in Stage 4. Stage 5 is separately authorized.

## Reproduce Stage 5 under the approved funding-excluded amendment

The original [funding-HOLD report](reports/research/stage05_oos_evaluation.md)
and v1 lock remain preserved. The user-approved
[v2 amendment](docs/stage05_pretest_amendment_v2_funding_excluded.md) omits funding
cash flows from the estimand; funding is unobserved, not zero. No funding-event
exclusions apply. The [v2 protocol](docs/stage05_pretest_policy_evaluator_lock_v2.md)
and `configs/stage05_pretest_lock_v2.yaml` freeze all other scientific choices.
Independent E1 development fits and 166 passing tests preceded the verified
[readiness record](reports/research/stage05_v2_artifacts/pretest_ready_v2.json)
and first 2026 outcome read.

```sh
.venv/bin/python scripts/stage05_v2.py all
```

This command verifies the frozen lock and resumes completed monthly checkpoints;
it does not retune or overwrite decisions. Use `report` to render existing
results. Original clean-run steps are `prepare`, `preflight`, `freeze`, then
`all`; preflight deliberately refuses once outcomes have been opened. Do not
delete readiness or outcome-opening evidence to simulate an untouched test.

- [Stage 5 research report](reports/research/stage05_oos_exfunding_v2.md): H1/H2,
  all independent/stress worlds, uncertainty, adverse cases and robustness.
- `reports/research/stage05_v2_artifacts/`: compact model registry, paired effect
  tables, readiness/QA, provenance and resource records.
- `results/stage05_exfunding_v2/`: ignored immutable decision receipts, scores
  and monthly checkpoints; the original canonical corpus is reused once.
- `figures/stage05_v2/`: seven diagnostics, including the complete stress matrix.
- [Recovery session](reports/sessions/20261028_0406_stage05_v2_recovery_session.md):
  actual commands, checks, preservation and resource accounting.

Monthly rolling fits use only elapsed history under fixed hyperparameters.
E0 is circular; E1 is independently parameterized, E2 removes cross terms, and
E3 stresses PSD kernels and assumed costs. These are hypothetical scenario
comparisons, not realized fills or causal execution savings. Forecast caps do
not guarantee feasibility against future realized volume. Stage 6 requires a
separate instruction.

## Data attribution and permitted use

Source: **Binance Vision** ([official documentation](https://github.com/binance/binance-public-data),
[archive](https://data.binance.vision/),
[dataset terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md)).
Terms accessed 2026-10-27: CC BY-NC-SA 4.0, noncommercial research; derivative data
and analytical summaries redistributed from this dataset require Binance Vision
attribution and the same license. Raw vendor data are excluded from Git.
This project is independent and does not imply Binance endorsement. Dataset terms
are distinct from the vendor repository's software license.

Public signed flow is an observational aggregate, not a causal estimate of our
hypothetical executions. QC success does not establish either research hypothesis.
