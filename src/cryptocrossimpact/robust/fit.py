"""Original sufficient-statistic estimator, isolated X2+X3 writes and gate."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from ..data.storage import sha256
from ..kernel.fit import Stats,transforms,normalize,estimate
from ..kernel.diagnostics import rescale_raw
from ..execution.impact_cost import ASSETS,cash_hessian
from ..evaluation.v2_fit import read_stats_once,E1_ridge,window,validate_fit
from .features import construct_asof
from .data import utc
from .common import paths,save,START
END=pd.Timestamp("2026-10-01",tz="UTC")

class Fitter:
    def __init__(self,root,store):
        self.root=Path(root);self.store=store;self.out,self.bulk=paths(root)
        f=json.loads((self.root/'reports/research/stage02_artifacts/features.json').read_text())
        self.base_l=np.array(f['liquidity_usdt']);self.all_taus=f['all_taus']
        self.days=read_stats_once(self.root/'results/kernel_development/daily.npz')
        # Jan-Jun2026 is already inspected history, used for elapsed fits only.
        for m in pd.period_range('2026-01','2026-06',freq='M').astype(str):
            self.days.update(read_stats_once(self.root/'results/stage05_exfunding_v2/daily_stats'/f'{m}.npz'))
        for file in sorted((self.bulk/'daily_stats').glob('*.npz')):
            self.days.update(read_stats_once(file))
        self.l_cache={};self.ridge,_=E1_ridge(root)

    def fit(self,origin,role,folder=None):
        origin=utc(origin);start,end=window(origin,role)
        if start<pd.Timestamp("2024-01-01",tz="UTC") or origin>END:raise ValueError("Unavailable fitting window")
        if origin>=pd.Timestamp(START):
            from .protocol import validate_ready
            validate_ready(self.root)
        folder=Path(folder) if folder else self.out/"models";folder.mkdir(parents=True,exist_ok=True)
        path=folder/f"{origin.strftime('%Y-%m')}_{role}.json"
        if path.exists():
            m=json.loads(path.read_text());validate_fit(m,origin,role);return m
        dates=pd.date_range(start,end,freq="D",inclusive="left").strftime("%Y-%m-%d")
        if any(day not in self.days for day in dates):raise ValueError("Missing full calendar-day fit block; no silent shortening")
        raw=Stats.zeros(len(next(iter(self.days.values())).xy))
        for day in dates:raw.add(self.days[day])
        key=(str(start),str(end))
        if key not in self.l_cache:
            data=self.store.paired(start,end,purpose="refit",asof=end)
            expected=pd.date_range(start,end,freq="min",inclusive="left")
            if not pd.DatetimeIndex(data.time).equals(expected):raise ValueError("Incomplete calibration source calendar")
            self.l_cache[key]=np.array([np.median(data.loc[data[f"valid_bar_{i}"]&(data[f"quote_volume_{i}"]>0),f"quote_volume_{i}"]) for i in range(2)])
        l=self.l_cache[key]
        converted=rescale_raw(raw,self.base_l,l);normal=transforms(converted)
        m=estimate(normalize(converted,normal),normal,[5,30] if role=="E1" else [60],self.all_taus,"B" if role=="E1" else role,self.ridge if role=="E1" else 1)
        m.update(schema="x2x3-asof-v1",role=role,origin=str(origin),training_start=str(start),training_end_exclusive=str(end),
            latest_target_open=str(end-pd.Timedelta(minutes=1)),latest_target_available=str(end),
            calendar_days=len(dates),expected_calendar_target_rows=len(dates)*1440,liquidity_usdt=l.tolist(),
            asset_order=list(ASSETS),venue="Binance",market="futures/um",memory_minutes=60,
            fit_id=f"x2x3-{origin.strftime('%Y-%m')}-{role}",source_manifest_sha256=sha256(self.root/"data/registry/source_manifest.json"),
            raw_statistics_coordinate_liquidity=self.base_l.tolist(),normalization_estimated_on="own eligible target window only",
            return_basis="G(0) current; G(l)-G(l-1) lags 1..H; no H+1 tail term",
            source_partition_ids=[f"{s}/{p}" for p in pd.period_range(start.tz_localize(None),(end-pd.Timedelta(minutes=1)).tz_localize(None),freq="M").astype(str) for s in ASSETS])
        kernel=validate_fit(m,origin,role)
        if kernel is not None:m["exact_cell_hessian_diagnostics"]=cash_hessian(kernel,60)[1]
        save(path,m);return m

    def observe_month(self,month):
        """Called AFTER that month's schedules/scores; retain only daily stats."""
        start=pd.Timestamp(month+"-01",tz="UTC");end=start+pd.offsets.MonthBegin(1)
        frame=self.store.paired(start-pd.Timedelta(minutes=1441),end,purpose="observed_month",asof=end)
        x,y,valid=construct_asof(frame,self.base_l,self.all_taus)
        take=(frame.time>=start).to_numpy();frame=frame.loc[take].reset_index(drop=True);x=x[take];y=y[take];valid=valid[take]
        dates=pd.DatetimeIndex(frame.time).strftime("%Y-%m-%d");records={}
        for day in np.unique(dates):
            mask=valid&(dates==day);records[str(day)]=Stats.rows(x[mask],y[mask]);self.days[str(day)]=records[str(day)]
        folder=self.bulk/"daily_stats";folder.mkdir(exist_ok=True)
        np.savez_compressed(folder/f"{month}.npz",keys=np.array(list(records)),n=np.array([s.n for s in records.values()]),
            gram=np.stack([s.gram for s in records.values()]),xy=np.stack([s.xy for s in records.values()]),yy=np.stack([s.yy for s in records.values()]))
        return frame,x,y,valid
