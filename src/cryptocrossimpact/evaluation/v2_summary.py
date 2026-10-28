"""Frozen H1/H2 statistics and adverse-case tables (separate from rendering)."""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.storage import sha256,utcnow
from .v2_common import locations,save,SCOPE
from .v2_protocol import validate_ready
from .v2_inference import contrasts,paired_interval


def h1_tables(daily):
    metrics=[];effects=[]
    for label,data in [("all",daily)]+list(daily.groupby("month")):
        per=[]
        for (model,asset),group in data.groupby(["model","asset"]):
            n=group.n.sum();sse=group.error_bps_sse.sum();variance=group.target_bps_sumsq.sum()-group.target_bps_sum.sum()**2/n
            row=dict(group=label,model=model,asset=asset,rows=int(n),standardized_mse=float(group.standardized_sse.sum()/n),
                mae_bps=float(group.error_bps_sae.sum()/n),rmse_bps=float(np.sqrt(sse/n)),conditional_explanatory_r2=float(1-sse/variance))
            metrics.append(row);per.append(row)
        for model,g in pd.DataFrame(per).groupby("model"):
            metrics.append(dict(group=label,model=model,asset="pooled",rows=int(g.rows.min()),standardized_mse=float(g.standardized_mse.mean()),
                mae_bps=float(g.mae_bps.mean()),rmse_bps=float(np.sqrt(np.mean(g.rmse_bps**2))),conditional_explanatory_r2=float(g.conditional_explanatory_r2.mean())))
        begin=pd.Timestamp("2026-01-01") if label=="all" else pd.Timestamp(label+"-01")
        end=pd.Timestamp("2026-07-01") if label=="all" else begin+pd.offsets.MonthBegin(1)
        days=pd.date_range(begin,end,freq="D",inclusive="left").strftime("%Y-%m-%d")
        for asset in ["pooled","BTCUSDT","ETHUSDT"]:
            d=data if asset=="pooled" else data[data.asset==asset]
            a=d[d.model=="A"].groupby("day").agg(sse=("standardized_sse","sum"),n=("n","sum")).reindex(days,fill_value=0)
            b=d[d.model=="B"].groupby("day").standardized_sse.sum().reindex(days,fill_value=0)
            ci=paired_interval(days,(a.sse-b).to_numpy(),a.n.to_numpy(),a.sse.to_numpy())
            effects.append(dict(group=label,asset=asset,delta_fit=float((a.sse.sum()-b.sum())/a.sse.sum()),
                mean_paired_standardized_loss_difference=ci["mean"],loss_difference_ci_low=ci["ci_low"],loss_difference_ci_high=ci["ci_high"],
                delta_fit_ci_low=ci["relative_ci_low"],delta_fit_ci_high=ci["relative_ci_high"],calendar_days=len(days),replicates=500))
    return pd.DataFrame(metrics),pd.DataFrame(effects)


def summarize(root,primary_only=False):
    root=Path(root);validate_ready(root);out,bulk=locations(root)
    index=json.loads((out/"primary_index.json").read_text());months=[r["month"] for r in index["months"]]
    scores=[];coverage=[];daily=[]
    for m in months:
        folder=bulk/"primary"/m;checkpoint=json.loads((folder/"checkpoint.json").read_text())
        for name,h in checkpoint["output_sha256"].items():
            if sha256(folder/name)!=h:raise RuntimeError("Primary output changed after checkpoint")
        scores.append(pd.read_parquet(folder/"scores.parquet"));coverage.append(pd.read_csv(folder/"coverage.csv"));daily.append(pd.read_csv(folder/"h1_daily.csv"))
    s=pd.concat(scores,ignore_index=True);c=pd.concat(coverage,ignore_index=True);h1=pd.concat(daily,ignore_index=True)
    if set(s.cost_scope)!={SCOPE} or not s.funding_cashflow_usdt.isna().all() or not s.all_in_cash_cost_usdt.isna().all():raise RuntimeError("Wrong cash accounting scope")
    effects,daytable=contrasts(s);effects.to_csv(out/"primary_h2_contrasts.csv",index=False);daytable.to_csv(out/"primary_h2_daily.csv",index=False)
    metrics,h1effects=h1_tables(h1);metrics.to_csv(out/"h1_metrics.csv",index=False);h1effects.to_csv(out/"h1_paired_effects.csv",index=False)
    cov=c.assign(month=pd.to_datetime(c.t0,utc=True).dt.strftime("%Y-%m")).groupby(["month","status"]).size().unstack(fill_value=0).reset_index()
    cov["nominal"]=[pd.Period(m).days_in_month*4 for m in cov.month];cov.to_csv(out/"coverage_by_month.csv",index=False)
    base=s[s.world=="E1"].copy();columns=["path_usdt","transient_usdt","temporary_usdt","fee_usdt","spread_usdt","shortfall_ex_funding_usdt",
        "shortfall_ex_funding_bps","full_cov_raw_risk_usdt_squared","full_cov_risk_preference_usdt"]
    decomposition=base.groupby("policy")[columns].mean().reset_index()
    for col in columns[:5]:decomposition[col.replace("usdt","bps")]=base.assign(value=1e4*base[col]/base.W_usdt).groupby("policy").value.mean().reindex(decomposition.policy).to_numpy()
    decomposition.to_csv(out/"E1_policy_decomposition.csv",index=False)
    assetrows=[]
    for asset in ("btc","eth"):
        for p,g in base.groupby("policy"):
            assetrows.append(dict(asset=asset,policy=p,mean_shortfall_ex_funding_usdt=float(g[f"{asset}_shortfall_ex_funding_usdt"].mean()),
                mean_shortfall_ex_funding_bps=float((1e4*g[f"{asset}_shortfall_ex_funding_usdt"]/g[f"{asset}_initial_usdt"]).mean())))
    pd.DataFrame(assetrows).to_csv(out/"E1_per_asset_costs.csv",index=False)
    regret=[]
    for w,g in s.groupby("world"):
        pivot=g.pivot(index="episode_id",columns="policy",values="shortfall_ex_funding_bps")
        r=pivot.T4-pivot.min(axis=1)
        regret.append(dict(world=w,episodes=len(pivot),maximum_T4_regret_bps=float(r.max()),mean_T4_regret_bps=float(r.mean()),
            T4_underperforms_T3_share=float((pivot.T4>pivot.T3).mean()),T4_underperforms_T3B_share=float((pivot.T4>pivot.T3B).mean())))
    pd.DataFrame(regret).to_csv(out/"adverse_world_regret.csv",index=False)
    lockpath=root/"configs/stage05_pretest_lock_v2.yaml"
    import yaml
    locked=yaml.safe_load(lockpath.read_text());threshold=locked["regime_thresholds"]
    s["liquidity_tercile"]=np.array(["low","middle","high"])[np.searchsorted(threshold["liquidity_initial_portfolio_usdt"],s.past_liquidity_usdt)]
    s["volatility_tercile"]=np.array(["low","middle","high"])[np.searchsorted(threshold["volatility_equal_log_return_sum_std_per_minute"],s.past_volatility)]
    regimes=[]
    for name in ("weekend","liquidity_tercile","volatility_tercile"):
        for label,group in s.groupby(name):
            table,_=contrasts(group);table=table[table.group=="all"].copy();table["regime_type"]=name;table["regime"]=str(label);regimes.append(table)
    pd.concat(regimes,ignore_index=True).to_csv(out/"regime_contrasts.csv",index=False)
    modelrows=[]
    for path in sorted((out/"models").glob("*.json")):
        m=json.loads(path.read_text())
        if m["role"]=="N0":continue
        l=np.array(m["liquidity_usdt"])
        for k,(tau,a) in enumerate(zip(m["taus_minutes"],np.array(m["matrices"]))):
            eig=np.linalg.eigvalsh(a)
            modelrows.append(dict(month=m["origin"][:7],role=m["role"],component=k,tau_minutes=tau,C00=a[0,0],C01=a[0,1],C11=a[1,1],
                eigen_min=eig[0],eigen_max=eig[-1],L_btc=l[0],L_eth=l[1],btc_self_100k_bps=a[0,0]*1e5/l[0],
                eth_self_100k_bps=a[1,1]*1e5/l[1],cross_100k_bps=a[0,1]*1e5/np.sqrt(l.prod()),training_start=m["training_start"],
                training_end_exclusive=m["training_end_exclusive"],training_rows=m["training_rows"],file_sha256=sha256(path)))
    pd.DataFrame(modelrows).to_csv(out/"asof_model_registry.csv",index=False)
    qa=dict(nominal=len(c),scored_episodes=int((c.status=="SCORED").sum()),coverage_statuses=c.status.value_counts().to_dict(),score_rows=len(s),
        policy_count=s.policy.nunique(),world_count=s.world.nunique(),negative_cash_rows=int((s.shortfall_ex_funding_usdt<0).sum()),
        maximum_terminal_residual_usdt=float(s.terminal_max_usdt.max()),maximum_normalized_primal_residual=float(s.normalized_physical_residual.max()),
        maximum_stationarity=float(s.stationarity.max()),maximum_decomposition_residual=float(s.decomposition_residual.max()),
        maximum_realized_participation=float(s.max_realized_participation.max()) if np.isfinite(s.max_realized_participation.max()) else "inf",
        zero_volume_cells_with_repetition_across_worlds=int(s.zero_realized_volume_cells.sum()),
        participation_over10pct_cells_E1=int(base.realized_participation_over_10pct_cells.sum()),funding_included=False,all_in_estimated=False)
    save(out/"oos_qa.json",qa)
    primaryfiles=["primary_h2_contrasts.csv","h1_metrics.csv","h1_paired_effects.csv","coverage_by_month.csv","E1_policy_decomposition.csv","adverse_world_regret.csv"]
    pindex=out/"primary_statistics_index.json"
    frozen={n:sha256(out/n) for n in primaryfiles}
    if pindex.exists():
        if json.loads(pindex.read_text())["sha256"]!=frozen:raise RuntimeError("Primary statistics changed after indexing")
    else:save(pindex,dict(status="PRIMARY_STATISTICS_FROZEN",utc=utcnow(),sha256=frozen))
    if not primary_only and (out/"robustness_index.json").exists():
        frames=[];fail=[]
        for m in months:
            folder=bulk/"robustness"/m;frames.append(pd.read_parquet(folder/"scores.parquet"));fail.extend(json.loads((folder/"failures.json").read_text()))
        robust=pd.concat(frames,ignore_index=True);tables=[]
        for variant,g in robust.groupby("variant"):
            table,_=contrasts(g);table["variant"]=variant;tables.append(table)
        rt=pd.concat(tables,ignore_index=True);rt.to_csv(out/"robustness_contrasts.csv",index=False);save(out/"robustness_failures.json",fail)
        linear=rt[(rt.group=="all")&rt.variant.str.match("fee_bps_|half_spread_bps_")]
        reference=effects[effects.group=="all"].set_index(["world","baseline"])
        discrepancy=max([abs(row.mean_delta_ex_funding_bps-reference.loc[(row.world,row.baseline),"mean_delta_ex_funding_bps"]) for row in linear.itertuples()] or [0])
        save(out/"robustness_qa.json",dict(rows=len(robust),variants=robust.variant.nunique(),failures=len(fail),linear_fee_spread_delta_invariance_max_bps=discrepancy))
    h1all=h1effects[(h1effects.group=="all")&(h1effects.asset=="pooled")].iloc[0]
    h2=effects[(effects.world=="E1")&(effects.baseline=="T3")&(effects.group=="all")].iloc[0]
    verdict=dict(stage="G4 OOS COMPLETE" if qa["scored_episodes"]==724 and (out/"robustness_index.json").exists() else "STAGE5_PARTIAL",
        implementation="PASS" if qa["scored_episodes"]==724 else "QUALIFIED",cost_scope=SCOPE,
        H1="SUPPORTS_HYPOTHESIS" if h1all.delta_fit>=.005 and h1all.loss_difference_ci_low>0 else "DOES_NOT_SUPPORT" if h1all.delta_fit<.005 else "INCONCLUSIVE",
        H2="SUPPORTS_HYPOTHESIS" if h2.mean_delta_ex_funding_bps>=.1 and h2.ci_low>0 else "DOES_NOT_SUPPORT" if h2.mean_delta_ex_funding_bps<.1 and h2.ci_high<.1 else "INCONCLUSIVE",
        H1_delta_fit=float(h1all.delta_fit),H2_E1_mean_bps=float(h2.mean_delta_ex_funding_bps),H2_E1_CI=[float(h2.ci_low),float(h2.ci_high)],
        adverse_world_means_negative=int(((effects.group=="all")&(effects.baseline=="T3")&(effects.world!="E0")&(effects.mean_delta_ex_funding_bps<0)).sum()),
        stage6_started=False,nominal=724,scored=qa["scored_episodes"],pretest_lock_sha256=sha256(lockpath))
    save(out/"verdict_v2.json",verdict)
    return verdict
