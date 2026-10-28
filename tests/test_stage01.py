import io
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import pytest

from cryptocrossimpact.data.pipeline import ROOT, Pipeline, archive_url, load_config, months
from cryptocrossimpact.data.schema import (COLUMNS, HEADER, canonicalize, parse_zip,
                                           signed_trade_quote, split_labels, validate_identity)
from cryptocrossimpact.data.storage import PublicSource, SourceError, sha256, write_parquet


@pytest.fixture
def config():
    return load_config(ROOT)


def frame(times=None):
    if times is None:
        start = pd.Timestamp("2024-05-01", tz="UTC").value // 10**6
        times = [start, start + 60000, start + 120000]
    result = pd.DataFrame([[t, 100, 110, 90, c, 10, t + 59999, 1000, 3, b / 100, b, 0]
                           for t, c, b in zip(times, [100, 105, 102], [600, 400, 500])], columns=COLUMNS)
    for col in set(COLUMNS) - {"open_time", "close_time", "count"}:
        result[col] = result[col].astype(float)
    return result


def zipped(tmp_path, df, header=True):
    target = tmp_path / "BTCUSDT-1m-2024-05.zip"
    with ZipFile(target, "w") as z:
        z.writestr("BTCUSDT-1m-2024-05.csv", df.to_csv(index=False, header=header))
    return target


def test_flow_units_clock_and_return(config):
    df = canonicalize(frame(), "BTCUSDT", "2024-05", config)
    assert df.signed_taker_quote_flow.tolist() == [200, -200, 0]
    assert df.sell_quote_volume.tolist() == [400, 600, 500]
    np.testing.assert_allclose(df.signed_taker_flow_ratio, [.2, -.2, 0])
    assert np.isnan(df.close_to_close_log_return.iloc[0])
    assert df.close_to_close_log_return.iloc[1] == pytest.approx(np.log(105 / 100))
    assert (df.available_at_utc.astype("int64") // 1000 > df.close_time).all()
    assert (df.available_at_utc - df.bar_open_utc == pd.Timedelta(minutes=1)).all()
    assert df.valid_bar.all()


@pytest.mark.parametrize("header", [True, False])
def test_parser_header_and_roundtrip(tmp_path, config, header):
    raw = frame()
    raw.loc[0, "quote_volume"] = 1000.1234567891234
    path = zipped(tmp_path, raw, header)
    url = archive_url(config, "BTCUSDT", "2024-05")
    parsed = parse_zip(path, "BTCUSDT", "2024-05", url)
    pd.testing.assert_frame_equal(raw, parsed, check_exact=True)
    canonical = canonicalize(parsed, "BTCUSDT", "2024-05", config)
    output = tmp_path / "canonical.parquet"
    write_parquet(output, canonical)
    pd.testing.assert_frame_equal(canonical, pd.read_parquet(output), check_exact=True)


@pytest.mark.parametrize("replacement", ["data/spot/monthly", "data/futures/cm/monthly", "data/futures/um/monthly/markPriceKlines"])
def test_wrong_market_rejected(config, replacement):
    url = archive_url(config, "BTCUSDT", "2024-05").replace("data/futures/um/monthly", replacement)
    with pytest.raises(ValueError, match="Wrong provider"):
        validate_identity(url, "BTCUSDT", "2024-05")


def test_wrong_symbol_and_interval(config):
    url = archive_url(config, "BTCUSDT", "2024-05")
    for bad in [url.replace("BTCUSDT", "ETHUSDT"), url.replace("1m", "5m")]:
        with pytest.raises(ValueError):
            validate_identity(bad, "BTCUSDT", "2024-05")
    with pytest.raises(ValueError):
        validate_identity(url, "SOLUSDT", "2024-05")


@pytest.mark.parametrize("fault", ["microseconds", "seconds", "duplicate", "unsorted", "bad_close", "off_minute"])
def test_bad_clocks_rejected(config, fault):
    raw = frame()
    if fault in ("microseconds", "seconds"):
        factor = 1000 if fault == "microseconds" else .001
        raw["open_time"] = (raw.open_time * factor).astype("int64")
    elif fault == "duplicate":
        raw.loc[1, "open_time"] = raw.open_time.iloc[0]
    elif fault == "unsorted":
        raw = raw.iloc[::-1]
    elif fault == "bad_close":
        raw.loc[0, "close_time"] += 1
    else:
        raw.loc[0, "open_time"] += 1
    with pytest.raises(ValueError):
        canonicalize(raw, "BTCUSDT", "2024-05", config)


def test_bad_header(tmp_path, config):
    raw = frame().rename(columns={"quote_volume": "made_up"})
    path = zipped(tmp_path, raw)
    with pytest.raises(ValueError, match="header"):
        parse_zip(path, "BTCUSDT", "2024-05", archive_url(config, "BTCUSDT", "2024-05"))


def test_gaps_invalid_and_zero_volume(config):
    raw = frame()
    raw.loc[2, "open_time"] += 60000
    raw.loc[2, "close_time"] += 60000
    df = canonicalize(raw, "BTCUSDT", "2024-05", config)
    assert not df.valid_return.iloc[2]
    assert len(df) == 3  # no fabricated missing bar
    raw.loc[1, "close"] = -1
    df = canonicalize(raw, "BTCUSDT", "2024-05", config)
    assert not df.valid_bar.iloc[1] and not df.valid_return.any()
    raw = frame()
    raw.loc[0, ["volume", "quote_volume", "count", "taker_buy_volume", "taker_buy_quote_volume"]] = 0
    df = canonicalize(raw, "BTCUSDT", "2024-05", config)
    assert df.valid_bar.iloc[0] and np.isnan(df.signed_taker_flow_ratio.iloc[0])
    assert df.signed_taker_quote_flow.iloc[0] == 0


def test_taker_bounds_mask_without_clipping(config):
    raw = frame()
    raw.loc[0, "taker_buy_quote_volume"] = 1200
    df = canonicalize(raw, "BTCUSDT", "2024-05", config)
    assert df.quality_bits.iloc[0] & 8
    assert df.taker_buy_quote_volume.iloc[0] == 1200
    assert not df.valid_return.iloc[1]


def test_boundaries_and_no_future_label(config):
    times = pd.DatetimeIndex(["2024-01-01", "2025-06-30 23:59", "2025-07-01", "2025-12-31 23:59", "2026-01-01", "2026-06-30 23:59"], tz="UTC")
    assert split_labels(times).tolist() == ["train", "train", "validation", "validation", "test", "test"]
    with pytest.raises(ValueError):
        split_labels(pd.DatetimeIndex(["2026-07-01"], tz="UTC"))
    with pytest.raises(ValueError):
        split_labels(pd.DatetimeIndex(["2025-01-01"]))
    raw = frame()
    previous = dict(symbol="BTCUSDT", open_time=int(raw.open_time.iloc[0]) - 60000, close=99, valid_bar=True)
    df = canonicalize(raw, "BTCUSDT", "2024-05", config, previous)
    assert df.close_to_close_log_return.iloc[0] == pytest.approx(np.log(100 / 99))
    previous["open_time"] -= 60000
    assert not canonicalize(raw, "BTCUSDT", "2024-05", config, previous).valid_return.iloc[0]
    previous["symbol"] = "ETHUSDT"
    with pytest.raises(ValueError):
        canonicalize(raw, "BTCUSDT", "2024-05", config, previous)


def test_month_boundary_return(config):
    start = pd.Timestamp("2025-07-01", tz="UTC").value // 10**6
    raw = frame([start, start + 60000, start + 120000])
    previous = dict(symbol="BTCUSDT", open_time=start - 60000, close=99, valid_bar=True)
    df = canonicalize(raw, "BTCUSDT", "2025-07", config, previous)
    assert df.valid_return.iloc[0] and df.split.iloc[0] == "validation"
    assert df.available_at_utc.iloc[0] == pd.Timestamp("2025-07-01 00:01", tz="UTC")


def test_buyer_maker_sign():
    np.testing.assert_array_equal(signed_trade_quote([100, 200], [3, 2], [True, False]), [-300, 400])


def test_future_rows_do_not_change_stale_diagnostic(config):
    start = pd.Timestamp("2024-05-01", tz="UTC").value // 10**6
    raw = pd.concat([frame().iloc[[0]]] * 40, ignore_index=True)
    raw["open_time"] = start + np.arange(40) * 60000
    raw["close_time"] = raw.open_time + 59999
    whole = canonicalize(raw, "BTCUSDT", "2024-05", config)
    prefix = canonicalize(raw.iloc[:20], "BTCUSDT", "2024-05", config)
    pd.testing.assert_frame_equal(whole.iloc[:20], prefix)
    assert not whole.stale_close_flag.iloc[:29].any()
    assert whole.stale_close_flag.iloc[29:].all()


def test_streamed_trade_aggregation(tmp_path):
    from cryptocrossimpact.data.trades import TRADE_HEADER, aggregate_zip
    start = pd.Timestamp("2024-05-06", tz="UTC").value // 10**6
    text = ",".join(TRADE_HEADER) + "\n"
    text += f"1,100,3,1,1,{start},true\n2,200,2,2,2,{start + 60000},false\n"
    path = tmp_path / "trades.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("BTCUSDT-aggTrades-2024-05-06.csv", text)
    totals, counts, metadata = aggregate_zip(path, "BTCUSDT", "2024-05-06")
    np.testing.assert_array_equal(totals[:2], [[-300, 300, 0], [400, 400, 400]])
    assert metadata["trade_rows"] == 2 and metadata["missing_aggregate_ids"] == 0
    assert counts[:2].tolist() == [1, 1]


def test_duplicate_trade_ids_rejected(tmp_path):
    from cryptocrossimpact.data.trades import TRADE_HEADER, aggregate_zip
    start = pd.Timestamp("2024-05-06", tz="UTC").value // 10**6
    text = ",".join(TRADE_HEADER) + "\n"
    text += f"1,100,3,1,1,{start},true\n1,100,2,2,2,{start + 1},false\n"
    path = tmp_path / "trades.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr("BTCUSDT-aggTrades-2024-05-06.csv", text)
    with pytest.raises(ValueError, match="Duplicate"):
        aggregate_zip(path, "BTCUSDT", "2024-05-06")


def test_cached_checksum_failure(tmp_path, config, monkeypatch):
    (tmp_path / "data/raw").mkdir(parents=True)
    path = tmp_path / "data/raw/BTCUSDT-1m-2024-05.zip"
    path.write_bytes(b"corrupted")
    source = PublicSource(tmp_path, config)
    monkeypatch.setattr(source, "checksum", lambda url: ("0" * 64, None))
    with pytest.raises(SourceError) as error:
        source.archive(archive_url(config, "BTCUSDT", "2024-05"))
    assert error.value.status == "CHECKSUM_ERROR"
    assert path.read_bytes() == b"corrupted"  # no destructive cleanup


def test_upstream_revision_hold(tmp_path, config, monkeypatch):
    source = PublicSource(tmp_path, config)
    monkeypatch.setattr(source, "checksum", lambda url: ("1" * 64, None))
    with pytest.raises(SourceError) as error:
        source.archive(archive_url(config, "BTCUSDT", "2024-05"), {"vendor_sha256": "0" * 64})
    assert error.value.status == "UPSTREAM_CHANGED"


def test_budget_guard(tmp_path, config):
    config["resources"]["stop_bytes"] = 10
    config["resources"]["initial_bytes"] = 0
    with pytest.raises(SourceError, match="30 GB"):
        PublicSource(tmp_path, config).guard(reserve=11)


@pytest.mark.integration
def test_real_vendor_pilots(config):
    manifest_path = ROOT / "data/registry/source_manifest.json"
    if not manifest_path.exists():
        pytest.skip("Acquire official pilot first")
    manifest = json.loads(manifest_path.read_text())
    for symbol in config["data"]["symbols"]:
        for month in config["pilot_months"]:
            entry = manifest["partitions"][f"{symbol}/{month}"]
            source = entry["sources"][0]
            raw_path = ROOT / source["local_archive"]
            assert sha256(raw_path) == source["vendor_sha256"] == source["sha256"]
            raw = parse_zip(raw_path, symbol, month, source["url"])
            canonical = pd.read_parquet(ROOT / entry["canonical_path"])
            pd.testing.assert_frame_equal(raw, canonical[COLUMNS], check_exact=True)
            assert len(canonical) == 31 * 1440
            assert canonical.valid_bar.all()
            np.testing.assert_array_equal(canonical.signed_taker_quote_flow,
                                          2 * raw.taker_buy_quote_volume - raw.quote_volume)


@pytest.mark.integration
def test_full_core_inventory(config):
    path = ROOT / "data/registry/qc_summary.json"
    if not path.exists():
        pytest.skip("Run full core QC first")
    summary = json.loads(path.read_text())
    assert summary["expected_partitions"] == 60
    assert summary["validated_partitions"] == 60
    assert not summary["missing_partitions"]
    assert summary["all_raw_canonical_checks"] == "PASS"
    assert sum(v["expected_minutes"] for v in summary["paired_by_split"].values()) == 912 * 1440
