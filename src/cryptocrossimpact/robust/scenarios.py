"""Deterministic, past-only joint liquidity paths and PSD kernel ambiguity."""
import hashlib
import numpy as np
import pandas as pd
from ..execution.impact_cost import Kernel,cash_hessian
from ..execution.policies import without_cross


class ScenarioSupportError(ValueError):pass


def joint_paths(history,asof,t0,point,seed=20261027):
    """12 equally weighted coherent BTC/ETH profiles, USDT/min, real zeros intact.

    Source hours lie in [midnight(asof)-28d,midnight(asof)); same episode HOD.
    Ratios use positive historical same-minute medians, then current V1 scale.
    Past data are sliced BEFORE value/quality operations; current hour is absent.
    """
    asof=pd.Timestamp(asof);t0=pd.Timestamp(t0);k=int((asof-t0).total_seconds()/60)
    if asof.tz is None or k<0 or k>=60 or point.shape!=(60-k,2):raise ValueError('Scenario clock/shape')
    end=asof.normalize();start=end-pd.Timedelta(days=28)
    h=history.loc[(history.time>=start)&(history.time<end)&(history.time.dt.hour==t0.hour)].sort_values('time')
    source=[];values=[]
    for day,g in h.groupby(h.time.dt.normalize(),sort=True):
        if len(g)!=60 or not np.array_equal(g.time.dt.minute,np.arange(60)):continue
        v=g[['quote_volume_0','quote_volume_1']].to_numpy()
        if not g[['valid_bar_0','valid_bar_1']].to_numpy().all() or not np.isfinite(v).all() or (v<0).any():continue
        source.append(day);values.append(v)
    if len(values)<12:raise ScenarioSupportError(f'Fewer than12 historical paired hours: {len(values)}')
    v=np.stack(values);positive=np.where(v>0,v,np.nan)
    reference=np.nanmedian(positive,axis=0)
    if not np.isfinite(reference).all() or (reference<=0).any():raise ScenarioSupportError('No positive historical minute reference')
    keys=[hashlib.sha256(f'{seed}|{t0.date()}|{t0.hour:02}|{day.date()}'.encode()).hexdigest() for day in source]
    selected=np.argsort(keys)[:12];ratios=v[selected,k:]/reference[None,k:]
    paths=ratios*point[None,:,:]
    if not np.isfinite(paths).all() or (paths<0).any():raise ValueError('Invalid joint path')
    return paths,dict(support=len(values),source_hours=[str(source[j]+pd.Timedelta(hours=t0.hour)) for j in selected],
        source_available_before=str(end),asof=str(asof),weights=[1/12]*12,
        retained_zero_capacity_cells=int((paths==0).sum()),minimum_capacity_usdt=float(paths.min()),
        path_turnover_min_usdt=float(paths.sum(axis=(1,2)).min()),path_turnover_max_usdt=float(paths.sum(axis=(1,2)).max()))


def ambiguity(b,fixed,diagonal=False):
    d=np.diag([1.,-1.]);diag=np.array([np.diag(np.diag(c)) for c in b.matrices])
    candidates=[b,without_cross(b),Kernel(b.assets,.5*b.matrices+.5*diag,b.taus_minutes,b.liquidity_usdt,'B_half_cross',b.source_sha256),
        Kernel(b.assets,np.array([d@c@d for c in b.matrices]),b.taus_minutes,b.liquidity_usdt,'B_opposite',b.source_sha256),fixed]
    names=['B','B_diagonal','B_half_cross','B_opposite','B_fixed_June2025']
    if diagonal:candidates=[without_cross(k) for k in candidates]
    keep=[];seen=[];audit=[]
    for name,k in zip(names,candidates):
        h,qa=cash_hessian(k,60);duplicate=next((names[j] for j,a in seen if np.array_equal(h,a)),None)
        audit.append(dict(scenario=name,diagonal=diagonal,duplicate_of=duplicate,source_sha256=k.source_sha256,
            liquidity_usdt=k.liquidity_usdt.tolist(),taus=k.taus_minutes.tolist(),hessian_min_eigenvalue=qa['min_eigenvalue']))
        if duplicate is None:keep.append((name,k));seen.append((names.index(name),h))
    # Nonnegative-sale elementwise dominance is sufficient for every conditional
    # cost including H_fp z_p. PSD order is separately recorded in physical units.
    from scipy.linalg import eigvalsh
    for row,(i,hi) in zip([a for a in audit if a['duplicate_of'] is None],seen):
        for j,hj in seen:
            if i==j:continue
            diff=hi-hj;scale=max(np.max(np.abs(hi)),np.max(np.abs(hj)),np.finfo(float).tiny)
            row[f'nonnegative_sale_dominates_{names[j]}']=bool(np.min(diff)>=-1e-12*scale)
            eigen=eigvalsh(diff);row[f'PSD_dominates_{names[j]}']=bool(eigen[0]>=-1e-9*max(np.max(np.abs(eigen)),np.finfo(float).tiny))
    return keep,audit


def overload(z,volume,W,p=.10):
    z=np.asarray(z);v=np.asarray(volume)
    if z.shape!=v.shape or W<=0 or not np.isfinite(v).all() or (v<0).any():raise ValueError('Invalid overload inputs')
    return float(np.maximum(z-p*v,0).sum()/W)


def empirical_cvar(values,alpha=.90):
    a=np.sort(np.asarray(values,dtype=float))[::-1]
    if not len(a) or not 0<=alpha<1 or not np.isfinite(a).all():raise ValueError('Invalid CVaR')
    mass=(1-alpha)*len(a);weights=np.minimum(np.maximum(mass-np.arange(len(a)),0),1)
    return float(a@weights/mass)
