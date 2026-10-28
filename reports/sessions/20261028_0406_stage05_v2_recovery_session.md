# Stage 5 recovery: approved funding-excluded evaluation

**UTC 2026-10-28 04:06–05:13; G4 OOS COMPLETE; implementation PASS.**
H1 **SUPPORTS_HYPOTHESIS** for conditional observational fit. H2
**DOES_NOT_SUPPORT** the prespecified 0.1 bp practical benefit. The sign of the
execution difference remains uncertain. **Stage 6 not begun; no decision needed.**

## Authority, preservation and changes

Read repository AGENTS.md, approved specification v1, core/Stage 2–4 configs,
SPEC_CHANGELOG, both Stage 5 prompts, v1 lock/pretest documents, prior reports,
funding-HOLD evidence and relevant source/tests. The user explicitly authorized
funding omission before outcomes. No other scientific definition was changed.
The core specification, original v1 protocol/lock, HOLD, previous results and
all 60 canonical partitions remain preserved. Git stayed `main` at
`6d5639af60649a80b9dccffeaf63d99a49d4b780`; initially/finally dirty with an
untracked research tree. No commit, push, reset or deletion of prior work.

The original lock SHA remains
`a691a3db76a776d4f8e31b43f6c68663145891e1974e2bf6dc0f061130192e31`.
It binds the old changelog, while recovery requires an append. Exact original
changelog, preflight source and README bytes are archived in
[docs/stage05_v1_preserved](../../docs/stage05_v1_preserved/README.md).
Active preflight now reconciles that archived original with the exact approved
append; all 47 historical bindings verify. Of 235 protected prior files, 232
remain unchanged live and these three have exact preserved originals. No old
funding audit was relabeled PASS. Canonical size/mtime snapshots are unchanged.

Created v2 amendment/protocol, evaluation config and immutable lock; new
`evaluation/v2_*.py`, `scripts/stage05_v2.py`, 42 v2 tests and separate compact
artifacts/bulk outputs. Stage 2/3/4 mathematical source is unchanged. New code
implements bounded as-of source access, own-window liquidity/normalization,
independent E1, immutable decisions, common-world five-component USDT/bp cash,
paired calendar-block inference and fixed sensitivities. README documents the
new stage; `results/experiment_index.csv` indexes it. Post-outcome readonly QA is
`scripts/audit_stage05_v2_outputs.py`. Renderer edits after opening are only
labels/layout and explanations of frozen outputs; numerical code/config stayed
locked. No new packages, data downloads, funding access or optional extension.

## What actually ran and the test firewall

Existing Python 3.14.6 `.venv` reused; package versions are in
[run manifest](../research/stage05_v2_artifacts/run_all_v2.json).
Preparation, independent fit replay, development smoke, final preflight tests,
freeze, full chronological `all`, post-ready tests, output audit and final
`report` rendering ran. Seed 20261027; no 2026 tuning.

E1 Sep/Dec 2025 proofs use exactly 180 days plus a 30-day gap, 259200 targets
apiece, tau=(5,30), ridge=1 chosen only from the frozen development table. Own
L/transforms and PSD fits are distinct from optimizer B; B replay matches old
artifacts to 1e-10. Development smoke: eight policy sets/528 scores. Before
opening: **166 tests passed, zero failed, two integration cases deselected**
(9.89 s; four existing parser warnings). A separate post-ready suite also passed
166 cases (22.35 s). Neither run is represented as a new real-source download
or an untouched-test experiment after opening.

[PRETEST_READY_v2](../research/stage05_v2_artifacts/pretest_ready_v2.json) UTC
04:34:16.844872; lock SHA
`5ac1646ab235f841c8e4c5454099ad09f5a6e6d434009853853e18b1987b3507`;
config SHA `cbf15533daf81e9518d1a7b48111a17e770ce66425889458c3be2d4061ad9930`.
First actual outcome read UTC 04:35:11.232689, after readiness and the first
six-policy decision receipt. Funding status is NOT_APPLICABLE_BY_APPROVED_SCOPE_AMENDMENT;
funding/all-in amounts remain null, not zero. No funding-event exclusions.

## Actual results and QA

Jan–Jun 2026: **724/724 episodes, 4344 primary schedules, 47784 scores** across
six policies and 11 worlds, with no structural QC/policy failures. H1 uses
260640 valid minute targets per asset. Monthly A/B/N0 use past 365-day fits;
E1 uses [month−210d,month−30d). Later refits use elapsed history only. Decisions
are persisted before evaluation bars; predicted volume sets inventories/caps.

Pooled standardized MSE A=0.792748, B=0.732888, N0=1.015011. Relative B gain
7.5509%, paired 95% interval [6.9758%,8.3614%]: descriptive same-minute response,
not a tradable forecast or causal own-trade impact.

T3-minus-T4 ex-funding shortfall, positive favoring T4: **E1 +0.020810 bp,
95% interval [−0.026669,+0.072799]**; E2 +0.015837 [−0.031752,+0.067750];
opposite-sign E3 +0.010864 [−0.036834,+0.062701]. All independent/stress pooled
primary intervals cross zero. March/May/June E1 points favor T3. T4 loses to T3
in 48.62% of E1 episodes; worst primary E1 difference −5.2945 bp. E1 secondary
T3B-minus-T4 +0.026573 bp [−0.033716,+0.093753]. Negative cash rows (15273),
adverse worlds/months, regret and regime results remain visible.

All **17** fixed robustness variants completed: **147696 scores, zero failures**,
7964 reoptimized decision sets. Fixed-100k and 30-minute means are negative in
E1/E2; all pooled primary sensitivity intervals cross zero. Fee/spread shifts
leave paired effects unchanged (maximum pooled difference 2.40e-16 bp).

The independent audit verifies every primary/sensitivity receipt, common beta,
as-of/model/window/cap/terminal identity, monthly hashes and funding omission.
Sixty-six direct triangular cash checks agree within 9.55e-12 USDT. Maximum
terminal residual 3.17e-8 USDT; normalized physical residual 3.11e-15; KKT
2.35e-15. All seven PNGs visually inspected; clipped labels/legend corrected.
Primary statistics remain identical to their pre-robustness hash index.
Final untracked-file whitespace inspection flags one extra EOF blank line in
locked `v2_features.py`; retained to preserve the numerical-source lock. This
cosmetic warning does not affect tests or scientific validity. Tracked diff
whitespace checks pass.

Realized minute participation reaches **146.68%** despite feasible forecast
caps. Such episodes stay in the sample; the replay cannot establish actual
fills, realized-liquidity feasibility, live savings or causal improvements.
Funding is unobserved/omitted, even if a horizon crosses actual settlements.
Risk preference is reported separately from cash; spread/fees are assumptions.

## Resources, outputs and recovery

Full OOS/robustness run: **35.20 min**, peak main-process
RSS **676.7 MiB**. Retained recovery additions
approximately **256.5 MiB** (project approximately 1.293 GB).
Peak additional disk is approximately the retained amount plus small atomic
writes, conservatively under 0.5 GB; not continuously sampled. No new corpus,
large temporary extraction or dependency cache. Limits remained well below
8 GB RAM/30 GB additional storage. Optional `ps` monitoring was sandbox-denied;
the actual run recorded its own RSS, so no escalation was needed.

[Research report](../research/stage05_oos_exfunding_v2.md),
[compact artifacts](../research/stage05_v2_artifacts/verdict_v2.json),
[seven figures](../../figures/stage05_v2/coverage.png),
[output audit](../research/stage05_v2_artifacts/robustness_output_audit_v2.json).
Bulk checkpoints: `results/stage05_exfunding_v2/primary/` and `robustness/`.

```sh
.venv/bin/python scripts/stage05_v2.py all
.venv/bin/python scripts/audit_stage05_v2_outputs.py
```

Every requested month is complete; restart verifies existing checkpoint hashes.
An interrupted partial month's strict receipt replay includes solver timing
metadata and may require continuation from saved receipts, never overwriting
those decisions. This limitation did not interrupt the completed run. Final
report rendering uses `scripts/stage05_v2.py report`; it does not reopen
canonical outcomes. No scientific blocker remains. **Stop at Stage 5.**
