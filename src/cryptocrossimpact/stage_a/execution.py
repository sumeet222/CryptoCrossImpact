"""Matched Stage A replay; immutable multiplier and sale prefixes before reveal."""
import json,time
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pandas as pd
from ..robust.workflow import development_episodes,model_bundle,diagnostics
from ..robust.data import Store
from ..robust.scenarios import joint_paths,overload
from ..execution.solver import build_problem
from ..execution.policies import without_cross
from ..execution.impact_cost import cash_hessian,Kernel,ASSETS
from ..evaluation.v2_score import evaluation_prices
from ..liquidity.workflow import score_schedule
from ..data.storage import sha256,utcnow
from .common import paths,save,digest,binding
from .state import StateQP,multipliers,state_hessian,triangle
from .fit import Fitter,kernel


def parity(root):
    root=Path(root);out,_=paths(root);store=Store(root);rows=[]
    for e in development_episodes(root,True):
        b,ws=model_bundle(root,e.t0.strftime('%Y-%m'),e.t0);base=build_problem(b,e.initial,e.forecast,e.covariance);q=StateQP(b,e.initial,.1*e.forecast,e.covariance,base.risk_multiplier);past=np.empty((0,2))
        for cut in range(0,60,5):
            t=e.t0+pd.Timedelta(minutes=cut);p,h=store.forecast(t,pd.date_range(t,periods=60-cut,freq='min'));bank,_=joint_paths(h,t,e.t0,p['V1']);a=np.ones_like(p['V1']);z,d=q.solve(past,p['V1'],bank,a);past=np.vstack([past,z[:5]]);q.commit(a[:5])
        with np.load(root/'results/extension_x2x3/selection'/f'{e.episode_id}.npz') as old:expected=old['L25'].copy()
        error=float(np.max(np.abs(past-expected)/e.initial))
        if error>1e-7:raise ValueError('Original L25 parity failure')
        rows.append(dict(episode_id=e.episode_id,max_schedule_error_over_initial=error,triangle_error_usdt=abs(triangle(b,past,q.ledger)-.5*past.ravel()@cash_hessian(b,60)[0]@past.ravel())))
    save(out/'baseline_parity.json',dict(status='PASS',cases=rows,old_selection_sha256=sha256(root/'reports/research/extension_x2x3_artifacts/development_selection.json')))
    return rows


def state_reference(root,month):
    _,bulk=paths(root)
    with np.load(bulk/'state_forecasts'/f'{month}.npz') as f:return f['reference'].copy()


def fitted_models(root,month,eta):
    origin=pd.Timestamp(month+'-01',tz='UTC');fitter=Fitter(root)
    b=fitter.fit((origin-pd.Timedelta(days=365)).strftime('%Y-%m-%d'),origin.strftime('%Y-%m-%d'),eta,[60],f'{month}_B_eta{eta}')
    end=origin-pd.Timedelta(days=30);e=fitter.fit((end-pd.Timedelta(days=180)).strftime('%Y-%m-%d'),end.strftime('%Y-%m-%d'),eta,[5,30],f'{month}_E_eta{eta}')
    return kernel(b),kernel(e)


def evaluator_worlds(root,e,monthly,stationary,selected):
    """Common realized-as-of V1 ledger, each minute known before that cell."""
    _,bulk=paths(root);month=e.t0.strftime('%Y-%m');ref=state_reference(root,month)
    with np.load(bulk/'state_forecasts'/f'{month}.npz') as f:
        start=int((e.t0-pd.Timestamp(month+'-01',tz='UTC')).total_seconds()/60);v=f['V1'][start:start+60]
    proposed=[('E_stationary',stationary,0,1.,False)]
    for eta in sorted(set([selected,.5,1])):
        k=monthly[eta][1] if eta else stationary
        prefix='E_conditional' if eta==selected else f'E_ablation_eta{eta}'
        proposed += [(prefix,k,eta,1.,False),(prefix+'_diag',k,eta,1.,True)]
        if eta==selected:proposed += [(prefix+'_amplitude0p5',k,eta,.5,False),(prefix+'_amplitude2',k,eta,2.,False),(prefix+'_eta0',k,0,1.,False)]
    worlds={};aliases={};seen={}
    for name,k,eta,amplitude,diag in proposed:
        c=k.matrices*amplitude
        if diag:c=np.array([np.diag(np.diag(x)) for x in c])
        k2=Kernel(ASSETS,c,k.taus_minutes,k.liquidity_usdt,name,k.source_sha256);a=multipliers(v,ref,eta);h=state_hessian(k2,a);key=digest(h)
        if key in seen:aliases[name]=seen[key];continue
        seen[key]=name;worlds[name]=SimpleNamespace(world_id=name,kernel=k2,hessian=h,kappa=.001,bins=60,a=a,world_hash=digest(dict(kernel=k2.source_sha256,C=k2.matrices,L=k2.liquidity_usdt,tau=k2.taus_minutes,state=a,exact_cell_hessian=h)))
    return worlds,aliases


def replay(root,e,monthly,selected,folder):
    root=Path(root);out,bulk=paths(root);folder=Path(folder);folder.mkdir(exist_ok=True);path=folder/f'{e.episode_id}.json'
    signature=digest(dict(code=binding(root),selection=selected,models={str(k):v[0].source_sha256 for k,v in monthly.items()}))
    if path.exists():
        r=json.loads(path.read_text())
        if r['signature']!=signature:raise ValueError('Stage A checkpoint code/selection changed')
        if sha256(folder/r['schedule_file'])!=r['schedule_sha256']:raise ValueError('Stage A schedule changed')
        return r
    month=e.t0.strftime('%Y-%m');b,ws=model_bundle(root,month,e.t0);stationary=next(w.kernel for w in ws if w.world_id=='E1');reference=state_reference(root,month)
    beta=build_problem(b,e.initial,e.forecast,e.covariance).risk_multiplier;caps=.1*e.forecast
    # Saved context schedules are immutable and were generated on identical inputs.
    with np.load(root/'results/extension_x2x3/selection'/f'{e.episode_id}.npz') as f:sales={p:f[q].copy() for p,q in [('A0','L25'),('N','N'),('TWAP','TWAP')]}
    arms={}
    for eta in [.5,1]:
        for mode in ['refresh','diag','frozen']:
            name=f'eta{eta}_{mode}';k=without_cross(monthly[eta][0]) if mode=='diag' else monthly[eta][0];arms[name]=(eta,mode,k)
        arms[f'fixed_eta{eta}']=(eta,'refresh',b)
    # Selected zero exact aliases avoid giving the null a different numerical fit.
    if selected==0:arms['A2']=(0,'diag',without_cross(b))
    solvers={n:StateQP(k,e.initial,caps,e.covariance,beta) for n,(_,_,k) in arms.items()};records={n:[] for n in arms};prefixes=[];store=Store(root);prior=None;arrival={}
    for n in arms:sales[n]=np.empty((0,2))
    for cut in range(0,60,5):
        clock=e.t0+pd.Timedelta(minutes=cut);p,h=store.forecast(clock,pd.date_range(clock,periods=60-cut,freq='min'),prior);bank,qa=joint_paths(h,clock,e.t0,p['V1']);committed={};aa={}
        if cut==0:np.testing.assert_array_equal(p['V0'],e.forecast)
        for name,(eta,mode,k) in arms.items():
            future=multipliers(p['V1'],reference,eta,p['floor'])
            if cut==0:arrival[name]=future.copy()
            if mode=='frozen':future=arrival[name][cut:]
            q=solvers[name];z,d=q.solve(sales[name],p['V1'],bank,future);sale=z[:5].copy();state=future[:5].copy();sales[name]=np.vstack([sales[name],sale]);q.commit(state)
            records[name].append(dict(**d,asof=str(clock),latest_open=p['qa']['latest_open'],prefix=sale.tolist(),multipliers=state.tolist()))
            committed[name]=sale.tolist();aa[name]=state.tolist()
        pp=folder/f'{e.episode_id}_prefix_{cut:02}.json';value=dict(asof=str(clock),revealed_until=str(clock+pd.Timedelta(minutes=5)),latest_open=p['qa']['latest_open'],committed=committed,multipliers=aa,scenario_sources=qa['source_hours'])
        if pp.exists():
            if json.loads(pp.read_text())!=value:raise ValueError('Committed prefix differs on resume')
        else:save(pp,value)
        prior=pp;prefixes.append(dict(path=str(pp.relative_to(root)),sha256=sha256(pp)))
    if selected==0:sales['A1']=sales['A0'];sales['A3']=sales['A0']
    else:
        for alias,mode in [('A1','refresh'),('A2','diag'),('A3','frozen')]:sales[alias]=sales[f'eta{selected}_{mode}']
    schedule=folder/f'{e.episode_id}.npz';np.savez_compressed(schedule,**sales,**{f'state_{n}':q.ledger for n,q in solvers.items()})
    decisions=folder/f'{e.episode_id}_decisions.json';save(decisions,dict(signature=signature,schedule_file=str(schedule.relative_to(root)),schedule_sha256=sha256(schedule),prefixes=prefixes,committed_utc=utcnow(),beta=beta,initial=e.initial.tolist(),caps_hash=digest(caps),covariance=e.covariance.tolist()))
    # Only now reveal future observations to a separate scorer instance.
    truth=Store(root).paired(e.t0,e.t0+pd.Timedelta(hours=1),purpose='score',asof=e.t0+pd.Timedelta(hours=1),commitment=decisions)
    prices,vreal=evaluation_prices(truth,e.t0,60);worlds,aliases=evaluator_worlds(root,e,monthly,stationary,selected);scores=[];over=[];qrows=[];triangle_error=0.
    for name,z in sales.items():
        for world,w in worlds.items():
            row=score_schedule(z,e.initial,e.forecast,e.p0,prices,vreal,w);scores.append(dict(episode_id=e.episode_id,day=e.t0.strftime('%Y-%m-%d'),month=month,weekend=e.t0.day_of_week>=5,past_liquidity_usdt=float(e.forecast.sum()),policy=name,**row))
            if e.t0.day==1 and e.t0.hour==0:
                err=abs(row['transient_usdt']-triangle(w.kernel,z,w.a));triangle_error=max(triangle_error,err)
                if err>1e-8*max(abs(row['transient_usdt']),1):raise ValueError('Full schedule conditional triangle discrepancy')
        ratio=np.divide(z,vreal,out=np.full_like(z,np.nan),where=vreal>0);finite=ratio[np.isfinite(ratio)]
        over.append(dict(episode_id=e.episode_id,day=e.t0.strftime('%Y-%m-%d'),month=month,weekend=e.t0.day_of_week>=5,past_liquidity_usdt=float(e.forecast.sum()),policy=name,overload=overload(z,vreal,e.initial.sum()),positive_volume_cells=len(finite),zero_cells=int((vreal==0).sum()),positive_sales_zero_cells=int(((vreal==0)&(z>1e-8)).sum()),over10=int((finite>.1).sum()),over20=int((finite>.2).sum()),over100=int((finite>1).sum()),max_finite_ratio=float(finite.max())))
        if name in solvers:
            d=diagnostics(z,e,records[name],beta);a=solvers[name].ledger;cash=.5*z.ravel()@state_hessian(arms[name][2],a)@z.ravel();qrows.append(dict(episode_id=e.episode_id,policy=name,**d,actual_committed_state_impact_usdt=float(cash)))
    r=dict(signature=signature,episode_id=e.episode_id,schedule_file=schedule.name,schedule_sha256=sha256(schedule),decision_file=str(decisions.relative_to(root)),decision_sha256=sha256(decisions),scores=scores,overload=over,diagnostics=qrows,aliases=aliases,records=records,triangle_error_usdt=triangle_error,world_hashes={n:digest(w.hessian) for n,w in worlds.items()},models={str(eta):[k.source_sha256 for k in pair] for eta,pair in monthly.items()})
    save(path,r);return r
