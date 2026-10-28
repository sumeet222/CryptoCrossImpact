"""Time-authorized X1-compatible volume/episode adapters; gated source access."""
from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np
import pandas as pd

from ..data.storage import sha256,utcnow
from ..episodes import config as policy_config
from ..liquidity.forecasts import seasonal
from ..execution.impact_cost import ASSETS,psd_diagnostics
from ..execution.solver import build_problem
from .common import paths,save,digest,START,END


def utc(t):
    t=pd.Timestamp(t)
    if t.tz is None or str(t.tz)!='UTC':raise ValueError('Explicit UTC required')
    return t


def forecast(frame,t,targets,profile=None):
    """Exact X1 V0/V1 formulas, with new period authorized by the caller's reader."""
    t=utc(t);targets=pd.DatetimeIndex(targets)
    if (targets<t).any() or (targets>=utc(END)).any():raise ValueError('Target outside authorized clock')
    start=t-pd.Timedelta(days=28);h=frame.loc[(frame.time>=start)&(frame.time<t)].sort_values('time')
    expected=pd.date_range(start,t,freq='min',inclusive='left')
    if not pd.DatetimeIndex(h.time).equals(expected):raise ValueError('Incomplete paired history')
    how=h.time.dt.day_of_week.to_numpy()*24+h.time.dt.hour.to_numpy();hod=h.time.dt.hour.to_numpy()
    keys=targets.day_of_week*24+targets.hour;v0=np.empty((len(targets),2));floors=[]
    for i in range(2):
        v=h[f'quote_volume_{i}'].to_numpy()
        if not h[f'valid_bar_{i}'].all() or not np.isfinite(v).all() or (v<0).any() or not (v>0).any():raise ValueError('Invalid completed turnover')
        floor=max(float(np.quantile(v[v>0],.01)),1e-8);floors.append(floor)
        for key in np.unique(keys):
            sample=v[how==key]
            if len(sample)<120:sample=v[hod==key%24]
            if len(sample)<120:sample=v
            v0[keys==key,i]=max(float(np.median(sample)),floor)
    p,qa=seasonal(frame,t) if profile is None else profile
    v1=np.maximum(v0*p[targets.minute],floors)
    return dict(V0=v0,V1=v1,floor=np.array(floors),qa=dict(**qa,latest_open=str(h.time.iloc[-1]),latest_available_at=str(t)))


@dataclass(frozen=True)
class Episode:
    episode_id:str
    t0:pd.Timestamp
    forecast:np.ndarray
    covariance:np.ndarray
    initial:np.ndarray
    p0:np.ndarray
    @property
    def input_hash(self):return digest(dict(t0=str(self.t0),V0=self.forecast,Sigma=self.covariance,X0=self.initial,P0=self.p0))


def make_episode(h,t,root):
    t=utc(t);p=forecast(h,t,pd.date_range(t,periods=60,freq='min'))
    known=h.loc[(h.time>=t-pd.Timedelta(days=28))&(h.time<t)].sort_values('time')
    if not np.array_equal(known.open_time.to_numpy(),pd.DatetimeIndex(known.time).as_unit('ms').asi8):raise ValueError('Wrong millisecond clock')
    close=known[['close_0','close_1']].to_numpy()
    if not np.isfinite(close).all() or (close<=0).any():raise ValueError('Invalid past price')
    returns=np.diff(np.log(close),axis=0)
    if len(returns)<40000:raise ValueError('Insufficient covariance returns')
    sigma=np.cov(returns,rowvar=False,ddof=1);psd_diagnostics(sigma)
    return Episode(t.strftime('%Y%m%dT%H%MZ'),t,p['V0'],sigma,.02*p['V0'].sum(axis=0),close[-1].copy())


class Store:
    """No 2026-Q3 path stat/hash/Parquet read without verified ready evidence.

    Only bounded rows are returned; rolling context never holds future policy
    rows. Scores/refits use distinct instances/call purposes.
    """
    def __init__(self,root):
        self.root=Path(root);m=json.loads((self.root/'data/registry/source_manifest.json').read_text())
        if (m['venue'],m['market'],m['interval'],m['price_type'])!=('Binance','futures/um','1m','last traded price'):raise ValueError('Wrong market identity')
        self.manifest=m;self.read_log=[];self.verified={};self.context=None;self.context_end=None;self.profile_cache={}

    def paired(self,start,end,purpose='decision',asof=None,commitment=None,full=False):
        start,end=utc(start),utc(end);asof=end if asof is None else utc(asof)
        if start>=end or end>asof or end>utc(END):raise ValueError('As-of/end refusal before I/O')
        if purpose=='score':
            from .protocol import verify_decisions
            if commitment is None:raise ValueError('Missing immutable decision receipt')
            verify_decisions(self.root,commitment)
        if purpose=='observed_month':full=True
        if end>utc(START):
            from .protocol import validate_ready
            ready=validate_ready(self.root)
            if purpose in ('refit','observed_month'):
                from .protocol import require_closed_history
                require_closed_history(self.root,end)
            out,_=paths(self.root)
            if purpose=='score' and (commitment is None or not Path(commitment).exists()):raise ValueError('Missing immutable decisions before score')
            if purpose=='decision' and start>=utc(START) and commitment is not None:
                record=json.loads(Path(commitment).read_text())
                if utc(record['revealed_until'])<end:raise ValueError('Prefix reveal authorization too early')
            new=json.loads((out/'new_source_manifest.json').read_text());self.manifest['partitions'].update(new['partitions'])
        cols=['bar_open_utc','open_time','available_at_utc','close','quote_volume','valid_bar','jump_flag','stale_close_flag']
        if full:cols+=['signed_taker_quote_flow','close_to_close_log_return','valid_return']
        months=pd.period_range(start.tz_localize(None),(end-pd.Timedelta(minutes=1)).tz_localize(None),freq='M').astype(str);frames=[]
        for month in months:
            legs=[]
            for symbol in ASSETS:
                entry=self.manifest['partitions'][f'{symbol}/{month}'];path=self.root/entry['canonical_path']
                if path not in self.verified:
                    if sha256(path)!=entry['canonical_sha256']:raise ValueError('Source fingerprint changed')
                    self.verified[path]=True
                f=pd.read_parquet(path,columns=cols,filters=[('bar_open_utc','>=',start),('bar_open_utc','<',end)])
                if not ((f.bar_open_utc>=start)&(f.bar_open_utc<end)&(f.available_at_utc<=asof)).all() or not (f.available_at_utc==f.bar_open_utc+pd.Timedelta(minutes=1)).all():raise ValueError('Bounded availability violation')
                legs.append(f)
                self.read_log.append(dict(partition=f'{symbol}/{month}',purpose=purpose,start=str(start),end=str(end),asof=str(asof),rows=len(f)))
            a,b=legs
            if not np.array_equal(a.open_time,b.open_time):raise ValueError('Pair clock mismatch')
            f=pd.DataFrame(dict(time=pd.to_datetime(a.bar_open_utc,utc=True),open_time=a.open_time.to_numpy()))
            for i,leg in enumerate(legs):
                for name in cols[3:]:f[f'{name}_{i}']=leg[name].to_numpy()
            frames.append(f)
        return pd.concat(frames,ignore_index=True)

    def history(self,t,commitment=None):
        t=utc(t);start=t.normalize()-pd.Timedelta(days=28)
        if self.context is None or self.context_end>t or self.context.time.iloc[0]>start:
            self.context=self.paired(start,t,asof=t,commitment=commitment)
        elif self.context_end<t:
            self.context=pd.concat([self.context.loc[self.context.time>=start],self.paired(self.context_end,t,asof=t,commitment=commitment)],ignore_index=True)
        self.context_end=t;return self.context.copy()

    def forecast(self,t,targets,commitment=None):
        h=self.history(t,commitment);key=str(utc(t).normalize())
        if key not in self.profile_cache:self.profile_cache={key:seasonal(h,t)}
        return forecast(h,t,targets,self.profile_cache[key]),h
