# Codex Research Extension — Combined Sessions 2–3: Robust Cross-Impact, Liquidity Risk, and New OOS Validation

**Project:** `CryptoCrossImpact`  
**Prompt version:** X2+X3 / 1.0  
**Date:** 2026-10-28  
**Status:** Authorized **single Codex implementation-and-evaluation assignment**, not a completed research result.  
**Primary question:** Can **admissible cross-impact uncertainty** and **ex-ante liquidity-tail protection**, added to the verified adaptive (MPC) execution framework, reduce realized **liquidity-overload risk** without an unacceptable increase in *model-based, funding-excluded* execution shortfall?  
**Scope:** (A) implement/verify robust control, (B) run limited **development-only** model selection, **freeze** the entire updated experimental protocol, and (C) independently test the frozen candidates on a **genuinely untouched** July–September 2026 holdout **if—and only if—the holdout eligibility gate passes**.  
**Out of scope:** Random stochastic Volterra kernels and a full adapted path-dependent stochastic-control theorem (**preserved future Option 2**); live fills or causal impact identification; unbounded model search; new alpha; nonlinear/EBM impact; SOL, spot–perp, L2/L4; production engineering; automatic revisions after the holdout is opened.

> **Execution instruction:** Read `AGENTS.md` and this complete prompt from the repository root. Work autonomously through the ordered gates. **Finish all feasible parts, but STOP before opening new holdout outcomes if any required pretest gate is unmet.** Record the exact blocker rather than bypassing it. Do not claim this work has succeeded until the underlying computations and tests have run. No commit/push unless separately authorized. This assignment combines the *originally planned* robust-optimization and independent-OOS sessions; it is one staged work order, not permission to bypass their scientific separation.

---

## 0. Inputs, precedence, and preservation

1. At the beginning, inspect branch, `git status --short`, repository tree, existing changes, file sizes and data manifests. Preserve dirty work, commits, prior models, figures, schemas, tests and results; no reset, overwriting previous research artifacts, forced Git actions or deletion of user work. Use `.venv` and existing `requirements.txt`; install only missing indispensable open-source dependencies. Never put credentials in source, configs, prompts or logs.
2. Read, in this order:
   - `AGENTS.md` and `CryptoCrossImpact_Research_Specification_v1_2026-10-27.md` (scientific foundation).
   - `SPEC_CHANGELOG.md`, Stage 3 mathematical report and implementation (exact-cell Hessians, no-manipulation and past-trade state), Stage 4 policy engine, **Stage 5 v2 funding-excluded lock/report**, and their model/manifest checks.
   - **X1 complete report**, under `reports/research/` (locate by title **“X1: adaptive execution and scenario-based stochastic liquidity”**), plus `docs/extensions/x1_adaptive_liquidity_protocol_v1.md`, `configs/extension_x1_adaptive_liquidity.yaml`, existing `scripts/extension_x1.py` and `src/cryptocrossimpact/` X1 modules. Use repository discovery rather than inventing paths.
   - `references/2403.10273v2.pdf` for AJNT notation. If present, read `CryptoCrossImpact_Research_Extensions_Literature_Survey_v1_2026-10-28.md` for literature context; absence is not a blocker. Main robust-control context: **Neuman–Stockinger–Zhang, *An Offline Learning Approach to Propagator Models*, arXiv:2309.02994**, and **Muhle-Karbe–Tuschmann, *Trading With Uncertainty About Signals and Price Impact*, SSRN 6275479**. These references motivate—not mathematically certify—the particular finite-scenario control below.
3. Do not change or re-score original Stage 1–5 numerical tables, Stage 5 v1/v2 protocols, original H1/H2 verdicts, X1 artifacts, or earlier project hypotheses. Create a distinct, versioned namespace, e.g. `docs/extensions/x2x3_robust_liquidity_protocol_v1.md`, `configs/extension_x2x3.yaml`, `src/cryptocrossimpact/robust/`, `scripts/extension_x2x3.py`, `results/extension_x2x3/`, `reports/research/extension_x2x3_*.md`, `figures/extension_x2x3/`, `tests/test_extension_x2x3.py`. Only create needed paths; reuse existing modules instead of copying entire data tables.
4. Source terms: **free and permitted data only**. Cite the source and retain the existing Binance Vision noncommercial/data-attribution caveats. Keep vendor ZIPs, canonical Parquet, large schedule arrays and caches out of Git. Respect `AGENTS.md`'s total storage limit; inventory storage before downloading. No cloud/L2 paid feed is mandatory.
5. **Evidence discipline:** X1 July–December 2025 results were exploratory and the original January–June 2026 OOS results have already been inspected. Thus neither is a *new* confirmation. A fresh holdout may be established only from genuinely unseen outcomes, chosen and locked before inspecting them. No favorable exploratory re-ranking, hindsight exclusions, or false “independent test” labels.

### Frozen motivating findings (historical facts, not new results)

- Original Stage 5: full-matrix B improved **contemporaneous explanatory MSE by 7.55%**, but its primary E1 modeled execution shortfall advantage was only **+0.02081 bp**, 95% CI **[−0.02667, +0.07280]**; the gain did not meet the predeclared practical benchmark. This never identified causal own-trade impact.
- X1 development: V1 minute-of-hour volume forecast improved V0 modestly. V2 recent-activity forecast did **not** pass its gate. Five-minute state-correct MPC was numerically valid, but full-B adaptive P2−static P1 E1 gain was **+0.00438 bp** (CI crosses zero). The scenario-weighted P4 gain was inconclusive; cross-impact did not improve the *incremental adaptation* effect.
- X1 liquidity warning: adaptive P2 exceeded **10% of realized minute turnover in ~4.89%** of positive-volume asset-minute cells, occasionally exceeded **100%**, and placed positive hypothetical orders in **36 zero-volume asset-minute cells**. X1's highest finite participation ratio was **375×** minute turnover. These are serious **hypothetical-fill feasibility failures**, not evidence of an execution strategy using future liquidity.
- **Do not fit complexity simply to rescue earlier average-cost performance.** New primary target is improvement in prospective decision-making under liquidity uncertainty, evaluated with independently observed post-decision data only for *scoring*.

---

## 1. Scientific hypotheses and comparator hierarchy

Keep distinct hypotheses, tested separately:

- **H-L (liquidity-risk primary):** Relative to the identical X1 **full-B/V1/5-minute MPC** policy P2, does a **past-only liquidity-tail-aware MPC** reduce the *out-of-sample realized excess-participation fraction* while preserving hard ex-ante cap/inventory feasibility? Report magnitude and day-clustered uncertainty, including all observed zero-volume events.
- **H-G (robust impact):** Does a **PSD-preserving finite-set worst-case impact optimizer** reduce policy regret/tail modeled cost under independent E1/E2/stress evaluators compared with nominal P2? It may increase mean shortfall; report the tradeoff rather than only a favored world.
- **H-GL (combined):** Does using both enhancements outperform using liquidity protection alone on the declared primary liquidity metric, *without worsening common-evaluator shortfall beyond a precommitted tolerance*? A combined policy need not win.
- **H-cross (controlled cross term):** At matched forecasts, uncertainty sets, penalty strength, horizon and risk, does full-matrix B provide incremental value relative to **B with the same diagonal self-impact matrices and all cross entries zero**? Do not confuse this with independently fitted A, which also changes self coefficients.

**No hypothesized positive result is required for project completion.** A rigorously demonstrated inability to control realized-liquidity risk from 1-minute public volume alone is a valuable negative conclusion.

### Fixed core policies

| ID | Policy | Impact uncertainty | Liquidity-risk protection | Adaptive information |
|---|---|---|---|---|
| **N** | X1 P2: full-B/V1 MPC (reproduce exactly) | Nominal fitted B | None | 5-minute replans |
| **G** | Robust-impact MPC | Finite admissible kernel set | None | Same |
| **L** | Liquidity-tail MPC | Nominal fitted B | Prespecified tail/CVaR penalty | Same |
| **GL** | Combined impact+liquidity MPC | Same finite kernel set as G | Same tail penalty as L | Same |
| **GL-D** | Diagonal-control version of GL | Each scenario's cross elements zero; same self entries | Same as GL | Same |
| **D** | X1 matched diagonal D1 | Nominal B with cross entries zero | None | Same |

Retain X1 P0 (static full-B/V0), P1 (static full-B/V1), P4 (scenario-weighted MPC) and capped TWAP as **background/context** if already reproducibly available, but do not require a full Cartesian × every prior policy or relabel them. Every primary policy starts with **the same asset-by-asset inventory, initially frozen risk coefficient, covariance, reference price, initial allowed cap schedule, fee/spread assumptions, period and information cutoff**. Implement **G,L,GL,GL-D** through the verified X1 five-minute MPC state engine, not by pretending all 60 minutes are known initially.

---

## 2. Development period and genuinely new held-out period

### 2.1 Development-only model fitting and policy selection

- Keep **training/scenario calibration** grounded in 2024-01 through 2025-06 and X1 development 2025-07 through 2025-12. Those months are already used for model-selection research, so label new experiments **exploratory**.
- Previously inspected 2026-01 through 2026-06 may be incorporated **only** as explicitly disclosed additional pre-holdout development history for fixed-window as-of fits. Do not advertise revised experiments on those same six months as new confirmation. Select all robust family/penalty choices using **development** results, not July–September test data.
- Primary development episodes are the previously locked **736 arrival times**, 00/06/12/18 UTC on every day of July–December 2025; 60-minute execution, BTC/ETH perpetuals, 1-minute bar data, five-minute replans. Reuse original source/episode definition and flagged records, never choose events based on realized outcomes.
- It is permitted to run **small development pilots** first, then a full development comparison, and make one transparent simplicity decision **before** new holdout access. After the freeze, no choice may use July–September outcomes.

### 2.2 Proposed fresh holdout: 2026-07-01 through 2026-09-30 UTC

**Predeclared target period:** 2026-07-01 00:00 UTC through 2026-09-30 23:59 UTC, **conditional** on the following explicit holdout eligibility gate:

1. Inspect local run registries, research reports, saved metrics, exploratory notebooks and repo metadata **without opening July–September price/volume/response outcomes**. Confirm that no July–September 2026 performance metrics, realized-participation diagnostics, execution evaluations or related model selection from this project were previously inspected. Merely knowing the calendar availability or archive filenames is fine; a vendor QC/missingness check after freezing is not model performance inspection.
2. Save a short `holdout_eligibility.json` stating dates, relevant previous artifacts, evidence of noninspection, and `ELIGIBLE`, `INELIGIBLE`, or `UNKNOWN`. **Do not infer eligibility just from the absence of a file**; if materially uncertain, stop the confirmatory branch and ask for a genuinely untouched period. Continue to finish all development outputs.
3. Before **reading any July–September canonical price/volume values**, complete and SHA-256 freeze: model/config, tuning decision and tie rules, solver, scenario construction, scoring code, QC/exclusion rule, all baselines, all planned contrasts, bootstrap unit and seed, and thresholds. Verify test results and make an immutable `PRETEST_READY_X2X3` manifest referencing code/config/spec/data-source identities and git/working-file hashes. No manually written ready flag can bypass checks.
4. **Only then**, if eligible, acquire the six needed **official Binance futures/um monthly 1-minute kline archives** (two symbols × July/August/September 2026) from the established Stage 1 URL pattern, plus `.CHECKSUM` files where supplied. No new `aggTrades` required. Check source terms, HTTP access, SHA/ZIP CRC, schema, timestamp units, pair alignment, coverage and existing Stage 1 QC contract. Only acquire/convert one canonical partition per symbol-month, without data duplication. If an archive is unavailable or disk/resource limits would be breached, stop the new OOS branch; do not silently change sample dates.
5. All outcome reading must be **behind a programmatic ready-lock gate**, and occur only in the scoring phase, **after immutable policy commitments**. Month-specific as-of fits may include elapsed July/August history when appropriate (e.g. August model fitted at August start), but **may never use that month's future**. Development choices never revise after any July–September outcome is observed.
6. This is a **short three-month holdout**. Use predeclared episode starts (four/day; nominal **368 episodes** for 92 days) and disclose uncertainty/limited power. Do not combine it with earlier inspected periods and present one giant “fresh OOS” interval.

**Important distinction:** It is acceptable for the model, as of September 1, to learn from prices/volumes from July–August already in the past, because the algorithm is frozen and walks forward. It is **not** acceptable to change tuning, feature definitions, baselines or score thresholds after inspecting July results.

### 2.3 No-lookahead invariants

- At arrival `t0`, latest available market bar opens `t0-1min`. At replan `t0+5min`, latest bar opens `t0+4min`. Freeze the next five-minute trade prefix **before** revealing any observations in that prefix. Preserve all already executed sale bins in each scenario's conditional impact state.
- A parent order is fixed at `t0`: `X0_i = 0.02 × sum_{k=0}^{59} V0_{i,k}(t0)` quote USDT, based only on the **original V0 forecast**. The initial matching cap is `0.10 × V0_i,k(t0)`, fixed across N,G,L,GL,GL-D,D and all replans. **Do not change nominal inventory or redefine a baseline's hard constraints to manufacture an advantage.** Hard terminal liquidation remains the *planned* control constraint.
- Core known inputs at arrival: full past-only monthly B, reference liquidity units, trailing-28d V1, frozen Stage 4 risk covariance/beta, `kappa=.001`, `theta=1`, zero alpha, fee 5 bp and half-spread 1 bp **assumptions**, funding excluded. A permitted five-minute update may revise the forecast and uncertainty scenarios using completed information only; it must not revise the already fixed parent, covariance/risk scale, or kernel during an episode in the core comparison.
- Recorded future prices and realized volume may be read only **after** the relevant committed decision; in the scorer they are **observed unaffected-path and overload diagnostics**, not an oracle about future liquidity. No centered windows or ex-post episode eligibility filter based on returns, liquidity states or performance.

---

## 3. Finite-scenario robust impact model (G and GL)

Use the **already fitted, symmetrically cash-scaled** PSD matrix kernels. Maintain fixed asset order and fitted `L` with each kernel, or explicitly use the verified congruence map to compare matrices in common physical USDT coordinates. Never mix numerical `C` across differing `L`. The reference estimator is a reduced-form public-flow regression, **not identified structural own-trade impact**.

For a frozen as-of origin, let the nominal kernel be

\[
G_0(t,s)=\mathbf1_{s\le t}\sum_a C_a e^{-(t-s)/\tau_a},\qquad C_a=C_a^\top\succeq0.
\]

### 3.1 Small, past-only kernel ambiguity family

- Start with **past-only** admissible alternatives reflecting *different shapes/cross structures*, not only scalar amplitude multiples: nominal full B; diagonal of B; weak-cross PSD interpolation `0.5 C + 0.5 diag(C)`; PSD-certified opposite-sign `D C D`, `D=diag(1,-1)`; and an alternative **past-fitted** or development-precommitted decay shape, if available without a new hyperparameter search. Use an alternative source-history fit with independently verified `L`/units when available. Optional amplitude stresses (`0.5×`, `2×` **entire** PSD matrices) are **evaluation worlds** first, not mandatory extra policies.
- At most **5 representative nonduplicate kernel scenarios** for the policy optimizer by default (6 only if a justified past-data estimator is available); retain scenario identities and provenance. Every component must be PSD; check the **exact-cell joint Hessian** in cash units. A negative cross coefficient is allowed when the complete matrix is PSD; never manipulate isolated off-diagonal entries in a way that violates admissibility.
- **Dominance check:** A set comprising only scalar multiples of one PSD kernel can make worst-case optimization trivially select the largest one. Report if one scenario is always active or PSD-dominates others on the feasible region. Such a result is a legitimate negative finding—**do not post-hoc search more kernels until robust policies look different**. Use the predeclared structural alternatives above first.
- Fit/scale/choose candidate scenarios from historical information available by each origin. Avoid adding a general random `G(t,s,\omega)` or invoking AJNT's deterministic-kernel theorem as justification for a **random** kernel. The finite set is a deterministic ambiguity set **at each decision time**.

### 3.2 Convex robust optimizer and carried past impact

For remaining sale vector `z_f`, committed past vector `z_p` and scenario `g`, compute the **future-controllable part** of the exact-cell quadratic impact cost:

\[
C_g^{\rm remain}(z_f\mid z_p)=\tfrac12z_f^\top H_{ff}^{(g)}z_f+z_f^\top H_{fp}^{(g)}z_p.
\]

The historically **sunk past-only** `\tfrac12 z_p^\top H_{pp}^{(g)}z_p` must not influence the active worst-case scenario through an irrelevant constant. Include every `H_fp` cross term; do **not reset transient impact at replans**. For conditional receding-horizon decisions, use an epigraph variable `t_G` satisfying

\[
t_G\ge C_g^{\rm remain}(z_f\mid z_p)\quad\text{for all }g\in\mathcal G_t.
\]

In **G**, minimize `t_G + nominal temporary cost + common remaining-inventory risk + fixed linear fee/spread` under identical nonnegative sale, cap and hard-terminal constraints. In GL add the liquidity-tail preference in §4. Do not add scenario-dependent constants for already executed trades to the epigraph. Every `H_ff` must be PSD, making the epigraph a valid convex quadratic constraint; use a CVXPY conic-capable installed solver (e.g. CLARABEL), not OSQP incorrectly applied to a QCQP. Verify equality with the existing nominal X1 QP for a singleton nominal set to numerical tolerance.

For numerical stability, use the existing Stage 3/X1 variable scaling. Verify objective decomposition independently by evaluating the **complete** exact-cell cost of the final 60-minute schedule against each evaluator. **Never sum 12 local MPC objectives** to obtain realized modeled cost.

---

## 4. Stochastic-liquidity approximation and tail protection (L and GL)

**This remains Option 1: forecast scenarios + adaptive constrained optimization. It is not a full stochastic Volterra policy theorem.** The issue to fix is *not merely* average volume error but the tail of insufficient tradable turnover relative to planned sales.

### 4.1 Coherent, past-only joint volume scenarios

- Reuse X1 **V1** as the nominal minute-level volume predictor; X1 V2 is *not* automatically promoted, since it failed its development gate. Retain X1's independently calibrated S1 quantile bands as diagnostics/initial checks but **do not assume marginal 10/50/90 factors are a coherent joint 60-minute path distribution**.
- Build a **small fixed bank of joint BTC/ETH path scenarios**, using time-aligned complete **historical** 60-minute turnover profiles/residuals sampled from the trailing 28 complete days at matching hour-of-day when possible. Use the same past historical day/hour for BTC and ETH to preserve their observed joint liquidity dependence; align the 60 minute positions and shrink/scale profiles by the *currently known* V1 forecast. For 5-minute replans use the latest past-only updated V1 and the same fixed, predetermined scenario-construction rule; future realized turnover is never a scenario input.
- For reproducibility, select **12 historical paths per episode/replan** with a fixed deterministic ranking/sampling key (date/seed); use fewer with an explicit minimum-support gate, never padding by secretly reading future days. Preserve source timestamps, training cutoff, scenario weights and diagnostic quantile coverage. Use no future-generation learned from the held-out period. Avoid implausible fabricated independence across minutes; perfect predictive joint path calibration is not claimed.
- Observed training-hour volume zeros remain **zero** in capacity scenarios; **never replace zeros with positive volume simply to make the tail-risk score convenient**. Only nominal *temporary-cost denominators* use the previously approved positive forecast floor.

### 4.2 A convex shortfall-risk penalty, not a clairvoyant cap

For a future candidate planned schedule `z_f`, joint historical scenario `s` with forecasted capacity path `V^{(s)}` and **fixed reference participation** `p=0.10`, define the nonnegative *fraction of remaining parent notional exceeding scenario participation capacity*, with a consistent denominator `W=sum_i X0_i`:

\[
e_s(z_f)=\frac1W\sum_{(i,k)\in\rm future}\left(z_{i,k}-0.10 V^{(s)}_{i,k}\right)_+.
\]

The primary risk term is **CVaR at 90% across the fixed joint-path scenario bank**:

\[
\operatorname{CVaR}_{.90}(e) =\min_{a\in\mathbb R}\left[a+\frac1{(1-.90)S}\sum_{s=1}^S(e_s-a)_+\right].
\]

Add the dimensionally explicit *preference* term

\[
C_{\rm liq-risk}=\frac{W}{10^4}\,\lambda_{\rm liq}\,\operatorname{CVaR}_{.90}(e),
\qquad\lambda_{\rm liq}\in\{0,25,100\}\;\text{bps per unit overload fraction}.
\]

Here `e=0.05` and `lambda_liq=100` correspond to **5 bp of parent notional** in *preference units*. This is a tunable risk aversion, **not a fee or a measured exchange cost**. Select at most **one** nonzero lambda using development results and the fixed criterion in §5; keep `lambda=0` as ablation. Implement CVaR with small convex epigraph/positive-part variables; check units, sign, weights and monotonicity. The hard feasible set **remains the shared original V0-based cap and full 60-minute terminal inventory**. In particular, the scenario paths are **not** mistaken for exchange-provided firm fills and cannot guarantee future liquidity.

**For L:** minimize nominal `C_G^{remain}(B)` + nominal V1 temporary + common risk + this CVaR preference.  
**For GL:** replace nominal impact with `t_G` in §3 and add exactly the *same* CVaR preference.  
**For G:** no liquidity CVaR.  
**For N:** neither robustness term.  
**For GL-D:** diagonalized scenario set, otherwise identical to GL.

### 4.3 Optional *separate* incomplete-fill stress test (not a new strategy policy)

If inexpensive, implement a **mechanical ex-post capacity-constrained execution evaluator**, independent of the policies: at each minute allow at most `p_real × recorded realized quote turnover` in the same asset, for `p_real∈{.05,.10,.20}`; carry unexecuted planned amounts to subsequent bins using a predetermined non-clairvoyant queue rule; do **not** substitute nonexistent fills for the rest. At the horizon report `executed_fraction`, `residual_notional`, affected days, and a separate **risk/mark-to-market diagnostic** for residual inventory. This is a *volume-allocation stress proxy* only, **not** a simulated market-order fill or a counterfactual order-book path, and must **never** enter initial policy decisions. Do not mix partially executed policies in the original hard-full-liquidation shortfall table. Avoid constructing a realistic matching engine; if the extra evaluator materially increases work, skip it and retain the required overload diagnostics.

**No policy guarantees feasible real fills when the market has zero turnover.** This is a feature of the research finding, not an error to conceal.

---

## 5. Development execution and predeclared simple selection

First run mathematical/unit and synthetic-recovery checks **without historical outcomes**. Then compare all six fixed core policies on the **same 736 development episodes** and the same independent E1/E2 evaluation rules as X1, including ex-funding shortfall and liquidity diagnostics. Do not use E0 self-score for a success claim.

**Predeclare decision rule before computing the first new development costs:**

1. Primary object for selecting `lambda_liq` is **mean realized overload fraction** (definition §7), paired against N. Choose the **smallest** nonzero lambda among {25,100} delivering at least **10% relative reduction** on development **without increasing** independently scored E1 mean shortfall by more than **0.10 bp**. The numbers are CV-project complexity/practicality thresholds, not universal significance claims. If neither qualifies, choose **no liquidity-protection enhancement** as the core continuation and still report L/GL as negative exploratory outcomes.
2. G uses the prespecified ambiguity family, with **no grid over penalty weights**. GL uses the same family and the selected lambda; no favorable scenario deletion. If all kernel ambiguity scenarios are redundant/dominated, note that G is not a meaningful change and prefer N/L.
3. Keep **one** selected candidate for new holdout against N, plus the fixed G/L/GL/GL-D ablations if computationally reasonable. Do **not** search dozens of kernel/scenario families by E1 profit and then claim out-of-sample validation.
4. Do **not** change liquidity-scenario bank size (12), tail level (90%), participation reference (10%), alpha (0), replan cadence (5min), hard horizon (60min), or source QC after inspecting results. If a locked choice fails preflight, stop the affected branch rather than silently replacing the scientific problem.
5. Save a compact `development_selection.json` with all tested variants/negative results, chosen lambda, full metric/tolerance basis, hashes and a **dated freeze declaration** before any July–September outcome access.

Do not treat a lower robust *training objective* as performance. Report for each policy: relevant active worst-case kernels, scenario dominance, average and worst-case modeled cost, estimated overload preference, realized overload risk, and covariance risk separately.

---

## 6. Genuine OOS execution: only after all gates pass

Before the first new holdout source-value read, perform **two distinct preflight gates**:

- **Mathematical/engineering gate:** original X1 parity; singleton robust → X1; zero lambda → nominal; diagonal robust → diagonal reference; PSD cash Hessians; permutation and cash-unit consistency; shifted/mutated future-bar data do not affect earlier trade decisions; robust epigraph and CVaR checks; zero-volume handling; finite termination; test of completed-prefix historical memory and correct full-cost scoring; time-respecting 365d as-of refits and E1 as-of evaluator; critical test failures halt new OOS access.
- **Protocol/data gate:** new holdout eligibility; source terms and resource budget; all development analyses and candidate selection finished; exact locked protocol plus code/config/run checksum; **no new outcome metrics read**; score runner must verify `PRETEST_READY_X2X3`, not merely trust a text flag.

Then perform the Jul–Sep 2026 experiment (if eligible), with original instrument/time/episode semantics, as-of monthly fitting, fixed policy family/criteria, five-minute adaptive updates and post-commit scoring. Respect the operational ordering: build a prefix using only completed bars; commit/persist it; reveal next observed bar for future decisions; score only after the schedule is frozen. If you instead choose to precompute a complete historical tape for efficient replay, enforce an **API-level causal filtration** which forbids any policy call from accessing samples newer than its current replan clock. Tests must explicitly mutate future rows and confirm past decisions remain identical.

For independence of evaluation models, keep **E1** defined as an alternative 180-day kernel fit ending at least 30 days before the evaluated month, with the fixed `(5,30)` decay family and historic fitting rules. **E2** is E1 diagonal without cross terms; predeclared E3 stresses from Stage 5 remain secondary evaluator worlds. All evaluation worlds are fixed identically across policy arms and do not receive privileged policy inputs. Funding continues to be **excluded** under the approved Stage 5 v2 amendment, with that exclusion in every headline and units. Actual exchange fees/spreads/BBO/fills remain unobserved. No E1/evaluator retuning by July–September scores.

If no valid fresh holdout exists or archive access fails: **finish the development result and an explicit `OOS_HOLD` report**, plus the tested holdout-capable code. **Do not** backfill confirmatory results from the already inspected January–June 2026 sample or open a different period without a new versioned precommit.

---

## 7. Primary metrics, uncertainty, and interpretation

**Required paired metrics**, each reported overall, by calendar month, by weekend/weekday and by ex-ante past-liquidity regimes (thresholds fixed on development data):

1. **Realized excess-participation fraction** (liquidity-risk primary):

   \[
   O_{\rm realized}(z)=\frac{\sum_{i,k}\max(z_{i,k}-.10\,V^{\rm realized}_{i,k},0)}{\sum_i X_{i,0}}.
   \]

   Here `Vrealized` is the **observed minute USDT turnover only in the scorer**. It may be zero (then the excess equals the planned sale). Report mean, median, p90/p95, worst day, `O=0` rate and mean/CI difference `O(N)-O(L/GL)`. The metric is an **overload diagnostic**, not actual unfilled volume nor a causal fill model.
2. **Participation incidents:** Number/share of positive-volume **asset-minute** cells exceeding 10%, 20%, 100% realized participation; number of positive-sale/zero-volume cells and number of affected episodes. Always distinguish “undefined ratio at zero realized volume” from zero violation. Report largest finite ratio and any >100% extremes, never hide them behind p99 alone.
3. **Independent model-based shortfall excluding funding**, per original Stage 5 v2 and X1: `C_path + C_transient(E) + C_temporary(E) + assumed fee + assumed halfspread`, in USDT and bps per total parent W. Separate **ex-ante inventory risk preference** from paid cash cost. Primary paired contrasts `C_E(N)-C_E(G/L/GL)` and `C_E(GL-D)-C_E(GL)`; positive means new policy lower assumed cost. Report E1, E2, and all predeclared stress evaluators, not only a favorable one.
4. **Tail decision risk:** per-episode worst-case cost across the **independent** E1/E2/E3 evaluation worlds, p95 of pairwise cost disadvantage, mean and max regret to the ex-post best of the *fixed* policies in each world, and fraction of episodes each robust arm loses to N. Ex-post “best” is descriptive only; no strategy uses it as an input.
5. **Feasibility/solver:** Original forecast-cap violations, terminal residual, sell-only status, MPC replan KKT/dual/epigraph violation, number of infeasible episodes, mean/peak solver time/RSS, and participation zeros. Keep adverse, incomplete or failed cases in outcome-status tables; do not substitute a zero cost for a failure.
6. **Cost versus liquidity-risk tradeoff:** Report a table/plot of each policy's *paired* `ΔO_realized` and `ΔC_E1 bp` with uncertainty, not a post-hoc single combined score. A predeclared practical-interest hurdle is **≥10% relative mean overload reduction vs N** with **≤0.10 bp increase in mean E1 modeled shortfall**; report interval uncertainty and whether the target is met. This is a heuristic interest threshold, not proof of superior executable trading.

**Statistical unit:** Calendar day; the four intraday execution windows share shocks. Use **paired seven-consecutive-day moving-block bootstrap**, 500 draws, seed `20261027`, with **whole-day policy/evaluator tuples** carried together. Preserve missing/excluded days and report CIs for paired means and the relative overload reduction (flag zero/near-zero denominators). Report full monthly effects and sample counts; avoid IID minute-level confidence intervals or claiming independent confidence from repeated model stress worlds. Treat the 3-month OOS study as potentially low-powered and do not tune from its uncertainty bands.

**Decision labels:** `ROBUST_GAIN_SUPPORTED`, `TRADEOFF_OR_MIXED`, `NO_PRACTICAL_GAIN`, `INCONCLUSIVE`, `OOS_HOLD`. Use measurements, CIs, time dependence and feasibility—not a preferred storyline. Any new holdout analysis after the initial registered comparison is **exploratory**, not a rerun of a pristine test.

---

## 8. Verification and computational discipline

Mandatory **focused tests** (add no unnecessary enterprise framework):

- Load existing X1 and Stage 2 models without changing hashes. Reproduce at least **three fixed 2025 X1 P2** episodes and their costs exactly up to numerical solver tolerance.
- For robust single-kernel singleton / `lambda_liq=0`, reproduce the X1 nominal conditional optimal schedule, including committed history. For GL-D with no cross-impact (and matching scenario self terms), reproduce diagonal numerical special cases. A synthetic negative cross coefficient is acceptable if the full matrix is PSD; indefinite matrices **must be rejected**.
- Validate each exact-cell Hessian in cash USDT, symmetry/PSD, `10^-4`, `sqrt(L)`, same-cell and cross-time factors. Check independent finite differences of conditional past/future impact gradients. A 5-minute replan must carry past trades; forgetting `H_fp z_p` must intentionally fail a fixture. No hidden projection of an indefinite Hessian.
- CVaR epigraph matches hand-calculated 2- or 3-scenario examples; `O(z)` is nonnegative/monotone in sale size at fixed volume; correctly handles zero-realized-volume without divide by zero. All robust/scenario inputs are past-origin only.
- Causal mutation tests at arrival and each replan: replace future volume, return and cross-flow values; committed/past decisions are byte-identical or agree at tight numerical tolerance. The final-test reader requires ready-lock authorization. Compare full-triangular independent cash scoring with schedule decomposition.
- Robust models are solved with a QCQP-capable solver, not OSQP-only. Independent solver or small enumerated quadratic check for a synthetic case; check feasibility, KKT/duality/epigraph gaps. Numerical tolerance must be expressed relative to economic scale, not a default that underflows tiny impact cash values.
- Verify that 2-leg initial inventory, frozen beta/Sigma, caps and common cost evaluator are identical across primary arms. Model U never enters execution. No future realized volume enters constraints or construction of liquidity scenarios.
- Test all relevant as-of origins and archive UTC milliseconds; no accidental `2026-07+` source read before the ready-lock. Preserve prior protected hash checks without repeatedly rehashing enormous raw archives.

Prefer **CVXPY+CLARABEL/OSQP where appropriate**, existing NumPy/Pandas/SciPy/Parquet, one Python package and thin script(s). A 60-min horizon × 2 assets × at most 12 paths × 5 kernel scenarios is modest on CPU, but repeated QCQPs may be expensive. Pilot on a handful of 2025 episodes before full dev/OOS. Avoid dense 500k-row refits within every 5-minute replan; reuse past-fitted matrices and cache kernel-specific 60×60 cell blocks. Process data by month, retain one canonical vendor dataset, and keep only compact run tables and selected illustrative schedules (unless reusable schedule caching is necessary). Stay below existing `AGENTS.md` storage/RAM rules; do **not** launch unbounded parallel jobs.

If runtime is materially disproportionate, simplify only **within predeclared bounds**—e.g. reduce *evaluation* diagnostics after recording the reason, not policy class, holdout definition or scenario weights after seeing outcomes. An abort/hold is preferable to a scientifically silent change. Persist idempotent checkpoints; a resumed run must not duplicate episodes or refit on future data.

---

## 9. Required final outputs and stop conditions

Produce a **development report** even if the holdout is blocked; if OOS executes, produce a separate **new-holdout report**. Recommended deliverables:

1. `docs/extensions/x2x3_robust_liquidity_protocol_v1.md` — all exact math, estimator/scenario construction, frozen variants, dates, data rights, causal information, normalization, thresholds, and limitations. `docs/extensions/x2x3_PRETEST_READY_v1.md` (and hash/JSON manifest) **only after tests, frozen selection and eligibility pass**. `SPEC_CHANGELOG.md` updated only for the new extension and with original documents unchanged.
2. `configs/extension_x2x3.yaml` — minimal explicit parameters, seed, past cutoffs, developer/holdout boundaries, kernel ambiguity set, 12-path bank, CVaR alpha .90, `lambda` candidates, scoring/evaluator grid, fixed baselines and report paths. No dynamic selection from final-test metrics.
3. Source + small tests: robust impact and liquidity-risk objectives, state-correct receding-horizon interface, scenario builder, evaluation controls and a thin `scripts/extension_x2x3.py` with `preflight`, `synthetic`, `development`, `freeze`, `holdout`, `report`, `all` commands. **`holdout` must refuse execution without valid ready lock**, and `all` must stop at a gate when necessary.
4. Data provenance: new archive manifest/checksums and QC for Jul–Sep only if eligible, with strict as-of read logs; one canonical partition set (no duplicated datasets).
5. Results/artifacts: `development_policy_comparison.csv`, `development_selection.json`, `kernel_ambiguity_audit.csv`, `liquidity_scenario_qa.csv`, `overload_diagnostics.csv`, and, if holdout runs, `holdout_policy_comparison.csv`, `primary_pairwise_contrasts.csv`, `holdout_monthly_regime.csv`, `independent_scenario_stress.csv`, `holdout_gate_audit.json`, `run_manifest.json`, and compact figure data.
6. Visuals: kernel ambiguity/active worst-case scenarios; forecast volume scenario paths vs **posthoc** observed (observed overlays not used for actions); paired liquidity overload/cost tradeoff; realized participation tails/zero-volume events; selected actual committed MPC paths with historical impact state. Render and inspect actual PNGs for clipping/incorrect labels. Use relative paths in Markdown.
7. A **substantive concise scientific closeout**: test N/G/L/GL/GL-D/D, all actual differences + CIs, event counts, alternate-world costs, failure status, whether the predeclared practical target held, and explicit limitations of model-based ex-funding and noncausal impact. No positive-result quota and no invented result.
8. New `reports/sessions/YYYYMMDD_HHMM_X2X3_robust_oos_session.md` as required by `AGENTS.md`, including created/modified/deleted paths, commands/tests run, pretest gate statuses and first outcome access receipt if any, data hashes and disk delta, run/restart instructions, exact scientific verdict, and next action. Keep it concise and audit-friendly.

**Absolute stop conditions:** Any breach of data-use/access restrictions, storage limit, original-file preservation, broken mathematics/causality, invalid or uncertain untouched-holdout status, failure to freeze protocol before future outcomes, invalid E1/evaluator independence, or unauthorized scientific-target change. Stop the affected branch with a `HOLD` report; do not bypass by relabeling previously inspected 2026 months. No live orders, no Stage 6 report rewrite or general stochastic Volterra theorem work.

### Terminal message format

At end of Codex session, report: `DEVELOPMENT: PASS/QUALIFIED/BLOCKED`; `PRETEST: READY/HOLD/NOT_REACHED`; `NEW_OOS: COMPLETE/HOLD/NOT_RUN`; headline **actual** liquidity excess and E1 costs with CIs when run; numerical tests; files and report paths; any blockers; storage delta. State explicitly whether July–September outcomes were opened. Separate implementation quality from scientific conclusions. Do not imply that a lower in-model robust objective is measured real execution improvement.

**Future research preserved, deliberately not started:** Option 2 — mathematically compatible stochastic adapted Volterra control with genuinely random matrix kernels, using AJNT, Ackermann–Kruse–Urusov, Muhle-Karbe–Tracy and Hamaguchi–Wang, including possible performance guarantees. Its theory/implementation require a distinct specification and direct theorem-level literature audit.

---

**End of combined X2+X3 Codex prompt.**
