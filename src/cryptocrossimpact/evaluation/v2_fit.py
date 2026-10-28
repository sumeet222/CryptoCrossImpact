"""Frozen-family sufficient-statistic refits with independent window L/normalizers."""
from dataclasses import dataclass
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.storage import sha256
from ..kernel.fit import Stats,transforms,normalize,estimate,predict,validate_components
from ..kernel.diagnostics import rescale_raw
from ..execution.impact_cost import ASSETS,UNITS,Kernel,cash_hessian,load_stage02
from ..execution.policies import AsOfKernel
from .v2_common import locations,save,config,digest
from .v2_data import utc,END
from .v2_features import construct_asof


def read_stats_once(path):
    with np.load(path,allow_pickle=False) as d:
        keys,n,g,x,y=[d[k] for k in ("keys","n","gram","xy","yy")]
    return {str(k):Stats(int(n[i]),g[i].copy(),x[i].copy(),y[i].copy()) for i,k in enumerate(keys)}


def E1_ridge(root):
    table=pd.read_csv(Path(root)/"reports/research/stage02_artifacts/candidate_selection.csv")
    rows=table[(table.model=="B")&(table.taus_minutes=="5;30")].copy()
    if len(rows)!=6 or not (rows.status=="optimal").all():raise ValueError("Invalid E1 development selection source")
    best=rows.validation_mse_pooled.min();near=rows[rows.validation_mse_pooled<=best/(1-.001)]
    chosen=float(near.sort_values("ridge",ascending=False).iloc[0].ridge)
    if chosen!=1.:raise ValueError("E1 choice differs from frozen v1")
    return chosen,rows


def window(origin,role):
    origin=utc(origin)
    if origin.day!=1 or origin!=origin.normalize():raise ValueError("Refit origin must be month start")
    if role=="E1":end=origin-pd.Timedelta(days=30);start=end-pd.Timedelta(days=180)
    elif role in ("A","B","N0"):end=origin;start=end-pd.Timedelta(days=365)
    else:raise ValueError("Unknown estimator role/U prohibited")
    return start,end


def validate_fit(model,origin,role):
    start,end=window(origin,role)
    if (model["role"]!=role or model["market"]!="futures/um" or model["venue"]!="Binance" or
        tuple(model["asset_order"])!=ASSETS or utc(model["training_start"])!=start or
        utc(model["training_end_exclusive"])!=end or utc(model["origin"])!=utc(origin) or
        model["units"]!=UNITS or model["status"]!="optimal" or model["ridge"]!=1 or
        model["taus_minutes"]!=([5,30] if role=="E1" else [] if role=="N0" else [60])):
        raise ValueError("Wrong fit window/role/market/normalization identity")
    if role!="N0":
        if model["model"] not in ("A","B") or not model["execution_kernel_export_allowed"]:raise ValueError("Diagnostic kernel prohibited")
        kernel=Kernel(ASSETS,model["matrices"],model["taus_minutes"],model["liquidity_usdt"],role,digest(model))
        if role=="A" and np.any(kernel.matrices[:,0,1]!=0):raise ValueError("A has cross impact")
        cash_hessian(kernel,60)
        return kernel
    return None


@dataclass(frozen=True)
class PolicyModel(AsOfKernel):
    def check(self,t0):
        t0=utc(t0)
        if self.training_end>t0 or self.training_start>=self.training_end or t0>=END:raise ValueError("Post-arrival/wrong model cutoff")
        if self.model_id.startswith("v2-") and self.training_end!=t0.normalize().replace(day=1):
            raise ValueError("Stale/wrong-month rolling policy model")


def policy_models(models,origin):
    result={}
    for role in ("A","B"):
        model=models[role];kernel=validate_fit(model,origin,role)
        result[role]=PolicyModel(kernel,utc(model["training_start"]),utc(model["training_end_exclusive"]),model["fit_id"],digest(model))
    return result


def fixed_policy_models(root):
    return {r:PolicyModel(load_stage02(root,r),pd.Timestamp("2024-01-01",tz="UTC"),pd.Timestamp("2025-07-01",tz="UTC"),
                         f"fixed-June2025-{r}",sha256(Path(root)/f"reports/research/stage02_artifacts/model_{r}.json")) for r in ("A","B")}


class Fitter:
    def __init__(self,root,store):
        self.root=Path(root);self.store=store;self.out,self.bulk=locations(root)
        f=json.loads((self.root/"reports/research/stage02_artifacts/features.json").read_text())
        self.base_l=np.array(f["liquidity_usdt"]);self.all_taus=f["all_taus"]
        if self.all_taus!=[2,5,10,30,60]:raise ValueError("Original sufficient-statistic basis changed")
        self.days=read_stats_once(self.root/"results/kernel_development/daily.npz")
        self.l_cache={};self.ridge,_=E1_ridge(root)

    def fit(self,origin,role,folder=None):
        origin=utc(origin);start,end=window(origin,role)
        if start<pd.Timestamp("2024-01-01",tz="UTC") or origin>END:raise ValueError("Unavailable fitting window")
        if origin.year>=2026:
            from .v2_protocol import validate_ready
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
        m.update(schema="stage05-asof-v2",role=role,origin=str(origin),training_start=str(start),training_end_exclusive=str(end),
            latest_target_open=str(end-pd.Timedelta(minutes=1)),latest_target_available=str(end),
            calendar_days=len(dates),expected_calendar_target_rows=len(dates)*1440,liquidity_usdt=l.tolist(),
            asset_order=list(ASSETS),venue="Binance",market="futures/um",memory_minutes=60,
            fit_id=f"v2-{origin.strftime('%Y-%m')}-{role}",source_manifest_sha256=sha256(self.root/"data/registry/source_manifest.json"),
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

    def restore_month(self,month):self.days.update(read_stats_once(self.bulk/"daily_stats"/f"{month}.npz"))

    def h1(self,frame,x,y,valid,models):
        month=pd.Timestamp(frame.time.iloc[0]).strftime("%Y-%m");daily=[]
        dates=pd.DatetimeIndex(frame.time).strftime("%Y-%m-%d")
        for role in ("N0","A","B"):
            m=models[role];l=np.array(m["liquidity_usdt"]);ratio=np.sqrt(self.base_l/l)
            design=x.copy();design[:,25:]*=np.tile(ratio,len(self.all_taus))
            target=y/ratio;pred=predict(m,design);ys=np.array(m["normalization"]["target_scale"])
            standardized=(target-pred)/ys;error_bps=(target-pred)/np.sqrt(l);actual_bps=target/np.sqrt(l)
            for day in np.unique(dates):
                mask=valid&(dates==day)
                for i,asset in enumerate(ASSETS):
                    daily.append(dict(day=day,month=month,model=role,asset=asset,n=int(mask.sum()),
                        standardized_sse=float(np.sum(standardized[mask,i]**2)),error_bps_sse=float(np.sum(error_bps[mask,i]**2)),
                        error_bps_sae=float(np.sum(np.abs(error_bps[mask,i]))),target_bps_sum=float(actual_bps[mask,i].sum()),
                        target_bps_sumsq=float(np.sum(actual_bps[mask,i]**2)),fit_id=m["fit_id"]))
        return daily
