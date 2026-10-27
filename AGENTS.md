# AGENTS.md — CryptoCrossImpact

> **Purpose.** Repository-wide instructions for Codex and other coding agents working on **CryptoCrossImpact**, a self-contained **CV / academic mathematical-finance research project**. Build a defensible, reproducible study of cryptocurrency cross-impact and joint optimal execution—not a production trading platform, live trading system, or exhaustive software framework. **Accuracy before attractive results; minimal credible engineering.**
>
> **Research authority.** `CryptoCrossImpact_Research_Specification_v1_2026-10-27.md` (or its latest **explicitly approved** successor, wherever it lives in the repository) defines the experiment: mathematics, sample, source references, data contract, configurations, evaluation, hypotheses, and gates. **Read it before substantive work.** This file governs *how* to execute it; it must not silently replace the science. The historical handoff is background, not an alternative experiment specification.

## 1. Authority, authorization, autonomy

**Priority:** (1) the user's current explicit directions and approvals; (2) the latest approved research specification and documented approved amendments; (3) the current authorized execution/stage instructions, insofar as consistent with the specification; (4) this `AGENTS.md`; (5) existing repository conventions. Resolve conflicts explicitly in the session report. An ambiguous instruction does **not** authorize redesigning an estimand, opening a locked test for tuning, or weakening scientific safeguards.

- **Start of each task:** inspect `git status --short`, branch/commit if available, relevant files and prior reports; locate/read the current specification, configuration and `SPEC_CHANGELOG.md` if present. Check existing data/manifests before obtaining new files. Preserve pre-existing and uncommitted work.
- **Scope:** obey the user's actual task. If asked to implement the full approved experiment, proceed independently through specification gates **G0–G4** and complete safe, feasible branches without routine confirmation. **G5 extensions** (SOL, spot–perp, L4, new theorem, signal/stochastic-control branches) are not automatic. Merely reading these instructions does not authorize downloading data, coding, or running experiments.
- **Routine autonomy:** choose sensible file organization, implement parsers and numerics, use free/open tools, rerun small failed downloads, repair documented parsing bugs, select specified fallbacks, add focused tests, and make small performance improvements. Explain nontrivial decisions, not every edit. Do not halt the entire project because one optional source or branch fails; mark that branch `BLOCKED`/`QUALIFIED` and continue independent valid work.
- **Pause the affected operation for explicit approval** before: paying for data/services; bypassing a provider's access or usage terms; downloading an enormous optional dataset; exceeding the storage ceiling in §4; overwriting/deleting user-created data, source, branches or results; modifying instruments, causal interpretation, statistical target, test dates, hypotheses, scoring protocol or nonnegotiable baselines; abandoning required mathematical validity; initiating live trading; or making an incompatible substantial research redesign. State the choice and a recommended Y/N decision. Continue unaffected tasks where possible.
- **Research adaptations are permitted but must be honest:** minor preprocessing/solver adjustments justified by schema, numerical stability, or development-validation evidence are allowed within the specification's change rules. Log material changes in `SPEC_CHANGELOG.md` with date, old/new setting, justification, status of final-test inspection, and effect on comparability. Do not silently relabel a different analysis as the preregistered experiment.
- If a prompt starts `learning mode:`, explain the key mathematics, units, data/time alignment, code changes, and likely failure points before editing, unless the user explicitly requests immediate implementation.

## 2. Scientific boundaries — mandatory, even for a CV project

The specification is the **single source of numerical defaults**; do not copy/maintain competing hyperparameter grids here. The following invariants are deliberately repeated because errors would invalidate the result:

1. **Data identity and time.** Core: Binance **USDⓈ-M perpetual** `BTCUSDT` and `ETHUSDT`, **one-minute** futures klines; 2024-01-01–2026-06-30 UTC. Development training: **2024-01–2025-06**; validation: **2025-07–2025-12**; untouched final outcome test: **2026-01–2026-06**. An exchange, spot pair, mark/index price, contract unit, or timestamp convention is **not** interchangeable with this contract. Verify actual archived schema and timestamps before trusting it.
2. **Order-flow definition.** Signed taker **quote-notional** flow in USDT: `q = 2*taker_buy_quote_volume - total_quote_volume`. Check aggressor sign with sampled `aggTrades` where feasible. It is not L2 order-flow imbalance or parent-order flow. Same-minute price/flow regression is **conditional descriptive response**, not an actionable forecast. Never use same-minute or later flow as information available to an earlier trade decision.
3. **Economic units and lag equation.** Use the specification's past-estimated liquidity normalization `L_i`, `f_i = q_i/sqrt(L_i)` and `y_i = 1e4*sqrt(L_i)*Δlog(close_i)`. `y` is **already a return**: do not difference it again. A level propagator `G(ℓ)` contributes `G(0)` at current flow and **`G(ℓ)-G(ℓ-1)`** on lag-`ℓ` flow. Preserve USDT/basis-point/time-step factors consistently through calibration, impact cash cost, and evaluation. No raw-unit PSD/symmetry shortcut.
4. **Admissibility.** The fitted symmetric matrix components of models A/B must be **positive semidefinite in cash-consistent coordinates**. Check the discrete symmetrized impact-cost Hessian and round-trip nonnegativity, including discretization/cell conventions. Do not optimize with an unrestricted statistical response matrix (model U) or repair a failing Hessian invisibly. Report meaningful numerical failures.
5. **Matched estimation.** Compare the specified no-flow diagnostic `N0`, unconstrained diagnostic `U`, diagonal admissible `A`, and full admissible `B` on matched samples, nuisance controls and comparable development search budgets. Correlated information and order-flow endogeneity remain even after nuisance adjustment. Never claim that the estimated public-flow response is the **causal effect of our hypothetical executions**.
6. **Matched optimization.** Implement/verify **two separate mathematical objects**: (V1) relevant published Abi Jaber–Neuman–Tuschmann deterministic/Nyström examples and (V2) this project's **sell-only, hard-terminal, no-round-trip constrained QP**. Do not claim V2 alone reproduces the unrestricted stochastic Fredholm theorem. All strategies share contemporaneously available forecasts, inventories, horizon, caps, risk accounting and cost assumptions. Predicted volumes—not future realized volumes—control participation caps and start sizes.
7. **Matched policies and independent scoring.** Core baselines **T0–T4**, particularly **T3 (joint/no cross-impact, full risk covariance)** versus **T4 (joint/full cross-impact)**, must be evaluated on the same eligible episodes. **E1–E3** are the prespecified separate/stressed evaluators. **E0 (optimizer's own kernel) is a circular diagnostic, not primary evidence.** Scoring may read future observed prices and volumes *after* a schedule is generated; the policy must not. Keep hypothetical execution effects separate from observed price-path shortfall and from the optimizer's risk preference.
8. **Test-set firewall.** Develop on training and validation only. Lock model/grid, exclusions, baselines, evaluator families, risk/cap conventions and uncertainty protocol **before any outcome-based final-test scoring**. Test-period **source-integrity/QC checks are allowed**, but no test-driven model/episode selection. Once final-test results are inspected, changes are labeled **exploratory**, or use a newly reserved untouched test window. Preserve all negative months, adverse scenarios, PSD-binding cases and failed strategies.
9. **Claim discipline.** Distinguish (a) observed statistical flow–return association, (b) **model-/scenario-based** execution-cost differences, and (c) **realized causal execution improvements** (not established by public kline replay). Do not claim live savings, exact reconstruction of historical BBO/fills from klines, a new general theorem, or first-ever implementation. Fees and spread proxies are assumptions unless specifically observed; equal-notional all-taker linear fees largely cancel from schedule comparisons.

Primary mathematical reference: **Abi Jaber–Neuman–Tuschmann, “Optimal Portfolio Choice With Cross-Impact Propagators”** [spec R01](https://arxiv.org/abs/2403.10273). Important mathematical/identification precedents: **Alfonsi–Klöck–Schied** [R02](https://arxiv.org/abs/1310.4471), **Naviglio et al.** [R05](https://arxiv.org/abs/2501.17096), **Hey–Neuman–Tuschmann** [R06](https://arxiv.org/abs/2510.06879). **The full bibliography and authoritative data URLs are in specification §§17–18; do not maintain a second drifting bibliography here.**

## 3. Scientific workflow and stop/go gates

Use specification **G0–G4** as the minimum end-to-end CV project, not a new research program:

- **G0/G1 — data acquisition and quality:** source probes, exact identities/fields/UTC clocks, checksum when available, complete chronological sample or disclosed QC exclusions. Never fill an outage with invented prices, volume or trade signs.
- **G2 — estimation:** synthetic known-kernel recovery; constrained A/B versus diagnostics; eigenvalue, normalization, coefficient/memory/stability checks; lag/placebo and past-only uncertainty where required. A negligible, unstable or wrong-sign cross effect is a legitimate finding, **not a mandate to search for significance**.
- **G3 — mathematical/numerical solver:** relevant published restricted example, independent constrained-QP special cases, asset-permutation/diagonal limits, discretization convergence, cash-unit/factor-two tests, hard liquidation, caps and solver-status checks. No execution-performance claims until the relevant correctness tests pass.
- **G4 — precommitted OOS evaluation:** fixed dates/episodes; T0–T4, E1–E3, actual path + **assumed** impact/temporary/spread/fee components; H1/H2 effect sizes, month/regime tables, paired time-block uncertainty, adverse scenarios and limitations. This is **CV-complete even when cross-impact adds no benefit**.
- **G5 — optional:** only one scientifically justified extension if it passes the spec's validation/resource gates and the task authorizes it. Never postpone completion of G4 to build optional deep data, dashboards or stochastic signal infrastructure.

Use compact statuses per gate: `PASS`, `QUALIFIED`, `BLOCKED`, `INVALID` for **implementation/data correctness**; separately `SUPPORTS_HYPOTHESIS`, `DOES_NOT_SUPPORT`, or `INCONCLUSIVE` for the **scientific result**. Passing software tests never implies an economic hypothesis succeeded. Do not alter an analysis after a negative result merely to make it look favorable.

## 4. Data, local storage, provenance and permissions

- **Required download contract:** official Binance `data/futures/um/monthly/klines/{SYMBOL}/1m/{SYMBOL}-1m-{YYYY-MM}.zip`, both symbols for **2024-01 through 2026-06** (60 monthly archives total), plus published checksums where available. The full URL pattern, columns, daily fallback and QA are in specification §3.1. Check a small probe before bulk acquisition; report inaccessible dates, region/access restrictions and terms rather than circumventing them.
- **Optional data are gated:** selected Binance `aggTrades` for sign/aggregation verification; sampled `bookDepth` only as **percentage-band liquidity**, not true BBO/full L2; small **same-venue** OKX L2+trades vignettes only if public, legal, manageable and explicitly in scope. Never mix Binance flow with OKX book as a matched venue. **Do not bulk-download the ~195 GB Hyperliquid L4 archive** as part of the core.
- **One canonical physical dataset:** inventory any existing validated files; download/parse each source partition once; use efficient monthly/streaming processing; checksum/schema/row-count check; atomically write a compact canonical partition; delete **only temporary files created by the current operation**, and only after verifying recovery/reproduction. No duplicate dataset per model, split, seed, or alternate feature run. Record manifest/status so reruns resume safely.
- **Provenance minimum:** for each source/partition store provider URL or archive ID, venue, `futures/um`, symbol, quote/base units, schema/clock convention, UTC coverage, rows/QC exclusions, checksum or fingerprint, access/reuse notes, and the canonical output. For reported experiments bind run ID, source manifest IDs, fit/decision cutoffs, spec/config hash, Git revision, seed, package versions and model/evaluator IDs. Prefer small JSON/CSV manifests, not a database.
- **Resource guardrail:** process on a CPU-only MacBook Air. Target **under 8 GB RAM**, by batches/sufficient statistics rather than giant dense matrices. Aim for **well under 30 GB incremental working storage**, including caches, downloads and intermediates; warn at **25 GB**, **stop and request approval before exceeding 30 GB**. This ceiling is an operational safeguard, not a reason to silently truncate scientific dates. Measure current usage and peak temporary space before large downloads. Reuse existing storage or skip optional feeds first.
- **Security/legal:** use genuinely free/public data under their actual permitted terms; don't redistribute raw archives or restricted inputs in Git/review bundles. No API credentials in prompts, code, reports, logs, notebook outputs or Git. Use exported environment variables or ignored `.env`, and commit at most a value-free `.env.example`.

## 5. Lean implementation and verification

**Suggested layout** (adapt existing folders; do not create empty scaffolding for its own sake):

```text
CryptoCrossImpact/
├── AGENTS.md                         # this file
├── .gitignore
├── CryptoCrossImpact_Research_Specification_v1_2026-10-27.md
├── SPEC_CHANGELOG.md                 # only when a scientific choice changes
├── README.md                         # one reproducible pilot and core-run guide
├── configs/core.yaml                # numerical experiment config, versioned
├── src/cryptocrossimpact/            # data, features, kernel, cost, QP, eval
├── scripts/                          # thin executable entry points
├── tests/                            # focused numeric/data/causality fixtures
├── data/README.md                    # source/rebuild directions (tracked)
├── data/registry/                   # small manifest files (tracked)
├── data/raw/, data/canonical/, data/tmp/  # local data (ignored)
├── results/experiment_index.csv      # small index (tracked)
├── results/...                      # bulky outputs (ignored)
├── figures/                         # selected compact final figures (tracked)
├── reports/                          # short research reports and session logs
└── logs/                             # ignored
```

- One Python 3.11+ virtual environment, a simple dependency file, `pathlib`/repo-relative paths, UTC-aware timestamps, a small CLI and straightforward modules. Favor `numpy`, `pandas`/`pyarrow`, `scipy`, `cvxpy` + a **real SDP-capable backend** for kernel fitting, a QP solver such as OSQP for schedules, `matplotlib`, and `pytest`. Verify actual solver capabilities. Don't hardcode Mac-specific paths or use an external project's datasets implicitly.
- Numerical code must express **units, shapes, timing conventions and assumptions** in concise docstrings/comments, especially where a factor of 2, lag difference, bar boundary or cash-notional conversion matters. Fail loudly on wrong input identity, nonfinite values, time leaks, negative eigenvalues, infeasibility or solver nonconvergence; never quietly coerce an invalid scientific outcome into a success.
- **Small targeted tests rather than elaborate CI:** (i) one real-source schema/signed-flow/timestamp smoke test; (ii) hand-calculated flow/return/impact cash-unit fixtures; (iii) PSD/no-manipulation and analytic QP/diagonal limit cases; (iv) no-future-information and wrong-market/spot/perp rejection; (v) inventory/cap feasibility and evaluator-independence checks; (vi) one regression test for each critical bug found. Rerun impacted tests after edits; full dataset fits only when relevant. State tests **not run**, never imply success.
- Numerical tolerances must be scale-aware and justified. Verify residuals and solver return statuses; diagnose discrepancies against the published examples **without reverse-engineering a match**. Report qualified reproduction where data or discretization conventions differ. No unsupported theorem-replication claims.
- Plot results with explicit axes/units/period/model/evaluator, save small data-behind-figure tables when useful, visually inspect rendered images, and use relative paths in Markdown reports. Record failures and null results alongside successes. A small research report and six meaningful figures matter more than generic orchestration.
- **Do not build** cloud orchestration, dashboards, real-time systems, database services, exchange order routers, Docker/Kubernetes, CI/CD pipelines, deep neural nets, or comprehensive simulators solely to embellish the CV. No unbounded retries or unattended background jobs without authorization.

## 6. Git and file safety

- Inspect Git status/diff **before and after** changes. Respect the existing branch and dirty worktree. No `git reset --hard`, forced pushes, deleting branches, overwriting the user's files, or unrequested commit/push. Ask before destructive cleanup of pre-existing work. Do not mutate another research project's repo.
- Track **code, specs, approved config, tests, lightweight manifests, Markdown reports/session notes, selected modest figures and small figure-data tables**. Keep large market datasets, caches, temporary/extracted files, machine-local config, model binaries, logs, ZIPs and secrets out of Git. `.gitignore` protects untracked files only: if large/secret files were already tracked, diagnose separately and request a safe remedy, not a destructive rewrite.
- Keep the worktree coherent. Do not silently edit the research specification to fit current code; an approved scientific deviation belongs in `SPEC_CHANGELOG.md` with its scientific consequences. Never falsify commit IDs, SHA-256 checks, test passes or research results.

## 7. Mandatory, concise Codex session report

For **every Codex task/session**, including a docs-only, interrupted or blocked task, write a **new** `reports/sessions/YYYYMMDD_HHMM_<phase>_<task>_session.md`. Aim for **one screen to two pages**, with extra detail only for unusual problems; no huge terminal dumps. Include:

1. **Task and status:** UTC time, active G-stage/prompt, spec/config revisions, Git branch/commit and initial/final dirty status; implementation `PASS/QUALIFIED/BLOCKED/INVALID` and **separate scientific conclusion** if one exists.
2. **Files changed and purpose:** created/edited/deleted paths (or partition glob + count + manifest); significant functions/inputs/outputs and their units/timing.
3. **What actually ran:** significant commands, data sources/date range/row counts, config/seed, output locations and a short reproducible restart command. Never describe planned tests as executed.
4. **Checks and results:** relevant tests passed/failed/not run; model/solver diagnostics, QC exclusions, empirical estimates and limitations; source-paper discrepancies if applicable. Keep observations distinct from inferences.
5. **Deviations, resources and recovery:** decisions/change-log links, holds and causes, current safe checkpoint, approximate retained/peak additional disk usage, and precise next action.

At the end of each Codex reply, summarize **what was done, actual scientific/QA verdict, important output paths, session-report path, disk impact, and any decisions needed**. Use this log to enable the next session to resume without rereading noisy chat history. A blocked optional branch must not conceal completed valid results elsewhere.

---

**Operating principle:** *Defensible cross-impact mathematics; honest separation of observed flow, hypothetical execution and causal effects; equal information and constraints; evaluate away from the fitted model; preserve negative results; reuse free data; and implement only the engineering needed to complete a strong CV research project.*
