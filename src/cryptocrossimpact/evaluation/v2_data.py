"""Hash-gated, bounded, filtered reads. No caller-controlled ready boolean."""
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.storage import sha256,utcnow
from ..kernel.features import ASSETS

FIREWALL=pd.Timestamp("2026-01-01",tz="UTC")
END=pd.Timestamp("2026-07-01",tz="UTC")


def utc(t):
    t=pd.Timestamp(t)
    if t.tz is None or str(t.tz)!="UTC":raise ValueError("Explicit UTC required")
    return t


class HistoricalStore:
    """Only returned rows within [start,end); asof limits all history reads.

    Integrity hashing reads whole source bytes AFTER readiness for 2026 files.
    PyArrow row filters return only authorized rows; future values cannot reach
    forecasting/refit code even if a physical Parquet row group spans the month.
    """
    def __init__(self,root):
        self.root=Path(root);self.manifest=json.loads((self.root/"data/registry/source_manifest.json").read_text())
        m=self.manifest
        if (m["venue"],m["market"],m["interval"],m["price_type"])!=("Binance","futures/um","1m","last traded price"):
            raise ValueError("Wrong venue/market/clock/price identity")
        self.verified={};self.read_log=[]

    def paired(self,start,end,*,purpose,asof=None,receipt=None):
        start,end=utc(start),utc(end)
        if start>=end or end>END:raise ValueError("Invalid history range")
        if purpose not in ("refit","decision","observed_month","score","pretest"):
            raise ValueError("Unidentified data purpose")
        if purpose in ("refit","decision","pretest") and (asof is None or end>utc(asof)):
            raise ValueError("History endpoint exceeds as-of cutoff")
        months=pd.period_range(start.tz_localize(None),(end-pd.Timedelta(minutes=1)).tz_localize(None),freq="M").astype(str)
        # Barrier is BEFORE path stat, fingerprint, open or Parquet I/O.
        if any(m>="2026-01" for m in months):
            if os.environ.get("CCI_PRETEST_ONLY")=="1":raise ValueError("Pretest process refuses 2026 before I/O")
            from .v2_protocol import validate_ready
            validate_ready(self.root)
            if purpose=="observed_month":
                from .v2_run import verify_closed_month
                verify_closed_month(self.root,end)
        if purpose=="score":
            from .v2_run import verify_receipt
            data=verify_receipt(receipt)
            if utc(data["t0"])!=start or start+pd.Timedelta(minutes=data["horizon_minutes"])!=end:
                raise ValueError("Outcome range disagrees with persisted decision")
        if any(m>="2026-01" for m in months):
            from .v2_common import locations,save
            out,_=locations(self.root);first=out/"first_outcome_open_v2.json"
            if not first.exists():save(first,dict(utc=utcnow(),purpose=purpose,start=str(start),end_exclusive=str(end),
                ready_sha256=sha256(out/"pretest_ready_v2.json"),decision_receipt_sha256=receipt["sha256"] if receipt else None))
        frames=[]
        cols=["open_time","bar_open_utc","available_at_utc","open","high","low","close","quote_volume",
              "signed_taker_quote_flow","close_to_close_log_return","valid_bar","valid_return","stale_close_flag","jump_flag"]
        for month in months:
            legs=[]
            for symbol in ASSETS:
                entry=self.manifest["partitions"][f"{symbol}/{month}"];path=self.root/entry["canonical_path"]
                if path not in self.verified:
                    if sha256(path)!=entry["canonical_sha256"]:raise ValueError("Canonical source hash changed")
                    self.verified[path]=entry["canonical_sha256"]
                frame=pd.read_parquet(path,columns=cols,filters=[("bar_open_utc",">=",start),("bar_open_utc","<",end)])
                if not (frame.available_at_utc==frame.bar_open_utc+pd.Timedelta(minutes=1)).all():raise ValueError("Wrong completed-bar time")
                if not ((frame.bar_open_utc>=start)&(frame.bar_open_utc<end)).all():raise ValueError("Filtered reader leaked rows")
                legs.append(frame)
                self.read_log.append(dict(partition=f"{symbol}/{month}",purpose=purpose,start=str(start),end_exclusive=str(end),
                    asof=str(asof) if asof is not None else None,rows=len(frame),utc=utcnow()))
            a,b=legs
            if not np.array_equal(a.open_time,b.open_time):raise ValueError("Unmatched paired timestamps")
            out=pd.DataFrame(dict(time=a.bar_open_utc.to_numpy(),open_time=a.open_time.to_numpy()))
            out["time"]=pd.to_datetime(out.time,utc=True)
            for i,leg in enumerate(legs):
                for col in cols[3:]:out[f"{col}_{i}"]=leg[col].to_numpy()
            frames.append(out)
        result=pd.concat(frames,ignore_index=True)
        if result.time.duplicated().any() or not result.time.is_monotonic_increasing:raise ValueError("Duplicate/unordered source")
        return result
