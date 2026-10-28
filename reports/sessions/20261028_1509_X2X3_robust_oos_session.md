# X2+X3 robust liquidity and independent OOS — completed session

UTC 2026-10-28 ~15:04–2026-10-28T16:57:54.786731+00:00. Combined X2+X3/1.0, config X2X3-1.0;
original research specification v1 (2026-10-27), funding-excluded Stage5 amendment.
**DEVELOPMENT PASS; PRETEST READY; NEW_OOS COMPLETE. Implementation PASS;
scientific TRADEOFF_OR_MIXED in both samples.** No full stochastic Volterra work.
Git `main`, `6d5639af60649a80b9dccffeaf63d99a49d4b780`; initial/final research tree
untracked/dirty, preserved. No commit, push, reset or deletion of prior work.

## Files and completed work

Created `src/cryptocrossimpact/robust/*.py` (14 files): joint past-only scenarios,
finite-set QCQP/CVaR, historical-state MPC, causal reader, unchanged-QC adapters,
monthly refits, gated acquisition/replay, audit, inference and reporting. Created
`configs/extension_x2x3.yaml`, `scripts/extension_x2x3.py`, audit wrapper,
`tests/test_extension_x2x3.py`, extension protocol/amendment/readiness documents.
New reports: `reports/research/extension_x2x3_development.md` and
`extension_x2x3_holdout.md`; full provenance/tables/models under
`reports/research/extension_x2x3_artifacts/`; ten inspected figures under
`figures/extension_x2x3/`; cached schedules/prefixes under
`results/extension_x2x3/`. No previous scientific file changed or deleted.

Fixed at arrival: parent=.02sum(V0) USDT, caps=.1V0, original beta/full Sigma,
reference price and kernel. Twelve paired historical 60-minute paths use only
preceding28 complete UTC days, current V1 and actual historical zero capacities.
CVaR90 uses ORIGINAL W; preference units are USDT, separate from paid/model cash.
Conditional impact retains Hfp*zpast, excludes sunk past-only constants. Policies
N/G/L/GL/GL-D/D share constraints/evaluators. E1 separate180d ending30d before
month; E2 diagonal E1 and eight fixed E3 worlds; E0 excluded. Funding omitted.

## What ran, gates and access chronology

Read AGENTS, specification/changelog/configs, completed X1 and prior-stage
reports/code, combined work order and recorded acquisition scopes. Applied PDF
skill to local AJNT pages, visually inspecting page9. Primary uncertainty-paper
and current official Binance terms checked; SSRN403 means no theorem inferred.
Positive recorded scopes through June2026 support ELIGIBLE; this is not mere
absence of July–September files, and covers recorded project work only.

Ran focused math/causality/real-parity tests, three-episode pilot, complete
`selection` and `combined` development commands (736 each), independent audit,
`freeze`, `holdout`, and `report`. Final actual pretest: **255 passed,0 failed,
2 integration tests deselected,4 existing pandas deprecation warnings**,17.46s.
Those integration tests would reopen original2026 source pilots. Covered
singleton/zero-lambda/diagonal/permutation limits, two-solver and enumerated
QCQP checks, cash units/PSD, all12 future-mutation replans, persistent impact,
CVaR/zeros, exact three-real-X1 schedule/cost parity, real as-of fit parity,
July/August/September fit-window math, and manually forged-ready rejection.

Readiness froze at **16:31:55.581243 UTC**, lock SHA256
`07a360ab2f80f967ab33e25f1d2fc7b5e2444c7a77301a18b5391a2bbc64bd6c`.
First July–September value access: **16:32:35.935300 UTC**, SOURCE_QC_ONLY_AFTER_FREEZE,
recorded in `first_source_value_open.json`. First full schedule commitment:
16:32:47.442353 UTC; scorer follows commitment in frozen code. Every later
five-minute prefix is persisted before the next bounded reveal. All choices
remain frozen after source access; only report rendering/presentation changed.

Sandbox DNS failed initially; authorized network escalation succeeded. Acquired
six official Binance futures/um monthly1m archives plus checksums (BTC/ETH,
July–September2026). **264960 rows,6 canonical partitions**, complete aligned
UTC-ms calendars, ZIP CRC/SHA/schema/original QC PASS; no QC exclusions or date
substitution. New archives in `data/raw/extension_x2x3/`; canonical
`data/canonical/{BTCUSDT,ETHUSDT}/2026-0{7,8,9}.parquet`. Original registry
unchanged; separate `new_source_manifest.json` binds every source/canonical SHA.
July124 and August124 episodes closed before later refits; September120. Each
B fit has525600 target rows, each E1 fit259200, with fixed as-of windows.

## Actual results and checks

Development L25 selected by the predeclared smallest qualifying penalty:
overload4.240568%→2.310721%, improvement1.929848 percentage points,
95%CI[1.524297,2.154112], relative45.5092%. E1 cost increase.085928bp,
CI[-.327700,.509381]. L100 adds no material protection and was not chosen.

Independent368-episode holdout: overload **4.315529%→2.501392%**,
improvement **1.814137points [1.437606,2.198859]**, relative42.0374%
[37.0653%,47.3692%]. E1 modeled funding-excluded cost N7.456735bp,
L7.309425bp: advantage **+.147310bp [-.409035,+.773331]**. Point practicality
criterion met; cost uncertainty permits adverse changes, hence mixed evidence.
GL versus L: overload improvement.008951points CI[-.0025,.0187], E1 advantage
+.004271bp[-.033452,.046745]; incremental robust benefit inconclusive. GL versus
GL-D E1 advantage-.005097bp[-.058111,.040381], cross benefit inconclusive.
June2025 B dominates every robust replan in both samples; no replacement family
searched. G overload reduction only2.89% OOS, below the practical10% criterion.

Development maximum finite ratio worsens375.17x→566.99x with36 positive-sale/
zero-volume cells retained. Holdout maximum2.86168x→1.77958x; >100% incidents
5→2 cells (4→2 episodes), no zero-volume cells. TWAP has still lower mean
holdout overload1.1509%. Worst-world p95 cost worsens N32.2883→L37.7786bp;
negative months/episodes, all ten worlds, regret/loss shares and grouped CIs
remain reported. No feasible real-fill, live saving or causal claim follows.

Independent audits PASS: development61824 prefixes/108 triangular cash checks,
max cash discrepancy3.18e-11USDT; holdout26496/42,9.66e-13USDT. X1 nominal
schedule discrepancy exactly0 in development. No cap violation, repair,
infeasibility or accepted inaccurate solver. Holdout max normalized primal
4.25e-10, KKT3.55e-9; terminal absolute error<=.000117USDT.
All ten rendered PNGs inspected; corrected overlapping labels. Final source
fingerprints and unchanged scientific bindings verified. See actual JUnit,
output audits, grouped CSVs, visual_QA and run_manifest rather than inferred tests.

## Deviations, resources and recovery

Root SPEC_CHANGELOG is bound by old locks: extension-only amendment records
scope without altering predecessors. Pre-outcome numerical recovery fixed
NumPy scalar-dual extraction and rejected inaccurate conic pilots; redundant
VaR>=0, bounded tighter tolerances and certified exact dominance presolve leave
objective/gates unchanged. Failed pilot versions retained. Before freeze, audit
world-cache/completeness and resume metadata corrections were reviewed; actual
old source bytes/hashes retained, fresh replay numerical AST unchanged.
macOS independently changed `reports/.DS_Store`; explicit metadata-only exception
records original hash. Research changes still halt preservation (tested).
All scientific artifacts among2745 protected paths and189 original data stat
snapshots unchanged. No robust family or scientific target changed from results.

CPU full-run times: selection1720.7s/455.8MiB peak, combined1455.6s/453.0MiB,
holdout1279.4s/489.2MiB. Earlier unreduced pilot observed~1.37GiB, below8GB.
Retained additional outputs/data **~552.0MiB (~.58GB)**;
conservative two-copy peak estimate~1.16GB,
well below30GB. Six new raw archives total~11.1MB. Seed20261027; Python3.14.6;
package versions and code/config/source hashes in run_manifest. Initial six-archive
preflight budget6GB; measured project storage~1.69GB during development.

Safe checkpoint: completed frozen experiment. Review the two research reports.
Reproducible audit/report commands:

```sh
.venv/bin/python scripts/audit_extension_x2x3.py
.venv/bin/python scripts/audit_extension_x2x3.py --holdout
.venv/bin/python scripts/extension_x2x3.py report
```

`holdout` validates the existing lock and resumes cached episodes; do not refreeze
or retune using these inspected months. No further decisions/blockers for this
assignment. Full stochastic Volterra research requires separate authorization.
