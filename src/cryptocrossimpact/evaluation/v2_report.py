"""Presentation only; statistical computation lives in frozen v2_summary."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..data.storage import sha256,utcnow
from ..execution.reporting import markdown_table
from .v2_common import locations,SCOPE,save
from .v2_summary import summarize
from .v2_run import receipts,verify_receipt


def figures(root):
    root=Path(root);out,bulk=locations(root);figdir=root/"figures/stage05_v2";figdir.mkdir(parents=True,exist_ok=True)
    coverage=pd.read_csv(out/"coverage_by_month.csv");x=np.arange(len(coverage))
    fig,ax=plt.subplots(figsize=(8,3.6),constrained_layout=True)
    ax.bar(x-.18,coverage.nominal,.36,label="nominal UTC arrivals");ax.bar(x+.18,coverage.SCORED,.36,label="scored common episodes")
    ax.set_xticks(x,coverage.month);ax.set_ylabel("Number of 60-minute episodes");ax.legend(fontsize=8)
    ax.set_title("2026 locked sample: structural QC only; funding omitted, no funding exclusions")
    fig.savefig(figdir/"coverage.png",dpi=140);plt.close(fig)
    m=pd.read_csv(out/"h1_metrics.csv");months=sorted(m[m.group!="all"].group.unique())
    fig,axes=plt.subplots(1,3,figsize=(12,3.7),constrained_layout=True)
    for ax,asset in zip(axes,["BTCUSDT","ETHUSDT","pooled"]):
        for model in ["N0","A","B"]:
            d=m[(m.asset==asset)&(m.model==model)&(m.group!="all")].set_index("group").reindex(months)
            ax.plot(np.arange(6),d.standardized_mse,"o-",label=model)
        ax.set_title(asset);ax.set_xticks(np.arange(6),[v[5:] for v in months]);ax.set_xlabel("2026 UTC month");ax.set_ylabel("Standardized response MSE")
    axes[0].legend();fig.suptitle("H1: same-minute conditional explanatory fit; observed flow is not an earlier forecast")
    fig.savefig(figdir/"h1_conditional_fit.png",dpi=140);plt.close(fig)
    models=pd.read_csv(out/"asof_model_registry.csv");b=models[models.role=="B"].groupby("month").sum(numeric_only=True)
    fig,axes=plt.subplots(1,2,figsize=(10,3.8),constrained_layout=True)
    for col,label in [("btc_self_100k_bps","BTC self"),("eth_self_100k_bps","ETH self"),("cross_100k_bps","symmetric cross")]:
        axes[0].plot(np.arange(6),b[col],"o-",label=label)
    axes[0].set_ylabel("B instantaneous response\n(bp per 100k USDT)");axes[0].legend(fontsize=8)
    for role in ("A","B","E1"):
        d=models[models.role==role].groupby("month").eigen_min.min()
        axes[1].plot(np.arange(6),d,"o-",label=role)
    axes[1].set_ylabel("Min. component eigenvalue\n(normalized f → y coordinates)");axes[1].legend(fontsize=8)
    for ax in axes:ax.set_xticks(np.arange(6),[v[5:] for v in months]);ax.set_xlabel("2026 fit origin month")
    fig.suptitle("2026 as-of B kernel drift and A/B/E1 PSD diagnostics; own liquidity units")
    fig.savefig(figdir/"kernel_drift.png",dpi=140);plt.close(fig)
    h2=pd.read_csv(out/"primary_h2_contrasts.csv");fig,ax=plt.subplots(figsize=(9,4),constrained_layout=True)
    labels=months+["all"]
    for offset,base in [(-.08,"T3"),(.08,"T3B")]:
        d=h2[(h2.world=="E1")&(h2.baseline==base)].set_index("group").reindex(labels)
        mean=d.mean_delta_ex_funding_bps.to_numpy();low=d.ci_low.to_numpy();high=d.ci_high.to_numpy()
        ax.errorbar(np.arange(7)+offset,mean,yerr=[mean-low,high-mean],fmt="o",capsize=3,label=f"{base} minus T4")
    ax.axhline(0,color="black",lw=.8);ax.axhline(.1,color="gray",ls=":",label="0.1 bp practical reference")
    ax.set_xticks(np.arange(7),labels);ax.set_ylabel("Modeled ex-funding shortfall difference (bp)")
    ax.legend(fontsize=8);ax.set_title("E1 paired contrasts; positive favors T4; 95% seven-day block intervals (500 draws)")
    fig.savefig(figdir/"E1_paired_contrasts.png",dpi=140);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(13,6),constrained_layout=True)
    names=[w for w in h2.world.unique() if w!="E0"]
    limit=max(abs(h2.mean_delta_ex_funding_bps.min()),abs(h2.mean_delta_ex_funding_bps.max()))
    for ax,base in zip(axes,["T3","T3B"]):
        d=h2[h2.baseline==base].pivot(index="world",columns="group",values="mean_delta_ex_funding_bps").reindex(index=names,columns=labels)
        im=ax.imshow(d,cmap="RdBu",vmin=-limit,vmax=limit,aspect="auto")
        ax.set_yticks(np.arange(len(names)),names);ax.set_xticks(np.arange(7),[v[5:] if v!="all" else v for v in labels]);ax.set_title(f"{base} minus T4; positive favors T4")
    fig.colorbar(im,ax=axes,label="Mean modeled shortfall difference excluding funding (bp)",shrink=.75)
    fig.suptitle("Jan–Jun 2026: all independent/stress worlds, including adverse outcomes; E0 excluded")
    fig.savefig(figdir/"scenario_heatmap.png",dpi=140);plt.close(fig)
    d=pd.read_csv(out/"E1_policy_decomposition.csv");fig,ax=plt.subplots(figsize=(10,4.2),constrained_layout=True)
    positive=np.zeros(len(d));negative=np.zeros(len(d))
    for col,label in [("path_bps","recorded path proxy"),("transient_bps","modeled transient"),("temporary_bps","assumed temporary"),("fee_bps","assumed fee"),("spread_bps","assumed half-spread")]:
        values=d[col].to_numpy();bottom=np.where(values>=0,positive,negative)
        ax.bar(d.policy,values,bottom=bottom,label=label);positive+=np.maximum(values,0);negative+=np.minimum(values,0)
    ax.axhline(0,color="black",lw=.7);ax.set_ylabel("Mean component (bp of episode starting notional)")
    ax.set_ylim(min(0,float(negative.min()))*1.05,float(positive.max())*1.25)
    ax.legend(fontsize=8,ncol=2);ax.set_title("E1 cash decomposition, 2026; excludes funding and risk preference; equal fee is constant")
    fig.savefig(figdir/"cash_decomposition.png",dpi=140);plt.close(fig)
    original=receipts(bulk/"primary/2026-01/decisions.jsonl")
    data=verify_receipt(original["20260105T0000Z"]);x0=np.array(data["initial"]);cap=np.array(data["caps"])
    fig,axes=plt.subplots(2,2,figsize=(11,6),constrained_layout=True)
    source=[]
    for p,z in data["schedules"].items():
        z=np.array(z);after=x0-np.cumsum(z,axis=0)
        for i,asset in enumerate(("BTC","ETH")):
            axes[i,0].plot(np.arange(60),z[:,i]/1000,label=p,ls="--" if p in ("T1","T3B") else "-")
            axes[i,1].plot(np.arange(61),np.r_[1,after[:,i]/x0[i]],label=p)
            for k in range(60):source.append(dict(policy=p,asset=asset,minute=k,sale_usdt=z[k,i],remaining_after_usdt=after[k,i],cap_usdt=cap[k,i]))
    for i,asset in enumerate(("BTC","ETH")):
        axes[i,0].plot(np.arange(60),cap[:,i]/1000,color="black",ls=":",label="forecast cap")
        axes[i,0].set_ylabel(f"{asset} sale (thousand USDT/min)");axes[i,1].set_ylabel(f"{asset} inventory / initial")
        for ax in axes[i]:ax.set_xlabel("Minutes since 2026-01-05 00:00 UTC")
    axes[0,0].legend(fontsize=7,ncol=2);fig.suptitle("Predetermined first Monday: frozen matched schedules; no funding cashflow modeled")
    fig.savefig(figdir/"representative_schedules.png",dpi=140);plt.close(fig)
    pd.DataFrame(source).to_csv(out/"representative_schedule_data.csv",index=False)


def report(root):
    root=Path(root);out,bulk=locations(root);figures(root)
    verdict=json.loads((out/"verdict_v2.json").read_text());qa=json.loads((out/"oos_qa.json").read_text())
    h1=pd.read_csv(out/"h1_metrics.csv");he=pd.read_csv(out/"h1_paired_effects.csv");h2=pd.read_csv(out/"primary_h2_contrasts.csv")
    pooled=h2[h2.group=="all"];decomp=pd.read_csv(out/"E1_policy_decomposition.csv");regret=pd.read_csv(out/"adverse_world_regret.csv")
    coverage=pd.read_csv(out/"coverage_by_month.csv");models=pd.read_csv(out/"asof_model_registry.csv")
    tests=json.loads((out/"test_results_v2.json").read_text());ready=json.loads((out/"pretest_ready_v2.json").read_text())
    postqa=json.loads((out/"post_ready_checks_v2.json").read_text()) if (out/"post_ready_checks_v2.json").exists() else None
    posttext=""
    if postqa:
        posttext=(f"A separate post-readiness suite passed {postqa['tests_passed']} cases. "
                  f"The post-outcome audit verified {postqa['audited_immutable_decisions']} immutable primary decisions "
                  f"and {postqa['independent_triangular_cash_checks']} independent triangular cash calculations; "
                  f"maximum discrepancy {postqa['maximum_triangular_cash_discrepancy_usdt']:.3g} USDT. "
                  "This is implementation QA, not additional pretest or economic evidence. "
                  "See post_ready_checks_v2.json and robustness_output_audit_v2.json in the artifact directory.")
    robust=pd.read_csv(out/"robustness_contrasts.csv") if (out/"robustness_contrasts.csv").exists() else None
    rqa=json.loads((out/"robustness_qa.json").read_text()) if (out/"robustness_qa.json").exists() else {}
    robust_display="Robustness tables pending."
    if robust is not None:
        rr=robust[(robust.group=="all")&(robust.baseline=="T3")];display=[]
        for variant,g in rr.groupby("variant"):
            row={"variant":variant}
            for world in ("E1","E2"):
                d=g[g.world==world].iloc[0]
                row[f"{world}_delta_bp_and_95pct_CI"]=f"{d.mean_delta_ex_funding_bps:.5g} [{d.ci_low:.5g}, {d.ci_high:.5g}]"
            display.append(row)
        robust_display=markdown_table(pd.DataFrame(display),["variant","E1_delta_bp_and_95pct_CI","E2_delta_bp_and_95pct_CI"])
    regime=pd.read_csv(out/"regime_contrasts.csv");regime=regime[(regime.world=="E1")&(regime.baseline=="T3")]
    participation_text=""
    participation_path=out/"realized_participation_by_policy.csv"
    if participation_path.exists():
        participation=pd.read_csv(participation_path)
        participation["maximum_realized_participation_pct"]=100*participation.maximum_realized_participation
        participation["over10pct_share_pct"]=100*participation.over10pct_share
        participation_text=markdown_table(participation,["policy","maximum_realized_participation_pct","over10pct_cells","total_asset_minute_cells","over10pct_share_pct"])
    primarytable=pooled[pooled.baseline=="T3"]
    secondary=pooled[pooled.baseline=="T3B"]
    text=f"""# Stage 5: locked BTC/ETH OOS evaluation — funding excluded

UTC: {utcnow()}. **{verdict['stage']}; implementation {verdict['implementation']}.**
H1: **{verdict['H1']}** for observational conditional response. H2: **{verdict['H2']}**
under the prespecified E1 practical/uncertainty comparison. Adverse E2/E3 worlds
remain explicit below; no universal evaluator or causal advantage is inferred.
Stage 6 was not begun.

We evaluate hypothetical, sell-only BTC/ETH perpetual-futures liquidation schedules
using recorded Binance prices and **model-based** transient/temporary impact
assumptions. All shortfalls **exclude funding payments** because verified
historical settlement-event/cashflow reconstruction was unavailable through
accessible sources. These amounts are not actual fills, live execution savings,
causal price effects, or all-in perpetual-futures P&L. This explicit ex-funding
scope was approved and frozen before the January–June 2026 test was opened.

## Lock lineage, sample and chronology

The original [v1 protocol](../../docs/stage05_pretest_policy_evaluator_lock_v1.md)
and [funding HOLD](stage05_oos_evaluation.md) remain historical artifacts, not
successful funding audits. The [approved amendment](../../docs/stage05_pretest_amendment_v2_funding_excluded.md)
supersedes funding accounting/prerequisite only. The [v2 protocol](../../docs/stage05_pretest_policy_evaluator_lock_v2.md)
and configs/stage05_pretest_lock_v2.yaml bind source, numerical code, grids,
independent E1 evidence, tests, normalization, scenarios and inference.
Ready UTC **{ready['utc']}**; v2 lock SHA-256 `{ready['amended_lock_sha256']}`.
The first actual outcome-opening receipt is in stage05_v2_artifacts/first_outcome_open_v2.json.

All 60 original canonical partitions are reused unchanged; no market or funding
data downloaded in this recovery. Dataset attribution: Binance Vision; derived
summaries follow recorded CC BY-NC-SA terms. Two USD-M perpetual last-trade 1m
contracts, UTC; 2026-01-01 through 2026-06-30. No funding-driven exclusions.
At t0, the last completed bar opens t0−1min; current/future bars are unavailable
to decisions. Filtered reads enforce actual requested bounds; mutation tests
verify future values cannot alter inputs/schedules. Immutable decisions and
model/world hashes precede outcome-bar reads. No within-month model revision.

{markdown_table(coverage,list(coverage.columns))}

Nominal {qa['nominal']}; scored common episodes {qa['scored_episodes']}; six
policies; {qa['world_count']} distinct worlds; {qa['score_rows']} primary rows.
Negative cash rows retained: {qa['negative_cash_rows']}. Failures/exclusions
have separate status logs, never zero costs. Maximum normalized physical
residual {qa['maximum_normalized_primal_residual']:.3g}; terminal residual
{qa['maximum_terminal_residual_usdt']:.3g} USDT; KKT stationarity
{qa['maximum_stationarity']:.3g}; decomposition residual
{qa['maximum_decomposition_residual']:.3g}. Realized participation is a diagnostic,
not an ex-post cap: max ratio {float(qa['maximum_realized_participation']):.5g}
({100*float(qa['maximum_realized_participation']):.2f}% of recorded minute turnover); E1 cells
above 10% across six schedules {qa['participation_over10pct_cells_E1']}.
Forecast-cap feasibility therefore does **not** establish executable fills or
feasibility against future realized liquidity. These cases remain in the sample;
the high realized-participation tail is a limitation of hypothetical replay.

{participation_text}

![Sample coverage](../../figures/stage05_v2/coverage.png)

## Frozen calibration and policies

Monthly A/B/N0 use the preceding 365 complete UTC days, fixed tau=60 min/ridge=1;
E1 uses [month−210d,month−30d), fixed tau=(5,30) min/ridge=1, with its own L and training
standardization. Sufficient statistics are congruently rescaled before fitting,
not coefficients copied between liquidity coordinates. Feature/forecast parity
on 2025 is tested against the original Stage 2/4 functions. Each monthly model
and evaluator is persisted before that month's scoring. Later fits use only
elapsed prior test history under the already frozen algorithm.

The two E1 development fits each have 259200 targets, exact 180-day/30-day-gap windows,
PSD components and reproducible fits distinct from optimizer B. Pretest evidence
and component diagnostics are under stage05_v2_artifacts/pretest_models/.
Rolling 2026 matrices, L, eigenvalues and file hashes are in asof_model_registry.csv.
Minimum component eigenvalue across fitted A/B/E1: {models.eigen_min.min():.6g}.
Decay remains a time constant in minutes, not a half-life; the exponential
level is not artificially cut off at regression memory 60.

T0 capped closest-TWAP; T1 past-only forecast-VWAP; T2 independent A with own variance
and shared global beta; T3 joint A/full risk; T3B B self terms/full risk; T4 full B.
T4–T3 compares separately fitted self AND cross terms; T4–T3B isolates cross terms.
X0=2% forecast 60-minute turnover, cap=10% forecast/bin, fixed 28-day seasonal medians and
ddof=1 covariance, theta=1, kappa=.001, fee=5 bp, half-spread=1 bp, zero alpha. T0 and T1 coincide
under constant within-hour forecasts; no forecast tuning separated them.

![As-of kernels](../../figures/stage05_v2/kernel_drift.png)

## H1: contemporaneous explanatory fit

{markdown_table(h1[h1.group=='all'],['model','asset','rows','standardized_mse','mae_bps','rmse_bps','conditional_explanatory_r2'])}

{markdown_table(he[he.asset=='pooled'],['group','delta_fit','delta_fit_ci_low','delta_fit_ci_high','mean_paired_standardized_loss_difference','loss_difference_ci_low','loss_difference_ci_high'])}

The pooled relative MSE difference is {100*verdict['H1_delta_fit']:.4f}% against
the 0.5% practical reference. Monthly points, per-asset errors and paired daily
loss uncertainty are retained. Flow q=2*taker-buy quote−total quote is observed
after the SAME bar; y=1e4 sqrt(L) log-return is already a return. Positive-lag
regressors use G(l)−G(l−1). This is not actionable forecasting or own-trade causal
identification; the prior lag-only null and lead-flow confounding remain relevant.

![Conditional fit](../../figures/stage05_v2/h1_conditional_fit.png)

## H2: common evaluator shortfall excluding funding

Delta=1e4(C(T3)−C(T4))/W; positive favors T4. E1 is an alternative past-data
parameterization, not randomized/causal independence. E2 removes each E1 cross
component; eight distinct E3 stress worlds cover joint amplitude, decay,
temporary curvature, cross interpolation and PSD-certified opposite sign.
Base repetitions are deduplicated explicitly via aliases. E0 is **IN_MODEL_ONLY**.

{markdown_table(primarytable,['world','paired_episodes','mean_delta_ex_funding_bps','ci_low','ci_high','negative_share','worst_episode_bps','relative_ratio_status'])}

Secondary controlled cross-term comparison:

{markdown_table(secondary,['world','mean_delta_ex_funding_bps','ci_low','ci_high','negative_share'])}

Monthly effects, medians, 25th/75th percentiles, cash differences, relative ratio
flags and confidence intervals are in primary_h2_contrasts.csv. E1 primary mean
{verdict['H2_E1_mean_bps']:.6g} bp, 95% interval
[{verdict['H2_E1_CI'][0]:.6g},{verdict['H2_E1_CI'][1]:.6g}], against the 0.1 bp practical
reference. {verdict['adverse_world_means_negative']} independent/stress worlds
have negative pooled primary means. No adverse world/month/episode was removed.
Intervals resample seven consecutive full calendar days, 500 shared draws,
seed20261027, preserving four within-day episodes/policy/world pairs and excluded
days. Means are episode-weighted. Monthly intervals use full within-month
calendars. Ratios are undefined for nonpositive or zero-crossing baseline cost.

The E1 sign remains uncertain, and its interval excludes the 0.1 bp practical
target. March, May and June have negative primary E1 point estimates; all six
monthly intervals cross zero. All independent/stress pooled primary intervals
also cross zero. These results do not establish a practical execution benefit.

![Paired E1](../../figures/stage05_v2/E1_paired_contrasts.png)

![Full stress matrix](../../figures/stage05_v2/scenario_heatmap.png)

Regret below is T4's cost minus the least cost among the six fixed policies in
the same episode/world. This is an ex-post descriptive comparison, not a policy
that could select the cheapest schedule before observing outcomes.

{markdown_table(regret,['world','maximum_T4_regret_bps','mean_T4_regret_bps','T4_underperforms_T3_share','T4_underperforms_T3B_share'])}

Regime results use UTC weekends and the unchanged 2025-only liquidity/volatility
terciles from v1; regime_contrasts.csv retains signed effects and block intervals.
They are overlapping time-series subsets, not independent experiments.

{markdown_table(regime,['regime_type','regime','paired_episodes','mean_delta_ex_funding_bps','ci_low','ci_high'])}

Worst-case episode IDs and signed contrasts are retained in
stage05_v2_artifacts/worst_episode_diagnostics.csv; they are diagnostics, not exclusions.

## Cash components, risk and robustness

{markdown_table(decomp,['policy','path_usdt','transient_usdt','temporary_usdt','fee_usdt','spread_usdt','shortfall_ex_funding_bps','full_cov_raw_risk_usdt_squared','full_cov_risk_preference_usdt'])}

Cash total sums five components only. Risk is an ex-ante preference/proxy, not
an expense paid to an exchange. Fee/spread are illustrative assumptions, not
observed historical tiers/BBO. All-in and funding-cashflow fields remain null.
Per-asset cash tables use each leg's starting notional; impact allocation is
quadratic bookkeeping, not causal attribution.

![E1 cash components](../../figures/stage05_v2/cash_decomposition.png)

![Predetermined schedules](../../figures/stage05_v2/representative_schedules.png)

All primary statistics were indexed before one-factor sensitivities. Robustness
compares E1/E2 for theta=0/2, sizes=.005/.01/.05, caps=.05/.20, horizons=30/120 min with
recomputed forecasts/size, fixed 100k USDT per leg and fixed June-2025 calibration. Open/OHLC and
fee/spread variants keep schedules unchanged. No scenario×size×risk full Cartesian
search. Robustness QA: `{rqa}`. Full paired monthly/pooled results and failures
are in robustness_contrasts.csv and robustness_failures.json; they cannot replace
the locked primary analysis. Fixed linear fees change levels, not paired timing
advantage. Changing horizon changes its forecast total and size as predeclared.

Primary T3-minus-T4 one-factor results (positive favors T4; full secondary
T3B contrasts remain in the same CSV):

{robust_display}

The fixed-100k and 30-minute sensitivities have negative pooled point estimates
under both E1 and E2. All pooled primary robustness intervals cross zero; none
replaces the original 60-minute, 2%-of-forecast primary analysis.

## Verification, limitations and restart

Pre-outcome suite: **{tests['passed']} passed, 0 failed**, two Stage 1 integration
tests deselected to avoid premature test access. Synthetic planted-kernel recovery,
independent E1 window/coordinates, exact cash factors/PSD across worlds,
funding omission, future mutation, immutable decisions, negative costs,
undefined participation, full-calendar paired bootstrap, and prior-stage
regressions passed before readiness. Outcome reads and output checkpoints carry
hashes; per-month manifests and the new run/session reports give resources.

{posttext}

The original public-flow endogeneity, same-bar information timing, hypothetical
impact interpretation, long selected decay and parameter uncertainty remain.
These scenario differences do not establish realized causal execution gains.
Funding omission limits any all-in perpetual-P&L claim, even for short horizons.
No optional C/D/SOL/L2/L4 branch or Stage 6 manuscript/CV synthesis was begun.

```sh
.venv/bin/python scripts/stage05_v2.py all
```

Completed monthly checkpoints resume without duplicate decisions; hashes and
frozen code/config must match. New results live under results/stage05_exfunding_v2
and this v2 report, preserving the original HOLD report and all prior results.
"""
    (root/"reports/research/stage05_oos_exfunding_v2.md").write_text(text)
