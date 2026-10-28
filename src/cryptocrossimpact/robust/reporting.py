"""X2+X3 reports/figures from frozen outputs; no policy/model tuning."""
import json
import os
from pathlib import Path
import platform
import importlib.metadata
import subprocess
import numpy as np
import pandas as pd
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[3]/'results/extension_x2x3/matplotlibcache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from ..data.storage import sha256,utcnow
from ..execution.impact_cost import load_stage02
from .common import paths,config,preserve,binding,save
from .scenarios import ambiguity,joint_paths
from .data import Store
from .workflow import development_episodes,model_bundle
from .inference import inputs,summarize


def table(f,columns=None):
    f=f[columns] if columns else f
    def cell(v):return f'{v:.6g}' if isinstance(v,(float,np.floating)) else str(v)
    return '| '+' | '.join(f.columns)+' |\n| '+' | '.join(['---']*len(f.columns))+' |\n'+'\n'.join('| '+' | '.join(cell(v) for v in r)+' |' for r in f.itertuples(index=False,name=None))


def phase_figures(root,phase):
    root=Path(root);out,bulk=paths(root);fig=root/'figures/extension_x2x3';fig.mkdir(exist_ok=True)
    held=phase=='holdout';scores,over,qa,selection=inputs(root,held)
    cost=pd.read_csv(out/f'{phase}_pairwise_cost_contrasts.csv');liq=pd.read_csv(out/f'{phase}_pairwise_overload_contrasts.csv')
    c=cost[(cost.group=='all')&(cost.world=='E1')&(cost.control=='N')].set_index('new')
    l=liq[(liq.group=='all')&(liq.control=='N')].set_index('new')
    f,ax=plt.subplots(figsize=(8,6))
    for policy in ['G','L','GL','GL-D','D']:
        a=l.loc[policy];b=c.loc[policy];x=a['mean']*100;y=b['mean']
        ax.errorbar(x,y,xerr=[[100*(a['mean']-a.ci_low)],[100*(a.ci_high-a['mean'])]],
            yerr=[[b['mean']-b.ci_low],[b.ci_high-b['mean']]],fmt='o',capsize=3,label=policy)
        offset={'G':(6,5),'D':(6,5),'L':(12,-25),'GL':(12,10),'GL-D':(12,28)}[policy]
        ax.annotate(policy,(x,y),xytext=offset,textcoords='offset points',arrowprops=dict(arrowstyle='-',lw=.5,color='.4'))
    threshold=.1*float(l.loc['L'].mean_control)*100
    ax.axvline(threshold,color='grey',ls='--',label='10% relative overload hurdle');ax.axhline(-.10,color='grey',ls=':',label='0.10 bp cost-increase limit')
    ax.axvline(0,color='.8');ax.axhline(0,color='.8');ax.set_xlabel('O(N) − O(policy), percentage points (positive favors policy)')
    ax.set_ylabel('E1 cost(N) − cost(policy), bp (funding excluded)');ax.set_title(f'{phase}: paired liquidity/cost tradeoff\n95% seven-day block descriptive intervals')
    ax.legend(fontsize=8);f.tight_layout();f.savefig(fig/f'{phase}_tradeoff.png',dpi=140);plt.close(f)
    f,(ax,bar)=plt.subplots(1,2,figsize=(12,5));policies=['N','G','L','GL','GL-D','D']
    for i,p in enumerate(policies):
        d=over[over.policy==p];values=d.max_finite_ratio.to_numpy()*100
        ax.scatter(i+.08*np.sin(np.arange(len(values))),values,s=7,alpha=.25)
        ax.scatter(i,np.max(values),marker='x',color='red')
    ax.set_yscale('log');ax.axhline(100,color='red',ls='--');ax.set_xticks(np.arange(len(policies)),policies);ax.set_ylabel('Episode maximum finite participation (%) · log scale')
    summary=pd.read_csv(out/f'{phase}_overload_diagnostics.csv').set_index('policy').loc[policies]
    bar.bar(np.arange(len(policies))-.15,summary.over10_pct,width=.3,label='>10%');bar.bar(np.arange(len(policies))+.15,summary.over20_pct,width=.3,label='>20%')
    bar.set_xticks(np.arange(len(policies)),[f'{p}\nsales @ V=0\n{int(summary.loc[p,"positive_sales_zero_cells"])}' for p in policies],fontsize=8)
    bar.set_ylabel('Positive-volume asset-minute incidents (%)');bar.legend();f.suptitle(f'{phase}: realized liquidity diagnostics; zero-volume ratios undefined/infeasible')
    f.tight_layout();f.savefig(fig/f'{phase}_participation.png',dpi=140);plt.close(f)
    means=cost[(cost.group=='all')&(cost.control=='N')].pivot(index='world',columns='new',values='mean')
    means=means.reindex(columns=policies[1:]);v=max(float(np.abs(means).max().max()),1e-6)
    f,ax=plt.subplots(figsize=(9,7));im=ax.imshow(means.to_numpy(),cmap='RdBu',vmin=-v,vmax=v,aspect='auto')
    ax.set_xticks(np.arange(len(means.columns)),means.columns);ax.set_yticks(np.arange(len(means)),means.index,fontsize=8)
    for i in range(len(means)):
        for j in range(len(means.columns)):ax.text(j,i,f'{means.iloc[i,j]:+.3f}',ha='center',va='center',fontsize=8)
    f.colorbar(im,ax=ax,label='Cost(N) − cost(policy), bp, funding excluded');ax.set_title(f'{phase}: every independent/stress world (no E0)')
    f.tight_layout();f.savefig(fig/f'{phase}_worlds.png',dpi=140);plt.close(f)


def scenario_diagnostics(root,holdout=False):
    """Reconstruct the frozen arrival bank from past data; posthoc labels only."""
    root=Path(root);out,bulk=paths(root);store=Store(root);rows=[];example=None;phase='holdout' if holdout else 'development'
    s1=np.array(json.loads((root/'reports/research/extension_x1_artifacts/scenario_calibration.json').read_text())['factors'])
    for p in sorted((bulk/('holdout' if holdout else 'selection')).glob('*.json')):
        if p.name.endswith('_decisions.json') or '_prefix_' in p.name:continue
        r=json.loads(p.read_text());t=pd.Timestamp(r['episode_id'][:8]+'T'+r['episode_id'][9:13]+'00Z')
        h=store.history(t);point=np.array(r['forecast_V1_at_arrival']);bank,qa=joint_paths(h,t,t,point);actual=np.array(r['source_actual_volume_posthoc'])
        quantiles=np.quantile(bank,[.1,.5,.9],axis=0)
        old_bands=point[:,None,:]*s1[np.searchsorted([5,15,60],np.arange(1,61),side='left')]
        for i,asset in enumerate(['BTCUSDT','ETHUSDT']):
            for b,left,right in [(0,0,5),(1,5,15),(2,15,60)]:
                for qi,q in enumerate([.1,.5,.9]):
                    a=actual[left:right,i];pred=quantiles[qi,left:right,i];err=a-pred
                    rows.append(dict(model='joint_12_paths',asset=asset,bucket=b,quantile=q,n=len(a),covered=int((a<=pred).sum()),pinball_sum_usdt=float(np.maximum(q*err,(q-1)*err).sum())))
                    pred=old_bands[left:right,qi,i];err=a-pred
                    rows.append(dict(model='X1_frozen_S1_marginal',asset=asset,bucket=b,quantile=q,n=len(a),covered=int((a<=pred).sum()),pinball_sum_usdt=float(np.maximum(q*err,(q-1)*err).sum())))
        if r['episode_id']=='20250801T0000Z':example=(point,bank,actual,r)
    f=pd.DataFrame(rows).groupby(['model','asset','bucket','quantile']).sum().reset_index();f['coverage']=f.covered/f.n;f['pinball_usdt']=f.pinball_sum_usdt/f.n
    f.to_csv(out/f'{phase}_scenario_coverage.csv',index=False)
    if example is None:return
    fig=root/'figures/extension_x2x3';fig.mkdir(exist_ok=True);point,bank,actual,r=example
    f,axes=plt.subplots(1,2,figsize=(12,4))
    for i,asset in enumerate(['BTCUSDT','ETHUSDT']):
        ax=axes[i]
        for path in bank:ax.plot(np.arange(60),path[:,i]/1e6,color='tab:blue',alpha=.15)
        ax.plot(point[:,i]/1e6,color='tab:red',label='V1 as of arrival');ax.plot(actual[:,i]/1e6,color='black',label='Observed posthoc')
        ax.set_title(asset);ax.set_xlabel('Minute after 2025-08-01 00:00 UTC');ax.set_ylabel('Turnover (million USDT/min)');ax.legend(fontsize=8)
    f.suptitle('Twelve coherent past-hour paths scaled by known V1; observed overlay only for scoring')
    f.tight_layout();f.savefig(fig/'joint_paths.png',dpi=140);plt.close(f)
    data=[]
    for s in range(12):
        for minute in range(60):data.append(dict(scenario=s,minute=minute,BTC_scenario_usdt=bank[s,minute,0],ETH_scenario_usdt=bank[s,minute,1],BTC_observed_posthoc_usdt=actual[minute,0],ETH_observed_posthoc_usdt=actual[minute,1]))
    pd.DataFrame(data).to_csv(out/'joint_paths_figure_data.csv',index=False)


def context_figures(root):
    root=Path(root);out,bulk=paths(root);fig=root/'figures/extension_x2x3';fig.mkdir(exist_ok=True)
    e=development_episodes(root,True)[-1];b,_=model_bundle(root,e.t0.strftime('%Y-%m'),e.t0);family,audit=ambiguity(b,load_stage02(root,'B'))
    f,axes=plt.subplots(2,2,figsize=(10,7));lags=np.arange(61)
    curve_data=[]
    for name,k in family:
        curve=k.level(lags)*100000/np.sqrt(k.liquidity_usdt[:,None]*k.liquidity_usdt[None,:])
        for i in range(2):
            for j in range(2):axes[i,j].plot(lags,curve[:,i,j],label=name)
        curve_data.extend([dict(scenario=name,lag_minute=int(l),BTC_BTC_bp=curve[l,0,0],BTC_ETH_bp=curve[l,0,1],ETH_BTC_bp=curve[l,1,0],ETH_ETH_bp=curve[l,1,1]) for l in lags])
    for i in range(2):
        for j in range(2):
            axes[i,j].set_title(f'{["BTC","ETH"][j]} sale → {["BTC","ETH"][i]} scenario displacement');axes[i,j].set_xlabel('Lag (minutes)');axes[i,j].set_ylabel('bp per 100000 reference USDT');axes[i,j].legend(fontsize=7)
    f.suptitle('As-of August2025 ambiguity in common cash-consistent units');f.tight_layout();f.savefig(fig/'kernel_ambiguity.png',dpi=140);plt.close(f)
    pd.DataFrame(curve_data).to_csv(out/'kernel_ambiguity_figure_data.csv',index=False)
    source=[]
    for p in (bulk/'combined').glob('*.json'):
        if '_decisions' in p.name or '_prefix_' in p.name:continue
        r=json.loads(p.read_text())
        for pol,records in r['records'].items():source.extend(dict(policy=pol,scenario=a.get('active_scenario','nominal')) for a in records)
    counts=pd.DataFrame(source).groupby(['policy','scenario']).size().unstack(fill_value=0);counts=counts.div(counts.sum(axis=1),axis=0)
    f,ax=plt.subplots(figsize=(9,4));counts.plot.bar(stacked=True,ax=ax);ax.set_ylabel('Share of replans active');ax.set_title('Development: active worst-case ambiguity (dominance retained)');ax.tick_params(axis='x',rotation=0);f.tight_layout();f.savefig(fig/'active_scenarios.png',dpi=140);plt.close(f)
    counts.to_csv(out/'active_scenario_shares.csv')
    sel=json.loads((out/'development_selection.json').read_text());r1=json.loads((bulk/'selection'/f'{e.episode_id}.json').read_text());r2=json.loads((bulk/'combined'/f'{e.episode_id}.json').read_text())
    with np.load(bulk/'selection'/r1['schedule_file']) as d:paths_={p:d[p].copy() for p in ['N','D',f'L{sel["display_lambda"]}']}
    paths_['L']=paths_.pop(f'L{sel["display_lambda"]}')
    with np.load(bulk/'combined'/r2['schedule_file']) as d:paths_.update({p:d[p].copy() for p in ['G','GL','GL-D']})
    f,axes=plt.subplots(3,2,figsize=(11,9),sharex=True)
    rec={**r1['records'],**r2['records']};rec['L']=rec[f'L{sel["display_lambda"]}']
    for i,asset in enumerate(['BTCUSDT','ETHUSDT']):
        for p in ['N','L','G','GL','GL-D']:
            z=paths_[p];before=e.initial-np.vstack([np.zeros(2),np.cumsum(z,axis=0)[:-1]])
            axes[0,i].plot(np.arange(61),np.r_[before[:,i],0]/e.initial[i],label=p)
            axes[1,i].plot(z[:,i]/1000,label=p)
            axes[2,i].step([r['k'] for r in rec[p]],[r['history_gradient_usdt_per_usdt'][i]*1e4 for r in rec[p]],where='post',label=p)
        axes[1,i].plot(.1*e.forecast[:,i]/1000,color='grey',ls=':',label='Fixed initial cap')
        for ax in axes[:,i]:ax.legend(fontsize=7)
        axes[0,i].set_title(asset);axes[0,i].set_ylabel('Remaining / original inventory');axes[1,i].set_ylabel('Committed sales (thousand USDT/min)');axes[2,i].set_ylabel('Carried impact marginal cost (bp)');axes[2,i].set_xlabel('Minute after arrival')
    f.suptitle('Predeclared 2025-08-01 00:00 UTC example: committed paths and impact memory');f.tight_layout();f.savefig(fig/'committed_paths.png',dpi=140);plt.close(f)


def phase_activity(root,phase):
    """Posthoc active-scenario and unchanged PSD/dominance provenance."""
    root=Path(root);out,bulk=paths(root);folder=bulk/('holdout' if phase=='holdout' else 'combined')
    rows=[];audits=[]
    for path in sorted(folder.glob('*.json')):
        if '_decisions' in path.name or '_prefix_' in path.name:continue
        r=json.loads(path.read_text())
        audits.extend(dict(episode_id=r['episode_id'],**a) for a in r['ambiguity_audit'])
        for policy in ['G','GL','GL-D']:
            for a in r['records'][policy]:
                rows.append(dict(policy=policy,scenario=a['active_scenario'],dominance_reduction=a.get('dominance_reduction',False),predicted_remaining_CVaR=a.get('cvar',0)))
    f=pd.DataFrame(rows)
    g=f.groupby(['policy','scenario']).agg(replans=('scenario','size'),dominance_reduction_share=('dominance_reduction','mean'),mean_predicted_remaining_CVaR=('predicted_remaining_CVaR','mean')).reset_index()
    g['active_share']=g.replans/g.groupby('policy').replans.transform('sum')
    g.to_csv(out/f'{phase}_active_scenario_shares.csv',index=False)
    pd.DataFrame(audits).to_csv(out/f'{phase}_kernel_ambiguity_audit.csv',index=False)
    return g


def report(root):
    root=Path(root);out,bulk=paths(root);sel=json.loads((out/'development_selection.json').read_text())
    summarize(root);scenario_diagnostics(root);context_figures(root);phase_figures(root,'development')
    held=(out/'holdout_scores.csv').exists()
    if held:summarize(root,True);scenario_diagnostics(root,True);phase_figures(root,'holdout')
    gate=json.loads((out/'holdout_gate_audit.json').read_text()) if (out/'holdout_gate_audit.json').exists() else dict(status='NOT_RUN',reason='Pretest/development not yet complete')
    protected=preserve(root,True);test=json.loads((out/'pretest_tests.json').read_text()) if (out/'pretest_tests.json').exists() else {}
    context=pd.read_csv(root/'reports/research/extension_x1_artifacts/policy_cost_summary.csv')
    context=context[context.policy.isin(['P0','P1','P4'])]
    phases=['development']+(['holdout'] if held else [])
    for phase in phases:
        activity=phase_activity(root,phase)
        verdict=json.loads((out/f'{phase}_verdict.json').read_text());cost=pd.read_csv(out/f'{phase}_pairwise_cost_contrasts.csv');liq=pd.read_csv(out/f'{phase}_pairwise_overload_contrasts.csv')
        policy=pd.read_csv(out/f'{phase}_policy_comparison.csv');o=pd.read_csv(out/f'{phase}_overload_diagnostics.csv');q=pd.read_csv(out/f'{phase}_solver_QA_summary.csv');stress=pd.read_csv(out/f'{phase}_independent_scenario_stress.csv');tail=pd.read_csv(out/f'{phase}_worst_world_tail.csv')
        primary=cost[(cost.group=='all')&(cost.world=='E1')];lo=liq[liq.group=='all']
        group_cost=cost[(cost.control=='N')&(cost.new=='L')&(cost.world=='E1')][['group','episodes','mean','ci_low','ci_high']].rename(columns={'mean':'E1_advantage_bps','ci_low':'E1_CI_low','ci_high':'E1_CI_high'})
        group_over=liq[(liq.control=='N')&(liq.new=='L')][['group','mean_control','mean_new','mean','ci_low','ci_high']].rename(columns={'mean_control':'O_N','mean_new':'O_L','mean':'overload_reduction','ci_low':'O_CI_low','ci_high':'O_CI_high'})
        group_table=group_cost.merge(group_over,on='group',validate='one_to_one')
        group_table.to_csv(out/f'{phase}_monthly_regime.csv',index=False)
        coverage=pd.read_csv(out/f'{phase}_scenario_coverage.csv')
        q['mean_solve_seconds']=q.solve_seconds/(o.set_index('policy').loc[q.policy,'episodes'].to_numpy()*12)
        lc=primary.set_index(['control','new']).loc[('N','L')];ll=lo.set_index(['control','new']).loc[('N','L')]
        on=o.set_index('policy').loc['N'];ol=o.set_index('policy').loc['L'];ot=o.set_index('policy').loc['TWAP']
        nt=policy[(policy.world=='E1')&(policy.policy=='TWAP')].iloc[0]
        gn=primary.set_index(['control','new']).loc[('N','G')]
        gl=lo.set_index(['control','new']).loc[('N','G')]
        glc=primary.set_index(['control','new']).loc[('L','GL')];gll=lo.set_index(['control','new']).loc[('L','GL')]
        crossc=primary.set_index(['control','new']).loc[('GL-D','GL')];crossl=lo.set_index(['control','new']).loc[('GL-D','GL')]
        text=f'''# X2+X3 {phase}: robust impact, liquidity tails and funding-excluded execution

UTC {utcnow()}. **Implementation PASS; scientific label {verdict['scientific_label']}.**
DEVELOPMENT: PASS. PRETEST: {'READY' if (out/'PRETEST_READY_X2X3.json').exists() else 'NOT_REACHED'}.
NEW_OOS: {gate['status']}. New July–September2026 source values opened:
**{(out/'first_source_value_open.json').exists()}**. This {phase} sample is
{'a separately frozen three-month holdout' if phase=='holdout' else 'exploratory July–December2025, already used for research/model selection'}.
No old H1/H2 or X1 result was changed. All amounts exclude funding, which is
unobserved/omitted, not zero. No live fills or causal own-trade gains are established.

## Frozen question and design

[Protocol](../../docs/extensions/x2x3_robust_liquidity_protocol_v1.md),
[config](../../configs/extension_x2x3.yaml), and
[extension change record](../../docs/extensions/x2x3_spec_amendment_v1.md) define
H-L overload risk, H-G independent-world regret/tails, H-GL incremental combined
protection and H-cross same-self diagonal comparison. Original documents remain
immutable; a root changelog append would break their old lock hashes, so the
new dated extension record preserves those predecessors.

N reproduces X1 P2 (B/V1/five-minute MPC); D is X1 D1. G uses fixed finite
admissible kernel ambiguity; L adds CVaR90 overload preference; GL combines;
GL-D diagonalizes each same-self scenario. TWAP is context, not part of the
six-policy ex-post regret reference. X0=.02sum(V0), cap0=.1V0, beta/full Sigma,
reference prices, B/tau/L and fee5bp/halfspread1bp assumptions are fixed at arrival.
Kappa.001, theta1, no alpha, 60min, four starts/day, exact-cell cash convention.
Observed next-bar closes and volume affect scoring only after commitment.
No future value/existence check selects episodes or constraints. Source clocks
are UTC bar open b, available at b+1min; prefixes persist before next reveal.

Ambiguity is B, diag(B), half-cross PSD interpolation, opposite-sign DBD and
frozen June2025 B with its own L. There are no new fitted kernel families.
E1 remains separate180d ending30d before month, tau5/30,ridge1; E2 diagonal E1;
all eight original E3 stresses retained, E0 excluded. Future as-of B fits use
365 complete preceding days, same tau60/ridge1. Already inspected Jan–Jun2026
is disclosed past calibration history only. No hyperparameter retuning after freeze.

## Conditional optimization and numerical checks

For scenario g, remaining transient cost is .5zf'Hff_g zf+zf'Hfp_g zp.
Past-only .5zp'Hpp_g zp is excluded from max ordering. Original reference-USDT
normalization10^-4 and each scenario's sqrt(L) factors appear once. Risk uses
Xremaining=X0−sum(zp), unchanged beta/Sigma. G/GL epigraphs are convex because
Hff_g is PSD; negative admissible cross terms are permitted. No material PSD
projection, cap relaxation, clipping or inventory repair. Never sum local QPs.

12 joint paired-asset historical hours come from preceding28 complete days at
matching hour. Deterministic SHA256 date/seed rank selects12; min support12,
otherwise HOLD. Each minute is scaled by its positive past matching-hour median
and current known V1. Zero historical capacity stays zero. Marginal S1 bands
are not substituted for a joint law. Scenario timestamps/support and posthoc
10/50/90 coverage diagnostics are retained. The bank approximates dependence;
it does not claim calibrated joint path coverage or firm liquidity.

For future z, e_s=sum(max(z−.1V_s,0))/ORIGINAL W. Preference is
(W/10000)*lambda*CVaR90(e), with equal scenario weights. e=.05,lambda100 means
5bp of preference, not paid cost. A nonnegative VaR bound is redundant because
e_s>=0; it improves numerical conditioning. Conic retries tighten tolerances
rather than changing acceptance gates. All attempts/status/KKT/duals/epigraph
checks are retained. Exact elementwise Hessian dominance proves redundant max
constraints on the nonnegative-sale cone; certified singleton QPs use the verified
X1 solver, while genuine QCQPs use CLARABEL. All declared scenarios/costs remain
in audits; no unfavorable ambiguity point is dropped for economic reasons.

Actual active-scenario shares for this {phase} sample:

{table(activity)}

Predicted remaining CVaR uses original W at every replan; these averages are
optimization diagnostics, not paid cash or joint calibration tests. All scenario
dual weights and full physical remaining costs stay in immutable episode records.

## Development selection fixed before holdout

Arrival-horizon marginal scenario diagnostics (not joint-path calibration):
joint12-path empirical quantiles versus the unchanged training-calibrated X1
S1 bands. These are diagnostics only; no scenario weighting or penalty is tuned
from this table. Buckets0/1/2 mean1–5/6–15/16–60min; pinball units USDT/min.

{table(coverage,['model','asset','bucket','quantile','coverage','pinball_usdt','n'])}

Selected lambda: **{sel['selected_lambda']}**; selected candidate: **{sel['selected_candidate']}**.
L25/L100 were compared on all736 fixed development episodes, selecting the
smallest nonzero lambda achieving>=10% mean overload reduction and E1 mean
shortfall increase<=.10bp. No GL-specific tuning; no penalty/family expansion.
If neither qualifies, candidate N continues and lambda25 L/GL/GL-D remain fixed
negative ablations. All tested variants, hashes and freeze time remain saved.

{table(pd.DataFrame(sel['tested']))}

Original X1 background/context values below are retained read-only, not rescored
or reinterpreted as X2/X3 confirmation. They use the same development episodes
and E1/E2 definitions and do not enter the six-policy regret reference.

{table(context,['world','policy','episodes','mean_bps','median_bps']) if phase=='development' else 'Original X1 background remains in the separate development report.'}

## Observed overload and liquidity incidents

O=sum_all(max(z−.1Vreal,0))/W, including zero-volume minutes. It is an overload
diagnostic, not unfilled volume or a fill model. Ratios at zero volume are
undefined; positive sales there are explicitly infeasible. Percentages below
use positive-volume asset-minute denominators; maxima and zero counts are retained.

{table(o)}

Paired overload differences positive favor new; units are fractions of original
parent notional (multiply100 for percentage points). Relative reductions and
95% intervals use shared seven-day calendar blocks,500draws,seed20261027.

{table(lo,['control','new','episodes','mean_control','mean_new','mean','ci_low','ci_high','relative_reduction','relative_ci_low','relative_ci_high','relative_ratio_status'])}

![Paired tradeoff](../../figures/extension_x2x3/{phase}_tradeoff.png)

## Common independent-world modeled shortfall, funding excluded

Every policy is scored once over its complete schedule under common V0 temporary
volume, next-close path, exact-cell evaluator impact and assumed linear fees/spread.
Risk and CVaR preferences stay separate from cash. Positive delta is
cost(control)−cost(new), bp of original total W. Full/month/weekend/past-liquidity
regime cuts retain all adverse cases. Regime thresholds are fixed from development
past-information turnover, not holdout realized liquidity. These are short,
time-dependent observational/scenario comparisons, not causal intervention evidence.

{table(policy[policy.world.isin(['E1','E2'])])}

{table(primary,['control','new','episodes','mean','ci_low','ci_high','negative_share','p95_disadvantage_bps','worst_bps'])}

TWAP context: mean overload={100*ot.mean_overload:.4f}% and E1 mean
shortfall={nt.mean_shortfall_bps:.5f}bp. Its overload is
{'lower' if ot.mean_overload<ol.mean_overload else 'higher'} than L's.
This descriptive baseline is retained; liquidity protection is not uniformly
best across the original strategies.

H-L: read N→L overload/cost jointly. H-G: N→G plus all independent-world tails.
H-GL: L→GL; H-cross: GL-D→GL holds each scenario self/tau/L and all other
inputs fixed. A low robust objective alone is not evidence of better performance.
The point practical-interest hurdle is>=10% relative overload reduction with
<=.10bp E1 mean cost increase; reported intervals preserve uncertainty and are
not independent evidence across correlated evaluator worlds.

The selected N→L contrast by calendar month, weekday/weekend and frozen past
liquidity tercile is below. Overload quantities are fractions of W; E1 advantage
is cost(N)−cost(L), bp, funding excluded. All other fixed-policy grouped
contrasts remain in the corresponding pairwise CSV files. Empty regimes have
no observations and are not pooled with another regime.

{table(group_table)}

Measured H-L: overload reduction **{100*ll['mean']:.4f} percentage points**,
95% interval[{100*ll.ci_low:.4f},{100*ll.ci_high:.4f}]; relative point reduction
{100*ll.relative_reduction:.2f}%. E1 cost increase (new minus N)
**{-lc['mean']:.5f}bp**, interval[{-lc.ci_high:.5f},{-lc.ci_low:.5f}].
The practical hurdle is a point criterion; uncertainty can still permit a cost
increase exceeding0.10bp. L's maximum finite participation is
{ol.maximum_finite_ratio:.2f}× versus N's {on.maximum_finite_ratio:.2f}×;
L retains {int(ol.positive_sales_zero_cells)} positive-sale/zero-volume cells.
Lower average overload therefore does not establish feasible realized fills or
a universally improved participation tail.

H-GL incremental mean overload reduction={100*gll['mean']:.5f}percentage points,
interval[{100*gll.ci_low:.5f},{100*gll.ci_high:.5f}]; E1 cost advantage
{glc['mean']:+.5f}bp[{glc.ci_low:+.5f},{glc.ci_high:+.5f}]. H-cross analogous
overload reduction={100*crossl['mean']:.5f}points, E1 cost advantage
{crossc['mean']:+.5f}bp[{crossc.ci_low:+.5f},{crossc.ci_high:+.5f}].
H-G mean overload reduction={100*gl['mean']:.5f}percentage points,
interval[{100*gl.ci_low:.5f},{100*gl.ci_high:.5f}]; E1 cost advantage
{gn['mean']:+.5f}bp[{gn.ci_low:+.5f},{gn.ci_high:+.5f}].
All independent-world H-G tail/regret outcomes below remain primary evidence;
dominance of one ambiguity point is explicitly not proof that uncertainty
optimization adds an adaptive kernel-selection benefit.

{table(tail)}

All ten evaluation worlds (including adverse E2/opposite/amplitude/decay/kappa)
and ex-post regret/loss shares are in {phase}_independent_scenario_stress.csv.
The ex-post best among six fixed policies is a descriptive reference, never a
policy available to the trader. Largest finite participation and zero-volume
failures are retained; no hypothetical order is asserted to be executable.

![Every independent world](../../figures/extension_x2x3/{phase}_worlds.png)

![Participation tails and zeros](../../figures/extension_x2x3/{phase}_participation.png)

## Development context figures and interpretation

[Cash-consistent ambiguity curves](../../figures/extension_x2x3/kernel_ambiguity.png),
[active worst-case scenarios](../../figures/extension_x2x3/active_scenarios.png),
[joint paths and posthoc overlay](../../figures/extension_x2x3/joint_paths.png), and
[committed MPC paths with carried state](../../figures/extension_x2x3/committed_paths.png)
are explicitly development illustrations. Frozen June2025 B is active in every
development G/GL/GL-D replan: that ambiguity family collapses to a stronger
fixed kernel on the nonnegative-sale feasible cone. No adaptive kernel-selection
benefit is established, and no replacement family was searched. The joint12-path
arrival bands have development 10% coverage about16–20% and 90% coverage about84–85%;
they are narrower than the frozen S1 marginal bands. This imperfect marginal
calibration is disclosed, not tuned away, and says nothing about joint-path
coverage guarantees.

## Implementation, preservation and limits

{table(q)}

Final pretest suite: {test.get('passed','not yet run')} passed,
{test.get('failures','not yet run')} failures; integration tests opening original
2026 source pilots excluded. Focused coverage: singleton/zero-lambda X1 parity,
three actual2025 P2 schedule/cost reproductions, cash/state/gradient/PSD checks,
independent SCS small conic/QP and enumerated two-kernel QCQP, CVaR hand cases, no-reset negative control, all12
replan future-field mutations, permutation, adapter/UTC/QC parity and guarded
ready/receipt access. Detailed JUnit/source hashes and independent complete-cost
output audits are in extension_x2x3_artifacts. All scientific artifacts among {protected['files']} protected prior paths and
{protected['data_files']} data stat snapshots are unchanged. macOS independently
changed Finder metadata reports/.DS_Store; its original hash and explicit
metadata-only exception remain recorded. Research files have no exemption.

Genuine OOS requires evidence-linked PRETEST_READY_X2X3 before six official
monthly archives can be acquired or parsed. Source QC is distinguished from
first policy outcome reveal. The ready lock binds code/config/spec/selection/
tests/source identities; a manual marker cannot unlock data. New source hashes,
CRC/schema/coverage and first-access receipts are retained if acquisition runs.
No holdout tuning, resampling of dates, alternate-source substitution or old
January–June test rebranding is allowed. Current OOS gate: **{gate['status']}**;
reason: {gate.get('reason','Required gates passed and registered run completed')}.

Binance Vision data attribution and recorded CC BY-NC-SA noncommercial terms
apply to derived summaries; raw archives are not redistributed. Current
[provider terms](https://github.com/binance/binance-public-data/blob/master/TERMS_AND_CONDITIONS.md)
were checked before new acquisition. [Neuman–Stockinger–Zhang](https://arxiv.org/abs/2309.02994)
motivates accounting for estimation uncertainty; no guarantee from that paper
is claimed for our finite-scenario construction. The referenced SSRN page
returned403, so its theorem/content was not independently verified. The local
AJNT benchmark remains a deterministic reference, distinct from this constrained
finite-scenario MPC. Full random stochastic Volterra control is not implemented.

Remaining limits: public-flow endogeneity, assumed intervention kernels, uncertain
joint volume law, three-month OOS power, unrealized fills, proxies for fees/spread,
funding omission and extreme actual liquidity/source anomalies. Negative, null,
dominated-ambiguity and infeasible-realized-liquidity findings are valid outcomes.

```sh
.venv/bin/python scripts/extension_x2x3.py development
.venv/bin/python scripts/audit_extension_x2x3.py
.venv/bin/python scripts/extension_x2x3.py freeze
.venv/bin/python scripts/extension_x2x3.py holdout
.venv/bin/python scripts/extension_x2x3.py report
```

Only freeze/holdout after all checks pass; holdout refuses a missing/invalid lock.
No commit/push or original-result rewrite. Future Option2 requires separate
theorem-level specification and authorization.
'''
        (root/f'reports/research/extension_x2x3_{phase}.md').write_text(text)
    if not held:
        (root/'reports/research/extension_x2x3_holdout.md').write_text('# X2+X3 new OOS — '+gate['status']+'\n\n'+gate.get('reason','Required pretest gates not yet reached.')+'\n\nJuly–September source values opened: '+str((out/'first_source_value_open.json').exists())+'. No confirmatory outcomes manufactured; development report remains complete.\n')
    retained=sum(p.stat().st_size for base in [out,bulk,root/'figures/extension_x2x3',root/'src/cryptocrossimpact/robust',root/'data/raw/extension_x2x3'] for p in base.rglob('*') if p.is_file())
    retained+=sum(p.stat().st_size for p in (root/'data/canonical').glob('*/2026-0[789].parquet'))
    manifest=dict(utc=utcnow(),code=binding(root),config=config(root),selection=sel,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
        git_status=subprocess.check_output(['git','status','--short'],cwd=root,text=True),python=platform.python_version(),
        packages={p:importlib.metadata.version(p) for p in ['numpy','scipy','pandas','cvxpy','clarabel','osqp','pyarrow','matplotlib']},
        config_sha256=sha256(root/'configs/extension_x2x3.yaml'),source_manifest_sha256=sha256(root/'data/registry/source_manifest.json'),
        original_spec_sha256=sha256(root/'CryptoCrossImpact_Research_Specification_v1_2026-10-27.md'),protocol_sha256=sha256(root/'docs/extensions/x2x3_robust_liquidity_protocol_v1.md'),
        seed=20261027,clock='UTC integer ms bar_open; available_at=open+1minute',funding_included=False,
        retained_bytes=retained,conservative_peak_additional_bytes=2*retained,preservation=protected,holdout_status=gate['status'],new_holdout_values_opened=(out/'first_source_value_open.json').exists())
    for name in ['new_source_manifest.json','new_source_qc.json','PRETEST_READY_X2X3.json','pretest_lock.json','first_source_value_open.json','development_output_audit.json','holdout_output_audit.json']:
        if (out/name).exists():manifest[name+'_sha256']=sha256(out/name)
    manifest['resources']={}
    for name in ['run_selection.json','run_combined.json','holdout_gate_audit.json']:
        if (out/name).exists():
            r=json.loads((out/name).read_text());manifest['resources'][name]=dict(sha256=sha256(out/name),**{k:r[k] for k in ['seconds','peak_rss_mib','complete','status'] if k in r})
    save(out/'run_manifest.json',manifest)
    print(dict(development='PASS',pretest='READY' if (out/'PRETEST_READY_X2X3.json').exists() else 'NOT_REACHED',new_OOS=gate['status'],retained_MiB=retained/1024**2),flush=True)
