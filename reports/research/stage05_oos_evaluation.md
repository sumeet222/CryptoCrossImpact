# Stage 5: pretest funding HOLD — OOS evaluation not run

UTC: 2026-10-28. **Implementation BLOCKED / PRETEST HOLD.** The mandatory funding
verification gate did not pass. **No January–June 2026 canonical market outcomes
were opened.** No ready lock was issued, no final-test episode was scored, and
Stage 6 was not begun. H1/H2 have no scientific verdict because they were not run.

## Predecessor and stopping rule

The [Stage 4 protocol](../../docs/stage05_pretest_policy_evaluator_lock_v1.md) and
its YAML/checksum are consistent. All **47 bound files** match the frozen lock
SHA-256 `a691a3db76a776d4f8e31b43f6c68663145891e1974e2bf6dc0f061130192e31`.
Status remains `PRETEST_LOCK_PENDING`; the originals are unchanged.

The Stage 5 prompt §1 requires actual verified funding settlements for F1
cashflows or F2 timestamp-only exclusions. Its fail-closed rule and the user's
explicit instruction require stopping before outcomes when this gate fails.
An archive checksum alone cannot establish settlement-time semantics.

| Check / operation | Actual status |
|---|---|
| Frozen Stage 4 lock, checksum and bindings | PASS, 47 files |
| Official funding REST access | HTTP 451, restricted-location response |
| One official development funding archive | HTTP 200, checksum/ZIP CRC PASS |
| Archive `calc_time` → actual settlement mapping | UNVERIFIED |
| Complete BTC/ETH settlement coverage, 2025–June 2026 plus boundaries | NOT VERIFIED |
| F1 or F2 admitted | Neither; PRETEST_FUNDING_HOLD |
| E1 development implementation/validation | NOT_RUN after funding hold |
| Versioned PRETEST_READY lock | NOT_CREATED |
| H1, H2, E0–E3 scoring, inference, robustness | NOT_RUN |
| 2026 nominal / eligible / scored episodes | 724 calendar labels / undetermined / 0 |

## Actual funding evidence and its limits

The documented [USD-M funding history endpoint](https://developers.binance.info/en/docs/catalog/core-trading-derivatives-trading-usd-s-m-futures/api/rest-api/market-data#get-funding-rate-history)
provides `fundingTime`. A single direct GET for **BTCUSDT January 1, 2025**
returned HTTP 451 and a provider message stating that service is unavailable
from a restricted location. The response and headers were retained; no alternate
IP, proxy, restricted endpoint workaround or repeated access attempt was used.

The explicitly permitted official archive alternative was probed on development
data only:
[BTCUSDT January 2025 funding archive](https://data.binance.vision/data/futures/um/monthly/fundingRate/BTCUSDT/BTCUSDT-fundingRate-2025-01.zip).
Its companion checksum matches SHA-256
`df725010d55458866eb5a47e9ee708c6796c9d7e77b14c38342cea11f381815e`;
ZIP CRC passes. The 825-byte ZIP contains one CSV, 93 rows, with fields
`calc_time, funding_interval_hours, last_funding_rate`. Candidate clock labels
are ordered and unique, from `2025-01-01T00:00:00.015Z` through
`2025-01-31T16:00:00Z`. They were retained without rounding to a presumed grid.
No funding-rate sign/magnitude was used to select an analysis or policy.

The inspected [official public-data README](https://github.com/binance/binance-public-data/blob/master/README.md)
does not define this archive's `calc_time` field or its equivalence to REST
`fundingTime`. A targeted primary-source search found an
[unanswered timestamp-semantics question in the provider repository](https://github.com/binance/binance-public-data/issues/519).
The retrieved comments contain no maintainer/member/owner answer establishing
the mapping. This is **missing verification**, not evidence that the archive
is corrupt or that its candidate labels are wrong. Third-party assumptions were
not substituted for the required verification.

Consequently, F2 cannot yet claim actual settlement-free episodes; F1 also lacks
verified event/rate semantics and full coverage. No ETH/full-range bulk download
or 2026 funding-rate inspection was performed after this finding. In particular,
no default eight-hour calendar or universal zero funding was invented.

## Checks, artifacts and preserved work

Added a small pretest-only audit in `evaluation/preflight.py`, a thin
`scripts/stage05.py` checkpoint and eight focused tests. The existing development
data reader is reused; its firewall was not widened. A manually written ready
flag cannot unlock the pretest reader. The current checkpoint implements no OOS
scorer or ready-flag writer.

**83 tests passed, 0 failed:** 8 new lock/evidence/barrier checks and 75 existing
Stage 3/4 mathematical/policy checks. This verifies the barrier and prior
numerics, not the funding gate or unimplemented Stage 5 estimators/scorers.
Regression source smoke reads June 2025 only. Stage 1 integration tests that
open 2026 source pilots were not run. The preflight CLI itself loads zero
canonical market rows. `pip check` passed; dependencies were unchanged.

Both `preflight` and `all` exit **2** with `PRETEST HOLD`, as intended. The latter
does not bypass the failed gate. Exact commands, packages, Git/source/lock hashes,
source probe fingerprints and checks are retained in
[stage05_artifacts](stage05_artifacts/). The 212 prior protected files and all
60 canonical size/mtime snapshots are unchanged; no old research result, config,
model, source manifest, specification or changelog was overwritten.

```sh
.venv/bin/python scripts/stage05.py preflight
.venv/bin/python scripts/stage05.py all
.venv/bin/python -m pytest tests/test_stage05_evaluation.py tests/test_stage03_execution.py tests/test_stage04_policies.py -q
```

The CLI is an **offline audit of retained probe evidence**, not a complete OOS
runner. A rerun currently reproduces the hold. New verified evidence and the
remaining Phase 5A implementation/tests are required before an OOS runner can
be enabled. No result figures or confidence intervals were fabricated.

## Exact recovery requirement

Obtain a legitimately accessible, documented actual funding-event history for
both contracts over the required development/test range and adjacent boundaries,
or authoritative archive timestamp semantics plus complete verified event
coverage. Then choose and test F1/F2 before outcomes. Complete E1's two 2025-only
180-day/gap-30 fits, synthetic recovery and E2/E3/cash/inference tests; preserve
v1 and issue a separate hash-linked ready lock only after every prerequisite
passes. Later-month as-of fits can use elapsed history under the frozen algorithm.
No current approval permits bypassing provider restrictions or weakening this gate.

The measured preflight runner peak RSS was approximately **171 MB**; its timed
audit body was 0.03 seconds, excluding interpreter/import startup. Test process
peak RAM was not instrumented. Retained added disk is under **0.2 MB**; exact
accounting and the session path are in `stage05_artifacts/resource_summary.json`.

**G4 OOS is NOT COMPLETE. H1/H2 and adverse scenario results are NOT_RUN.
Final-test outcomes remain unopened; stop before Stage 6.**
