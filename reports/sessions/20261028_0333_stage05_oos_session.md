# Stage 5 pretest funding hold — session

**UTC:** 2026-10-28; pretest run 03:32, reporting from 03:33.
**Implementation BLOCKED / PRETEST HOLD / PRETEST_FUNDING_HOLD.** G4 OOS is not
complete. H1/H2, evaluator comparisons, inference and robustness are **NOT_RUN**;
no scientific result is inferred from a source-access failure. **2026 canonical
outcomes were never opened; Stage 6 was not begun.**

## Authority, starting state and preservation

Read local AGENTS.md, approved specification v1.0, changelog, Stage 2–4 configs,
prior reports/checkpoints and the complete Stage 5 prompt. Rechecked the actual
Stage 4 pretest docs/YAML, checksum and cited handoff SHA. All **47 bindings**
match predecessor lock
`a691a3db76a776d4f8e31b43f6c68663145891e1974e2bf6dc0f061130192e31`.
Specification remains `bc5d9686…`; exact prompt/spec/code hashes are in
`reports/research/stage05_artifacts/run_all.json`.

Git remained `main` at `6d5639af60649a80b9dccffeaf63d99a49d4b780`. Initial/final
tree contains untracked research work; Stage 5 adds files within existing roots.
No tracked changes, commit, push, reset or deletion. All **212 protected prior
files** and **60 canonical size/mtime snapshots** match the initial snapshot.
The frozen v1 lock, specification, changelog, prior source/config/models/results,
source manifests and datasets were not edited. Canonical preservation uses stat
metadata, never test-file contents.

## What actually ran and what blocked

Probed the official USD-M `fundingRate` endpoint once for BTCUSDT January 1, 2025:
**HTTP 451**, provider restricted-location message. Did not retry through another
host, region or proxy. The authorized official Binance Vision archive alternative
was probed on BTCUSDT **January 2025 only**: ZIP/checksum HTTP 200, SHA-256 and CRC
PASS. One CSV has 93 ordered unique `calc_time` labels and fields
`calc_time,funding_interval_hours,last_funding_rate`; its first label is 15ms
after midnight. Retained exact labels; no snapping or presumed funding schedule.

Official REST docs define `fundingTime`, but the inspected provider README does
not define archive `calc_time` equivalence. A targeted source check and provider
issue/comments yielded no authoritative mapping. This is **unverified semantics**,
not a claim of bad data. The single development probe cannot establish complete
BTC/ETH funding-event coverage for 2025–June 2026 and boundaries. Neither F1 nor
F2 was admitted; no 2026 funding-rate signs/magnitudes were inspected.

Following the user's explicit stop rule and prompt Phase 5A gate, stopped before
E1 implementation/OOS access. No full funding bulk download, 2026 refit, outcome
scoring, scenario comparison or bootstrap was performed. Nominal calendar labels:
**724 episodes**; eligibility **undetermined**, scored **0**. No ready manifest
was written, no assumptions changed and no scientific changelog entry was needed.

## Files, actual QA and reproducibility

Created `src/cryptocrossimpact/evaluation/{__init__,preflight}.py`,
`scripts/stage05.py`, `tests/test_stage05_evaluation.py`, the new research report,
compact preflight/provenance/test/preservation artifacts and this session report.
Only new ignored `data/raw/funding_stage05/` probe files were downloaded: the
2025 ZIP/checksum, REST/archive headers/response, official README and issue
comments. Raw vendor inputs remain out of Git; source URLs/hashes are recorded.

The pretest reader rejects 2026 before even source-manifest I/O, reuses the
existing development reader, and cannot be unlocked by a fabricated ready flag.
The current CLI deliberately has no scorer or readiness writer. Both
`scripts/stage05.py preflight` and `all` were run and exit **2**, with the saved
funding HOLD and no canonical row loads. This is an offline probe-evidence audit,
not a completed Stage 5 evaluation engine.

**83 tests passed, 0 failed, 9.80s:** 8 new pretest tests plus 45 Stage 3 and
30 Stage 4 tests. Checks cover predecessor consistency, checksum-versus-semantics
distinction, pre-I/O refusal for both symbols at January/June 2026, fake-ready
rejection, stop-on-hold, and prior mathematical/policy regressions. Stage 4's real
source smoke reads June 2025 only; no 2026 integration tests were run. E1 recovery,
funding-cash conventions, evaluator/scorer and bootstrap tests remain NOT_RUN.
Software tests passing do not mean the funding gate passed.

```sh
.venv/bin/python scripts/stage05.py preflight
.venv/bin/python scripts/stage05.py all
.venv/bin/python -m pytest tests/test_stage05_evaluation.py tests/test_stage03_execution.py tests/test_stage04_policies.py -q
```

Used existing Python 3.14.6 `.venv`; `pip check` passed. NumPy2.5.4,
pandas3.1.0, SciPy1.18.1, CVXPY1.9.3 and other versions are bound in manifests.
No dependencies installed. Initial project storage **1024339239 bytes**; added
disk under **0.2MB** (exact final accounting in resource_summary.json). Measured
preflight peak RSS **171098112 bytes**; audit body **0.0264s**, excluding startup.
Pytest process peak was not measured. No storage/RAM ceiling was approached.

## Safe checkpoint and required next action

Primary outputs: `reports/research/stage05_oos_evaluation.md` and
`reports/research/stage05_artifacts/`. The original `PRETEST_LOCK_PENDING` remains
intact. Obtain permitted, documented actual funding timestamps/full-range
coverage or authoritative archive semantics and complete calendar evidence;
then complete E1 development validation and remaining pretest tests before
issuing a new ready lock. Source clarification/data are needed, not permission
to bypass restrictions or replace funding with a conventional clock. Do not
resume 2026 scoring merely by changing a status field.

**No January–June 2026 canonical outcomes opened; no Stage 6 work.**
