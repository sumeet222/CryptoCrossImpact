# X1 adaptive execution and stochastic-liquidity approximation

**2026-10-28 UTC; authorized X1.0 completed. X1-G0/G1/G2 PASS.**
Implementation **PASS**; primary adaptive-cost scientific result **INCONCLUSIVE**.
Original specification v1 unchanged; X1 config/protocol hashes and source/model
bindings are in `../research/extension_x1_artifacts/run_manifest.json`.
Git remained `main`, commit `6d5639af60649a80b9dccffeaf63d99a49d4b780`.
Initial/final worktree dirty with the pre-existing untracked research tree;
no commit, push, reset, deletion or prior-artifact overwrite. Initial preservation
snapshot 14:27:18 UTC; implementation/read work preceded that snapshot.

## Changed files and purpose

New only: `configs/extension_x1_adaptive_liquidity.yaml`,
`docs/extensions/x1_adaptive_liquidity_protocol_v1.md`, `x1_change_log.md`;
`src/cryptocrossimpact/liquidity/{__init__,forecasts,workflow,reporting}.py`;
`src/cryptocrossimpact/execution/adaptive.py`; `scripts/extension_x1.py`,
`scripts/audit_extension_x1.py`; `tests/test_extension_x1.py`; new X1 research
report/artifacts, four figures, this session report, ignored `results/extension_x1`.
Original README, SPEC_CHANGELOG, result index and all Stage1–5 files remain intact;
X1 has its own dated change log and experiment index.

V0 retains Stage4's exact algorithm; V1 adds complete-day pooled intrahour
ratios/shrinkage; V2 uses completed-span5/60 EWMA and tau15. Volumes/sales are
USDT per minute/reference USDT; covariance fractional log-return variance/min.
The MPC carries remaining inventory and exact cash `H_fp*z_p`, holds original
caps/covariance/beta/kernel fixed, and commits five-minute prefixes before later
observations. No alpha, cap relaxation, inventory repair or new kernel fit family.
D0/D1 are B's own diagonal (T3B), not separately fitted A. P4M is the required
median-only scenario control. E1/E2 are common across arms, funding excluded;
risk remains a preference separate from cash. No local-QP objective sums.

## Actually ran

Existing Python3.14.6 `.venv`, no packages or market downloads. Read AGENTS,
original specification, authorized X1 prompt, changelog/configs, Stage3/4/5 reports,
prior session and code/tests/manifests. Optional literature survey absent.

- Initial old regression:117 passed. X1 focused runs grew to36 cases.
- `scripts/extension_x1.py forecasts`:2076 training origins Jan29 2024–Jun30 2025,
  28d warmup;736 development origins Jul1–Dec31 2025. Training249120 and
  development88320 asset-minute forecast labels, three development models264960
  rows. Strict reader opened only48 canonical partitions in2024–2025. Quantiles
  trained on matured training labels only, buckets1–5/6–15/16–60.
- `pilot`: Jul5 00:00, Jul31 18:00, Aug1 00:00; full pilot rerun gives
  byte-identical schedules and exactly identical E1/E2 metrics.
- `development`: all736 common episodes,6624 schedules including TWAP/VWAP,
  13248 E1/E2 scores. P0/P1/P2/D0/D1/P4/P4M complete; P3 NOT_RUN under its
  declared forecast gate. Six causal E1 fits:259200 targets each,180d with30d
  gap, tau5/30,ridge1, own L/standardization, existing frozen fit API.
- Full impacted suite: **202 passed,0 failures/errors,2 integration tests
  deselected**,19.50s;36 X1 +166 old cases. Four existing parser deprecation
  warnings. `pip check` passed. The omitted integration tests open2026 pilots.
- Output audit:736 episodes,37536 QP-issued prefixes;108 independent triangular
  cash checks and108 full-score reproductions. `report` rendered tables/figures;
  all four PNGs visually inspected, including a final outlier-visible liquidity
  plot and terminal inventory endpoint.

Restart, without new final-test reads:

```sh
.venv/bin/python scripts/extension_x1.py development
.venv/bin/python scripts/audit_extension_x1.py
.venv/bin/python scripts/extension_x1.py report
```

Existing receipts/schedules are verified/resumed; config/scenario/numerical locks
reject drift. Test command and JUnit are in X1 artifacts/test_results.json.

## Actual scientific and QA findings

V1 improves V0: pooled daily log-squared-volume error gain0.0104001,
95% descriptive7d/500draw interval[0.0066231,0.0140047]; MAE gain18174.5USDT/min
[9090.25,27391.98]. V2 worsens log error on average:−0.009515
[−0.026852,+0.004227] versus V1; it fails the gate, remains a negative forecast
result, and is not opportunistically retuned. Scenario bands use V1; all
asset/bucket/quantile coverages meet the declared5percentage-point tolerance,
max error4.212points. Tail pinball/coverage improve over the degenerate point
reference; median calibration is slightly worse. Bands are marginal approximations.

Primary E1 control-minus-new adaptive P1−P2: **+0.0043823bp**,
95%[−0.0022766,+0.0105146]; E2 +0.004378bp with interval crossing zero.
Static V1 versus P0 has E1 point−0.012700bp despite better forecasts. Diagonal
adaptation +0.005605bp[0.000341,0.010691] is small and descriptive; it establishes
no cross-impact benefit. P4 versus P2 +0.015156bp[−0.028512,+0.058051];
scenario weighting versus matched median also uncertain. All monthly/regime
signs, negative episodes and adverse-case IDs are retained.

P1→P2 above10% observed-volume participation falls only4.9148%→4.8944%; above20%
1.0262%→1.0092%. P4 above10%=4.6894%, with severe tails retained. Every arm has
36 positive-sale zero-volume asset-minutes; P2's maximum finite ratio375.17×,
P4's399.94×. Extreme cases concentrate in2025-08-29 06:00 and remain included.
These are strong simulator/source-liquidity feasibility limitations, not fills.
No causal execution or all-in funding-inclusive savings is established.

Ex-ante cap violations0; repairs0; max terminal2.24e-8USDT; max KKT4.85e-15.
P0 versus old T4 max sale error/initial1.09e-15. Independent triangular cash
max discrepancy3.18e-11USDT; full-score reproduction difference0.
All **456 prior protected files and60 canonical stat snapshots unchanged**.
No2026 canonical partition opened, including no fresh July–September holdout.

## Recovery, resources and next action

One temporary indentation error was corrected before pilot/lock. During the
initial full replay, strict JSON serialization rejected the old scorer's infinite
participation for the zero-turnover episode. Its committed schedule was preserved.
An X1 wrapper now uses null plus explicit `INFEASIBLE_POSITIVE_SALE_ZERO_VOLUME`;
no trade or cash value changes. Original X1 source/lock/failure record are archived
under provenance; AST comparison verifies existing forecast/policy/development
algorithms unchanged. A regression passes; resume recovers the missing episode.
Initial/recovery runtime/RSS records and lock v1→v2 lineage remain available.
No failed episode was assigned zero cost or dropped.

Forecast run124.3s; full replay including serialization recovery528.3s (8.80min);
measured replay peakRSS301.9MiB. Tests/rendering peakRSS not separately measured.
Retained payload approximately227MiB (about235MiB allocated), conservative additional peak<0.5GiB,
well within the8GB/30GB guardrails. No duplicate canonical corpus. Matplotlib
cache is under ignored X1 results. Optional `ps` monitoring was sandbox-denied;
runner resource measurements sufficed, so no monitoring escalation was needed.

Primary report: `../research/extension_x1_adaptive_liquidity.md`.
Tables/manifests/audit: `../research/extension_x1_artifacts/`.
Figures: `../../figures/extension_x1/`; immutable bulk: `../../results/extension_x1/`.
**No decision is needed to finish X1.** Next safe step: review the exploratory
negative/mixed findings and liquidity failures, then separately authorize Session2
if desired. Robust/minimax optimization and future Option2 (random Volterra
kernels/full adapted path control) were not begun. No fresh OOS confirmation.

Final QA UTC 2026-10-28T14:49:35.111640+00:00: all eight manifest code hashes verified, four final figures visually reviewed, new-file/tracked whitespace checks clean; preservation still456/456 files and60/60 canonical stat snapshots. Git branch/commit and dirty status unchanged.
