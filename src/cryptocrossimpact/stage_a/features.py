"""Causal per-minute V1 state and receiver-specific return-response design."""
import numpy as np
import pandas as pd
from scipy.signal import lfilter
from ..kernel.features import construct,feature_names,guard_times
from ..liquidity.forecasts import seasonal
from .state import multipliers

TAUS=[5,30,60]
NC=1+len(feature_names())


def monthly_state(frame,month):
    """Compute existing V1 at EACH minute from opens<t; bounded monthly panel.

    January2024 uses explicit identity state only: there is no earlier data.
    Otherwise require28 complete days at month start. Vref fixed for month.
    """
    guard_times(frame.time);origin=pd.Timestamp(month+'-01',tz='UTC');end=origin+pd.offsets.MonthBegin(1)
    take=(frame.time>=origin)&(frame.time<end);times=pd.DatetimeIndex(frame.time);n=len(frame)
    if month=='2024-01':return np.ones((int(take.sum()),2)),None,dict(identity_warmup=int(take.sum()),month=month)
    h=frame.loc[(frame.time>=origin-pd.Timedelta(days=28))&(frame.time<origin)]
    if len(h)!=40320:raise ValueError('State missing month-start28d history')
    reference=np.array([np.median(h.loc[h[f'valid_bar_{i}']&(h[f'quote_volume_{i}']>0),f'quote_volume_{i}']) for i in range(2)])
    how=np.asarray(times.day_of_week*24+times.hour);hod=np.asarray(times.hour);v0=np.empty((n,2));floors=np.empty_like(v0)
    for i in range(2):
        volume=frame[f'quote_volume_{i}'].to_numpy();level=np.full(n,np.nan)
        for key in np.unique(how):
            ix=np.flatnonzero(how==key);s=pd.Series(volume[ix],index=times[ix])
            level[ix]=s.rolling('28D',closed='left',min_periods=120).median().to_numpy()
        missing=~np.isfinite(level)
        if missing.any():
            for key in np.unique(hod[missing]):
                ix=np.flatnonzero(hod==key);s=pd.Series(volume[ix],index=times[ix]);values=s.rolling('28D',closed='left',min_periods=120).median().to_numpy()
                use=missing[ix];level[ix[use]]=values[use]
        s=pd.Series(volume,index=times);fallback=s.rolling('28D',closed='left',min_periods=1).median().to_numpy();level=np.where(np.isfinite(level),level,fallback)
        positive=pd.Series(np.where(volume>0,volume,np.nan),index=times)
        floor=positive.rolling('28D',closed='left',min_periods=1).quantile(.01).to_numpy()
        floors[:,i]=np.maximum(floor,1e-8);v0[:,i]=np.maximum(level,floors[:,i])
    result=np.full((n,2),np.nan)
    for day in pd.date_range(origin,end,freq='D',inclusive='left'):
        profile,_=seasonal(frame,day);ix=np.flatnonzero((times>=day)&(times<day+pd.Timedelta(days=1)))
        result[ix]=np.maximum(v0[ix]*profile[times[ix].minute],floors[ix])
    if not np.isfinite(result[take]).all():raise ValueError('Incomplete causal V1 state')
    return result[take],reference,dict(identity_warmup=0,month=month,reference=reference.tolist(),latest_reference_open=str(origin-pd.Timedelta(minutes=1)))


def response_design(frame,liquidity,a,taus=TAUS,memory=60):
    """n×response×predictor: full scaled-level change, not a_t*return basis."""
    base,y,valid=construct(frame,liquidity,taus,memory)
    f=np.column_stack([frame[f'signed_taker_quote_flow_{i}']/np.sqrt(liquidity[i]) for i in range(2)])
    a=np.asarray(a)
    if a.shape!=f.shape or not np.isfinite(a).all():raise ValueError('Response state alignment')
    pieces=[]
    prev_a=np.vstack([a[:1],a[:-1]])
    for tau in taus:
        phi=np.exp(-np.arange(memory+1)/tau)
        current=lfilter(phi,[1.],a*f,axis=0)
        previous=lfilter(phi[:-1],[1.],a*f,axis=0)
        previous=np.vstack([np.zeros((1,2)),previous[:-1]])
        z=a[:,:,None]*current[:,None,:]-prev_a[:,:,None]*previous[:,None,:]
        pieces.append(z)
    x=np.concatenate([np.repeat(base[:,:NC,None],2,axis=2).transpose(0,2,1),np.concatenate(pieces,axis=2)],axis=2)
    # Same original joint mask; never improve eta fit via different eligibility.
    valid &= np.isfinite(x).all(axis=(1,2))
    return x,y,valid
