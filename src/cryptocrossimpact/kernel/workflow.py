"""Reproducible development fits and compact artifacts; no test outcomes read."""
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from ..data.pipeline import provenance, load_config as core_config
from ..data.storage import sha256, utcnow, write_json
from .features import ASSETS, DevelopmentStore, batches, feature_names, metadata
from .fit import Stats, transforms, normalize, columns, estimate, loss, predict, finite_grid_check


def config(root):
    return yaml.safe_load((Path(root)/"configs/stage02_kernel.yaml").read_text())


def locations(root):
    root=Path(root); cfg=config(root)
    out=root/cfg["output"];out.mkdir(parents=True,exist_ok=True)
    cache=root/"results/kernel_development";cache.mkdir(parents=True,exist_ok=True)
    return out,cache


def save_stats(path, records):
    keys=list(records)
    np.savez_compressed(path,keys=np.array(keys), n=np.array([records[k].n for k in keys]),
        gram=np.stack([records[k].gram for k in keys]),xy=np.stack([records[k].xy for k in keys]),yy=np.stack([records[k].yy for k in keys]))


def read_stats(path):
    with np.load(path,allow_pickle=False) as d:
        return {str(k): Stats(int(d["n"][i]),d["gram"][i],d["xy"][i],d["yy"][i]) for i,k in enumerate(d["keys"])}


def total(records, predicate=lambda key:True):
    first=next(iter(records.values())); result=Stats.zeros(len(first.xy))
    for key,stats in records.items():
        if predicate(key): result.add(stats)
    return result


def make_provenance(root, store, cfg):
    result=provenance(Path(root),core_config(Path(root)))
    result.update(stage="G2 development only",stage02_config_sha256=sha256(Path(root)/"configs/stage02_kernel.yaml"),
        primary_paper_path="references/2403.10273v2.pdf",primary_paper_sha256=sha256(Path(root)/"references/2403.10273v2.pdf"),
        source_manifest_sha256=sha256(Path(root)/"data/registry/source_manifest.json"),
        development_partition_ids=sorted(set(store.read_log)),canonical_sha256={str(p.relative_to(root)):h for p,h in store.verified.items()},
        data_latest_open_utc="2025-12-31T23:59:00+00:00", final_outcome_scoring_performed=False)
    return result


def prepare(root, memory=None, mode="primary", suffix=""):
    cfg=config(root);out,cache=locations(root);store=DevelopmentStore(root)
    liquidity=store.liquidity()
    p=1+len(feature_names())+2*len(cfg["decays_minutes"])
    monthly,daily,coverage={}, {}, []
    for month,frame,x,y,valid in batches(store,liquidity,cfg["decays_minutes"],memory or cfg["memory_minutes"],mode):
        monthly[month]=Stats.rows(x[valid],y[valid])
        dates=pd.DatetimeIndex(frame.time).strftime("%Y-%m-%d")
        for day in np.unique(dates):
            mask=valid & (dates==day)
            daily[str(day)]=Stats.rows(x[mask],y[mask])
        target_valid=frame.valid_return_0 & frame.valid_return_1
        coverage.append(dict(month=month,split="train" if month<"2025-07" else "validation",source_rows=len(frame),eligible=int(valid.sum()),
            unavailable_target=int((~target_valid).sum()),unavailable_history_or_mode=int((target_valid & ~valid).sum()),
            retained_zero_volume_btc=int((frame.quote_volume_0.eq(0)&valid).sum()),
            retained_zero_volume_eth=int((frame.quote_volume_1.eq(0)&valid).sum()),
            retained_stale_btc=int((frame.stale_close_flag_0&valid).sum()),retained_stale_eth=int((frame.stale_close_flag_1&valid).sum())))
        print(f"Features {mode} H={memory or cfg['memory_minutes']} {month}: {valid.sum():,}/{len(frame):,}",flush=True)
    train=total(monthly,lambda k:k<"2025-07")
    normal=transforms(train)
    save_stats(cache/f"monthly{suffix}.npz",monthly);save_stats(cache/f"daily{suffix}.npz",daily)
    write_json(out/f"features{suffix}.json",dict(liquidity_usdt=liquidity.tolist(),liquidity_cutoff="2025-07-01T00:00:00Z exclusive",
        normalization=normal,all_taus=cfg["decays_minutes"],memory_minutes=memory or cfg["memory_minutes"],mode=mode,
        common_return_factor="omitted: .5*(BTC_lag1+ETH_lag1) is exactly redundant",feature_metadata=metadata(),
        primary_flow="observed same-bar q; available only after bar completion; conditional response, not forecast",
        coverage=coverage,provenance=make_provenance(root,store,cfg)))
    pd.DataFrame(coverage).to_csv(out/f"sample_coverage{suffix}.csv",index=False)
    return monthly,daily,normal,liquidity


def load_prepared(root,suffix=""):
    out,cache=locations(root)
    f=json.loads((out/f"features{suffix}.json").read_text())
    return read_stats(cache/f"monthly{suffix}.npz"),read_stats(cache/f"daily{suffix}.npz"),f


def select_winner(models,tie=.001):
    best=min(m["validation_mse_pooled"] for m in models)
    tied=[m for m in models if m["validation_mse_pooled"] <= best/(1-tie)]
    # A fixed lexicographic preference after the 0.1% practical tie band.
    return min(tied,key=lambda m:(len(m["taus_minutes"]),-m["ridge"],m["validation_mse_pooled"],m["taus_minutes"]))


def fit_grid(root):
    cfg=config(root);out,_=locations(root)
    monthly,_,f=load_prepared(root);normal=f["normalization"]
    training=normalize(total(monthly,lambda k:k<"2025-07"),normal)
    validation=normalize(total(monthly,lambda k:k>="2025-07"),normal)
    winners={}; attempted=[]; all_models={name:[] for name in ("N0","U","A","B")}
    families=[(5,),(5,30)]+[(t,) for t in cfg["decays_minutes"]]+list(itertools.combinations(cfg["decays_minutes"],2))
    families=list(dict.fromkeys(families))
    for name in ("N0","U","A","B"):
        for taus in ([()] if name=="N0" else families):
            for ridge in cfg["ridge"]:
                try:
                    m=estimate(training,normal,taus,cfg["decays_minutes"],name,ridge,cfg["solver"])
                    vs=validation.subset(m["indices"])
                    vm=loss(vs,np.array(m["theta_standardized"]))
                    m.update(validation_mse=vm.tolist(),validation_mse_pooled=float(vm.mean()),
                        liquidity_usdt=f["liquidity_usdt"],asset_order=ASSETS,memory_minutes=cfg["memory_minutes"],
                        training_start="2024-01-01",training_end_exclusive="2025-07-01",validation_start="2025-07-01",validation_end_exclusive="2026-01-01",
                        provenance=f["provenance"],return_basis="G(0) current; G(l)-G(l-1) lags 1..H; no H+1 tail term")
                    if name in ("A","B"): m["finite_grid_check"]=finite_grid_check(m)
                    all_models[name].append(m)
                    row=dict(model=name,taus_minutes=";".join(map(str,taus)),ridge=ridge,status=m["status"],solver=m["solver"],objective=m["objective"],
                        train_rows=training.n,validation_rows=validation.n,train_mse_btc=m["standardized_training_mse"][0],train_mse_eth=m["standardized_training_mse"][1],
                        validation_mse_btc=float(vm[0]),validation_mse_eth=float(vm[1]),validation_mse_pooled=float(vm.mean()),
                        minimum_component_eigenvalue=min([min(d["eigenvalues"]) for d in m["component_diagnostics"]],default=None))
                except Exception as error:
                    row=dict(model=name,taus_minutes=";".join(map(str,taus)),ridge=ridge,status="FAILED",error=f"{type(error).__name__}: {error}")
                attempted.append(row)
            pd.DataFrame(attempted).to_csv(out/"candidate_selection.csv",index=False)
            print(f"Grid {name} tau={taus}: {len(attempted)} total candidates",flush=True)
        if not all_models[name]: raise RuntimeError(f"No valid {name} fit")
        winner=select_winner(all_models[name],cfg["tie_relative_mse"])
        winners[name]=winner
        write_json(out/f"model_{name}.json",winner)
    write_json(out/"selection.json",dict(status="PASS",attempted=len(attempted),failed=sum(r["status"]=="FAILED" for r in attempted),
        search_budget={k:len(v) for k,v in all_models.items()},screening="none; all 15 families and six penalties for U/A/B",
        tie_rule="Within 0.1% relative MSE: fewer components, then stronger ridge, then MSE",selected={k:dict(taus_minutes=m["taus_minutes"],ridge=m["ridge"],validation_mse=m["validation_mse"]) for k,m in winners.items()}))
    return winners


def winners(root):
    out,_=locations(root)
    return {k:json.loads((out/f"model_{k}.json").read_text()) for k in ("N0","U","A","B")}


def prediction_metrics(root):
    cfg=config(root);out,_=locations(root);models=winners(root)
    store=DevelopmentStore(root);liquidity=np.array(models["B"]["liquidity_usdt"])
    ys=np.array(models["B"]["normalization"]["target_scale"])
    groups={};activity_values=[]
    for month,frame,x,y,valid in batches(store,liquidity,cfg["decays_minutes"]):
        if month<"2025-07":
            at=1+feature_names().index("activity_0_60")
            et=1+feature_names().index("activity_1_60")
            activity_values.append((x[valid,at]+x[valid,et])/2)
    threshold=float(np.median(np.concatenate(activity_values)))
    at=1+feature_names().index("activity_0_60");et=1+feature_names().index("activity_1_60")
    for month,frame,x,y,valid in batches(store,liquidity,cfg["decays_minutes"]):
        split="train" if month<"2025-07" else "validation"
        sets={split:valid,f"month:{month}":valid}
        if split=="validation":
            weekend=pd.DatetimeIndex(frame.time).day_of_week>=5
            high=(x[:,at]+x[:,et])/2>=threshold
            sets.update({"validation_weekend":valid&weekend,"validation_weekday":valid&~weekend,
                         "validation_liquidity_high":valid&high,"validation_liquidity_low":valid&~high})
        for name,m in models.items():
            pred=predict(m,x)
            for group,mask in sets.items():
                e=(y[mask]-pred[mask])/ys
                target=y[mask]/ys
                if not len(e):continue
                key=(group,name)
                if key not in groups:groups[key]=dict(n=0,sse=np.zeros(2),sae=np.zeros(2),ysum=np.zeros(2),y2=np.zeros(2),esum=np.zeros(2),ee=np.zeros((2,2)))
                g=groups[key];g["n"]+=len(e);g["sse"]+=np.sum(e*e,axis=0);g["sae"]+=np.abs(e).sum(axis=0)
                g["ysum"]+=target.sum(axis=0);g["y2"]+=(target*target).sum(axis=0);g["esum"]+=e.sum(axis=0);g["ee"]+=e.T@e
    rows=[]
    for (group,name),g in groups.items():
        mse=g["sse"]/g["n"];mae=g["sae"]/g["n"]
        cov=g["ee"]/g["n"]-np.outer(g["esum"]/g["n"],g["esum"]/g["n"])
        corr=float(cov[0,1]/np.sqrt(cov[0,0]*cov[1,1]))
        r2=1-g["sse"]/(g["y2"]-g["ysum"]**2/g["n"])
        for j,asset in enumerate(ASSETS):
            rows.append(dict(group=group,model=name,asset=asset,rows=g["n"],standardized_mse=mse[j],mae_bps=mae[j]*ys[j]/np.sqrt(liquidity[j]),
                rmse_bps=np.sqrt(mse[j])*ys[j]/np.sqrt(liquidity[j]),conditional_response_r2=r2[j],residual_cross_correlation=corr))
        rows.append(dict(group=group,model=name,asset="pooled",rows=g["n"],standardized_mse=float(mse.mean()),mae_bps=float(np.mean(mae*ys/np.sqrt(liquidity))),
            rmse_bps=float(np.sqrt(np.mean(mse*ys**2/liquidity))),conditional_response_r2=float(r2.mean()),residual_cross_correlation=corr))
    pd.DataFrame(rows).to_csv(out/"fit_metrics.csv",index=False)
    write_json(out/"regime_definition.json",dict(liquidity_threshold=threshold,statistic="mean BTC/ETH log1p(mean preceding 60-minute USDT quote turnover)",
        threshold_estimated_on="2024-01–2025-06 only",applied_to="validation only",calendar_weekend="UTC Saturday/Sunday",future_data_used=False))
    return pd.DataFrame(rows)
