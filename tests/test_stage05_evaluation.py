"""Blocked pretest checks only; no 2026 price/flow, scoring or inference tests."""
from pathlib import Path
import json

import pandas as pd
import pytest

from cryptocrossimpact.evaluation.preflight import (PretestHold,read_pretest_partition,verify_predecessor,funding_probe,preflight)

ROOT=Path(__file__).resolve().parents[1]


def test_frozen_predecessor():
    result=verify_predecessor(ROOT)
    assert result["status"]=="PASS" and result["bindings_verified"]==47


@pytest.mark.parametrize("symbol",["BTCUSDT","ETHUSDT"])
@pytest.mark.parametrize("month",["2026-01","2026-06"])
def test_pretest_refuses_before_any_io(monkeypatch,symbol,month):
    monkeypatch.setattr(Path,"open",lambda *a,**k:pytest.fail("Forbidden file I/O"))
    monkeypatch.setattr(pd,"read_parquet",lambda *a,**k:pytest.fail("Forbidden Parquet I/O"))
    with pytest.raises(PretestHold,match="before I/O"):read_pretest_partition(ROOT,symbol,month)


def test_unverified_archive_cannot_authorize_funding():
    result=funding_probe(ROOT)
    assert result["rest_http_status"]==451
    assert result["archive"]["checksum"]==result["archive"]["zip_crc"]=="PASS"
    assert result["archive"]["rows"]==93
    assert result["actual_settlement_mapping_verified"] is False
    assert result["funding_method_admitted"] is None
    assert result["full_2025_2026_both_symbol_calendar_verified"] is False


def test_all_stops_at_first_mandatory_hold(monkeypatch):
    monkeypatch.setattr(pd,"read_parquet",lambda *a,**k:pytest.fail("No market reads allowed"))
    result=preflight(ROOT)
    assert result["status"]=="PRETEST HOLD"
    assert result["E1_development_validation"]=="NOT_RUN_AFTER_FUNDING_HOLD"
    assert result["scored_2026_episodes"]==0
    assert result["pretest_ready_written"] is False


def test_fake_ready_file_does_not_unlock_pretest_reader(tmp_path,monkeypatch):
    (tmp_path/"PRETEST_READY.json").write_text(json.dumps({"status":"PRETEST_READY"}))
    monkeypatch.setattr(pd,"read_parquet",lambda *a,**k:pytest.fail("Forbidden I/O"))
    with pytest.raises(PretestHold):read_pretest_partition(tmp_path,"BTCUSDT","2026-01")
