"""PSD regression with receiver-specific state regressors and matched ridge."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import cvxpy as cp
from ..kernel.fit import Stats,validate_components
from ..kernel.features import DevelopmentStore,construct
from ..kernel.workflow import read_stats,save_stats
from ..execution.impact_cost import Kernel,ASSETS
from ..data.storage import sha256
from .features import NC,TAUS,monthly_state,response_design
from .state import multipliers
from .common import paths,save,digest,binding


def rows(x,y):
    return Stats(len(x),np.stack([x[:,i].T@x[:,i] for i in range(2)]),np.column_stack([x[:,i].T@y[:,i] for i in range(2)]),np.sum(y*y,axis=0))


def total(records,start,end):
    available=[v for k,v in records.items() if start<=k<end]
    if not available:raise ValueError('Empty fit window')
    p=len(available[0].xy);s=Stats(0,np.zeros((2,p,p)),np.zeros((p,2)),np.zeros(2))
    for v in available:s.add(v)
    return s


def rescale(s,base_l,liquidity):
    factors=np.r_[np.ones(NC),np.tile(np.sqrt(base_l/liquidity),len(TAUS))];ys=np.sqrt(liquidity/base_l)
    return Stats(s.n,s.gram*factors[None,:,None]*factors[None,None,:],s.xy*factors[:,None]*ys[None,:],s.yy*ys**2)


def estimate(raw,taus,liquidity,eta,ridge=1.):
    indices=list(range(NC))+[NC+2*TAUS.index(t)+j for t in taus for j in range(2)]
    g=raw.gram[:,indices][:,:,indices];xy=raw.xy[indices];n=raw.n
    mean=g[:,0,:]/n;scale=np.sqrt(np.maximum(np.diagonal(g,axis1=1,axis2=2)/n-mean**2,0));mean[:,0]=0;scale[:,0]=1
    ys=np.sqrt(raw.yy/n-(xy[0]/n)**2)
    if (scale<=1e-14).any() or (ys<=0).any():raise ValueError('Unidentified design')
    gs=[];hs=[]
    for i in range(2):
        t=np.diag(1/scale[i]);t[0,1:]=-mean[i,1:]/scale[i,1:]
        gs.append(t.T@g[i]@t/n);hs.append(t.T@xy[:,i]/ys[i]/n)
    gs=np.stack(gs);hs=np.column_stack(hs);cref=float(np.median(ys[:,None]/scale[:,NC:]))
    controls=cp.Variable((NC,2));cs=[cp.Variable((2,2),symmetric=True) for _ in taus];constraints=[c>>0 for c in cs]
    beta=cp.vstack([controls]+[cp.hstack([cp.multiply(c[i,:]*cref,scale[i,NC+2*k:NC+2*k+2]/ys[i])[:,None] for i in range(2)]) for k,c in enumerate(cs)])
    objective=0
    for i in range(2):
        objective+=.5*(cp.quad_form(beta[:,i],cp.psd_wrap((gs[i]+gs[i].T)/2))-2*hs[:,i]@beta[:,i]+raw.yy[i]/ys[i]**2/n)
    objective+=.5*ridge*cp.sum_squares(beta[1:])
    problem=cp.Problem(cp.Minimize(objective),constraints);problem.solve(solver='CLARABEL',tol_gap_abs=1e-9,tol_gap_rel=1e-8,tol_feas=1e-9,max_iter=250)
    if problem.status!='optimal':raise ValueError('PSD estimator '+str(problem.status))
    c=np.stack([v.value*cref for v in cs]);qa=validate_components(c);theta=beta.value
    if max(float(np.max(k.violation())) for k in constraints)>1e-6:raise ValueError('PSD residual')
    mse=[float(theta[:,i]@gs[i]@theta[:,i]-2*theta[:,i]@hs[:,i]+raw.yy[i]/ys[i]**2/n) for i in range(2)]
    return dict(eta=eta,matrices=c.tolist(),taus_minutes=taus,liquidity_usdt=np.asarray(liquidity).tolist(),indices=indices,mean=mean.tolist(),scale=scale.tolist(),target_scale=ys.tolist(),theta=theta.tolist(),training_rows=n,training_mse=mse,status=problem.status,objective=float(problem.value),component_diagnostics=qa,ridge=ridge)


def predict(model,x):
    x=x[:,:,model['indices']];mean=np.asarray(model['mean']);scale=np.asarray(model['scale']);theta=np.asarray(model['theta'])
    return np.column_stack([((x[:,i]-mean[i])/scale[i])@theta[:,i] for i in range(2)])*np.asarray(model['target_scale'])


def kernel(model):return Kernel(ASSETS,model['matrices'],model['taus_minutes'],model['liquidity_usdt'],'stage_a',digest(model))


def prepare(root):
    root=Path(root);out,bulk=paths(root);store=DevelopmentStore(root);features=json.loads((root/'reports/research/stage02_artifacts/features.json').read_text());l=np.array(features['liquidity_usdt'])
    cache=bulk/'statistics';cache.mkdir(exist_ok=True);states=bulk/'state_forecasts';states.mkdir(exist_ok=True)
    if (out/'feature_manifest.json').exists():return json.loads((out/'feature_manifest.json').read_text())
    context=None;state_context={e:np.empty((0,2)) for e in [0,.5,1]};days={e:{} for e in [0,.5,1]};qa=[]
    for month in pd.period_range('2024-01','2025-12',freq='M').astype(str):
        frame=store.paired(month);offset=0 if context is None else len(context);combined=frame if context is None else pd.concat([context,frame],ignore_index=True)
        point,ref,meta=monthly_state(combined,month)
        a={eta:np.ones_like(point) if ref is None else multipliers(point,ref,eta) for eta in [0,.5,1]}
        np.savez_compressed(states/f'{month}.npz',V1=point,reference=np.array([np.nan,np.nan]) if ref is None else ref,**{f'a{e}':a[e] for e in [.5,1]})
        clock=pd.DatetimeIndex(frame.time);dates=clock.strftime('%Y-%m-%d');expected=None
        for eta in [0,.5,1]:
            all_a=np.vstack([state_context[eta],a[eta]]);x,y,good=response_design(combined,l,all_a);x=x[offset:];y=y[offset:];good=good[offset:]
            if expected is not None:np.testing.assert_array_equal(good,expected)
            expected=good
            for day in np.unique(dates):
                take=good&(dates==day);days[eta][str(day)]=rows(x[take],y[take])
            state_context[eta]=all_a[-40320:].copy()
        qa.append(dict(**meta,rows=len(frame),eligible=int(good.sum()),minimum_a=float(a[1].min()),maximum_a=float(a[1].max()),clip_low=int((a[1]==.5).sum()),clip_high=int((a[1]==2).sum())))
        context=combined.iloc[-40320:].copy();print('StageA features',month,int(good.sum()),flush=True)
    for eta in [0,.5,1]:save_stats(cache/f'eta{eta}.npz',days[eta])
    result=dict(status='PASS',liquidity_usdt=l.tolist(),QA=qa,source_reads=store.read_log,code=binding(root),state_forecast_cache='compact V1/A only; no duplicated market/feature panels')
    save(out/'feature_manifest.json',result);return result


class Fitter:
    def __init__(self,root):
        self.root=Path(root);self.out,self.bulk=paths(root);self.store=DevelopmentStore(root)
        f=json.loads((self.out/'feature_manifest.json').read_text());self.l=np.array(f['liquidity_usdt']);self.days={e:read_stats(self.bulk/'statistics'/f'eta{e}.npz') for e in [0,.5,1]};self.lcache={}

    def fit(self,start,end,eta,taus=[60],name=None):
        if end>'2026-01-01':raise ValueError('Development fitter refuses2026 before I/O')
        name=name or f'{start}_{end}_eta{eta}_'+','.join(map(str,taus));folder=self.out/'models';folder.mkdir(exist_ok=True);path=folder/(name+'.json')
        if path.exists():return json.loads(path.read_text())
        if (start,end) not in self.lcache:self.lcache[start,end]=self.store.liquidity(start,end)
        l=self.lcache[start,end];raw=rescale(total(self.days[eta],start,end),self.l,l);m=estimate(raw,taus,l,eta);m.update(training_start=start,training_end_exclusive=end,source_manifest_sha256=sha256(self.root/'data/registry/source_manifest.json'))
        save(path,m);return m
