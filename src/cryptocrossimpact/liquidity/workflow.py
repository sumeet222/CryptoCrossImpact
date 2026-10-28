"""Bounded X1 training/forecast/development workflow; preserves original artifacts."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import resource
import subprocess
import time

import numpy as np
import pandas as pd
import yaml

from ..data.storage import sha256,utcnow
from ..episodes import construct_episode,config as policy_config
from ..kernel.features import DevelopmentStore,FIREWALL
from ..execution.policies import load_models,without_cross
from ..execution.solver import build_problem,capped_uniform_reference
from ..execution.adaptive import AdaptiveQP,replay
from ..evaluation.v2_common import save,digest
from ..evaluation.v2_fit import Fitter,read_stats_once,E1_ridge,validate_fit
from ..evaluation.v2_score import World,score_schedule as _score_schedule,evaluation_prices
from ..evaluation.v2_inference import paired_interval
from .forecasts import predict,seasonal,calibrate,bands,bucket


def score_schedule(*args,**kwargs):
    """Keep infeasible zero-volume participation explicit and JSON-compliant.

    This changes no cash amount, trade, exclusion or finite ratio. Infinity is
    represented as null PLUS an infeasibility status, never as a finite ratio.
    """
    result=_score_schedule(*args,**kwargs)
    value=result['max_realized_participation']
    if value is not None and np.isposinf(value):
        result['max_realized_participation']=None
        result['max_realized_participation_status']='INFEASIBLE_POSITIVE_SALE_ZERO_VOLUME'
    return result


def locations(root):
    root=Path(root);out=root/'reports/research/extension_x1_artifacts';bulk=root/'results/extension_x1'
    out.mkdir(parents=True,exist_ok=True);bulk.mkdir(parents=True,exist_ok=True)
    return out,bulk


def cfg(root):return yaml.safe_load((Path(root)/'configs/extension_x1_adaptive_liquidity.yaml').read_text())


def origins(start,end):
    return pd.date_range(start,end,freq='6h',inclusive='left')


class X1Store(DevelopmentStore):
    """Filtered parquet scans: no 2026 partition or future row in policy history.

    The rolling cache only ever contains completed rows. Scorer uses a distinct
    instance after immutable decision receipts exist. No future flow/price object
    is passed into forecasting callbacks.
    """
    def __init__(self,root):
        super().__init__(root)
        if self.manifest['venue']!='Binance' or self.manifest['price_type']!='last traded price':raise ValueError('Wrong source identity')
        self.context=None;self.context_end=None;self.profile_cache={};self.calls=[]

    def paired(self,start,end,purpose='history',asof=None):
        start=pd.Timestamp(start);end=pd.Timestamp(end);asof=end if asof is None else pd.Timestamp(asof)
        if start.tz is None or end.tz is None or str(start.tz)!='UTC' or str(end.tz)!='UTC' or end>asof or end>FIREWALL or start>=end:
            raise ValueError('X1 as-of/firewall refusal before I/O')
        months=pd.period_range(start.tz_localize(None),(end-pd.Timedelta(minutes=1)).tz_localize(None),freq='M').astype(str)
        chunks=[]
        cols=['bar_open_utc','available_at_utc','open_time','close','quote_volume','valid_bar','jump_flag','stale_close_flag']
        for month in months:
            legs=[]
            for asset in ('BTCUSDT','ETHUSDT'):
                if month>='2026-01':raise ValueError('X1 2026 refused before opening')
                entry=self.manifest['partitions'][f'{asset}/{month}'];path=self.root/entry['canonical_path']
                if path not in self.verified:
                    if sha256(path)!=entry['canonical_sha256']:raise ValueError('Canonical hash changed')
                    self.verified[path]=True
                f=pd.read_parquet(path,columns=cols,filters=[('bar_open_utc','>=',start.to_pydatetime()),('bar_open_utc','<',end.to_pydatetime())])
                if not ((f.bar_open_utc>=start)&(f.bar_open_utc<end)&(f.available_at_utc<=asof)).all():raise ValueError('Filter/availability violated')
                if not (f.available_at_utc==f.bar_open_utc+pd.Timedelta(minutes=1)).all():raise ValueError('Clock convention')
                self.read_log.append(f'{asset}/{month}');legs.append(f)
            a,b=legs
            if not np.array_equal(a.open_time,b.open_time):raise ValueError('Paired source mismatch')
            f=pd.DataFrame(dict(time=a.bar_open_utc,open_time=a.open_time,available_at_utc=a.available_at_utc))
            for i,leg in enumerate(legs):
                for name in cols[3:]:f[f'{name}_{i}']=leg[name].to_numpy()
            chunks.append(f)
        self.calls.append(dict(start=str(start),end_exclusive=str(end),asof=str(asof),purpose=purpose))
        return pd.concat(chunks,ignore_index=True)

    def history(self,t):
        t=pd.Timestamp(t);start=t.normalize()-pd.Timedelta(days=28)
        if self.context is None or self.context_end>t or self.context.time.iloc[0]>start:
            self.context=self.paired(start,t,asof=t)
        elif self.context_end<t:
            self.context=pd.concat([self.context.loc[self.context.time>=start],self.paired(self.context_end,t,asof=t)],ignore_index=True)
        self.context_end=t
        return self.context.copy()

    def forecast(self,t,targets):
        h=self.history(t);key=str(pd.Timestamp(t).normalize())
        if key not in self.profile_cache:
            self.profile_cache={key:seasonal(h,t)}
        return predict(h,t,targets,self.profile_cache[key])


def preservation(root,verify=False):
    root=Path(root);out,_=locations(root);path=out/'preservation_initial.json'
    if verify:
        initial=json.loads(path.read_text());changed=[]
        for name,val in initial['files'].items():
            p=root/name
            if not p.exists() or sha256(p)!=val:changed.append(name)
        for name,val in initial['canonical_stats'].items():
            p=root/name
            if not p.exists() or [p.stat().st_size,p.stat().st_mtime_ns]!=val:changed.append(name)
        result=dict(prior_files=len(initial['files']),canonical_partitions=len(initial['canonical_stats']),changed=changed)
        save(out/'preservation_final.json',result)
        if changed:raise RuntimeError('Protected artifacts changed: '+str(changed))
        return result
    if path.exists():return json.loads(path.read_text())
    files={}
    for folder in ['src','scripts','tests','configs','docs','reports','figures','results','data/registry','references','prompts']:
        for p in (root/folder).rglob('*'):
            if not p.is_file() or '__pycache__' in str(p) or 'extension_x1' in str(p) or '/liquidity/' in str(p) or p.name=='adaptive.py' or '/extensions/' in str(p):continue
            files[str(p.relative_to(root))]=sha256(p)
    for name in ['AGENTS.md','README.md','SPEC_CHANGELOG.md','requirements.txt','CryptoCrossImpact_Research_Specification_v1_2026-10-27.md']:
        files[name]=sha256(root/name)
    stats={str(p.relative_to(root)):[p.stat().st_size,p.stat().st_mtime_ns] for p in (root/'data/canonical').rglob('*.parquet')}
    save(path,dict(utc=utcnow(),files=files,canonical_stats=stats,git=subprocess.check_output(['git','status','--short'],cwd=root,text=True),
        branch=subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip(),
        commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()))
    return json.loads(path.read_text())


def forecast_metrics(rows):
    """Initial origin forecasts, actual zero retained in log1p losses and MAE."""
    parts=[]
    for model,g in rows.groupby('model',sort=False):
        for grouping in [['asset'],['asset','bucket'],['asset','minute'],['asset','month']]:
            for key,d in g.groupby(grouping,sort=True):
                key=(key,) if not isinstance(key,tuple) else key
                record=dict(model=model,grouping='/'.join(grouping),**dict(zip(grouping,key)),n=len(d),
                    mae_usdt=float(np.abs(d.actual-d.predicted).mean()),rmsle=float(np.sqrt(d.log_squared.mean())),
                    median_ape_positive=float((np.abs(d.actual-d.predicted)/d.actual).loc[d.actual>0].median()),
                    zero_labels=int((d.actual==0).sum()))
                parts.append(record)
    return pd.DataFrame(parts)


def forecasts(root):
    root=Path(root);out,bulk=locations(root);c=cfg(root)
    if (out/'forecast_gate.json').exists():return json.loads((out/'forecast_gate.json').read_text())
    preservation(root);store=X1Store(root);train={m:[] for m in ('V1','V2')};actual=[];floors=[];times=[];rows=[];qa=[]
    start=time.perf_counter()
    for phase,left,right in [('training',c['train_start'],c['train_end']),('development',c['development_start'],c['development_end'])]:
        for no,t in enumerate(origins(left,right)):
            targets=pd.date_range(t,periods=60,freq='min');p=store.forecast(t,targets)
            # Labels read separately only after past-only predictions are complete.
            truth=store.paired(t,t+pd.Timedelta(hours=1),purpose=phase+'_forecast_labels',asof=t+pd.Timedelta(hours=1))
            if not pd.DatetimeIndex(truth.time).equals(targets) or not truth[['valid_bar_0','valid_bar_1']].to_numpy().all():raise ValueError('Structural forecast-label QC')
            v=truth[['quote_volume_0','quote_volume_1']].to_numpy()
            qa.append(dict(phase=phase,origin=str(t),**p['qa']))
            if phase=='training':
                for m in train:train[m].append(p[m])
                actual.append(v);floors.append(p['floor']);times.append(t)
            else:
                for m in ('V0','V1','V2'):
                    for i,asset in enumerate(('BTCUSDT','ETHUSDT')):
                        rows.append(pd.DataFrame(dict(origin=str(t),day=t.strftime('%Y-%m-%d'),month=t.strftime('%Y-%m'),model=m,asset=asset,
                            minute=np.arange(60),bucket=bucket(np.arange(1,61)),predicted=p[m][:,i],actual=v[:,i],floor=p['floor'][i],
                            log_squared=(np.log1p(v[:,i])-np.log1p(p[m][:,i]))**2)))
            if (no+1)%200==0:print(f'X1 {phase} forecasts {no+1}',flush=True)
    f=pd.concat(rows,ignore_index=True);f.to_parquet(bulk/'forecast_labels_development.parquet',index=False)
    metrics=forecast_metrics(f);metrics.to_csv(out/'forecast_metrics.csv',index=False)
    # Forecast-only gate before any execution scoring.
    pivot=f.groupby(['day','model']).log_squared.mean().unstack();delta=pivot.V1-pivot.V2
    ci=paired_interval(pivot.index,delta.to_numpy(),np.ones(len(delta)))
    a=metrics[metrics.grouping=='asset'].pivot(index='asset',columns='model',values='rmsle')
    enabled=ci['ci_low']>0 and bool((a.V2<=1.01*a.V1).all())
    base='V2' if enabled else 'V1'
    scenario=calibrate(np.stack(train[base]),np.stack(actual),np.stack(floors),np.arange(1,61),times,c['minimum_bucket_labels'])
    scenario['base']=base;save(out/'scenario_calibration.json',scenario)
    calibration=[]
    g=f[f.model==base].copy();b=bands(np.ones((60,2)),scenario['factors'])
    for asset_i,asset in enumerate(('BTCUSDT','ETHUSDT')):
        for buck,d in g[g.asset==asset].groupby('bucket'):
            for qi,q in enumerate([.1,.5,.9]):
                factor=np.array(scenario['factors'])[int(buck),qi,asset_i];pred=d.predicted*factor
                error=d.actual-pred
                calibration.append(dict(asset=asset,bucket=int(buck),quantile=q,n=len(d),coverage=float((d.actual<=pred).mean()),
                    pinball_usdt=float(np.maximum(q*error,(q-1)*error).mean()),factor=factor))
    cal=pd.DataFrame(calibration);cal.to_csv(out/'scenario_coverage.csv',index=False)
    scenario_pass=bool((np.abs(cal.coverage-cal['quantile'])<=c['scenario_coverage_tolerance']).all())
    daily=f.groupby(['day','model','asset']).agg(log_squared=('log_squared','mean'),mae_usdt=('actual',lambda x:0)).reset_index()
    # Actual daily absolute errors, then shared daily block comparison.
    f['absolute_error']=np.abs(f.actual-f.predicted)
    daily=f.groupby(['day','model','asset']).agg(log_squared=('log_squared','mean'),mae_usdt=('absolute_error','mean')).reset_index()
    daily.to_csv(out/'forecast_daily.csv',index=False);cis=[]
    for old,new in [('V0','V1'),('V1','V2'),('V0','V2')]:
        for metric in ['log_squared','mae_usdt']:
            table=daily.groupby(['day','model'])[metric].mean().unstack();diff=table[old]-table[new]
            cis.append(dict(control=old,new=new,metric=metric,**paired_interval(table.index,diff.to_numpy(),np.ones(len(diff)))))
    pd.DataFrame(cis).to_csv(out/'forecast_paired_intervals.csv',index=False)
    save(out/'forecast_qa.json',qa)
    gate=dict(V2_enabled=enabled,base=base,V2_forecast_gain=ci,scenario_enabled=scenario_pass,
        scenario_status='PASS' if scenario_pass else 'QUALIFIED_MARGINAL_COVERAGE_FAILED',
        scenario_max_coverage_error=float(np.abs(cal.coverage-cal['quantile']).max()),
        training_origins=len(times),development_origins=736,forecast_rows=len(f),seconds=time.perf_counter()-start,
        scenario_sha256=sha256(out/'scenario_calibration.json'),config_sha256=sha256(root/'configs/extension_x1_adaptive_liquidity.yaml'),
        protocol_sha256=sha256(root/'docs/extensions/x1_adaptive_liquidity_protocol_v1.md'),execution_scores_inspected=False,
        partitions=sorted(set(store.read_log)),final_test_partitions_opened=0)
    save(out/'forecast_gate.json',gate);print(json.dumps(gate,indent=2),flush=True);return gate


class DevelopmentFitter(Fitter):
    """Reuse frozen Stage5 E1 fit method; redirect every write to X1 namespace."""
    def __init__(self,root,store):
        self.root=Path(root);self.store=store;self.out,self.bulk=locations(root)
        f=json.loads((self.root/'reports/research/stage02_artifacts/features.json').read_text())
        self.base_l=np.array(f['liquidity_usdt']);self.all_taus=f['all_taus']
        self.days=read_stats_once(self.root/'results/kernel_development/daily.npz');self.l_cache={};self.ridge,_=E1_ridge(root)

    def fit(self,origin,role='E1',folder=None):
        if pd.Timestamp(origin)>=FIREWALL or role!='E1':raise ValueError('X1 development E1 only')
        return super().fit(origin,role,self.out/'models')


def beta_for(e,kernel,pc):
    return build_problem(kernel,e.initial,e.forecast,e.covariance,cap_fraction=pc['cap_fraction'],kappa=pc['kappa'],theta=pc['theta'],fee_bps=pc['fee_bps'],half_spread_bps=pc['half_spread_bps']).risk_multiplier


def numerical_lock(root):
    """Persist numerical code identity before economic replay; refuse drift."""
    root=Path(root);out,_=locations(root)
    files=[p for p in (root/'src/cryptocrossimpact').rglob('*.py')
           if p.name not in ('reporting.py','v2_report.py','stage04_reporting.py')]
    current={str(p.relative_to(root)):sha256(p) for p in files}
    path=out/'numerical_lock_v2.json'
    if path.exists():
        if json.loads(path.read_text())['code_sha256']!=current:raise ValueError('Numerical code changed after X1 replay lock')
    else:
        predecessor=out/'numerical_lock.json'
        save(path,dict(utc=utcnow(),code_sha256=current,execution='exploratory development only',
            predecessor_sha256=sha256(predecessor),
            revision='Output-only zero-volume infinity serialization fix; trades, costs, gates and numeric algorithms unchanged',
            predecessor_source='provenance/workflow_before_zero_serialization_fix.py'))
    return sha256(path)


def episode_policies(root,e,store,models,gate,scenario):
    """Past-volume callback only; all initial constraints immutable across arms."""
    pc=policy_config(root);b=models['B'].kernel;beta=beta_for(e,b,pc);caps=.1*e.forecast
    specs=[('P0',b,'V0',False,False,False),('P1',b,'V1',False,False,False),('P2',b,'V1',True,False,False),
        ('D0',without_cross(b),'V1',False,False,False),('D1',without_cross(b),'V1',True,False,False)]
    if gate['V2_enabled']:specs.append(('P3',b,'V2',True,False,False))
    if gate['scenario_enabled']:
        specs.extend([('P4',b,gate['base'],True,True,False),('P4M',b,gate['base'],True,False,True)])
    paths={};diagnostics=[];receipts={};used={};solvers={}
    for name,kernel,model,adaptive,scen,med in specs:
        solvers[name]=AdaptiveQP(kernel,e.initial,caps,e.covariance,beta)
        paths[name]=np.empty((0,2));receipts[name]=[];used[name]=[]
    # Interleave arms: commit ALL current prefixes before revealing the next
    # completed bars. No future-origin forecast is preloaded into a policy.
    for k in range(0,60,5):
        t=e.t0+pd.Timedelta(minutes=k)
        prediction=store.forecast(t,pd.date_range(t,periods=60-k,freq='min'))
        if k==0:
            p0=prediction
            np.testing.assert_array_equal(prediction['V0'],e.forecast)
        for name,kernel,model,adaptive,scen,med in specs:
            if k and not adaptive:continue
            point=prediction[model];band=bands(point,scenario['factors']) if scen or med else None
            inverse=(np.sum(np.array([.25,.5,.25])[None,:,None]/band,axis=1) if scen else 1/band[:,1,:] if med else 1/point)
            z,record=solvers[name].solve(paths[name],inverse)
            count=min(5 if adaptive else 60,len(z));prefix=z[:count].copy();prefix.setflags(write=False)
            receipts[name].append(dict(**record,asof=str(t),latest_open=prediction['qa']['latest_open'],
                latest_available_at=prediction['qa']['latest_available_at'],prefix=prefix.tolist(),point_forecast=point.tolist()))
            paths[name]=np.vstack([paths[name],prefix]);used[name].append(point[:count])
    for name,kernel,model,adaptive,scen,med in specs:
        z=paths[name];record=receipts[name];used[name]=np.vstack(used[name])
        before=e.initial-np.vstack([np.zeros(2),np.cumsum(z,axis=0)[:-1]])
        raw=float(np.einsum('ki,ij,kj->',before,e.covariance,before))
        diagnostics.append(dict(episode_id=e.episode_id,policy=name,status='PASS',beta=beta,
            input_hash=e.input_hash,model_hash=kernel.source_sha256,kernel_kind='B_SELF_ONLY' if name.startswith('D') else 'B',
            max_terminal_usdt=float(np.max(np.abs(z.sum(axis=0)-e.initial))),minimum_sale_usdt=float(z.min()),
            minimum_cap_slack_usdt=float((caps-z).min()),exante_cap_violation_cells=int(np.sum(z-caps>1e-7*np.maximum(e.initial,1.))),
            primal=max(r['primal'] for r in record),kkt=max(r['kkt'] for r in record),decomposition=max(r['decomposition'] for r in record),
            solve_seconds=sum(r['seconds'] for r in record),max_replan_seconds=max(r['seconds'] for r in record),replans=len(record),
            raw_risk_usdt_squared=raw,risk_preference_usdt=beta*raw,repairs=0))
    # Volume-proportional diagnostic under original fixed caps, no hidden projection.
    v1=p0['V1'];vw=v1*(e.initial/v1.sum(axis=0));tw=capped_uniform_reference(e.initial,caps)
    if (vw>caps+1e-7*np.maximum(e.initial,1.)).any():raise RuntimeError('V1 VWAP violates fixed caps')
    paths['TWAP']=tw;paths['VWAP']=vw
    return paths,diagnostics,receipts,used,p0


def development(root,pilot=False):
    root=Path(root);out,bulk=locations(root);gate=json.loads((out/'forecast_gate.json').read_text());scenario=json.loads((out/'scenario_calibration.json').read_text())
    if sha256(out/'scenario_calibration.json')!=gate['scenario_sha256'] or sha256(root/'configs/extension_x1_adaptive_liquidity.yaml')!=gate['config_sha256'] or sha256(root/'docs/extensions/x1_adaptive_liquidity_protocol_v1.md')!=gate['protocol_sha256']:
        raise ValueError('Forecast gate/config/calibration changed')
    code_hash=numerical_lock(root)
    store=X1Store(root);scorer=X1Store(root);fitter=DevelopmentFitter(root,X1Store(root));pc=policy_config(root)
    inputs=pd.read_parquet(root/'results/stage04_development/inputs_development.parquet');records=[json.loads(s) for s in inputs.episode_json]
    if len(records)!=736:raise ValueError('Stage4 common universe changed')
    if pilot:records=[r for r in records if pd.Timestamp(r['t0']) in pd.DatetimeIndex(cfg(root)['pilot_origins'])]
    from ..episodes import Episode
    suffix='pilot' if pilot else 'development';folder=bulk/suffix;folder.mkdir(exist_ok=True)
    all_scores=[];all_diagnostics=[];part=[];failures=[];summary=[];last=None;start=time.perf_counter()
    original_schedules=pd.read_parquet(root/'results/stage04_development/schedules_development.parquet')
    for no,r in enumerate(records):
        e=Episode(r['episode_id'],pd.Timestamp(r['t0']),r['forecast'],r['covariance'],r['initial'],r['p0'],r['provenance'])
        receipt=folder/f'{e.episode_id}.json';schedule_path=folder/f'{e.episode_id}.npz'
        if receipt.exists() and schedule_path.exists():
            saved=json.loads(receipt.read_text())
            if saved['input_hash']!=e.input_hash or saved['gate_hash']!=sha256(out/'forecast_gate.json') or saved['schedule_sha256']!=sha256(schedule_path):raise ValueError('Replay checkpoint mismatch')
            all_scores.extend(saved['scores']);all_diagnostics.extend(saved['diagnostics']);part.extend(saved['participation']);summary.append(saved['baseline_check']);continue
        month=e.t0.strftime('%Y-%m')
        if month!=last:
            models=load_models(root,month,e.t0);fit=fitter.fit(month+'-01T00:00:00Z');e1=validate_fit(fit,month+'-01T00:00:00Z','E1')
            worlds=[World('E1',e1,.001),World('E2',without_cross(e1),.001)];last=month
        try:
            # Rebuild original arrival independently, using only completed history.
            rebuilt=construct_episode(store.history(e.t0),e.t0,pc)
            if rebuilt.input_hash!=e.input_hash:raise ValueError('Stage4 input parity failed')
            paths,diagnostics,receipts,used,p0=episode_policies(root,e,store,models,gate,scenario)
            prior=original_schedules[(original_schedules.episode_id==e.episode_id)&(original_schedules.policy=='T4')].sort_values('minute')
            prior=prior[['btc_sales_usdt','eth_sales_usdt']].to_numpy()
            error=float(np.max(np.abs(paths['P0']-prior)/e.initial))
            if error>1e-7:raise ValueError('P0 != Stage4 T4')
            baseline_check=dict(episode_id=e.episode_id,schedule_error_over_initial=error,
                V1_V0_relative_l2=float(np.linalg.norm(p0['V1']-p0['V0'])/np.linalg.norm(p0['V0'])),
                VWAP_TWAP_relative_l2=float(np.linalg.norm(paths['VWAP']-paths['TWAP'])/np.linalg.norm(paths['TWAP'])))
            np.savez_compressed(schedule_path,**paths,**{f'forecast_{k}':v for k,v in used.items()})
            # Immutable commitments persisted BEFORE future score bars are opened.
            decisions=dict(episode_id=e.episode_id,input_hash=e.input_hash,gate_hash=sha256(out/'forecast_gate.json'),
                config_hash=gate['config_sha256'],numerical_lock_hash=code_hash,schedule_sha256=sha256(schedule_path),committed_utc=utcnow(),
                original_caps_hash=digest(.1*e.forecast),covariance_hash=digest(e.covariance),
                model_hash=models['B'].model_hash,world_hashes={w.world_id:w.world_hash for w in worlds},
                receipts=receipts,diagnostics=diagnostics,baseline_check=baseline_check,
                funding_included=False,observation_latency='bar_open+1minute')
            decision_path=folder/f'{e.episode_id}_decisions.json'
            if decision_path.exists():
                old=json.loads(decision_path.read_text())
                if old['schedule_sha256']!=sha256(schedule_path):raise ValueError('Immutable decision changed')
            else:save(decision_path,decisions)
            truth=scorer.paired(e.t0,e.t0+pd.Timedelta(hours=1),purpose='committed_schedule_scoring',asof=e.t0+pd.Timedelta(hours=1))
            prices,vreal=evaluation_prices(truth,e.t0,60)
            scores=[];participation=[]
            for name,z in paths.items():
                for world in worlds:
                    value=score_schedule(z,e.initial,e.forecast,e.p0,prices,vreal,world)
                    scores.append(dict(episode_id=e.episode_id,policy=name,day=e.t0.strftime('%Y-%m-%d'),month=month,
                        weekend=e.t0.day_of_week>=5,liquidity_usdt=float(e.forecast.sum()),**value))
                ratio=np.divide(z,vreal,out=np.full_like(z,np.nan),where=vreal>0);positive=ratio[np.isfinite(ratio)]
                participation.append(dict(episode_id=e.episode_id,policy=name,positive_cells=len(positive),zero_volume_cells=int((vreal==0).sum()),
                    positive_sales_zero_volume=int(((vreal==0)&(z>1e-8)).sum()),over10=int((positive>.1).sum()),over20=int((positive>.2).sum()),over100=int((positive>1).sum()),
                    maximum=float(positive.max()) if len(positive) else None,p95=float(np.quantile(positive,.95)),p99=float(np.quantile(positive,.99))))
            completed_record=dict(**{k:v for k,v in decisions.items() if k!='receipts'},scores=scores,participation=participation,decision_sha256=sha256(decision_path))
            save(receipt,completed_record);all_scores.extend(scores);all_diagnostics.extend(diagnostics);part.extend(participation);summary.append(baseline_check)
        except (ValueError,RuntimeError) as exc:
            failures.append(dict(episode_id=e.episode_id,reason=str(exc),common_failure=True));save(out/f'failures_{suffix}.json',failures)
            if pilot:raise
        if (no+1)%25==0:print(f'X1 {suffix} {no+1}/{len(records)} elapsed {(time.perf_counter()-start)/60:.2f}min',flush=True)
    pd.DataFrame(all_scores).to_csv(out/f'scores_{suffix}.csv',index=False);pd.DataFrame(all_diagnostics).to_csv(out/f'policy_diagnostics_{suffix}.csv',index=False)
    pd.DataFrame(part).to_csv(out/f'participation_episodes_{suffix}.csv',index=False);pd.DataFrame(summary).to_csv(out/f'baseline_parity_{suffix}.csv',index=False)
    save(out/f'failures_{suffix}.json',failures)
    result=dict(nominal=len(records),complete=len(summary),failures=len(failures),scores=len(all_scores),
        seconds=time.perf_counter()-start,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024**2,
        forecast_gate=gate,policy_status={p:('PASS' if p in {d['policy'] for d in all_diagnostics} else 'NOT_RUN_FORECAST_GATE') for p in ['P0','P1','P2','P3','P4','P4M','D0','D1']},
        canonical_partitions=sorted(set(store.read_log+scorer.read_log+fitter.store.read_log)),
        policy_reads=store.calls,score_reads=scorer.calls,final_test_partitions_opened=0)
    save(out/f'run_{suffix}.json',result)
    if pilot:
        # Independent complete pilot reconstruction; schedules byte-identical,
        # deterministic E1/E2 cash/participation metrics exactly reproduced.
        matches=[]
        for r in records:
            e=Episode(r['episode_id'],pd.Timestamp(r['t0']),r['forecast'],r['covariance'],r['initial'],r['p0'],r['provenance'])
            paths,*_=episode_policies(root,e,X1Store(root),load_models(root,e.t0.strftime('%Y-%m'),e.t0),gate,scenario)
            with np.load(folder/f'{e.episode_id}.npz') as old:
                match=all(np.array_equal(old[p],z) for p,z in paths.items())
            prior=json.loads((folder/f'{e.episode_id}.json').read_text())
            fit=fitter.fit(e.t0.normalize().replace(day=1));e1=validate_fit(fit,e.t0.normalize().replace(day=1),'E1')
            ws={'E1':World('E1',e1,.001),'E2':World('E2',without_cross(e1),.001)}
            truth=scorer.paired(e.t0,e.t0+pd.Timedelta(hours=1),purpose='pilot_reproducibility',asof=e.t0+pd.Timedelta(hours=1))
            prices,vreal=evaluation_prices(truth,e.t0,60)
            metric_match=True
            for row in prior['scores']:
                again=score_schedule(paths[row['policy']],e.initial,e.forecast,e.p0,prices,vreal,ws[row['world']])
                metric_match &= all(row[k]==v for k,v in again.items())
            matches.append(dict(origin=str(e.t0),schedule_byte_identical=match,metrics_identical=metric_match))
        save(out/'pilot_reproducibility.json',matches)
        if not all(m['schedule_byte_identical'] and m['metrics_identical'] for m in matches):raise RuntimeError('Pilot not deterministic')
    return result
