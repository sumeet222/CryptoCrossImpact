"""Standalone Stage A closeout and small figures; no numerical policy changes."""
import os,json,platform,subprocess,importlib.metadata
from pathlib import Path
import numpy as np
import pandas as pd
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[3]/'results/extension_a/matplotlibcache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from ..data.storage import sha256,utcnow
from ..execution.impact_cost import Kernel,ASSETS
from ..robust.workflow import model_bundle
from .common import paths,save,preserve,binding,config
from .fit import kernel
from .summary import summarize,audit


def table(f,cols=None):
    if cols:f=f[cols]
    def cell(x):
        if x is None or isinstance(x,(float,np.floating)) and not np.isfinite(x):return 'not applicable'
        return f'{x:.6g}' if isinstance(x,(float,np.floating)) else str(x)
    return '| '+' | '.join(f.columns)+' |\n| '+' | '.join(['---']*len(f.columns))+' |\n'+'\n'.join('| '+' | '.join(cell(x) for x in r)+' |' for r in f.itertuples(index=False,name=None))


def parameters(root):
    root=Path(root);out,_=paths(root);rows=[]
    for month in pd.period_range('2025-07','2025-12',freq='M').astype(str):
        b,ws=model_bundle(root,month,pd.Timestamp(month+'-01',tz='UTC'));e=next(w.kernel for w in ws if w.world_id=='E1')
        for role,k in [('B',b),('E',e)]:
            for j,c in enumerate(k.matrices):rows.append(dict(month=month,role=role,eta=0,tau=k.taus_minutes[j],C00=c[0,0],C01=c[0,1],C11=c[1,1],minimum_eigenvalue=np.linalg.eigvalsh(c)[0],cross_ratio=c[0,1]/np.sqrt(c[0,0]*c[1,1]),L0=k.liquidity_usdt[0],L1=k.liquidity_usdt[1],cross_bp_per_100k=1e5*c[0,1]/np.sqrt(np.prod(k.liquidity_usdt))))
        for eta in [.5,1]:
            for role in ['B','E']:
                m=json.loads((out/'models'/f'{month}_{role}_eta{eta}.json').read_text());k=kernel(m)
                for j,c in enumerate(k.matrices):rows.append(dict(month=month,role=role,eta=eta,tau=k.taus_minutes[j],C00=c[0,0],C01=c[0,1],C11=c[1,1],minimum_eigenvalue=np.linalg.eigvalsh(c)[0],cross_ratio=c[0,1]/np.sqrt(c[0,0]*c[1,1]),L0=k.liquidity_usdt[0],L1=k.liquidity_usdt[1],cross_bp_per_100k=1e5*c[0,1]/np.sqrt(np.prod(k.liquidity_usdt))))
    f=pd.DataFrame(rows);f.to_csv(out/'monthly_parameters.csv',index=False);return f


def figures(root):
    root=Path(root);out,bulk=paths(root);fig=root/'figures/extension_a';fig.mkdir(exist_ok=True);parameters_=parameters(root);response=pd.read_csv(out/'response_metrics.csv');cost=pd.read_csv(out/'execution_contrasts.csv');over=pd.read_csv(out/'overload_diagnostics.csv');selected=json.loads((out/'eta_selection.json').read_text())['selected_eta']
    f,axes=plt.subplots(1,2,figsize=(12,4.5));ratio=np.geomspace(.05,20,150);curves=[]
    for eta in [0,.5,1]:
        a=np.clip(ratio**(-eta/2),.5,2);axes[0].plot(ratio,a,label=f'eta={eta}')
        m=json.loads((out/'models'/f'initial_eta{eta}.json').read_text());k=kernel(m)
        for state,v in [('low forecast',.5),('reference',1.),('high forecast',2.)]:
            mult=np.clip((1/v)**(eta/2),.5,2);lags=np.arange(61);bp=1e5*k.level(lags)[:,0,1]/np.sqrt(np.prod(k.liquidity_usdt))*mult**2
            if eta:axes[1].plot(lags,bp,label=f'eta={eta} {state}',ls={'low forecast':'-','reference':'--','high forecast':':'}[state])
            elif state=='reference':axes[1].plot(lags,bp,color='black',label='eta=0 stationary')
            curves.extend(dict(eta=eta,state=state,lag_minute=int(t),cross_bp_per_100k=float(b)) for t,b in zip(lags,bp))
    axes[0].set_xscale('log');axes[0].set_xlabel('Past-known V1 / fixed month Vref');axes[0].set_ylabel('Multiplier a (dimensionless)');axes[0].set_title('Declared clipped state law');axes[0].legend()
    axes[1].set_xlabel('Lag (minutes)');axes[1].set_ylabel('Cross displacement (bp per100000 USDT)');axes[1].set_title('Initial fitted kernels: common low/reference/high forecast ratios');axes[1].legend(fontsize=7);f.tight_layout();f.savefig(fig/'state_kernel_curves.png',dpi=140);plt.close(f);pd.DataFrame(curves).to_csv(out/'kernel_curve_figure_data.csv',index=False)
    f,axes=plt.subplots(2,2,figsize=(12,8))
    for i,asset in enumerate(['BTCUSDT','ETHUSDT']):
        for eta in [0,.5,1]:
            g=response[(response.asset==asset)&(response.model==f'S_fit_eta{eta}')&response.group.str.match('2025-')].sort_values('group');axes[0,i].plot(g.group,g.standardized_mse,'o-',label=f'eta={eta}')
        axes[0,i].set_title(f'{asset} conditional response (fixed initial fit)');axes[0,i].set_ylabel('Training-standardized MSE');axes[0,i].tick_params(axis='x',rotation=30);axes[0,i].legend()
        role=['B','E'][i]
        for eta in [0,.5,1]:
            g=parameters_[(parameters_.role==role)&(parameters_.eta==eta)].groupby('month').cross_bp_per_100k.sum();axes[1,i].plot(g.index,g.values,'o-',label=f'eta={eta}')
        axes[1,i].set_title(f'{role}: monthly past-fitted total cross coefficient');axes[1,i].set_ylabel('Cross bp per100000 USDT at reference state');axes[1,i].tick_params(axis='x',rotation=30);axes[1,i].legend()
    f.tight_layout();f.savefig(fig/'response_parameter_stability.png',dpi=140);plt.close(f)
    overload_rows=pd.read_csv(out/'development_overload.csv');baseline_rows=overload_rows[overload_rows.policy=='A0'].sort_values(['overload','episode_id'],ascending=[False,True]);eid=baseline_rows.iloc[0].episode_id;r=json.loads((bulk/'development'/f'{eid}.json').read_text());d=json.loads((root/r['decision_file']).read_text());x=np.array(d['initial']);observed=np.array(json.loads((root/'results/extension_x2x3/selection'/f'{eid}.json').read_text())['source_actual_volume_posthoc']);data=[]
    with np.load(bulk/'development'/r['schedule_file']) as z:
        f,axes=plt.subplots(3,2,figsize=(12,9),sharex=True)
        for i,asset in enumerate(['BTCUSDT','ETHUSDT']):
            for p in ['A0','eta0.5_refresh','eta0.5_diag','eta0.5_frozen','eta1_refresh','TWAP']:
                a=z[p];axes[0,i].plot(np.arange(61),np.r_[x[i],x[i]-np.cumsum(a[:,i])]/x[i],label=p)
                excess=np.maximum(a[:,i]-.1*observed[:,i],0);axes[1,i].plot(excess/x.sum()*100,label=p)
                if 'state_'+p in z:axes[2,i].plot(z['state_'+p][:,i],label=p)
                for t in range(60):data.append(dict(policy=p,asset=asset,minute=t,sale_usdt=a[t,i],realized_volume_usdt_posthoc=observed[t,i],excess_usdt=excess[t],multiplier=z['state_'+p][t,i] if 'state_'+p in z else 1.))
            axes[0,i].set_title(asset);axes[0,i].set_ylabel('Remaining / original inventory');axes[1,i].set_ylabel('Minute overload / original W (%)');axes[2,i].set_ylabel('Committed ex-ante multiplier');axes[2,i].set_xlabel('Minute after '+pd.to_datetime(eid,format='%Y%m%dT%H%MZ',utc=True).strftime('%Y-%m-%d %H:%M UTC'))
            for ax in axes[:,i]:ax.legend(fontsize=6)
        f.suptitle('Posthoc illustration: largest A0 overload; immutable committed sales/state');f.tight_layout();f.savefig(fig/'committed_inventory_overload.png',dpi=140);plt.close(f)
    pd.DataFrame(data).to_csv(out/'committed_path_figure_data.csv',index=False)
    f,axes=plt.subplots(1,3,figsize=(14,6),sharey=True)
    allcost=cost[(cost.group=='all')&(cost.control=='A0')];worlds=sorted(allcost.world.unique());labels=['A1','eta0.5_refresh','eta1_refresh']
    for ax,p in zip(axes,labels):
        g=allcost[allcost.new==p].set_index('world').reindex(worlds)
        for i,row in enumerate(g.itertuples()):ax.plot([row.ci_low,row.ci_high],[i,i],color='tab:blue');ax.scatter(row.mean,i,color='tab:blue',s=20)
        ax.axvline(0,color='.5');ax.axvline(.1,color='.5',ls=':');ax.set_yticks(np.arange(len(worlds)),worlds,fontsize=7);ax.set_title(p+(' (selected null)' if p=='A1' and selected==0 else ' (secondary)'));ax.set_xlabel('Cost(A0)−cost(policy), bp\n95% seven-day block interval')
    f.suptitle('Common independent/scenario worlds · funding excluded · descriptive development');f.tight_layout();f.savefig(fig/'independent_world_cost_intervals.png',dpi=140);plt.close(f)
    policies=['A0','A1','A2','eta0.5_refresh','eta1_refresh','fixed_eta0.5','TWAP'];g=over.set_index('policy').loc[policies];f,(ax,bar)=plt.subplots(1,2,figsize=(13,5));raw=pd.read_csv(out/'development_overload.csv')
    for i,p in enumerate(policies):
        v=raw[raw.policy==p].max_finite_ratio.to_numpy()*100;ax.scatter(i+.07*np.sin(np.arange(len(v))),v,alpha=.2,s=7);ax.scatter(i,v.max(),marker='x',color='red')
    ax.axhline(100,color='red',ls='--');ax.set_yscale('log');ax.set_xticks(np.arange(len(policies)),policies,rotation=30,ha='right',fontsize=7);ax.set_ylabel('Maximum finite participation per episode (%)')
    bar.bar(np.arange(len(g)),g['mean']*100);bar.set_xticks(np.arange(len(g)),[p+'\nsales @ V=0:'+str(int(g.loc[p,'positive_sales_zero_cells'])) for p in policies],rotation=30,ha='right',fontsize=6);bar.set_ylabel('Mean observed overload (% of original W)');f.suptitle('Development adverse liquidity: ALL finite extremes and explicit zero-volume sales');f.tight_layout();f.savefig(fig/'adverse_participation_tails.png',dpi=140);plt.close(f)


def state_distributions(root):
    root=Path(root);out,bulk=paths(root);values={}
    for file in sorted((bulk/'state_forecasts').glob('*.npz')):
        group='training' if file.stem<'2025-07' else 'validation'
        with np.load(file) as data:
            for eta in [.5,1]:values.setdefault((group,eta),[]).append(data[f'a{eta}'].copy())
    rows=[]
    for (group,eta),parts in values.items():
        a=np.vstack(parts)
        for i,asset in enumerate(['BTCUSDT','ETHUSDT']):
            q=np.quantile(a[:,i],[0,.01,.1,.5,.9,.99,1]);rows.append(dict(period=group,eta=eta,asset=asset,n=len(a),minimum=q[0],p01=q[1],p10=q[2],median=q[3],p90=q[4],p99=q[5],maximum=q[6],clip_low_share=float((a[:,i]==.5).mean()),clip_high_share=float((a[:,i]==2).mean())))
    f=pd.DataFrame(rows);f.to_csv(out/'state_distributions.csv',index=False);return f


def risk_accounting(root):
    """Common full-schedule inventory risk; local CVaR preference kept separate."""
    root=Path(root);out,bulk=paths(root);rows=[]
    old=pd.read_csv(root/'reports/research/extension_x2x3_artifacts/selection_solver_diagnostics.csv')
    old=old[old.policy=='L25'].set_index('episode_id')
    new=pd.read_csv(out/'development_diagnostics.csv').set_index(['episode_id','policy'])
    for path in sorted((bulk/'development').glob('*_decisions.json')):
        d=json.loads(path.read_text());eid=path.name.removesuffix('_decisions.json');x=np.array(d['initial']);sigma=np.array(d['covariance']);beta=d['beta']
        with np.load(root/d['schedule_file']) as arrays:
            for name in arrays.files:
                if name.startswith('state_'):continue
                z=arrays[name];before=x-np.vstack([np.zeros(2),np.cumsum(z,axis=0)[:-1]])
                raw=float(np.einsum('ki,ij,kj->',before,sigma,before));pref=beta*raw
                cv=None
                if (eid,name) in new.index:cv=float(new.loc[(eid,name),'liquidity_preference_at_arrival_usdt'])
                elif name in ['A0','A1','A3']:cv=float(old.loc[eid,'liquidity_preference_at_arrival_usdt'])
                rows.append(dict(policy=name,risk_raw_usdt_squared=raw,risk_preference_usdt=pref,risk_preference_bps=1e4*pref/x.sum(),tentative_arrival_CVaR_preference_usdt=cv))
    f=pd.DataFrame(rows).groupby('policy').mean().reset_index();f.to_csv(out/'matched_risk_preferences.csv',index=False)
    return f


def report(root):
    root=Path(root);out,bulk=paths(root);fig=root/'figures/extension_a';audit_result=audit(root);summarize(root);figures(root);risk=risk_accounting(root);distribution=state_distributions(root)
    selection=json.loads((out/'eta_selection.json').read_text());m=pd.read_csv(out/'response_metrics.csv');contrasts=pd.read_csv(out/'response_contrasts.csv');tail=pd.read_csv(out/'tail120_metrics.csv');policies=pd.read_csv(out/'policy_comparison.csv');cost=pd.read_csv(out/'execution_contrasts.csv');liq=pd.read_csv(out/'overload_contrasts.csv');over=pd.read_csv(out/'overload_diagnostics.csv');qa=pd.read_csv(out/'solver_QA.csv');params=pd.read_csv(out/'monthly_parameters.csv');feature=json.loads((out/'feature_manifest.json').read_text());conf=json.loads((out/'confirmation_status.json').read_text()) if (out/'confirmation_status.json').exists() else dict(status='CONFIRMATION_HOLD',reason='Optional separately frozen October experiment not established',new_October_values_opened=False)
    tests=json.loads((out/'final_tests.json').read_text()) if (out/'final_tests.json').exists() else dict(passed='pending',failures='pending')
    eigen=float(params.minimum_eigenvalue.min());test=(out/'final_stdout.txt').read_text() if (out/'final_stdout.txt').exists() else (out/'development_preflight_stdout.txt').read_text();eta=selection['selected_eta'];maincost=cost[(cost.group=='all')&(cost.world=='E_stationary')];mainliq=liq[liq.group=='all'];primary=maincost[maincost.new.isin(['A1','eta0.5_refresh','eta1_refresh'])&(maincost.control=='A0')]
    basic=m[(m.group=='all')&m.asset.isin(['BTCUSDT','ETHUSDT','pooled'])];stateqa=pd.DataFrame(feature['QA']);stateqa['clip_fraction_eta1']=(stateqa.clip_low+stateqa.clip_high)/(2*stateqa.rows)
    text=f'''# Stage A: liquidity-dependent admissible transient cross-impact

UTC {utcnow()}. **Development implementation PASS; H-A1 DOES_NOT_SUPPORT;
selected eta={eta}. October: {conf['status']}.**
**QA access scope QUALIFIED:** one inherited test loaded unused, previously
inspected2026 derived caches after eta selection; disclosed below.
All development evidence is
exploratory/post-search. No October source values were opened. January–September2026
remain previously inspected background, not a fresh test of Stage A. No Option2
stochastic Volterra-control theory or feedback-optimality research was begun.

## Question, inherited evidence and scope

Does changing transient impact with ex-ante liquidity add value beyond the
successful X2/X3 L25 liquidity-CVaR preference? Prior42% July–September overload
reduction, uncertain modeled cost, stronger TWAP liquidity, and dominated GL
remain unchanged in their separate reports. Here we use original786239 synchronized
training minutes (Jan2024–Jun2025),264960 validation minutes and736 fixed
Jul–Dec2025 development execution episodes. Binance UM BTCUSDT/ETHUSDT one-minute
last-trade prices and USDT quote taker flow; no new source acquisition/dataset.
Data attribution: Binance Vision official futures/um archives; recorded reuse
conditions and source-rebuild details remain in the original
[data documentation](../../data/README.md). Raw archives are not redistributed.
[Protocol](../../docs/extensions/a_liquidity_impact_protocol_v1.md) and
[config](../../configs/extension_a_liquidity_impact.yaml) declare all choices.

## Mathematics, estimator and causal state

G(t,s)=A(t)sum C_a exp(-(t-s)/tau_a)A(s), C_a symmetric PSD in original
cash-consistent q/sqrt(L)→1e4 sqrt(L) return coordinates. a_i is clipped[.5,2]
(Vref/V1)^(eta/2), V1 known strictly before the bar. Vref is the positive-turnover
median of28 complete days before month start. It is separate from each fit's L.
January2024 has no preceding month-start history: identity state is declared for
all candidates, preserving exact original sample/rows; no future reference is
used. Its internal unit-placeholder V1 array is not a turnover forecast and never
sets an inventory/cap. February onward has complete support. This startup
limitation is explicit.

For block diagonal D of the piecewise-constant minute multipliers, exact-cell
H_A=D H0 D and z'H_A z=(Dz)'H0(Dz)>=0 for every signed z. This proves only
frozen-path admissibility. Same-cell triangle and off-time exponential factors
are unchanged, with no extra minute factor. Every committed sale retains its
original ex-ante multiplier. Replans concatenate immutable past A and newly
forecast future A; remaining cost=.5zf'Hff zf+zf'Hfp zp. No state reset or
rewriting past fills. V1 is exogenous to hypothetical orders; feedback is unmodeled.

Regression uses the difference of FULL scaled displacements, not a_t times the
stationary return basis. Current level lags0..H and prior level lags0..H−1
match the original finite-lag return equation at eta0, without an H+1 tail.
This is an approximation to the infinite response; execution integrates the
untruncated exponential over the60-minute horizon. H120 sensitivity is separate.
Receiver-specific state regressors have training-only scales; PSD constraints
apply after restoring economic C. Same nuisance controls, rows, y, target loss
weights and ridge1; tau60 only, eta0/.5/1 only. No execution-cost eta selection.

Original Stage2 eta0 reproduction: largest C discrepancy
{selection['eta0_max_matrix_error']:.3g}, validation standardized MSE discrepancy
{selection['eta0_validation_MSE_error']:.3g}. Three actual L25 schedule reproductions
are exact; selected eta0 A1/A3 are explicit A0 aliases, avoiding a changed baseline.

## Observed-data response result — primary empirical layer

Smallest eta within0.1% of minimum is selected; promotion additionally requires
>=.5% relative MSE gain, PSD and timing/state checks. **Selected eta0.**
Eta.5 worsens pooled validation MSE by6.7096% (95% block interval5.0956–8.5050%);
eta1 worsens22.6740% (19.3531–26.2474%). Both fail the response gate, with no new
candidate search. Same-minute public-flow response is descriptive/explanatory,
not a deployable return forecast, own-trade causal law or structural identification.

{table(basic,['model','asset','n','standardized_mse','mae_bps','explanatory_r2'])}

Positive contrast below favors the new model. Standardized squared-error
averages use paired7-calendar-day blocks500draws seed20261027. The fixed-C
sensitivity keeps old stationary C AND nuisance terms, changing state mechanism
only; S_fit re-estimates the complete constrained model.

{table(contrasts,['model','mean','ci_low','ci_high','relative_reduction','relative_ci_low','relative_ci_high'])}

H120 refits (same candidates and dates; no tail-based re-selection):

{table(tail[(tail.group=='all')&(tail.asset=='pooled')],['model','standardized_mse','mae_bps','explanatory_r2'])}

The failure persists at H120 (about7.0%/23.4% worse), so the eta result is not
explained by selecting a more favorable truncation convention. Full per-asset,
monthly, weekday/weekend, low/high STRICTLY PAST activity groups are in
response_metrics.csv; training-only regime threshold reused from Stage2.
Monthly own-window B/E parameter drift and eigendiagnostics are in
monthly_parameters.csv. Minimum economic component eigenvalue={eigen:.6g}.
State distributions/clip rates below are diagnostics, not additional tuning.

{table(stateqa,['month','rows','identity_warmup','minimum_a','maximum_a','clip_fraction_eta1'])}

Calendar-state distributions (including the declared startup identity):

{table(distribution)}

![State law and curves](../../figures/extension_a/state_kernel_curves.png)
![Response and coefficient stability](../../figures/extension_a/response_parameter_stability.png)

## Matched execution and independent scenario evaluation

A0 is immutable original X2/X3 L25; A1 uses selected eta0 (exact A0 alias);
A2 is same-B-self diagonal WITH the same L25 CVaR; A3 selected eta0 also aliases
A0. Failed secondary eta.5/1 refresh/diag/frozen variants and fixed-C .5/1 remain
reported rather than promoted. N and unchanged TWAP are context. All use original
X0=.02sum(V0), cap=.1V0, V1, full Sigma/beta, CVaR90 lambda25/twelve paired paths,
60min/five-minute MPC and assumed fee5bp/halfspread1bp. Neither risk nor CVaR
preference is paid cash. A0 caches are reused; new policies have immutable
prefix receipts, state ledger, complete schedule and post-commit scoring.

B_eta refits365 preceding complete days, tau60/ridge1. Conditional evaluator
refits180d ending30d before month, tau5/30/ridge1, own L/standardization. E_stationary
is the OLD independent E1. Conditional evaluation uses ONE common per-minute V1
state path known BEFORE each respective minute, separate from each policy's
five-minute forecast/commitment state ledger. Full cash uses recorded next closes,
exact-cell transient, frozen V0 temporary, assumed fees/spread; funding is omitted,
not assumed zero. No local objective sum, future-volume cap or reconstructed fills.

At selected eta0, E_conditional and eta-strength0 alias E_stationary exactly.
Conditional diagonal and amplitude.5/2 remain adverse/null worlds. Secondary
independently fitted eta.5/1 full/diagonal evaluators remain labeled ablation
worlds. All worlds are common across every arm; alias mappings are in episode
receipts. No optimizer self-score is the sole or primary evidence.

{table(policies[policies.world=='E_stationary'],['policy','episodes','mean_bps','median_bps','p95_bps','path_usdt','transient_usdt','temporary_usdt'])}

Main stationary-world differences, cost(control)−cost(new), bp of original W,
funding excluded; positive favors new. All other worlds, monthly, weekday/weekend
and development-fixed past-liquidity terciles are in execution_contrasts.csv.

{table(maincost,['control','new','mean','ci_low','ci_high','negative_share','p95_disadvantage_bps','worst_bps'])}

Selected A0→A1 cost and overload contrasts are EXACTLY0 by nesting, not a new
positive result. The.1bp practicality hurdle is not met by a changed selected
policy. A2→A1 isolates stationary same-self cross impact; nonzero-eta secondary
results cannot overturn the failed response gate or become a retrospectively
selected model. In E_stationary the failed eta.5/1 refresh variants yield only
0.00821bp (95% interval −0.04231 to0.05595) and0.00288bp (−0.11313 to0.11090)
mean modeled savings. Both intervals include zero and point estimates fall below
0.1bp. Mean overload increases by0.0273 and0.0873 percentage points of W,
respectively (95% intervals0.0092–0.0465 and0.0538–0.1276): an adverse
liquidity tradeoff, not an execution win. The inventory illustration is explicitly
selected posthoc as the largest original A0 overload, solely to display that failure;
it does not select any model, policy or eligible episode.
Adverse cases/regret/loss shares remain in scenario_tails.csv
and adverse_episodes.csv, including large negative differences.

![Matched inventories and committed states](../../figures/extension_a/committed_inventory_overload.png)
![Independent-world costs and uncertainty](../../figures/extension_a/independent_world_cost_intervals.png)

Common full-schedule risk accounting below uses the SAME beta/Sigma and
pre-trade inventory for every arm, including TWAP. The CVaR column is the
preference for the tentative arrival plan, not a sum of MPC objectives or paid
cash. Context entries marked not applicable mean the policy did not optimize that preference.

{table(risk)}

## Liquidity realism — co-primary risk diagnostic

Overload=sum(max(z−.1Vreal,0))/ORIGINAL W. It is not actual unfilled volume.
Positive-volume ratios and counts exclude zero denominators; positive sales
at zero turnover remain explicitly NON-EXECUTABLE and remain in overload.
All extremes and negative months are preserved. Better mean cost with worse
overload/tails is a tradeoff. TWAP's lower overload is retained prominently.

{table(over)}

{table(mainliq[mainliq.new.isin(['A1','eta0.5_refresh','eta1_refresh','fixed_eta0.5'])],['control','new','mean_old','mean_new','mean','ci_low','ci_high'])}

![All participation extremes](../../figures/extension_a/adverse_participation_tails.png)

## Gates, QA, provenance and limits

A-G0 PASS; A-G1 PASS; A-G2 PASS (scientific gate rejects nonzero eta);
A-G3 PASS; A-G4 **{conf['status']}**; A-G5 complete. {conf['reason']}
No PRETEST_READY_A was created, no October archive acquired or source values
opened, and no inspected2026 period was relabeled confirmation. Negative
complete development is the authorized definition of done; optional confirmation
is not forced. Future confirmation would require a separately evidence-bound
pretest, source availability/noninspection and unchanged frozen criteria.

Actual final regression: **{tests['passed']} passed, {tests['failures']} failures**,
three deselections (two original integration cases and the eager legacy loader).
Four pre-existing parser deprecation warnings remain. Numerical/feasibility checks:

{table(qa)}

Audited736 episodes; {audit_result['prefixes']} immutable sale/state prefixes;
maximum independent full-triangular cash discrepancy
{audit_result['maximum_triangle_error_usdt']:.3g}USDT. Original L25 E1 complete-score
parity discrepancy={audit_result['original_L25_E1_score_error_bps']:.3g}bp.
No cap/terminal repair, state reset or ignored KKT failure. Focused tests include
hand cells/signed PSD/units, eta0 regression and schedule nesting, independent
normal-equation/known-kernel recovery, conditional gradients, permutation,
negative past-multiplier rewrite and future mutations0/5/55/59, vectorized minute
V1 parity, zero-volume output and exact read-once-loader parity. Full regression
results and test/source hashes are in development_preflight/final JUnit and logs;
original integration tests that open2026 pilot data were deselected.
One inherited X2 regression test eagerly loaded previously inspected Jan–Aug2026
sufficient statistics (eight caches) after eta selection while checking a2025 fit. They were not
used in Stage A inputs, calibration, selection or policies, and no2026 canonical
values were read for Stage A. This unnecessary inherited-QA access is disclosed.
The final rerun excludes that legacy loader test and substitutes a Stage A
365d-B/180d-E1 equivalence test whose reader log is entirely2024–2025.
No October source values were accessed in this session; independent October
eligibility was not certified. This is an inherited-QA access-scope qualification,
not new-holdout contamination.

All {audit_result['preservation']['files']} earlier protected files/locks and
{audit_result['preservation']['data_stat_snapshots']} original data snapshots
remain unchanged; OS metadata is excluded from this scientific inventory.
Initial bool/NaN synthetic fixture and pilot scorer-world-hash bugs were fixed
before full replay; failed pilot and initial JUnit are retained. Statistics loading
uses byte-identical read-once arrays, with source/version clarification in
read_once_fix.json. No old source or locked changelog was edited. Stage A protocol
records the authorized extension and startup convention, rather than changing
previous science. New raw data0 bytes; resource/code/package manifests and
session report give actual run time/disk/RAM and bounded restart commands.

[AJNT](https://arxiv.org/abs/2403.10273) treats deterministic matrix Volterra
kernels; our exact frozen-path congruence is elementary, not its random-kernel
theorem. [Alfonsi–Klöck–Schied](https://arxiv.org/abs/1310.4471) is prior matrix
admissibility theory. [Muhle-Karbe–Wang–Webster](https://doi.org/10.1287/opre.2022.0627)
uses stochastic liquidity as a proxy for nonlinear impact; it does not validate
our inverse-volume law. [Muhle-Karbe–Tracy](https://ssrn.com/abstract=4885733) is a2024
multi-asset working-paper precedent: abstract consulted, full PDF403, no detailed
theorem imported. [Naviglio et al.](https://arxiv.org/abs/2501.17096) motivates the
identification caution. These sources do not prove own-trade cost causality here.

The empirical conclusion is to retain L25's stationary kernel: this restricted
inverse-liquidity law worsened observed response fit, and the selected execution
policy did not change. Funding, actual BBO/fills, endogenous volume response,
public-flow confounding and repeated development reuse remain limitations. No
live saving, all-in perpetual P&L or broad failure of every possible state law is
established. H-A2 is INCONCLUSIVE for nonzero modeled-cost ablations; H-A3
DOES_NOT_SUPPORT an overload-safe improvement. Exact next decision: retain eta0/L25; pursue another state law or a
stochastic-control theorem only under a new separately authorized specification.

```sh
.venv/bin/python scripts/extension_a.py math
.venv/bin/python scripts/extension_a.py features
.venv/bin/python scripts/extension_a.py fit
.venv/bin/python scripts/extension_a.py pilot
.venv/bin/python scripts/extension_a.py development
.venv/bin/python scripts/verify_extension_a.py
.venv/bin/python scripts/extension_a.py report
```
'''
    (root/'reports/research/extension_a_liquidity_impact.md').write_text(text)
    retained=sum(p.stat().st_size for base in [out,bulk,fig] for p in base.rglob('*') if p.is_file());run=json.loads((out/'development_run.json').read_text());save(out/'run_manifest.json',dict(utc=utcnow(),code=binding(root),config=config(root),selected_eta=eta,source_manifest_sha256=sha256(root/'data/registry/source_manifest.json'),specification_sha256=sha256(root/'CryptoCrossImpact_Research_Specification_v1_2026-10-27.md'),old_L25_selection_sha256=sha256(root/'reports/research/extension_x2x3_artifacts/development_selection.json'),eta_selection_sha256=sha256(out/'eta_selection.json'),source_reads=feature['source_reads'],period='2024-01 through2025-12 only',new_October_values_opened=False,confirmation_status=conf['status'],retained_bytes=retained,conservative_peak_additional_bytes=2*retained,development=run,preservation=audit_result['preservation'],python=platform.python_version(),packages={n:importlib.metadata.version(n) for n in ['numpy','pandas','scipy','cvxpy','clarabel','osqp','matplotlib']},git_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),git_status=subprocess.check_output(['git','status','--short'],cwd=root,text=True),seed=20261027))
    print(dict(development='PASS',selected_eta=eta,confirmation=conf['status'],retained_MiB=retained/1024**2))
