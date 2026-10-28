"""Development-only, frozen causal episode inputs. No outcome/cost scorer.

Canonical time is bar OPEN; availability is open+1min. A t0 decision includes
the bar opening t0-1min, never the bar opening t0. Volume is USDT/bin and
covariance is fractional log-return variance per minute (no extra delta here).
"""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from .kernel.features import DevelopmentStore, FIREWALL
from .execution.impact_cost import ASSETS, psd_diagnostics


def utc(value):
    value=pd.Timestamp(value)
    if value.tz is None or str(value.tz)!="UTC":
        raise ValueError("Explicit UTC required")
    return value


def guard_arrival(value):
    value=utc(value)
    if value < pd.Timestamp("2025-07-01",tz="UTC") or value>=FIREWALL:
        raise ValueError("Stage 4 firewall: development arrivals only; refused before I/O")
    return value


def config(root):
    return yaml.safe_load((Path(root)/"configs/stage04_policies.yaml").read_text())


def arrivals(start="2025-07-01T00:00:00Z",end="2026-01-01T00:00:00Z",hours=(0,6,12,18)):
    start=guard_arrival(start);end=utc(end)
    if end>FIREWALL or end<=start:raise ValueError("Stage 4 date firewall")
    return pd.DatetimeIndex([d+pd.Timedelta(hours=h) for d in pd.date_range(start.normalize(),end.normalize(),freq="D")
                            for h in hours if start<=d+pd.Timedelta(hours=h)<end])


class EpisodeUnavailable(ValueError):
    """Objective common input-quality exclusion, never a policy preference."""


class EpisodeStore(DevelopmentStore):
    """Reuse Stage 2 checksummed loader; retain at most two monthly frames."""
    def __init__(self,root):
        super().__init__(root);self.cache={}

    def history(self,t0,days=28):
        t0=guard_arrival(t0);start=t0-pd.Timedelta(days=days)
        months=pd.period_range(start.tz_localize(None),(t0-pd.Timedelta(minutes=1)).tz_localize(None),freq="M").astype(str)
        self.cache={k:v for k,v in self.cache.items() if k in months}
        for month in months:
            if month not in self.cache:self.cache[month]=self.paired(month)
        frame=pd.concat([self.cache[m] for m in months],ignore_index=True)
        return frame.loc[(frame.time>=start)&(frame.time<t0)].copy()


@dataclass(frozen=True)
class Episode:
    episode_id: str
    t0: pd.Timestamp
    forecast: np.ndarray
    covariance: np.ndarray
    initial: np.ndarray
    p0: np.ndarray
    provenance: dict

    def __post_init__(self):
        guard_arrival(self.t0)
        for name in ("forecast","covariance","initial","p0"):
            a=np.array(getattr(self,name),dtype=float,copy=True);a.setflags(write=False)
            object.__setattr__(self,name,a)
        if self.provenance.get("forecast_kind")!="past_only_hour_of_week_median":
            raise ValueError("Realized/unknown volume is not a forecast")
        if utc(self.provenance["latest_available_at"])>self.t0 or utc(self.provenance["latest_open"])>=self.t0:
            raise ValueError("Episode inputs leak after arrival")
        if self.forecast.ndim!=2 or self.forecast.shape[1]!=2 or (self.forecast<=0).any() or not np.isfinite(self.forecast).all():
            raise ValueError("Invalid forecast units/shape")
        if self.initial.shape!=(2,) or (self.initial<=0).any() or not np.isfinite(self.initial).all():raise ValueError("Invalid initial inventory")
        if self.p0.shape!=(2,) or not np.isfinite(self.p0).all() or (self.p0<=0).any():raise ValueError("Invalid arrival close")
        psd_diagnostics(self.covariance)

    @property
    def input_hash(self):
        h=hashlib.sha256(self.episode_id.encode())
        for a in (self.forecast,self.covariance,self.initial,self.p0):h.update(a.tobytes())
        h.update(json.dumps(self.provenance,sort_keys=True).encode())
        return h.hexdigest()


def construct_episode(frame,t0,cfg):
    """Slice available history BEFORE examining numeric fields; future mutation safe.

    Complete paired history is required. Verified zeros are retained in medians;
    floor is past-positive 1st percentile. Returns use two closes inside window,
    so 28d supplies 40319 one-minute returns, not a cross-window return.
    """
    t0=guard_arrival(t0);start=t0-pd.Timedelta(days=cfg["history_days"])
    hist=frame.loc[(frame.time>=start)&(frame.time<t0)].copy().sort_values("time")
    expected=pd.date_range(start,t0,freq="min",inclusive="left")
    if not pd.DatetimeIndex(hist.time).equals(expected):raise EpisodeUnavailable("missing_duplicate_history_minute")
    if not np.array_equal(hist.open_time.to_numpy(),expected.as_unit("ms").asi8):raise ValueError("Wrong UTC millisecond clock")
    if "available_at_utc" in hist and not (hist.available_at_utc==hist.time+pd.Timedelta(minutes=1)).all():
        raise ValueError("Wrong completed-bar availability")
    n=int(cfg["horizon_minutes"])
    if cfg["delta_minutes"]!=1 or n<1:raise ValueError("Empirical episode grid must be one minute")
    future=pd.date_range(t0,periods=n,freq="min")
    how=hist.time.dt.day_of_week.to_numpy()*24+hist.time.dt.hour.to_numpy()
    hod=hist.time.dt.hour.to_numpy();target=future.day_of_week*24+future.hour
    forecast=np.empty((n,2));closes=np.empty((len(hist),2));details=[]
    for i in range(2):
        if not hist[f"valid_bar_{i}"].all():raise EpisodeUnavailable("invalid_history_bar")
        v=hist[f"quote_volume_{i}"].to_numpy(dtype=float);closes[:,i]=hist[f"close_{i}"]
        if not np.isfinite(v).all() or (v<0).any() or not np.isfinite(closes[:,i]).all() or (closes[:,i]<=0).any():
            raise EpisodeUnavailable("invalid_history_value")
        positive=v[v>0]
        if not len(positive):raise EpisodeUnavailable("no_positive_past_turnover")
        floor=max(float(np.quantile(positive,cfg["floor_positive_quantile"])),cfg["floor_epsilon_usdt"])
        fallback={"hour_of_week":0,"hour_of_day":0,"overall":0};floor_count=0;counts=[]
        for key in np.unique(target):
            take=target==key;sample=v[how==key];kind="hour_of_week"
            if len(sample)<cfg["fine_class_minimum"]:
                sample=v[hod==key%24];kind="hour_of_day"
                if len(sample)<cfg["coarse_class_minimum"]:sample=v;kind="overall"
            estimate=float(np.median(sample));floor_count+=int(take.sum())*(estimate<floor)
            forecast[take,i]=max(estimate,floor);fallback[kind]+=int(take.sum());counts.append(len(sample))
        details.append(dict(asset=ASSETS[i],floor_usdt=floor,floor_bins=floor_count,class_bins=fallback,
                            minimum_class_count=min(counts),zero_turnover_bars=int((v==0).sum())))
    returns=np.diff(np.log(closes),axis=0)
    if len(returns)<cfg["minimum_covariance_returns"]:raise EpisodeUnavailable("insufficient_covariance_returns")
    covariance=np.cov(returns,rowvar=False,ddof=1);psd=psd_diagnostics(covariance)
    # np.cov is symmetric/PSD constructively; no eigenvalue clipping applied.
    provenance=dict(venue="Binance",market="futures/um",price_type="last traded price",asset_order=list(ASSETS),
        history_start=str(start),history_end_exclusive=str(t0),latest_open=str(hist.time.iloc[-1]),latest_available_at=str(t0),
        history_rows=len(hist),covariance_returns=len(returns),covariance_convention="sample_ddof1; consecutive log closes inside 28d; per-minute",
        covariance_psd=psd,forecast_kind=cfg["forecast_kind"],forecast_qa=details,
        diagnostic_jump_bars=sum(int(hist[f"jump_flag_{i}"].sum()) for i in range(2)),
        diagnostic_stale_bars=sum(int(hist[f"stale_close_flag_{i}"].sum()) for i in range(2)),
        forecast_units="USDT per one-minute bin",inventory_units="reference USDT",test_outcomes_unopened=True)
    return Episode(t0.strftime("%Y%m%dT%H%MZ"),t0,forecast,covariance,cfg["initial_fraction"]*forecast.sum(axis=0),closes[-1],provenance)
