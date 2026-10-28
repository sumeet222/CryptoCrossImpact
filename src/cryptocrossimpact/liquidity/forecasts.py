"""USDT/min volume forecasts. All numeric operations follow the as-of slice."""
import numpy as np
import pandas as pd

from ..kernel.features import FIREWALL


def completed(frame, asof, days=28):
    asof=pd.Timestamp(asof)
    if asof.tz is None or str(asof.tz)!='UTC' or asof>FIREWALL:
        raise ValueError('UTC development as-of required')
    start=asof-pd.Timedelta(days=days)
    h=frame.loc[(frame.time>=start)&(frame.time<asof)].sort_values('time').copy()
    expected=pd.date_range(start,asof,freq='min',inclusive='left')
    if not pd.DatetimeIndex(h.time).equals(expected):raise ValueError('Incomplete/duplicate completed history')
    if 'available_at_utc' in h and not (h.available_at_utc==h.time+pd.Timedelta(minutes=1)).all():
        raise ValueError('Invalid availability clock')
    for i in range(2):
        v=h[f'quote_volume_{i}'].to_numpy()
        if not h[f'valid_bar_{i}'].all() or not np.isfinite(v).all() or (v<0).any():
            raise ValueError('Invalid completed turnover')
    return h


def baseline(h, asof, targets):
    """Volume-only identical Stage 4 median/fallback/floor, including real zeros."""
    targets=pd.DatetimeIndex(targets);asof=pd.Timestamp(asof)
    if (targets<asof).any() or (targets>=FIREWALL).any():raise ValueError('Invalid forecast targets')
    how=h.time.dt.day_of_week.to_numpy()*24+h.time.dt.hour.to_numpy()
    hod=h.time.dt.hour.to_numpy();keys=targets.day_of_week*24+targets.hour
    v0=np.empty((len(targets),2));floors=[];clips=0
    for i in range(2):
        v=h[f'quote_volume_{i}'].to_numpy();positive=v[v>0]
        if not len(positive):raise ValueError('No positive past turnover')
        floor=max(float(np.quantile(positive,.01)),1e-8);floors.append(floor)
        for key in np.unique(keys):
            sample=v[how==key]
            if len(sample)<120:sample=v[hod==key%24]
            if len(sample)<120:sample=v
            estimate=float(np.median(sample));take=keys==key
            v0[take,i]=max(estimate,floor);clips+=int(take.sum())*int(estimate<floor)
    return v0,np.array(floors),clips


def seasonal(frame, asof):
    """28 COMPLETE UTC days; robust positive within-hour reference, no imputation."""
    end=pd.Timestamp(asof).normalize();start=end-pd.Timedelta(days=28)
    h=frame.loc[(frame.time>=start)&(frame.time<end)].sort_values('time')
    profile=np.ones((60,2));counts=[];excluded=[];fallback=[]
    full=pd.DatetimeIndex(h.time).equals(pd.date_range(start,end,freq='min',inclusive='left'))
    for i in range(2):
        ratios=[];bad=0
        if full:
            v=h[f'quote_volume_{i}'].to_numpy().reshape(-1,60)
            valid=h[f'valid_bar_{i}'].to_numpy().reshape(-1,60)
            good=valid.all(axis=1)&np.isfinite(v).all(axis=1)&(v>=0).all(axis=1)&(v>0).any(axis=1)
            bad=int((~good).sum());v=v[good]
            reference=np.nanmedian(np.where(v>0,v,np.nan),axis=1)
            ratios=list(v/reference[:,None])
        for _,hour in ([] if full else h.groupby(h.time.dt.floor('h'),sort=False)):
            v=hour[f'quote_volume_{i}'].to_numpy()
            if (len(hour)!=60 or not np.array_equal(hour.time.dt.minute,np.arange(60)) or
                not hour[f'valid_bar_{i}'].all() or not np.isfinite(v).all() or (v<0).any() or not (v>0).any()):
                bad+=1;continue
            ratios.append(v/np.median(v[v>0]))
        n=len(ratios);counts.append(n);excluded.append(bad);fallback.append(n<24)
        if n>=24:
            p=(n*np.median(np.stack(ratios),axis=0)+50)/(n+50)
            p=np.maximum(p,np.finfo(float).eps);profile[:,i]=p/p.mean()
    return profile,dict(profile_hours=counts,excluded_hours=excluded,flat_fallback=fallback,
                        profile_start=str(start),profile_end_exclusive=str(end))


def predict(frame, asof, targets, profile=None):
    """k=0 denotes next bar. EWMA adjust=False, all observations open<asof."""
    h=completed(frame,asof);v0,floor,clips=baseline(h,asof,targets)
    p,qa=seasonal(frame,asof) if profile is None else profile
    v1=np.maximum(v0*p[pd.DatetimeIndex(targets).minute],floor)
    d=[]
    for i in range(2):
        s=h[f'quote_volume_{i}'];fast=s.ewm(span=5,adjust=False).mean().iloc[-1]
        slow=s.ewm(span=60,adjust=False).mean().iloc[-1]
        d.append(np.clip(np.log((fast+floor[i])/(slow+floor[i])),-np.log(2),np.log(2)))
    lead=(pd.DatetimeIndex(targets)-pd.Timestamp(asof)).total_seconds().to_numpy()/60
    v2=np.maximum(v1*np.exp(np.exp(-lead[:,None]/15)*np.array(d)),floor)
    return dict(V0=v0,V1=v1,V2=v2,floor=floor,qa=dict(**qa,V0_floor_bins=clips,
        V1_floor_bins=int(np.sum(v0*p[pd.DatetimeIndex(targets).minute]<floor)),
        V2_floor_bins=int(np.sum(v1*np.exp(np.exp(-lead[:,None]/15)*np.array(d))<floor)),
        activity_log_ratio=list(d),latest_open=str(h.time.iloc[-1]),latest_available_at=str(asof)))


def bucket(leads):
    return np.searchsorted([5,15,60],np.asarray(leads),side='left')


def calibrate(predicted, actual, floors, leads, origins, minimum=1000):
    """Training-only matured residuals; arrays [origins,60,2], USDT/min."""
    origins=pd.DatetimeIndex(origins)
    if origins.tz is None or (origins+pd.Timedelta(hours=1)>pd.Timestamp('2025-07-01',tz='UTC')).any():
        raise ValueError('Scenario labels must mature within training')
    predicted=np.asarray(predicted);actual=np.asarray(actual);floors=np.asarray(floors)
    if predicted.shape!=actual.shape or predicted.shape[2]!=2 or not np.isfinite(actual).all() or (actual<0).any() or (predicted<=0).any():
        raise ValueError('Invalid residual calibration labels')
    residual=np.log(np.maximum(actual,floors[:,None,:])/predicted)
    factors=np.empty((3,3,2));counts=np.empty((3,2),int);pooled=[]
    for i in range(2):
        small=any(np.sum(bucket(leads)==b)*len(origins)<minimum for b in range(3));pooled.append(small)
        for b in range(3):
            sample=residual[:,:,i].ravel() if small else residual[:,bucket(leads)==b,i].ravel()
            counts[b,i]=len(sample);factors[b,:,i]=np.exp(np.quantile(sample,[.1,.5,.9]))
    if not np.isfinite(factors).all() or (factors<=0).any() or (np.diff(factors,axis=1)<0).any():raise ValueError('Invalid bands')
    return dict(factors=factors.tolist(),counts=counts.tolist(),pooled=pooled,
        origins=len(origins),first_origin=str(origins.min()),last_origin=str(origins.max()),
        latest_label_available=str(origins.max()+pd.Timedelta(hours=1)),
        residual='log(max(realized,past_positive_p1_floor)/point_forecast)')


def bands(point, factors):
    f=np.asarray(factors)[bucket(np.arange(1,len(point)+1))]
    result=point[:,None,:]*f
    if (result<=0).any() or not np.isfinite(result).all() or (np.diff(result,axis=1)<0).any():raise ValueError('Invalid scenario volume')
    return result
