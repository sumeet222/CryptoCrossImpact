#!/usr/bin/env python3
"""Independent read-only audit of committed X1 development outputs; no 2026 I/O."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from cryptocrossimpact.data.storage import sha256,utcnow
from cryptocrossimpact.evaluation.v2_common import save,digest
from cryptocrossimpact.execution.impact_cost import triangular_cash
from cryptocrossimpact.execution.policies import without_cross,load_models
from cryptocrossimpact.episodes import Episode
from cryptocrossimpact.liquidity.workflow import X1Store,locations,preservation,numerical_lock,beta_for
from cryptocrossimpact.episodes import config
from cryptocrossimpact.evaluation.v2_fit import validate_fit
from cryptocrossimpact.evaluation.v2_score import World,score_schedule,evaluation_prices

root=Path(__file__).resolve().parents[1];out,bulk=locations(root)
lock=numerical_lock(root);accepted_locks={lock,sha256(out/'numerical_lock.json')};pc=config(root);gate=json.loads((out/'forecast_gate.json').read_text())
inputs={}
for s in pd.read_parquet(root/'results/stage04_development/inputs_development.parquet').episode_json:
    r=json.loads(s);inputs[r['episode_id']]=Episode(r['episode_id'],pd.Timestamp(r['t0']),r['forecast'],r['covariance'],r['initial'],r['p0'],r['provenance'])
max_terminal=0;max_cash_error=0;max_score_error=0;max_baseline_error=0;episodes=0;prefixes=0;triangular_checks=0;score_checks=0
store=X1Store(root);models_cache={}
old=pd.read_parquet(root/'results/stage04_development/schedules_development.parquet')
old=old[old.policy=='T4'].set_index('episode_id')
for path in sorted((bulk/'development').glob('*_decisions.json')):
    receipt=json.loads(path.read_text());eid=receipt['episode_id'];e=inputs[eid];month=e.t0.strftime('%Y-%m')
    assert e.t0.year==2025 and receipt['input_hash']==e.input_hash
    assert receipt['numerical_lock_hash'] in accepted_locks and receipt['gate_hash']==sha256(out/'forecast_gate.json')
    assert receipt['original_caps_hash']==digest(.1*e.forecast) and receipt['covariance_hash']==digest(e.covariance)
    assert receipt['funding_included'] is False
    score=json.loads(path.with_name(eid+'.json').read_text())
    assert score['decision_sha256']==sha256(path)
    npz=path.with_name(eid+'.npz');assert sha256(npz)==receipt['schedule_sha256']
    if month not in models_cache:
        m=json.loads((out/'models'/f'{month}_E1.json').read_text());k=validate_fit(m,e.t0.normalize().replace(day=1),'E1')
        assert m['training_rows']==259200 and pd.Timestamp(m['training_end_exclusive'])<=e.t0.normalize().replace(day=1)-pd.Timedelta(days=30)
        models_cache[month]=(load_models(root,month,e.t0),[World('E1',k,.001),World('E2',without_cross(k),.001)])
    models,worlds=models_cache[month]
    assert receipt['model_hash']==models['B'].model_hash
    assert receipt['world_hashes']=={w.world_id:w.world_hash for w in worlds}
    betas={d['beta'] for d in receipt['diagnostics']}
    assert len(betas)==1 and next(iter(betas))==beta_for(e,models['B'].kernel,pc)
    with np.load(npz) as data:
        for policy,records in receipt['receipts'].items():
            z=data[policy];caps=.1*e.forecast
            residual=float(np.max(np.abs(z.sum(axis=0)-e.initial)));max_terminal=max(max_terminal,residual)
            assert np.max(np.abs(z.sum(axis=0)-e.initial)/e.initial)<=1e-7
            assert (z>=-1e-7*e.initial).all() and (z<=caps+1e-7*e.initial).all()
            committed=[]
            for r in records:
                t=e.t0+pd.Timedelta(minutes=r['k'])
                assert pd.Timestamp(r['asof'])==t and pd.Timestamp(r['latest_open'])==t-pd.Timedelta(minutes=1) and pd.Timestamp(r['latest_available_at'])==t
                assert r['kkt']<2e-6 and r['primal']<1e-7 and r['decomposition']<1e-8
                assert np.array_equal(e.initial-np.vstack(committed).sum(axis=0) if committed else e.initial,np.array(r['remaining']))
                committed.append(np.array(r['prefix']));prefixes+=1
            np.testing.assert_array_equal(z,np.vstack(committed))
        prior=old.loc[eid].sort_values('minute')[['btc_sales_usdt','eth_sales_usdt']].to_numpy()
        max_baseline_error=max(max_baseline_error,float(np.max(np.abs(data['P0']-prior)/e.initial)))
        assert max_baseline_error<1e-7
        # Predeclared first origin per month: independent triangular cash and
        # complete five-component score reproduction, all arms/worlds.
        if e.t0.day==1 and e.t0.hour==0:
            truth=store.paired(e.t0,e.t0+pd.Timedelta(hours=1),purpose='posthoc_output_audit',asof=e.t0+pd.Timedelta(hours=1))
            prices,vol=evaluation_prices(truth,e.t0,60)
            for row in score['scores']:
                world=next(w for w in worlds if w.world_id==row['world']);z=data[row['policy']]
                cash=triangular_cash(world.kernel,z);err=abs(cash-row['transient_usdt']);max_cash_error=max(max_cash_error,err);triangular_checks+=1
                assert err<=1e-8*max(abs(cash),1)
                again=score_schedule(z,e.initial,e.forecast,e.p0,prices,vol,world)
                for key in ['shortfall_ex_funding_bps','path_usdt','transient_usdt','temporary_usdt','fee_usdt','spread_usdt']:
                    error=abs(row[key]-again[key]);max_score_error=max(max_score_error,error);assert error<1e-10*max(abs(row[key]),1)
                score_checks+=1
    episodes+=1
assert episodes==736
result=dict(utc=utcnow(),status='PASS',episodes=episodes,prefixes=prefixes,independent_triangular_checks=triangular_checks,
    full_score_reproductions=score_checks,maximum_triangular_error_usdt=max_cash_error,maximum_score_error=max_score_error,
    maximum_terminal_usdt=max_terminal,maximum_baseline_schedule_error_over_initial=max_baseline_error,
    matched_beta_caps_inventory_covariance_models_worlds_verified=True,prefix_clock_commitments_verified=True,
    preservation=preservation(root,True),audit_partitions=sorted(set(store.read_log)),final_test_partitions_opened=0)
save(out/'output_audit.json',result);print(json.dumps(result,indent=2))
