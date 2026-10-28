"""Chronological development/holdout replay and predeclared selection."""
import json
from pathlib import Path
import resource
import time
import numpy as np
import pandas as pd

from ..episodes import config as policy_config
from ..execution.impact_cost import load_stage02,Kernel,triangular_cash
from ..execution.policies import load_models,without_cross
from ..execution.solver import build_problem,capped_uniform_reference
from ..execution.adaptive import AdaptiveQP
from ..evaluation.v2_fit import validate_fit
from ..evaluation.v2_score import worlds,evaluation_prices
from ..liquidity.workflow import score_schedule
from .common import paths,config,binding,save,digest,preserve,START,END
from .data import Store,Episode,make_episode,utc
from .scenarios import ambiguity,joint_paths,overload,empirical_cvar
from .solver import RobustQP


def development_episodes(root,pilot=False):
    rows=[json.loads(s) for s in pd.read_parquet(Path(root)/'results/stage04_development/inputs_development.parquet').episode_json]
    if len(rows)!=736:raise ValueError('Original universe changed')
    episodes=[Episode(r['episode_id'],pd.Timestamp(r['t0']),np.array(r['forecast']),np.array(r['covariance']),np.array(r['initial']),np.array(r['p0'])) for r in rows]
    return [e for e in episodes if str(e.t0) in {str(pd.Timestamp(t)) for t in config(root)['pilot_origins']}] if pilot else episodes


def model_bundle(root,month,t0):
    root=Path(root)
    if month<'2026-01':
        b=load_models(root,month,t0)['B'].kernel
        path=root/'reports/research/extension_x1_artifacts/models'/f'{month}_E1.json'
        fit=json.loads(path.read_text());e1=validate_fit(fit,pd.Timestamp(month+'-01',tz='UTC'),'E1')
    else:
        from .fit import Fitter
        out,_=paths(root);fitter=Fitter(root,Store(root));origin=pd.Timestamp(month+'-01',tz='UTC')
        bm=fitter.fit(origin,'B');em=fitter.fit(origin,'E1');b=validate_fit(bm,origin,'B');e1=validate_fit(em,origin,'E1')
    return b,[w for w in worlds(e1,b) if w.world_id!='E0']


def diagnostics(z,e,records,beta):
    caps=.1*e.forecast;before=e.initial-np.vstack([np.zeros(2),np.cumsum(z,axis=0)[:-1]])
    terminal=np.max(np.abs(z.sum(axis=0)-e.initial));norm=max(float(np.max(np.abs(z.sum(axis=0)-e.initial)/e.initial)),
        float(np.max(np.maximum(-z,0)/e.initial)),float(np.max(np.maximum(z-caps,0)/e.initial)))
    if norm>1e-7:raise RuntimeError('Whole schedule physical failure')
    return dict(terminal_max_usdt=float(terminal),normalized_physical=norm,minimum_sale_usdt=float(z.min()),
        cap_violations=int(np.sum(z-caps>1e-7*e.initial)),repairs=0,beta=beta,covariance_hash=digest(e.covariance),initial_hash=digest(e.initial),caps_hash=digest(caps),
        risk_raw_usdt_squared=float(np.einsum('ki,ij,kj->',before,e.covariance,before)),
        risk_preference_usdt=float(beta*np.einsum('ki,ij,kj->',before,e.covariance,before)),
        primal=max(r['primal'] for r in records),kkt=max(r['kkt'] for r in records),
        epigraph_gap=max(r.get('epigraph_gap',0) for r in records),decomposition=max(r['decomposition'] for r in records),
        solve_seconds=sum(r['seconds'] for r in records),maximum_solve_seconds=max(r['seconds'] for r in records),
        cvar_at_arrival=records[0].get('cvar',0),liquidity_preference_at_arrival_usdt=records[0].get('liquidity_preference_usdt',0),
        active_scenarios=[r.get('active_scenario','nominal') for r in records])


def replay_episode(root,e,b,worlds_,store,scorer,folder,specs):
    """Interleave policy arms; persist current prefixes before any next reveal."""
    root=Path(root);folder=Path(folder);folder.mkdir(parents=True,exist_ok=True);receipt=folder/f'{e.episode_id}.json'
    signature=digest(dict(code=binding(root),config=config(root),specs=specs))
    if receipt.exists():
        r=json.loads(receipt.read_text())
        if r['signature']!=signature:
            from .protocol import compatible_signatures
            if r['signature'] not in compatible_signatures(root,config(root),specs):raise ValueError('Checkpoint/source identity changed')
        if r['schedule_sha256']!=__import__('cryptocrossimpact.data.storage',fromlist=['sha256']).sha256(folder/r['schedule_file']):raise ValueError('Checkpoint schedule changed')
        return r
    fixed=load_stage02(root,'B');family,audit=ambiguity(b,fixed);diagonal,daudit=ambiguity(b,fixed,True)
    ref=build_problem(b,e.initial,e.forecast,e.covariance);beta=ref.risk_multiplier;caps=.1*e.forecast
    solvers={};sales={};records={};forecasts={};prefixes=[];scenario_qa=[];prediction0=None
    for name,kind,lam in specs:
        kernels=diagonal if kind=='robust_diagonal' else family if kind=='robust' else [('B',b)]
        if kind=='nominal_diagonal':solver=AdaptiveQP(without_cross(b),e.initial,caps,e.covariance,beta)
        elif kind=='nominal' and lam==0:solver=AdaptiveQP(b,e.initial,caps,e.covariance,beta)
        else:solver=RobustQP(kernels,e.initial,caps,e.covariance,beta)
        solvers[name]=solver;sales[name]=np.empty((0,2));records[name]=[];forecasts[name]=[]
    prior=None
    for k in range(0,60,5):
        clock=e.t0+pd.Timedelta(minutes=k);targets=pd.date_range(clock,periods=60-k,freq='min')
        p,h=store.forecast(clock,targets,commitment=prior)
        if k==0:
            prediction0=p
            np.testing.assert_array_equal(p['V0'],e.forecast)
        bank,qa=joint_paths(h,clock,e.t0,p['V1']);scenario_qa.append(dict(episode_id=e.episode_id,k=k,**qa))
        committed={}
        for name,kind,lam in specs:
            solver=solvers[name]
            if isinstance(solver,AdaptiveQP):z,d=solver.solve(sales[name],1/p['V1'])
            else:
                try:z,d=solver.solve(sales[name],p['V1'],bank,lam)
                except RuntimeError as exc:raise RuntimeError(f'{name} k={k}: {exc}') from exc
            prefix=z[:min(5,len(z))].copy();prefix.setflags(write=False)
            sales[name]=np.vstack([sales[name],prefix]);forecasts[name].append(p['V1'][:len(prefix)])
            records[name].append(dict(**d,asof=str(clock),latest_open=p['qa']['latest_open'],prefix=prefix.tolist()))
            committed[name]=prefix.tolist()
        prefix_path=folder/f'{e.episode_id}_prefix_{k:02}.json'
        value=dict(episode_id=e.episode_id,asof=str(clock),revealed_until=str(clock+pd.Timedelta(minutes=5)),latest_open=p['qa']['latest_open'],
            input_hash=e.input_hash,signature=signature,committed=committed,scenario_sources=qa['source_hours'])
        if prefix_path.exists():
            old=json.loads(prefix_path.read_text())
            if old!=value:raise RuntimeError('Immutable prefix replay differs')
        else:save(prefix_path,value)
        from ..data.storage import sha256
        prefixes.append(dict(path=str(prefix_path.relative_to(root)),sha256=sha256(prefix_path)));prior=prefix_path
    # Diagnostic background TWAP is generated from frozen cap, not a new arm.
    sales['TWAP']=capped_uniform_reference(e.initial,caps)
    schedule=folder/f'{e.episode_id}.npz';np.savez_compressed(schedule,**sales)
    decisions=folder/f'{e.episode_id}_decisions.json'
    value=dict(episode_id=e.episode_id,t0=str(e.t0),signature=signature,input_hash=e.input_hash,schedule_file=str(schedule.relative_to(root)),
        schedule_sha256=sha256(schedule),prefixes=prefixes,beta=beta,covariance=e.covariance.tolist(),initial=e.initial.tolist(),
        caps_hash=digest(caps),model_hash=b.source_sha256,world_hashes={w.world_id:w.world_hash for w in worlds_},committed_utc=__import__('cryptocrossimpact.data.storage',fromlist=['utcnow']).utcnow())
    if decisions.exists():
        old=json.loads(decisions.read_text())
        if old['schedule_sha256']!=value['schedule_sha256']:raise RuntimeError('Persisted schedule changed')
    else:save(decisions,value)
    truth=scorer.paired(e.t0,e.t0+pd.Timedelta(hours=1),purpose='score',asof=e.t0+pd.Timedelta(hours=1),commitment=decisions)
    prices,vreal=evaluation_prices(truth,e.t0,60);scores=[];liquidity=[];diags=[]
    for name,z in sales.items():
        for world in worlds_:
            s=score_schedule(z,e.initial,e.forecast,e.p0,prices,vreal,world)
            scores.append(dict(episode_id=e.episode_id,day=e.t0.strftime('%Y-%m-%d'),month=e.t0.strftime('%Y-%m'),weekend=e.t0.day_of_week>=5,
                past_liquidity_usdt=float(e.forecast.sum()),policy=name,**s))
        ratio=np.divide(z,vreal,out=np.full_like(z,np.nan),where=vreal>0);finite=ratio[np.isfinite(ratio)]
        liquidity.append(dict(episode_id=e.episode_id,day=e.t0.strftime('%Y-%m-%d'),month=e.t0.strftime('%Y-%m'),weekend=e.t0.day_of_week>=5,
            past_liquidity_usdt=float(e.forecast.sum()),policy=name,W_usdt=float(e.initial.sum()),overload=overload(z,vreal,e.initial.sum()),
            positive_volume_cells=len(finite),zero_cells=int((vreal==0).sum()),positive_sales_zero_cells=int(((vreal==0)&(z>1e-8)).sum()),
            over10=int((finite>.1).sum()),over20=int((finite>.2).sum()),over100=int((finite>1).sum()),
            max_finite_ratio=float(finite.max()) if len(finite) else None,p99_finite_ratio=float(np.quantile(finite,.99)) if len(finite) else None))
        if name!='TWAP':diags.append(dict(episode_id=e.episode_id,policy=name,**diagnostics(z,e,records[name],beta)))
    # Nominal parity with completed X1 outcomes/schedules, never modify X1.
    parity={}
    if e.t0.year==2025:
        original=root/'results/extension_x1/development'/f'{e.episode_id}.npz'
        with np.load(original) as old:
            for name,key in [('N','P2'),('D','D1')]:
                if name in sales:
                    error=float(np.max(np.abs(sales[name]-old[key])/e.initial));parity[name]=error
                    if error>1e-7:raise RuntimeError('X1 nominal/diagonal parity failed')
    r=dict(signature=signature,episode_id=e.episode_id,schedule_file=schedule.name,schedule_sha256=sha256(schedule),decision_path=str(decisions.relative_to(root)),
        decision_sha256=sha256(decisions),scores=scores,liquidity=liquidity,diagnostics=diags,records=records,
        scenario_qa=scenario_qa,ambiguity_audit=audit+daudit,parity=parity,
        forecast_V1_at_arrival=prediction0['V1'].tolist(),source_actual_volume_posthoc=vreal.tolist())
    save(receipt,r);return r


def specifications(phase,lam=25):
    if phase=='selection':return [('N','nominal',0),('D','nominal_diagonal',0),('L25','nominal',25),('L100','nominal',100)]
    if phase=='pilot':return specifications('selection')+[('G','robust',0),('GL','robust',25),('GL-D','robust_diagonal',25)]
    return [('G','robust',0),('GL','robust',lam),('GL-D','robust_diagonal',lam)]


def run(root,phase='selection',pilot=False):
    root=Path(root);out,bulk=paths(root);preserve(root);start=time.perf_counter()
    c=config(root);lam=25
    if phase=='combined':lam=json.loads((out/'development_selection.json').read_text())['display_lambda']
    specs=specifications('pilot' if pilot else phase,lam);folder=bulk/(('pilot_'+digest(binding(root))[:10]) if pilot else phase)
    store=Store(root);scorer=Store(root);results=[];failed=[];last=None
    for j,e in enumerate(development_episodes(root,pilot)):
        month=e.t0.strftime('%Y-%m')
        if month!=last:b,ws=model_bundle(root,month,e.t0);last=month
        try:r=replay_episode(root,e,b,ws,store,scorer,folder,specs);results.append(r)
        except (ValueError,RuntimeError) as exc:
            failed.append(dict(episode_id=e.episode_id,reason=str(exc)));save(out/f'failures_{"pilot" if pilot else phase}.json',failed)
            raise
        if (j+1)%10==0:print(f'X2X3 {phase} {j+1}/736 {(time.perf_counter()-start)/60:.2f}min',flush=True)
    label='pilot' if pilot else phase
    for key,filename in [('scores','scores'),('liquidity','overload'),('diagnostics','solver_diagnostics'),('scenario_qa','liquidity_scenario_qa')]:
        pd.DataFrame([v for r in results for v in r[key]]).to_csv(out/f'{label}_{filename}.csv',index=False)
    pd.DataFrame([dict(episode_id=r['episode_id'],**v) for r in results for v in r['ambiguity_audit']]).to_csv(out/f'{label}_kernel_ambiguity_audit.csv',index=False)
    save(out/f'run_{label}.json',dict(complete=len(results),failed=failed,seconds=time.perf_counter()-start,
        peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,code=binding(root),config_hash=digest(c),
        source_reads=store.read_log+scorer.read_log,new_holdout_values_opened=False))
    if pilot:
        # Rerun last pilot independently: exact N/D; conic solutions tolerance.
        e=development_episodes(root,True)[-1];r=results[-1]
        save(out/'pilot_parity.json',dict(episodes=3,nominal_max_error_over_initial=max(max(a['parity'].values()) for a in results),
            conic_checked=True,source_asof_checks=True,all_primary_policies=True))
    return results


def selection(root):
    root=Path(root);out,_=paths(root);l=pd.read_csv(out/'selection_overload.csv');s=pd.read_csv(out/'selection_scores.csv');rows=[]
    baseline=l[l.policy=='N'].set_index('episode_id');cost=s[(s.policy=='N')&(s.world=='E1')].set_index('episode_id')
    if len(baseline)!=736:raise ValueError('Incomplete development selection')
    chosen=None
    for lam in [25,100]:
        policy=f'L{lam}';a=l[l.policy==policy].set_index('episode_id');b=s[(s.policy==policy)&(s.world=='E1')].set_index('episode_id')
        if not a.index.equals(baseline.index) or not b.index.equals(cost.index):raise ValueError('Unpaired selection universe')
        reduction=float((baseline.overload.mean()-a.overload.mean())/baseline.overload.mean());increase=float((b.shortfall_ex_funding_bps-cost.shortfall_ex_funding_bps).mean())
        eligible=reduction>=.10 and increase<=.10
        rows.append(dict(lambda_liq=lam,baseline_mean_overload=float(baseline.overload.mean()),mean_overload=float(a.overload.mean()),relative_reduction=reduction,E1_cost_increase_bps=increase,qualifies=eligible))
        if eligible and chosen is None:chosen=lam
    result=dict(status='FROZEN_DEVELOPMENT_SELECTION',utc=__import__('cryptocrossimpact.data.storage',fromlist=['utcnow']).utcnow(),
        tested=rows,selected_lambda=chosen,display_lambda=chosen if chosen else 25,selected_candidate='L' if chosen else 'N',
        past_liquidity_terciles_usdt=baseline.past_liquidity_usdt.quantile([1/3,2/3]).tolist(),
        rule='Smallest nonzero lambda with >=10% overload reduction and <=0.10bp E1 increase; select on L only',
        new_holdout_values_opened=False,bindings={str(p.relative_to(root)):__import__('cryptocrossimpact.data.storage',fromlist=['sha256']).sha256(p) for p in [out/'selection_overload.csv',out/'selection_scores.csv']})
    path=out/'development_selection.json'
    if path.exists() and json.loads(path.read_text())['tested']!=rows:raise ValueError('Selection changed')
    if not path.exists():save(path,result)
    return json.loads(path.read_text())
