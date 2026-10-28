"""Time-authorized adapters of the frozen Stage 2/4 feature mathematics.

Bodies below are copied without changing numerical formulas; only development
date guards/record class differ. Pretest parity checks bind exact 2025 outputs
to the original functions. Original source remains untouched.
"""
from dataclasses import dataclass
import numpy as np
import pandas as pd

from ..episodes import Episode,EpisodeUnavailable
from ..kernel.features import flow_basis,RETURN_LAGS,ACTIVITY,VOLS
from ..execution.impact_cost import ASSETS,psd_diagnostics
from .v2_data import utc,END


def checked_arrival(t0):
    t0=utc(t0)
    if not pd.Timestamp("2025-07-01",tz="UTC")<=t0<END:raise ValueError("Out-of-scope arrival")
    return t0


def guard_times(times):
    times=pd.DatetimeIndex(times)
    if times.tz is None or str(times.tz)!="UTC" or (times>=END).any():raise ValueError("Wrong feature clock")


@dataclass(frozen=True)
class EpisodeV2(Episode):
    def __post_init__(self):
        checked_arrival(self.t0)
        for name in ("forecast","covariance","initial","p0"):
            a=np.array(getattr(self,name),dtype=float,copy=True);a.setflags(write=False);object.__setattr__(self,name,a)
        if self.provenance["forecast_kind"]!="past_only_hour_of_week_median":raise ValueError("Realized volume is not a forecast")
        if utc(self.provenance["latest_available_at"])>self.t0 or utc(self.provenance["latest_open"])>=self.t0:raise ValueError("Future episode input")
        if self.forecast.ndim!=2 or self.forecast.shape[1]!=2 or not np.isfinite(self.forecast).all() or (self.forecast<=0).any():raise ValueError("Invalid forecast")
        if self.initial.shape!=(2,) or (self.initial<=0).any() or not np.isfinite(self.initial).all():raise ValueError("Invalid inventory")
        if self.p0.shape!=(2,) or not np.isfinite(self.p0).all() or (self.p0<=0).any():raise ValueError("Invalid arrival price")
        psd_diagnostics(self.covariance)


def make_episode(frame,t0,cfg):
    """Slice available history BEFORE examining numeric fields; future mutation safe.

    Complete paired history is required. Verified zeros are retained in medians;
    floor is past-positive 1st percentile. Returns use two closes inside window,
    so 28d supplies 40319 one-minute returns, not a cross-window return.
    """
    t0=checked_arrival(t0);start=t0-pd.Timedelta(days=cfg["history_days"])
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
        forecast_units="USDT per one-minute bin",inventory_units="reference USDT",test_outcomes_unopened=(t0.year<2026))
    return EpisodeV2(t0.strftime("%Y%m%dT%H%MZ"),t0,forecast,covariance,cfg["initial_fraction"]*forecast.sum(axis=0),closes[-1],provenance)


def construct_asof(frame, liquidity, taus, memory=60, mode="primary"):
    """Return raw design, y and common eligibility; windows end at target t-1.

    r_t and f_t are available after target bar completion. Nuisances never use
    target-bar prices/volumes. Full 1440-return history and target must be valid.
    """
    guard_times(frame.time)
    if not np.all(np.isfinite(liquidity)) or np.any(np.asarray(liquidity) <= 0):
        raise ValueError("Positive training-only liquidity units required")
    n = len(frame)
    controls, valid = [], np.ones(n, dtype=bool)
    f = np.zeros((n, 2))
    r = np.zeros((n, 2))
    for j in range(2):
        ret = frame[f"close_to_close_log_return_{j}"]
        volume = frame[f"quote_volume_{j}"]
        controls.extend(ret.shift(lag).to_numpy() for lag in RETURN_LAGS)
        controls.extend(np.log1p(volume.shift(1).rolling(w, min_periods=w).mean()).to_numpy() for w in ACTIVITY)
        med = volume.shift(1).rolling(1440, min_periods=1440).median()
        controls.append((np.log1p(volume.shift(1)) - np.log1p(med)).to_numpy())
        controls.extend(np.sqrt(ret.shift(1).pow(2).rolling(w, min_periods=w).mean()).to_numpy() for w in VOLS)
        past_good = frame[f"valid_return_{j}"].astype(int).shift(1).rolling(1440, min_periods=1440).sum()
        valid &= (past_good.to_numpy() == 1440) & frame[f"valid_return_{j}"].to_numpy() & frame[f"valid_bar_{j}"].to_numpy()
        f[:, j] = frame[f"signed_taker_quote_flow_{j}"].to_numpy() / np.sqrt(liquidity[j])
        r[:, j] = ret.to_numpy()
    time = pd.DatetimeIndex(frame.time)
    tod = (time.hour * 60 + time.minute).to_numpy() / 1440
    dow = (time.day_of_week.to_numpy() + tod) / 7
    controls.extend([np.sin(2*np.pi*tod), np.cos(2*np.pi*tod), np.sin(2*np.pi*dow), np.cos(2*np.pi*dow)])
    basis = flow_basis(f, taus, memory, mode)
    design = np.column_stack([np.ones(n), *controls, basis.reshape(n, -1)])
    y = 1e4 * np.sqrt(liquidity) * r
    # Calendar continuity catches an omitted minute even when all stored flags pass.
    clock = frame.open_time
    valid &= (clock - clock.shift(1440)).to_numpy() == 1440 * 60000
    valid &= np.isfinite(design).all(axis=1) & np.isfinite(y).all(axis=1)
    return design, y, valid

