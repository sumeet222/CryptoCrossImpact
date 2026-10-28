"""Paired full-calendar seven-day blocks, never IID episodes/minutes."""
import numpy as np
import pandas as pd


def block_indices(days,replicates=500,block=7,seed=20261027):
    if days<block:raise ValueError("Too few full calendar days")
    rng=np.random.default_rng(seed);starts=rng.integers(0,days-block+1,size=(replicates,(days+block-1)//block))
    return (starts[:,:,None]+np.arange(block)).reshape(replicates,-1)[:,:days]


def paired_interval(days,sums,counts,baseline_sums=None):
    """Row=every calendar day, including exclusions with count0; sum/count pooling."""
    sums=np.asarray(sums,dtype=float);counts=np.asarray(counts,dtype=float)
    if len(sums)!=len(days) or len(counts)!=len(days) or not np.isfinite(sums).all() or not np.isfinite(counts).all():raise ValueError("Calendar/aggregate mismatch")
    idx=block_indices(len(days));den=counts[idx].sum(axis=1);valid=den>0
    boot=np.divide(sums[idx].sum(axis=1),den,out=np.full(len(idx),np.nan),where=valid)
    point=float(sums.sum()/counts.sum()) if counts.sum()>0 else None
    answer=dict(mean=point,ci_low=float(np.nanquantile(boot,.025)) if valid.any() else None,
                ci_high=float(np.nanquantile(boot,.975)) if valid.any() else None,bootstrap_zero_eligible_replicates=int((~valid).sum()),
                replicates=500,block_calendar_days=7,eligible_observations=int(counts.sum()),calendar_days=len(days))
    if baseline_sums is not None:
        b=np.asarray(baseline_sums);base=np.divide(b[idx].sum(axis=1),den,out=np.full(len(idx),np.nan),where=valid)
        bp=float(b.sum()/counts.sum()) if counts.sum()>0 else np.nan
        stable=np.isfinite(bp) and bp>0 and valid.any() and np.nanquantile(base,.025)>0
        ratio=np.divide(boot,base,out=np.full(len(idx),np.nan),where=valid&(base>0))
        answer.update(relative_reduction=float(point/bp) if stable else None,
            relative_ci_low=float(np.nanquantile(ratio,.025)) if stable else None,relative_ci_high=float(np.nanquantile(ratio,.975)) if stable else None,
            relative_ratio_status="ESTIMATED" if stable else "UNDEFINED_BASELINE_NONPOSITIVE_OR_INTERVAL_CROSSES_ZERO")
    return answer


def contrasts(scores,start="2026-01-01",end="2026-07-01"):
    """One common world; pair on episode, preserve missing pairs/failures externally."""
    rows=[];daily_tables=[]
    keys=["episode_id","day","month","W_usdt"]
    for world,group in scores.groupby("world",sort=False):
        for baseline in ("T3","T3B"):
            a=group[group.policy==baseline].set_index("episode_id");b=group[group.policy=="T4"].set_index("episode_id")
            common=a.index.intersection(b.index);unmatched=len(a.index.union(b.index))-len(common)
            a=a.loc[common];b=b.loc[common]
            paired=pd.DataFrame(dict(day=a.day,month=a.month,delta_bps=a.shortfall_ex_funding_bps-b.shortfall_ex_funding_bps,
                delta_usdt=a.shortfall_ex_funding_usdt-b.shortfall_ex_funding_usdt,baseline_usdt=a.shortfall_ex_funding_usdt))
            groups=[("all",paired)]+[(m,d) for m,d in paired.groupby("month")]
            for label,part in groups:
                begin=pd.Timestamp(start) if label=="all" else pd.Timestamp(label+"-01")
                finish=pd.Timestamp(end) if label=="all" else begin+pd.offsets.MonthBegin(1)
                days=pd.date_range(begin,finish,freq="D",inclusive="left").strftime("%Y-%m-%d")
                d=part.groupby("day").agg(sums=("delta_bps","sum"),count=("delta_bps","size"),cash=("delta_usdt","sum"),base=("baseline_usdt","sum")).reindex(days,fill_value=0)
                ci=paired_interval(days,d.sums.to_numpy(),d["count"].to_numpy())
                ratio=paired_interval(days,d.cash.to_numpy(),d["count"].to_numpy(),d.base.to_numpy())
                rows.append(dict(world=world,baseline=baseline,group=label,paired_episodes=len(part),mean_delta_ex_funding_bps=ci.pop("mean"),
                    median_delta_bps=float(part.delta_bps.median()),q25_delta_bps=float(part.delta_bps.quantile(.25)),q75_delta_bps=float(part.delta_bps.quantile(.75)),
                    positive_share=float((part.delta_bps>0).mean()),negative_share=float((part.delta_bps<0).mean()),worst_episode_bps=float(part.delta_bps.min()),
                    mean_delta_usdt=float(part.delta_usdt.mean()),relative_reduction=ratio.get("relative_reduction"),
                    relative_ci_low=ratio.get("relative_ci_low"),relative_ci_high=ratio.get("relative_ci_high"),relative_ratio_status=ratio.get("relative_ratio_status"),
                    unmatched_episode_count=unmatched,**ci))
            for day,d in paired.groupby("day"):
                daily_tables.append(dict(world=world,baseline=baseline,day=day,n=len(d),sum_delta_bps=float(d.delta_bps.sum())))
    return pd.DataFrame(rows),pd.DataFrame(daily_tables)
