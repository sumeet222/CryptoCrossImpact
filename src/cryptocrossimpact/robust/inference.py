"""Paired calendar-day uncertainty and fixed-world tail/overload summaries."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from ..evaluation.v2_inference import paired_interval
from .common import paths,save


def inputs(root,holdout=False):
    out,_=paths(root);selection=json.loads((out/'development_selection.json').read_text())
    if holdout:
        s=pd.read_csv(out/'holdout_scores.csv');o=pd.read_csv(out/'holdout_overload.csv');q=pd.read_csv(out/'holdout_solver_diagnostics.csv')
    else:
        def read(suffix):
            f=pd.concat([pd.read_csv(out/f'{phase}_{suffix}.csv') for phase in ['selection','combined']],ignore_index=True)
            return f.drop_duplicates(['episode_id','policy']+(['world'] if suffix=='scores' else []))
        s=read('scores');o=read('overload');q=read('solver_diagnostics')
        for f in [s,o,q]:f.loc[f.policy==f'L{selection["display_lambda"]}','policy']='L'
        s=s[~s.policy.isin(['L25','L100'])];o=o[~o.policy.isin(['L25','L100'])];q=q[~q.policy.isin(['L25','L100'])]
    return s,o,q,selection


def summarize(root,holdout=False):
    out,_=paths(root);scores,over,qa,selection=inputs(root,holdout);label='holdout' if holdout else 'development'
    left,right=('2026-07-01','2026-10-01') if holdout else ('2025-07-01','2026-01-01')
    calendar=pd.date_range(left,right,freq='D',inclusive='left').strftime('%Y-%m-%d')
    if holdout:edges=selection['past_liquidity_terciles_usdt']
    else:edges=over[over.policy=='N'].past_liquidity_usdt.quantile([1/3,2/3]).tolist()
    for f in [scores,over]:f['liquidity_regime']=pd.cut(f.past_liquidity_usdt,[-np.inf,*edges,np.inf],labels=['low','middle','high']).astype(str)
    pairs=[('N','G'),('N','L'),('N','GL'),('N','GL-D'),('N','D'),('L','GL'),('GL-D','GL')]
    effects=[];liquidity_effects=[];adverse=[]
    groupings=[('all',None)]+[(m,('month',m)) for m in sorted(over.month.unique())]+[(f'weekend_{w}',('weekend',w)) for w in [False,True]]+[(f'liquidity_{v}',('liquidity_regime',v)) for v in ['low','middle','high']]
    def ci(d,metric,baseline=None,days=calendar):
        daily=d.groupby('day').agg(total=(metric,'sum'),n=(metric,'size'))
        daily=daily.reindex(days,fill_value=0)
        base=None if baseline is None else d.groupby('day')[baseline].sum().reindex(days,fill_value=0).to_numpy()
        return paired_interval(days,daily.total.to_numpy(),daily.n.to_numpy(),base)
    for old,new in pairs:
        a=over[over.policy==old].set_index('episode_id');b=over[over.policy==new].set_index('episode_id')
        if not a.index.equals(b.index):raise ValueError('Unpaired policy episodes')
        d=a.copy();d['difference']=a.overload-b.overload;d['baseline']=a.overload
        for group,condition in groupings:
            part=d if condition is None else d[d[condition[0]]==condition[1]]
            days=calendar
            if group.startswith('202'):
                start=pd.Timestamp(group+'-01');days=pd.date_range(start,start+pd.offsets.MonthBegin(1),freq='D',inclusive='left').strftime('%Y-%m-%d')
            if not len(part):continue
            liquidity_effects.append(dict(control=old,new=new,group=group,episodes=len(part),mean_control=float(part.overload.mean()),
                mean_new=float(b.loc[part.index].overload.mean()),median_difference=float(part.difference.median()),**ci(part,'difference','baseline',days)))
        for world,g in scores.groupby('world'):
            a=g[g.policy==old].set_index('episode_id');b=g[g.policy==new].set_index('episode_id');d=a.copy()
            d['difference']=a.shortfall_ex_funding_bps-b.shortfall_ex_funding_bps
            for group,condition in groupings:
                part=d if condition is None else d[d[condition[0]]==condition[1]];days=calendar
                if group.startswith('202'):
                    start=pd.Timestamp(group+'-01');days=pd.date_range(start,start+pd.offsets.MonthBegin(1),freq='D',inclusive='left').strftime('%Y-%m-%d')
                if not len(part):continue
                effects.append(dict(control=old,new=new,world=world,group=group,episodes=len(part),median_difference_bps=float(part.difference.median()),
                    negative_share=float((part.difference<0).mean()),p95_disadvantage_bps=float((-part.difference).quantile(.95)),worst_bps=float(part.difference.min()),**ci(part,'difference',days=days)))
            bad=d.nsmallest(5,'difference').reset_index();bad['control']=old;bad['new']=new;adverse.append(bad)
    effect=pd.DataFrame(effects);le=pd.DataFrame(liquidity_effects)
    effect.to_csv(out/f'{label}_pairwise_cost_contrasts.csv',index=False);le.to_csv(out/f'{label}_pairwise_overload_contrasts.csv',index=False)
    pd.concat(adverse,ignore_index=True).to_csv(out/f'{label}_adverse_episodes.csv',index=False)
    policy=scores.groupby(['world','policy']).agg(episodes=('episode_id','size'),mean_shortfall_bps=('shortfall_ex_funding_bps','mean'),median_shortfall_bps=('shortfall_ex_funding_bps','median'),
        path_usdt=('path_usdt','mean'),transient_usdt=('transient_usdt','mean'),temporary_usdt=('temporary_usdt','mean'),fee_usdt=('fee_usdt','mean'),spread_usdt=('spread_usdt','mean')).reset_index()
    policy.to_csv(out/f'{label}_policy_comparison.csv',index=False)
    rows=[]
    for policy,g in over.groupby('policy'):
        den=g.positive_volume_cells.sum();daily=g.groupby('day').overload.mean()
        rows.append(dict(policy=policy,episodes=len(g),mean_overload=g.overload.mean(),median_overload=g.overload.median(),p90_overload=g.overload.quantile(.9),p95_overload=g.overload.quantile(.95),
            zero_overload_rate=(g.overload==0).mean(),worst_day=daily.idxmax(),worst_day_mean_overload=daily.max(),positive_volume_cells=den,
            over10_pct=100*g.over10.sum()/den,over20_pct=100*g.over20.sum()/den,over100_pct=100*g.over100.sum()/den,
            zero_volume_cells=g.zero_cells.sum(),positive_sales_zero_cells=g.positive_sales_zero_cells.sum(),zero_sale_affected_episodes=(g.positive_sales_zero_cells>0).sum(),
            maximum_finite_ratio=g.max_finite_ratio.max(),episodes_over100=(g.over100>0).sum()))
    overload_summary=pd.DataFrame(rows);overload_summary.to_csv(out/f'{label}_overload_diagnostics.csv',index=False)
    tails=[];fixed=['N','G','L','GL','GL-D','D']
    for world,g in scores[scores.policy.isin(fixed)].groupby('world'):
        wide=g.pivot(index='episode_id',columns='policy',values='shortfall_ex_funding_bps');best=wide.min(axis=1)
        for policy in fixed:
            regret=wide[policy]-best;diff=wide[policy]-wide.N
            tails.append(dict(world=world,policy=policy,mean_shortfall_bps=wide[policy].mean(),mean_regret_bps=regret.mean(),maximum_regret_bps=regret.max(),
                p95_disadvantage_to_N_bps=diff.quantile(.95),loses_to_N_share=(diff>0).mean()))
    stress=pd.DataFrame(tails);stress.to_csv(out/f'{label}_independent_scenario_stress.csv',index=False)
    worst=scores[scores.policy.isin(fixed)].groupby(['episode_id','policy']).shortfall_ex_funding_bps.max().unstack()
    worst_rows=[]
    for policy in fixed:
        disadvantage=worst[policy]-worst.N
        worst_rows.append(dict(policy=policy,mean_worst_world_bps=worst[policy].mean(),p95_worst_world_bps=worst[policy].quantile(.95),
            p95_worst_world_disadvantage_to_N_bps=disadvantage.quantile(.95),maximum_worst_world_disadvantage_to_N_bps=disadvantage.max()))
    pd.DataFrame(worst_rows).to_csv(out/f'{label}_worst_world_tail.csv',index=False)
    q=qa.groupby('policy').agg(cap_violations=('cap_violations','sum'),terminal_max_usdt=('terminal_max_usdt','max'),KKT_max=('kkt','max'),epigraph_gap_max=('epigraph_gap','max'),
        decomposition_max=('decomposition','max'),primal_max=('primal','max'),repairs=('repairs','sum'),solve_seconds=('solve_seconds','sum'),maximum_solve_seconds=('maximum_solve_seconds','max'),
        risk_preference_mean_usdt=('risk_preference_usdt','mean'),liquidity_preference_at_arrival_mean_usdt=('liquidity_preference_at_arrival_usdt','mean')).reset_index()
    q.to_csv(out/f'{label}_solver_QA_summary.csv',index=False)
    primary=le[(le.control=='N')&(le.new==('L' if selection['selected_candidate']=='L' else 'GL'))&(le.group=='all')].iloc[0]
    cost=effect[(effect.control=='N')&(effect.new==primary['new'])&(effect.world=='E1')&(effect.group=='all')].iloc[0]
    practical=primary.get('relative_reduction',0)>=.1 and cost['mean']>=-.1
    verdict='ROBUST_GAIN_SUPPORTED' if practical and primary.ci_low>0 and cost.ci_low>=-.1 else 'TRADEOFF_OR_MIXED' if practical else 'NO_PRACTICAL_GAIN' if primary.get('relative_reduction',0)<.1 else 'INCONCLUSIVE'
    result=dict(phase=label,implementation='PASS',scientific_label=verdict,selected_candidate=selection['selected_candidate'],selected_lambda=selection['selected_lambda'],
        reported_enhancement=primary['new'],mean_overload_difference=primary['mean'],overload_CI=[primary.ci_low,primary.ci_high],relative_overload_reduction=primary.get('relative_reduction'),
        E1_mean_cost_advantage_bps=cost['mean'],E1_cost_CI=[cost.ci_low,cost.ci_high],practical_hurdle_point_estimate=bool(practical),
        scope='modeled_execution_shortfall_excluding_funding; overload diagnostic; no live/causal fill claim')
    save(out/f'{label}_verdict.json',result);return result
