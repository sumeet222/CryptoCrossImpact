"""Fixed contrasts, calendar-block uncertainty, failure/tail and QA tables."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from ..evaluation.v2_inference import paired_interval
from ..data.storage import sha256,utcnow
from .common import paths,save,preserve


def summarize(root):
    root=Path(root);out,bulk=paths(root);s=pd.read_csv(out/'development_scores.csv');o=pd.read_csv(out/'development_overload.csv');q=pd.read_csv(out/'development_diagnostics.csv')
    selection=json.loads((out/'eta_selection.json').read_text());eta=selection['selected_eta'];edges=json.loads((root/'reports/research/extension_x2x3_artifacts/development_selection.json').read_text())['past_liquidity_terciles_usdt']
    for f in [s,o]:f['regime']=pd.cut(f.past_liquidity_usdt,[-np.inf,*edges,np.inf],labels=['low','middle','high']).astype(str)
    calendar=pd.date_range('2025-07-01','2026-01-01',inclusive='left').strftime('%Y-%m-%d');cost=[];liquidity=[]
    pairs=[('A0','A1'),('A2','A1'),('A3','A1')]
    for e in [.5,1]:pairs += [('A0',f'eta{e}_refresh'),(f'eta{e}_diag',f'eta{e}_refresh'),(f'eta{e}_frozen',f'eta{e}_refresh'),('A0',f'fixed_eta{e}'),(f'fixed_eta{e}',f'eta{e}_refresh')]
    groups=[('all',None)]+[(m,('month',m)) for m in sorted(o.month.unique())]+[(f'weekend_{w}',('weekend',w)) for w in [False,True]]+[(f'liquidity_{v}',('regime',v)) for v in ['low','middle','high']]
    labels=set(o.month.unique())
    for old,new in pairs:
        a=o[o.policy==old].set_index('episode_id');b=o[o.policy==new].set_index('episode_id');d=a.copy();d['difference']=a.overload-b.overload;d['baseline']=a.overload
        if not a.index.equals(b.index):raise ValueError('Unmatched Stage A overload sample')
        for group,condition in groups:
            part=d if condition is None else d[d[condition[0]]==condition[1]]
            if not len(part):continue
            days=calendar if group not in labels else pd.date_range(group+'-01',pd.Timestamp(group+'-01')+pd.offsets.MonthBegin(1),inclusive='left').strftime('%Y-%m-%d')
            daily=part.groupby('day').agg(delta=('difference','sum'),n=('difference','size'),base=('baseline','sum')).reindex(days,fill_value=0)
            liquidity.append(dict(control=old,new=new,group=group,mean_old=float(part.overload.mean()),mean_new=float(b.loc[part.index].overload.mean()),**paired_interval(days,daily.delta.to_numpy(),daily.n.to_numpy(),daily.base.to_numpy())))
        for world,g in s.groupby('world'):
            a=g[g.policy==old].set_index('episode_id');b=g[g.policy==new].set_index('episode_id');d=a.copy();d['difference']=a.shortfall_ex_funding_bps-b.shortfall_ex_funding_bps
            if not a.index.equals(b.index):raise ValueError('Unmatched Stage A common world')
            for group,condition in groups:
                part=d if condition is None else d[d[condition[0]]==condition[1]]
                if not len(part):continue
                days=calendar if group not in labels else pd.date_range(group+'-01',pd.Timestamp(group+'-01')+pd.offsets.MonthBegin(1),inclusive='left').strftime('%Y-%m-%d')
                daily=part.groupby('day').agg(delta=('difference','sum'),n=('difference','size')).reindex(days,fill_value=0)
                cost.append(dict(control=old,new=new,world=world,group=group,negative_share=float((part.difference<0).mean()),p95_disadvantage_bps=float((-part.difference).quantile(.95)),worst_bps=float(part.difference.min()),**paired_interval(days,daily.delta.to_numpy(),daily.n.to_numpy())))
    pd.DataFrame(cost).to_csv(out/'execution_contrasts.csv',index=False);pd.DataFrame(liquidity).to_csv(out/'overload_contrasts.csv',index=False)
    policies=s.groupby(['world','policy']).agg(episodes=('episode_id','size'),mean_bps=('shortfall_ex_funding_bps','mean'),median_bps=('shortfall_ex_funding_bps','median'),p95_bps=('shortfall_ex_funding_bps',lambda x:x.quantile(.95)),path_usdt=('path_usdt','mean'),transient_usdt=('transient_usdt','mean'),temporary_usdt=('temporary_usdt','mean'),fee_usdt=('fee_usdt','mean'),spread_usdt=('spread_usdt','mean')).reset_index();policies.to_csv(out/'policy_comparison.csv',index=False)
    rows_=[]
    for p,g in o.groupby('policy'):
        daily=g.groupby('day').overload.mean();den=g.positive_volume_cells.sum();rows_.append(dict(policy=p,episodes=len(g),mean=g.overload.mean(),median=g.overload.median(),p90=g.overload.quantile(.9),p95=g.overload.quantile(.95),worst_day=daily.idxmax(),worst_day_mean=daily.max(),zero_rate=(g.overload==0).mean(),over10=int(g.over10.sum()),over20=int(g.over20.sum()),over100=int(g.over100.sum()),positive_volume_cells=int(den),over10_pct=100*g.over10.sum()/den,over20_pct=100*g.over20.sum()/den,over100_pct=100*g.over100.sum()/den,positive_sales_zero_cells=int(g.positive_sales_zero_cells.sum()),zero_sale_episodes=int((g.positive_sales_zero_cells>0).sum()),maximum_finite_ratio=g.max_finite_ratio.max()))
    pd.DataFrame(rows_).to_csv(out/'overload_diagnostics.csv',index=False)
    qa=q.groupby('policy').agg(cap_violations=('cap_violations','sum'),repairs=('repairs','sum'),terminal_max_usdt=('terminal_max_usdt','max'),normalized_primal_max=('primal','max'),KKT_max=('kkt','max'),decomposition_max=('decomposition','max'),solve_seconds=('solve_seconds','sum'),maximum_solve_seconds=('maximum_solve_seconds','max'),risk_preference_mean_usdt=('risk_preference_usdt','mean'),CVaR_preference_at_arrival_mean_usdt=('liquidity_preference_at_arrival_usdt','mean'),committed_state_impact_mean_usdt=('actual_committed_state_impact_usdt','mean')).reset_index();qa['mean_solve_seconds']=qa.solve_seconds/(736*12);qa.to_csv(out/'solver_QA.csv',index=False)
    tails=[];adverse=[]
    for world,g in s.groupby('world'):
        wide=g.pivot(index='episode_id',columns='policy',values='shortfall_ex_funding_bps');best=wide.min(axis=1)
        for p in wide:
            delta=wide.A0-wide[p];regret=wide[p]-best;tails.append(dict(world=world,policy=p,mean_regret_bps=regret.mean(),maximum_regret_bps=regret.max(),p95_disadvantage_to_A0_bps=(-delta).quantile(.95),negative_share=(delta<0).mean(),worst_delta_bps=delta.min()))
            for eid in delta.nsmallest(5).index:adverse.append(dict(world=world,policy=p,episode_id=eid,A0_minus_policy_bps=delta[eid]))
    pd.DataFrame(tails).to_csv(out/'scenario_tails.csv',index=False);pd.DataFrame(adverse).to_csv(out/'adverse_episodes.csv',index=False)
    save(out/'verdict.json',dict(implementation='PASS',selected_eta=eta,H_A1='DOES_NOT_SUPPORT' if eta==0 else 'SUPPORTS_HYPOTHESIS',H_A2='NO_INCREMENTAL_SELECTED_POLICY' if eta==0 else 'ASSESS_INDEPENDENT_WORLD_INTERVALS',H_A3='NO_SELECTED_POLICY_CHANGE' if eta==0 else 'ASSESS_OVERLOAD_AND_TAILS',scope='exploratory development; descriptive response and modeled funding-excluded cash, not causal/live fills'))


def audit(root):
    root=Path(root);out,bulk=paths(root);complete=[p for p in (bulk/'development').glob('*.json') if '_decisions' not in p.name and '_prefix_' not in p.name]
    if len(complete)!=736:raise ValueError('Stage A complete736 gate')
    prefixes=0;tri=0.;zero=True
    for path in complete:
        r=json.loads(path.read_text());dpath=root/r['decision_file'];d=json.loads(dpath.read_text())
        if sha256(dpath)!=r['decision_sha256'] or sha256(root/d['schedule_file'])!=d['schedule_sha256']:raise ValueError('Receipt/schedule change')
        if len(d['prefixes'])!=12:raise ValueError('Missing prefixes')
        with np.load(root/d['schedule_file']) as saved:
            x=np.array(d['initial'])
            for policy,recs in r['records'].items():
                z=saved[policy];a=saved['state_'+policy];zs=[];aa=[]
                if np.max(np.abs(z.sum(axis=0)-x)/x)>1e-7:raise ValueError('Terminal failure')
                for rec,proof in zip(recs,d['prefixes']):
                    p=root/proof['path']
                    if sha256(p)!=proof['sha256']:raise ValueError('Prefix hash')
                    v=json.loads(p.read_text());np.testing.assert_array_equal(v['committed'][policy],rec['prefix']);np.testing.assert_array_equal(v['multipliers'][policy],rec['multipliers'])
                    if pd.Timestamp(rec['latest_open'])!=pd.Timestamp(rec['asof'])-pd.Timedelta(minutes=1):raise ValueError('Clock violation')
                    if rec['primal']>1e-7 or rec['kkt']>2e-5:raise ValueError('Numerical failure')
                    zs.extend(rec['prefix']);aa.extend(rec['multipliers']);prefixes+=1
                np.testing.assert_array_equal(z,zs);np.testing.assert_array_equal(a,aa)
            if 'A1' in saved and json.loads((out/'eta_selection.json').read_text())['selected_eta']==0:
                np.testing.assert_array_equal(saved['A0'],saved['A1']);np.testing.assert_array_equal(saved['A0'],saved['A3'])
        tri=max(tri,r['triangle_error_usdt'])
    old=pd.read_csv(root/'reports/research/extension_x2x3_artifacts/selection_scores.csv');new=pd.read_csv(out/'development_scores.csv')
    a=old[(old.policy=='L25')&(old.world=='E1')].set_index('episode_id');b=new[(new.policy=='A0')&(new.world=='E_stationary')].set_index('episode_id')
    if len(a)!=736 or not a.index.sort_values().equals(b.index.sort_values()):raise ValueError('A0 common universe mismatch')
    a=a.sort_index();b=b.sort_index();baseline_error=float(np.max(np.abs(a.shortfall_ex_funding_bps-b.shortfall_ex_funding_bps)))
    if baseline_error>1e-9:raise ValueError('Original L25 complete-score parity failure')
    result=dict(original_L25_E1_score_error_bps=baseline_error,status='PASS',episodes=736,prefixes=prefixes,maximum_triangle_error_usdt=tri,selected_eta0_A0_A1_A3_exact=True,preservation=preserve(root),utc=utcnow());save(out/'development_output_audit.json',result);return result
