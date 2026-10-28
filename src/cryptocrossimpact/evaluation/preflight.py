"""Fail-closed Stage 5 source/lock audit; no OOS scorer or ready-flag writer.

An official archive checksum verifies bytes, not whether calc_time means an
actual funding settlement. This checkpoint admits neither F1 nor F2 without
that semantic verification and complete two-instrument calendar coverage.
"""
import csv
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import re
from zipfile import ZipFile

import pandas as pd
import yaml

from ..data.storage import sha256
from ..kernel.features import DevelopmentStore


class PretestHold(RuntimeError):
    pass


def verify_predecessor(root):
    root=Path(root);path=root/"configs/stage05_pretest_lock.yaml"
    lock=yaml.safe_load(path.read_text());digest=sha256(path)
    companion=(root/"configs/stage05_pretest_lock.sha256").read_text().split()
    if companion!=[digest,"stage05_pretest_lock.yaml"]:
        raise PretestHold("PRETEST_PROTOCOL_HOLD: predecessor checksum mismatch")
    if lock["version"]!="stage05-pretest-lock-v1" or lock["status"]!="PRETEST_LOCK_PENDING":
        raise PretestHold("PRETEST_PROTOCOL_HOLD: unexpected predecessor version/status")
    for name,expected in lock["bindings"].items():
        if sha256(root/name)!=expected:
            # v2 explicitly authorizes an appended changelog, not rewriting v1.
            # Verify the exact archived predecessor AND approved current bytes.
            archive=root/"docs/stage05_v1_preserved"
            if name!="SPEC_CHANGELOG.md" or not (archive/"lineage.json").exists():
                raise PretestHold(f"PRETEST_PROTOCOL_HOLD: bound file changed: {name}")
            lineage=json.loads((archive/"lineage.json").read_text())
            if (sha256(archive/name)!=expected or sha256(root/name)!=lineage["amended_changelog_sha256"] or
                not (root/name).read_bytes().startswith((archive/name).read_bytes()) or
                sha256(root/"docs/stage05_pretest_amendment_v2_funding_excluded.md")!=lineage["amendment_sha256"]):
                raise PretestHold("PRETEST_PROTOCOL_HOLD: unauthorized changelog lineage")
    citation=json.loads((root/"reports/research/stage04_artifacts/pretest_lock_status.json").read_text())
    if citation["sha256"]!=digest:raise PretestHold("PRETEST_PROTOCOL_HOLD: handoff hash mismatch")
    return dict(status="PASS",sha256=digest,bindings_verified=len(lock["bindings"]))


def funding_probe(root):
    """Inspect saved actual network responses and ONE 2025 archive only.

    No 2026 archive/rate/sign data are acquired or parsed here. Rates are never
    summarized. Archive timestamps remain candidate calc_time, not settlements.
    """
    folder=Path(root)/"data/raw/funding_stage05"
    headers=(folder/"rest_probe_headers.txt").read_text()
    statuses=re.findall(r"^HTTP/\S+\s+(\d{3})",headers,re.MULTILINE)
    if not statuses:raise PretestHold("PRETEST_FUNDING_HOLD: missing HTTP probe status")
    response=json.loads((folder/"rest_probe_BTCUSDT_2025.json").read_text())
    path=folder/"BTCUSDT-fundingRate-2025-01.zip"
    expected=(folder/(path.name+".CHECKSUM")).read_text().split()
    if len(expected)!=2 or expected[1].lstrip("*")!=path.name or expected[0]!=sha256(path):
        raise PretestHold("PRETEST_FUNDING_HOLD: archive checksum mismatch")
    with ZipFile(path) as archive:
        if archive.namelist()!=["BTCUSDT-fundingRate-2025-01.csv"] or archive.testzip() is not None:
            raise PretestHold("PRETEST_FUNDING_HOLD: wrong archive member or CRC failure")
        reader=csv.DictReader(io.TextIOWrapper(archive.open(archive.namelist()[0])))
        fields=reader.fieldnames
        if fields!=["calc_time","funding_interval_hours","last_funding_rate"]:
            raise PretestHold("PRETEST_FUNDING_HOLD: unexpected archive schema")
        times=[int(row["calc_time"]) for row in reader]
    if not times or times!=sorted(set(times)):
        raise PretestHold("PRETEST_FUNDING_HOLD: duplicate/unordered archive clocks")
    if any(not 1735689600000<=t<1738368000000 for t in times):
        raise PretestHold("PRETEST_FUNDING_HOLD: probe outside January 2025")
    readme=(folder/"official_public_data_README.md").read_text()
    return dict(status="PRETEST_FUNDING_HOLD",rest_http_status=int(statuses[-1]),
        rest_message=response.get("msg") if isinstance(response,dict) else "Non-error response requires complete-range verification",
        archive=dict(http_status=200,path=str(path.relative_to(root)),sha256=sha256(path),checksum="PASS",zip_crc="PASS",
                     schema=fields,rows=len(times),candidate_first_calc_time_ms=times[0],candidate_last_calc_time_ms=times[-1],
                     candidate_first_utc=datetime.fromtimestamp(times[0]/1000,timezone.utc).isoformat(),
                     candidate_last_utc=datetime.fromtimestamp(times[-1]/1000,timezone.utc).isoformat()),
        official_readme_defines_archive_calc_time=("calc_time" in readme),
        actual_settlement_mapping_verified=False,full_2025_2026_both_symbol_calendar_verified=False,
        funding_method_admitted=None,
        reason="REST fundingTime history inaccessible (HTTP451); archive calc_time settlement mapping and complete two-symbol range unverified",
        remedy="Obtain permitted documented fundingTime history, or authoritative archive timestamp semantics plus complete verified BTC/ETH event coverage, then complete E1 development validation before readiness")


def read_pretest_partition(root,symbol,month,columns=None):
    """Actual pretest loading path refuses test inputs before ANY file I/O.

    A hand-written PRETEST_READY file cannot enable this pretest-only reader.
    The scientific funding/E1 gate must be completed by a future validated run.
    """
    if symbol not in ("BTCUSDT","ETHUSDT") or pd.Period(month,freq="M")>=pd.Period("2026-01",freq="M"):
        raise PretestHold("PRETEST HOLD: 2026 outcomes refused before I/O")
    return DevelopmentStore(root).read(symbol,month,columns)


def preflight(root):
    predecessor=verify_predecessor(root)
    funding=funding_probe(root)
    # User explicitly says stop when a mandatory check fails. E1 and final
    # scoring are NOT_RUN, not certified by earlier software tests.
    return dict(status="PRETEST HOLD",implementation="BLOCKED",predecessor=predecessor,funding=funding,
        E1_development_validation="NOT_RUN_AFTER_FUNDING_HOLD",E2_E3_evaluation="NOT_RUN",
        H1="NOT_RUN",H2="NOT_RUN",statistical_inference="NOT_RUN",robustness="NOT_RUN",
        nominal_2026_episodes=724,eligible_2026_episodes=None,scored_2026_episodes=0,
        canonical_market_rows_loaded=0,test_outcomes_unopened=True,stage6_started=False,
        pretest_ready_written=False)
