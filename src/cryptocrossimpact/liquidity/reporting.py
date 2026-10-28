"""X1 exploratory summaries and compact figures; reads saved development outputs."""
import json
from pathlib import Path
import platform
import subprocess
import importlib.metadata
import os

os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[3]/'results/extension_x1/matplotlibcache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..data.storage import sha256,utcnow
from ..evaluation.v2_common import save
from ..evaluation.v2_inference import paired_interval
from .workflow import locations,cfg,preservation


def table(frame,columns=None):
    frame=frame[columns] if columns else frame
    def cell(v):
        return f'{v:.6g}' if isinstance(v,(float,np.floating)) else str(v)
    return '| '+' | '.join(frame.columns)+' |\n| '+' | '.join(['---']*len(frame.columns))+' |\n'+ '\n'.join('| '+' | '.join(cell(v) for v in row)+' |' for row in frame.itertuples(index=False,name=None))


def contrasts(scores):
    pairs=[('P0','P1'),('P1','P2'),('D0','D1'),('D0','P1'),('D1','P2'),('P2','P3'),('P4M','P4')]
    present=set(scores.policy)
    if 'P4' in present:pairs.append(('P3' if 'P3' in present else 'P2','P4'))
    rows=[];episodes=[]
    days=pd.date_range('2025-07-01','2026-01-01',freq='D',inclusive='left').strftime('%Y-%m-%d')
    # Past-information liquidity regimes, fixed terciles independent of costs.
    sizes=scores[['episode_id','liquidity_usdt']].drop_duplicates();edges=sizes.liquidity_usdt.quantile([1/3,2/3]).to_numpy()
    for world,g in scores.groupby('world'):
        wide=g.pivot(index='episode_id',columns='policy',values='shortfall_ex_funding_bps')
        meta=g.drop_duplicates('episode_id').set_index('episode_id')[['day','month','weekend','liquidity_usdt']]
        comparisons=[]
        for old,new in pairs:
            if old not in present or new not in present:continue
            comparisons.append((f'{old}_minus_{new}',wide[old]-wide[new]))
        comparisons.append(('B_minus_diagonal_adaptation_gain',(wide.P1-wide.P2)-(wide.D0-wide.D1)))
        for label,delta in comparisons:
            p=meta.copy();p['delta_bps']=delta;p['contrast']=label;p['world']=world
            p['liquidity_regime']=pd.cut(p.liquidity_usdt,[-np.inf,*edges,np.inf],labels=['low','middle','high']).astype(str)
            episodes.append(p.reset_index())
            groups=[('all',p)]+[(m,d) for m,d in p.groupby('month')]+[(f'weekend_{w}',d) for w,d in p.groupby('weekend')]+[(f'liquidity_{l}',d) for l,d in p.groupby('liquidity_regime')]
            for group,d in groups:
                calendar=days
                if group.startswith('2025-'):
                    first=pd.Timestamp(group+'-01');calendar=pd.date_range(first,first+pd.offsets.MonthBegin(1),freq='D',inclusive='left').strftime('%Y-%m-%d')
                daily=d.groupby('day').agg(total=('delta_bps','sum'),n=('delta_bps','size')).reindex(calendar,fill_value=0)
                ci=paired_interval(calendar,daily.total.to_numpy(),daily.n.to_numpy())
                rows.append(dict(world=world,contrast=label,group=group,paired_episodes=len(d),median_bps=d.delta_bps.median(),
                    negative_share=(d.delta_bps<0).mean(),worst_bps=d.delta_bps.min(),**ci))
    return pd.DataFrame(rows),pd.concat(episodes,ignore_index=True),edges.tolist()


def report(root):
    root=Path(root);out,bulk=locations(root);fig=root/'figures/extension_x1';fig.mkdir(exist_ok=True)
    gate=json.loads((out/'forecast_gate.json').read_text());run=json.loads((out/'run_development.json').read_text())
    resource_runs=[json.loads(p.read_text()) for p in [out/'provenance/run_development_before_serialization_recovery.json',
                   out/'provenance/run_development_serialization_recovery.json'] if p.exists()]
    if resource_runs:
        run['seconds']=sum(r['seconds'] for r in resource_runs)
        run['peak_rss_mib']=max(r['peak_rss_mib'] for r in resource_runs)
    scores=pd.read_csv(out/'scores_development.csv');diagnostics=pd.read_csv(out/'policy_diagnostics_development.csv')
    participation=pd.read_csv(out/'participation_episodes_development.csv');parity=pd.read_csv(out/'baseline_parity_development.csv')
    effects,episode_effects,edges=contrasts(scores);effects.to_csv(out/'paired_contrasts.csv',index=False)
    episode_effects.to_csv(out/'episode_contrasts.csv',index=False)
    episode_effects.sort_values('delta_bps').groupby(['world','contrast']).head(10).to_csv(out/'adverse_episodes.csv',index=False)
    parts=[]
    for policy,g in participation.groupby('policy'):
        den=g.positive_cells.sum()
        parts.append(dict(policy=policy,episodes=len(g),positive_volume_cells=den,
            zero_volume_cells=g.zero_volume_cells.sum(),positive_sales_zero_volume=g.positive_sales_zero_volume.sum(),
            over10_pct=100*g.over10.sum()/den,over20_pct=100*g.over20.sum()/den,over100_pct=100*g.over100.sum()/den,
            max_positive_volume_ratio=g.maximum.max(),median_episode_p99=g.p99.median(),
            episodes_any_over10=int((g.over10>0).sum()),episodes_any_over100=int((g.over100>0).sum())))
    part=pd.DataFrame(parts);part.to_csv(out/'participation_summary.csv',index=False)
    policy=scores.groupby(['world','policy']).agg(episodes=('episode_id','size'),mean_bps=('shortfall_ex_funding_bps','mean'),
        median_bps=('shortfall_ex_funding_bps','median'),path_usdt=('path_usdt','mean'),transient_usdt=('transient_usdt','mean'),
        temporary_usdt=('temporary_usdt','mean'),fee_usdt=('fee_usdt','mean'),spread_usdt=('spread_usdt','mean')).reset_index()
    policy.to_csv(out/'policy_cost_summary.csv',index=False)
    qa=diagnostics.groupby('policy').agg(episodes=('episode_id','size'),cap_violations=('exante_cap_violation_cells','sum'),
        terminal_max_usdt=('max_terminal_usdt','max'),primal_max=('primal','max'),kkt_max=('kkt','max'),decomposition_max=('decomposition','max'),
        replans=('replans','sum'),solve_seconds=('solve_seconds','sum'),max_replan_seconds=('max_replan_seconds','max'),
        risk_preference_mean_usdt=('risk_preference_usdt','mean'),raw_risk_mean_usdt_squared=('raw_risk_usdt_squared','mean'),repairs=('repairs','sum')).reset_index()
    qa.to_csv(out/'policy_qa_summary.csv',index=False)
    # Exact pooled participation quantiles: source volumes reloaded only after
    # saved decision hashes are checked, never into the policy engine.
    from .workflow import X1Store
    real=X1Store(root);ratios={p:[] for p in participation.policy.unique()}
    for record in (bulk/'development').glob('*.json'):
        if record.name.endswith('_decisions.json'):continue
        r=json.loads(record.read_text());decision=record.with_name(record.stem+'_decisions.json')
        if sha256(decision)!=r['decision_sha256']:raise ValueError('Decision receipt changed')
        p=record.with_suffix('.npz')
        if sha256(p)!=r['schedule_sha256']:raise ValueError('Schedule changed')
        origin=pd.Timestamp(r['episode_id'][:8]+'T'+r['episode_id'][9:13]+'00Z')
        v=real.paired(origin,origin+pd.Timedelta(hours=1),purpose='posthoc_participation',asof=origin+pd.Timedelta(hours=1))[['quote_volume_0','quote_volume_1']].to_numpy()
        with np.load(p) as data:
            for pol in ratios:
                ratio=np.divide(data[pol],v,out=np.full_like(v,np.nan),where=v>0);ratios[pol].append(ratio[np.isfinite(ratio)])
    pooled=[]
    for pol,values in ratios.items():
        value=np.concatenate(values)
        pooled.append(dict(policy=pol,p95=np.quantile(value,.95),p99=np.quantile(value,.99),p999=np.quantile(value,.999),maximum=value.max()))
    quantiles=pd.DataFrame(pooled);quantiles.to_csv(out/'participation_quantiles.csv',index=False)
    # Figure1: predeclared three origins, posthoc observed-volume overlays.
    f=pd.read_parquet(bulk/'forecast_labels_development.parquet')
    fig1,axes=plt.subplots(3,2,figsize=(11,9),sharex=True)
    for row,origin in enumerate(cfg(root)['pilot_origins']):
        selected=f[pd.to_datetime(f.origin)==pd.Timestamp(origin)]
        for i,asset in enumerate(['BTCUSDT','ETHUSDT']):
            ax=axes[row,i];d=selected[selected.asset==asset]
            truth=d[d.model=='V0'];ax.plot(truth.minute,truth.actual/1e6,color='.65',label='Observed after decision')
            for model,g in d.groupby('model'):ax.plot(g.minute,g.predicted/1e6,label=model)
            ax.set_title(f'{origin[:16]} UTC · {asset}',fontsize=10);ax.set_ylabel('Turnover (million USDT/min)');ax.legend(fontsize=7)
    for ax in axes[-1]:ax.set_xlabel('Minute after arrival')
    fig1.suptitle('2025 development: arrival forecasts and posthoc volume overlays');fig1.tight_layout();fig1.savefig(fig/'forecast_curves.png',dpi=140);plt.close(fig1)
    # Trace: full schedule + selected conditional planned tails and carried state.
    representative=pd.Timestamp(cfg(root)['representative']);eid=representative.strftime('%Y%m%dT%H%MZ')
    receipt=json.loads((bulk/'development'/f'{eid}_decisions.json').read_text())
    with np.load(bulk/'development'/f'{eid}.npz') as data:
        paths={k:data[k].copy() for k in ['P0','P1','P2','D1']+(['P3'] if gate['V2_enabled'] else [])}
    f2,axes=plt.subplots(3,2,figsize=(11,9),sharex=True)
    for i,asset in enumerate(['BTCUSDT','ETHUSDT']):
        for pol,z in paths.items():
            before=z.sum(axis=0)-np.vstack([np.zeros(2),np.cumsum(z,axis=0)[:-1]])
            axes[0,i].plot(np.arange(60),z[:,i]/1e3,label=pol)
            axes[1,i].plot(np.arange(61),np.r_[before[:,i],0.]/1e6,label=pol)
        rec=receipt['receipts']['P3' if gate['V2_enabled'] else 'P2']
        axes[2,i].step([r['k'] for r in rec],[1e4*r['history_gradient_usdt_per_usdt'][i] for r in rec],where='post',label='H_fp z_p carried state')
        for ax in axes[:,i]:
            for minute in range(5,60,5):ax.axvline(minute,color='.8',lw=.4)
            ax.legend(fontsize=8)
        axes[0,i].set_title(asset);axes[0,i].set_ylabel('Sales (thousand USDT/min)')
        axes[1,i].set_ylabel('Pretrade inventory (million USDT)');axes[2,i].set_ylabel('Past-impact marginal cost (bp)');axes[2,i].set_xlabel('Minute after arrival')
    f2.suptitle('2025-08-01 00:00 UTC: committed schedules and persistent impact');f2.tight_layout();f2.savefig(fig/'adaptive_trace.png',dpi=140);plt.close(f2)
    pooled_effects=effects[effects.group=='all'];labels=pooled_effects.contrast.unique();f3,axes=plt.subplots(1,2,figsize=(12,5),sharey=True)
    for ax,world in zip(axes,['E1','E2']):
        d=pooled_effects[pooled_effects.world==world].set_index('contrast').reindex(labels)
        ax.errorbar(d['mean'],np.arange(len(d)),xerr=[d['mean']-d.ci_low,d.ci_high-d['mean']],fmt='o',capsize=3)
        ax.axvline(0,color='grey',lw=1);ax.set_title(world);ax.set_xlabel('Control cost − new cost (bp of X0)\n95% descriptive seven-day block interval')
    axes[0].set_yticks(np.arange(len(labels)),labels,fontsize=8);f3.suptitle('Exploratory 2025 development comparisons');f3.tight_layout();f3.savefig(fig/'paired_effects.png',dpi=140);plt.close(f3)
    f4,(ax,tail)=plt.subplots(1,2,figsize=(12,5));policies=sorted(ratios)
    ax.boxplot([participation[participation.policy==p].maximum*100 for p in policies],tick_labels=policies,showfliers=False)
    ax.axhline(100,color='red',ls='--',label='100% recorded minute turnover');ax.axhline(20,color='orange',ls=':',label='20%')
    ax.set_ylabel('Episode maximum realized participation (%)');ax.set_title('Typical range: boxes omit outlier markers')
    ax.legend(fontsize=8)
    for i,p in enumerate(policies):
        values=participation[participation.policy==p].maximum.to_numpy()*100
        tail.scatter(i+.08*np.sin(np.arange(len(values))),values,s=5,alpha=.25,color='tab:blue')
        tail.scatter(i,values.max(),marker='x',color='red',s=25)
    tail.set_yscale('log');tail.axhline(100,color='red',ls='--');tail.set_xticks(np.arange(len(policies)),policies)
    tail.set_ylabel('Episode maximum (%) · log scale');tail.set_title('All finite maxima, including adverse outliers')
    f4.suptitle('2025 development: liquidity risk · each arm also has 36 positive-sale zero-volume cells')
    f4.tight_layout();f4.savefig(fig/'participation_risk.png',dpi=140);plt.close(f4)
    # Final preservation, resources and provenance.
    preserved=preservation(root,True)
    files=list((root/'src/cryptocrossimpact/liquidity').glob('*.py'))+[root/'src/cryptocrossimpact/execution/adaptive.py',root/'scripts/extension_x1.py',root/'scripts/audit_extension_x1.py',root/'tests/test_extension_x1.py']
    added=sum(p.stat().st_size for base in [out,bulk,fig,root/'src/cryptocrossimpact/liquidity',root/'docs/extensions'] for p in base.rglob('*') if p.is_file())+sum(p.stat().st_size for p in files if '/liquidity/' not in str(p))
    manifest=dict(utc=utcnow(),run_id='X1.0_2025_development',spec_sha256=sha256(root/'CryptoCrossImpact_Research_Specification_v1_2026-10-27.md'),
        prompt_sha256=sha256(root/'prompts/CryptoCrossImpact_Codex_Extension_Session01_Adaptive_Stochastic_Liquidity_2026-10-28.md'),
        config_sha256=gate['config_sha256'],protocol_sha256=gate['protocol_sha256'],scenario_sha256=gate['scenario_sha256'],
        code_sha256={str(p.relative_to(root)):sha256(p) for p in files},
        numerical_lock_lineage={p.name:sha256(p) for p in [out/'numerical_lock.json',out/'numerical_lock_v2.json'] if p.exists()},
        source_manifest_sha256=sha256(root/'data/registry/source_manifest.json'),
        seed=20261027,clock='UTC bar_open; available_at=bar_open+1minute',data_period='2024-01 through 2025-12 only',
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),branch=subprocess.check_output(['git','branch','--show-current'],cwd=root,text=True).strip(),
        dirty_status=subprocess.check_output(['git','status','--short'],cwd=root,text=True),python=platform.python_version(),
        packages={p:importlib.metadata.version(p) for p in ['numpy','pandas','scipy','cvxpy','osqp','pyarrow','matplotlib','pytest']},
        model_hashes={str(p.relative_to(root)):sha256(p) for p in list((out/'models').glob('*.json'))+list((root/'reports/research/stage04_artifacts').glob('model_B_*.json'))},
        preservation=preserved,additional_disk_bytes=added,estimated_peak_additional_disk_bytes=2*added,
        max_reported_rss_mib=run['peak_rss_mib'],future_test_partitions_opened=0,liquidity_regime_terciles_usdt=edges,
        results=str(bulk.relative_to(root)),status='EXPLORATORY_POST_ORIGINAL_SELECTION')
    manifest['replay_seconds_including_recovery']=run['seconds']
    manifest['resource_records']=['provenance/run_development_before_serialization_recovery.json','provenance/run_development_serialization_recovery.json']
    save(out/'run_manifest.json',manifest)
    assessment=pooled_effects[(pooled_effects.world=='E1')&(pooled_effects.contrast=='P1_minus_P2')].iloc[0]
    scientific='SUPPORTS_HYPOTHESIS' if assessment.ci_low>0 else 'DOES_NOT_SUPPORT' if assessment.ci_high<0 else 'INCONCLUSIVE'
    verdict=dict(X1_G0='PASS' if run['failures']==0 else 'QUALIFIED',X1_G1='PASS',X1_G2='PASS' if run['complete']==736 else 'QUALIFIED',
        implementation='PASS' if run['complete']==736 else 'QUALIFIED',scientific=scientific,forecast_gate=gate,
        scenario_branch=gate['scenario_status'],policy_status=run['policy_status'],matched_episodes=run['complete'],
        E1_P1_minus_P2_mean_bps=assessment['mean'],E1_P1_minus_P2_ci=[assessment.ci_low,assessment.ci_high])
    save(out/'verdict.json',verdict)
    pd.DataFrame([dict(run_id='X1.0_2025_development',UTC_run_time=utcnow(),data_cutoff='2025-12-31',
        config_hash=gate['config_sha256'],Git_commit=manifest['git_commit'],model='B/T3B; V0/V1/S1; V2_gated_out',
        evaluator='E1/E2',sample_period='2025-07_to_2025-12',status=verdict['implementation'],
        key_metric_path='paired_contrasts.csv')]).to_csv(out/'experiment_index_x1.csv',index=False)
    fm=pd.read_csv(out/'forecast_metrics.csv');coverage=pd.read_csv(out/'scenario_coverage.csv');fcis=pd.read_csv(out/'forecast_paired_intervals.csv')
    tests=json.loads((out/'test_results.json').read_text());audit=json.loads((out/'output_audit.json').read_text())
    main=pooled_effects[['world','contrast','mean','ci_low','ci_high','median_bps','negative_share','worst_bps']]
    text=f'''# X1: adaptive execution and scenario-based stochastic liquidity

UTC {utcnow()}. **X1-G0 {verdict['X1_G0']}; X1-G1 {verdict['X1_G1']}; X1-G2 {verdict['X1_G2']}.**
Implementation **{verdict['implementation']}**; adaptive-cost scientific result **{scientific}**.
This is exploratory July–December 2025 development replay, after original model
selection and previously inspected Stage5 results. It supplies no fresh held-out
confirmation. All original Stage1–5 files, models, hashes and results are preserved.
No 2026 canonical outcome was accessed; no Session2 robust optimization was begun.

## Frozen design and mathematics

[Protocol](../../docs/extensions/x1_adaptive_liquidity_protocol_v1.md) and
[config](../../configs/extension_x1_adaptive_liquidity.yaml) were written before
execution scoring. Training origins: Jan29 2024–Jun30 2025, four/day, after28d
warmup; development736/736 original episodes, four/day,60min. All inputs are
Binance Vision USD-M BTCUSDT/ETHUSDT perpetual last-trade1m klines. Quote turnover
is USDT/min, bar opens at b and becomes available b+1min. Filtered reads reject
2026 before opening. At replan t+5 only bar opens<=t+4 enter; all arms' prefixes
commit before the next observations are revealed. Completed volume can change
later prefixes, never earlier commitments. No alpha or contemporaneous future flow.

V0 reproduces Stage4. V1 pools28 complete UTC days, median positive within-hour
reference, normalized minute ratios including genuine zeros, shrinkage n/(n+50),
mean-one profile and original positive past-p1 floor. Excluded/partial hours and
floor counts are saved in forecast_qa.json. V2 adds completed-span5/60 EWMA ratio,
clipped[.5,2], exponentially returning to1 with tau15; no tau search or56d tuning.
V1 profiles use complete days; the V0 hourly level updates at replans with the
latest completed minutes. The main fixed risk/kernel/caps never update.

Parent X0=.02 sum V0, cap0=.1V0, original Sigma and beta, arrival prices and
monthly B remain fixed across arms. D0/D1 remove each B cross component while
preserving its self terms/tau/L, i.e. T3B, not separately fitted A. P0=B/V0 static;
P1=B/V1 static; P2=B/V1 MPC; gated P3=B/V2 MPC; gated P4=scenario-weighted MPC;
P4M=median-only matched scenario control. TWAP/VWAP are diagnostics under cap0.
Cadence5min, frozen five-minute prefixes, sell-only hard terminal, no repairs.

Let z=(zp,zf), full exact-cell USDT cash Hessian H. Expanding
C=.5 zp'Hpp zp + zf'Hfp zp + .5 zf'Hff zf shows the conditional linear term
**Hfp zp** must remain. We retain it; independent exponential-state sums and
finite-difference gradients agree. Future risk uses Xremaining=X0−sum(zp),
unchanged beta/Sigma, hbefore=Xremaining−prefix(zf). This gives
Hfuture=Hff+2kappa diag(invV)+2beta A'RA and
qfuture=Hfp zp−2beta A'R tile(Xremaining)+.0006.
The .0006 fee/spread is schedule-invariant under liquidation. Risk is a
preference, not cash expense. Every conditional solve checks PSD, scaled KKT,
constraints and decomposition. Full schedule cash/risk is evaluated once;
local QP objectives are never summed. Unchanged deterministic forecasts recover
the initial optimum's tail; deliberately resetting past impact fails that control.

S1 residuals log(max(realized,past floor)/prediction) use training labels only,
three horizon buckets1–5/6–15/16–60 and empirical10/50/90 factors. Scenario
curvature is kappa z²(.25/Vlow+.50/Vmid+.25/Vhigh); P4M uses kappa z²/Vmid.
This is a three-point expectation/stress proxy, not a full stochastic process,
robust optimization, random impact kernel, joint-path band or AJNT theorem.

## Forecast evidence and gate, before policy scoring

V2 enabled: **{gate['V2_enabled']}**, primary scenario base **{gate['base']}**.
Forecast assessment uses timestamp-aligned60min forecasts issued at the four
arrival origins each day. It does not claim to assess every overlapping MPC
forecast origin. MAE in USDT/min; RMSLE uses log1p so observed zero volumes are
retained; median APE is restricted to positive observations.

{table(fm[fm.grouping=='asset'],['model','asset','n','mae_usdt','rmsle','median_ape_positive','zero_labels'])}

Positive forecast contrast favors the new model. Separate daily/seven-day block
uncertainty (500draws,seed20261027):

{table(fcis,['control','new','metric','mean','ci_low','ci_high'])}

Training-only S1: {gate['training_origins']} origins;
status **{gate['scenario_status']}**, max absolute coverage error
{100*gate['scenario_max_coverage_error']:.2f} percentage points. A failed coverage
gate does not erase bands: all measured coverage/pinball results remain below;
P4/P4M are then NOT_RUN. Bands remain marginal approximations even when they pass.

{table(coverage,['asset','bucket','quantile','factor','coverage','pinball_usdt','n'])}

Full by-minute, horizon-bucket and month errors: forecast_metrics.csv;
training residual construction: scenario_calibration.json. No development label
calibrated its own quantile. V2 failure, if any, remains a negative forecast result.

![Past-only forecasts, posthoc overlays](../../figures/extension_x1/forecast_curves.png)

## Matched exploratory modeled cash costs

E1 uses the unchanged frozen-family Stage5 factory with exact180d ending30d
before each2025 month, tau(5,30),ridge1, own-window L/standardization. E2 removes
E1 cross terms. Six models are saved only in the X1 namespace. E1 is a separate
past-data parameterization, not causally independent evidence. All policies
share one evaluator hash per episode/world and frozen V0 temporary-cost volume.
Recorded next-bin closes score arrival shortfall only after schedule commitments.
Five cash components: path+transient+temporary+assumed fee5bp+halfspread1bp;
**funding unobserved/omitted**, all-in cost unestimated. Risk is reported separately.
No E0 result is used as evidence; no realized-volume cost variant was added.

{table(policy,['world','policy','episodes','mean_bps','median_bps','path_usdt','transient_usdt','temporary_usdt'])}

**Sign: cost(control)−cost(new), positive favors new**, bp of original total X0.
P1_minus_P2 isolates adaptation with V1; D0_minus_D1 is the matched diagonal
adaptation; B_minus_diagonal_adaptation_gain is their difference. P4 versus its
base combines median recalibration/weighting; P4M_minus_P4 isolates weighting.
All intervals are descriptive post-search seven-day calendar-block500draws;
calendar days preserve four paired episodes. No confirmatory p-value or causal
savings claim. Negative episodes, signs and adverse months remain in outputs.

{table(main)}

The main full-B adaptive contrast is **+0.004382bp** under E1,
95% descriptive interval **[−0.002277,+0.010515]**: its sign remains uncertain
and the magnitude is small. The diagonal V1 adaptation contrast is +0.005605bp
[+0.000341,+0.010691]; it does not establish an advantage of cross-impact.
V1 static versus original P0 has a negative E1 point (−0.012700bp), despite
better volume forecasts. Scenario P4 versus P2 is +0.015156bp
[−0.028512,+0.058051]; median-controlled scenario weighting is also uncertain.
These are development diagnostics, not evidence of causal execution savings.

Monthly, weekend and past-liquidity-tercile effects: paired_contrasts.csv;
worst10 cases per contrast/world: adverse_episodes.csv. Terciles use episode-start
past-predicted turnover only. Effects must be read across E1/E2; not every
forecast or adaptive change need improve cash costs.

![Paired modeled-cost effects](../../figures/extension_x1/paired_effects.png)

## Feasibility, liquidity risk and runtime

{table(qa,['policy','episodes','cap_violations','terminal_max_usdt','primal_max','kkt_max','replans','max_replan_seconds','repairs'])}

No silent clipping, cap relaxation or terminal repair. Risk/raw USDT² and full
runtime/decomposition are in policy_qa_summary.csv. Original T4 reproduction
max sale difference / initial inventory={parity.schedule_error_over_initial.max():.3g};
V1 vs V0 median relative L2={parity.V1_V0_relative_l2.median():.4g};
forecast VWAP vs TWAP median relative L2={parity.VWAP_TWAP_relative_l2.median():.4g}.
Matched policies use identical initial/covariance/cap/input hashes and beta.

{table(part)}

Threshold denominators and maximum-ratio columns use positive-volume asset-minutes. Zero-volume bins are
undefined and positive sales in them explicitly infeasible. Exact pooled upper
quantiles are in participation_quantiles.csv; episode p95/p99/max and miss
concentration are retained. Above100% is evidence that modeled orders cannot be
interpreted as executable fills; it is retained, not repaired or excluded.
Forecast-cap feasibility is not realized-liquidity feasibility. Compare all arms'
participation rates/maxima rather than inferring liquidity improvement from cost.

For P1→P2, the share above10% falls only from4.9148% to4.8944% of
positive-volume cells; above20% from1.0262% to1.0092%. P4 lowers the above10%
share to4.6894%, but retains severe outliers. Every arm has **36 positive-sale
asset-minutes with observed zero turnover**, explicitly infeasible. P2's largest
finite ratio is **375.17 times** recorded turnover; P4's is399.94 times.
These extreme development-source/liquidity cases invalidate any fill claim and
remain in all comparisons. Neither feedback nor the scenario proxy solves
realized-liquidity feasibility in this replay. Episode-level concentration and
adverse IDs are retained, not used to revise eligibility.

![Committed schedules, inventory and carried state](../../figures/extension_x1/adaptive_trace.png)

![Realized participation risk](../../figures/extension_x1/participation_risk.png)

## Verification, limitations and next-session handoff

Focused tests cover future mutations/availability, original V0/T4 parity,
complete-hour/zero/scenario construction, signed admissible cross terms,
Hessian/state/gradient identities, unchanged-tail time consistency at0/5/55/59,
zero inventory/kernel, independent CLARABEL parity, risk/cap/terminal checks,
scenario curvature and common-evaluator independence. Actual pytest results are
saved in test_results.json/pytest.xml. Original source tests were rerun excluding
Stage1 integration cases because they open2026 source pilots. Pilot deterministic
rerun evidence is pilot_reproducibility.json. All {preserved['prior_files']} prior
protected files and {preserved['canonical_partitions']} canonical stat snapshots
are unchanged. Numerical-source/config/scenario/model/source hashes, versions and
reader bounds are in run_manifest.json and run_development.json.

Final suite: **{tests['passed']} passed, {tests['failures']} failed, {tests['errors']} errors**;
{tests['X1_tests']} X1 cases; two integration cases deselected; four pre-existing
parser deprecation warnings. pip check passed. One temporary indentation error
during editing was corrected before the pilot/lock. The output-only zero-volume
JSON failure and unchanged numerical algorithm AST are preserved in
zero_volume_serialization_fix.json and provenance/. No episode was removed.
The independent output audit verifies all736 episodes/{audit['prefixes']} issued
prefixes and {audit['independent_triangular_checks']} direct triangular cash checks:
max discrepancy {audit['maximum_triangular_error_usdt']:.3g} USDT, complete-score
reproduction discrepancy {audit['maximum_score_error']:.3g}, max terminal
{audit['maximum_terminal_usdt']:.3g} USDT. Source/model/cap/risk/clock checks pass.

Scenario tail calibration improves on using a single V1 point as every quantile;
the median is slightly worse, retained as a negative result. The numerical
comparison is scenario_point_reference.csv; this degenerate point reference is
not a competing probabilistic model.

Data attribution: [Binance Vision public-data documentation](https://github.com/binance/binance-public-data),
recorded CC BY-NC-SA terms; no raw data redistributed. Mathematics builds on the
locally verified [AJNT v2](../../references/2403.10273v2.pdf), using the constrained
applied variant, not the stochastic Fredholm theorem. Public-flow confounding is
discussed in [Naviglio et al.](https://arxiv.org/abs/2501.17096).
No new causal identification, live savings, BBO/fills or all-in perpetual-P&L
claims. Development reuse, unmodeled volume dependence, marginal-band
misspecification, deterministic impact and proxy temporary liquidity remain limits.

Incremental retained disk ~{added/1024**2:.1f}MiB; conservative temporary/retained
peak estimate<{2*added/1024**2:.1f}MiB. Replay measured peakRSS
{run['peak_rss_mib']:.1f}MiB, runtime{run['seconds']/60:.2f}min. No packages/downloads.

```sh
.venv/bin/python -m pytest tests/test_extension_x1.py -q
.venv/bin/python scripts/extension_x1.py forecasts
.venv/bin/python scripts/extension_x1.py pilot
.venv/bin/python scripts/extension_x1.py development
.venv/bin/python scripts/extension_x1.py report
```

Existing decisions resume by input/gate/schedule hashes; they are not overwritten.
The safe next action is to review this exploratory evidence before separately
authorizing Session2. Preserve future Option2 (genuinely random Volterra kernels
and adapted path control) as future research; it is not implemented here.
Stop before robust optimization and any new final-test access.
'''
    (root/'reports/research/extension_x1_adaptive_liquidity.md').write_text(text)
    print(json.dumps(verdict,indent=2),flush=True)
    return verdict
