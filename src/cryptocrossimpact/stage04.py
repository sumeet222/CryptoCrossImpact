"""Thin development workflow: inputs, decisions, QA, protocol lock; no scorer."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data.storage import sha256,utcnow
from .episodes import Episode,EpisodeStore,EpisodeUnavailable,arrivals,config,construct_episode
from .execution.policies import POLICIES,prepare_models,load_models,generate_policies


def paths(root):
    root=Path(root);out=root/"reports/research/stage04_artifacts";bulk=root/"results/stage04_development"
    out.mkdir(parents=True,exist_ok=True);bulk.mkdir(parents=True,exist_ok=True)
    return out,bulk


def save(path,value):
    path.write_text(json.dumps(value,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x),allow_nan=False)+"\n")


def build(root,smoke=False):
    cfg=config(root);out,bulk=paths(root);store=EpisodeStore(root);records=[];excluded=[]
    times=arrivals(end="2025-07-03T00:00:00Z") if smoke else arrivals()
    for t0 in times:
        try:e=construct_episode(store.history(t0,cfg["history_days"]),t0,cfg)
        except EpisodeUnavailable as exc:
            excluded.append(dict(t0=str(t0),reason=str(exc)));continue
        records.append(dict(episode_id=e.episode_id,t0=str(t0),input_hash=e.input_hash,forecast=e.forecast.tolist(),
            covariance=e.covariance.tolist(),initial=e.initial.tolist(),p0=e.p0.tolist(),provenance=e.provenance))
    # A single compact input table; no raw market-data replication per policy.
    suffix="smoke" if smoke else "development"
    pd.DataFrame({"episode_json":[json.dumps(r,sort_keys=True) for r in records]}).to_parquet(bulk/f"inputs_{suffix}.parquet",index=False)
    save(out/f"build_{suffix}.json",dict(nominal=len(times),eligible=len(records),excluded=excluded,
        partition_reads=store.read_log,unique_partitions=sorted(set(store.read_log)),
        input_table=f"results/stage04_development/inputs_{suffix}.parquet",sha256=sha256(bulk/f"inputs_{suffix}.parquet"),
        final_test_partitions_opened=0,source_manifest_sha256=sha256(Path(root)/"data/registry/source_manifest.json")))
    return records


def read_episodes(root,smoke=False):
    _,bulk=paths(root);suffix="smoke" if smoke else "development"
    records=[json.loads(s) for s in pd.read_parquet(bulk/f"inputs_{suffix}.parquet").episode_json]
    return [Episode(r["episode_id"],pd.Timestamp(r["t0"]),r["forecast"],r["covariance"],r["initial"],r["p0"],r["provenance"]) for r in records]


def policies(root,smoke=False):
    cfg=config(root);out,bulk=paths(root);episodes=read_episodes(root,smoke);summary=[];failures=[];chunks=[];geometry=[];fixed_rows=[]
    suffix="smoke" if smoke else "development";digest=hashlib.sha256();oldpath=out/f"policies_{suffix}.json"
    old=json.loads(oldpath.read_text()) if oldpath.exists() else None
    sensitivity=0;last_month=None
    for number,e in enumerate(episodes):
        month=e.t0.strftime("%Y-%m")
        if month!=last_month:models=load_models(root,month,e.t0);last_month=month
        try:result,rows=generate_policies(e,models,cfg)
        except (ValueError,RuntimeError) as exc:
            failures.append(dict(episode_id=e.episode_id,reason=str(exc),all_policies_common_exclusion=True));continue
        summary.extend(rows)
        for name in POLICIES:
            p=result[name];z=p["sales"];digest.update(e.episode_id.encode()+name.encode()+z.tobytes())
            chunks.append(pd.DataFrame(dict(episode_id=e.episode_id,policy=name,minute=np.arange(len(z)),
                btc_sales_usdt=z[:,0],eth_sales_usdt=z[:,1],btc_before_usdt=p["before"][:,0],eth_before_usdt=p["before"][:,1],
                btc_after_usdt=p["after"][:,0],eth_after_usdt=p["after"][:,1])))
        for contrast in ("T3","T3B"):
            z=result["T4"]["sales"];other=result[contrast]["sales"]
            geometry.append(dict(episode_id=e.episode_id,month=month,contrast=f"T4_vs_{contrast}",
                relative_rate_l2=float(np.linalg.norm(z-other)/np.linalg.norm(other)),
                maximum_inventory_difference_over_initial=float(np.max(np.abs(np.cumsum(z-other,axis=0))/e.initial))))
        # Fixed calendar rule, selected before reading schedule diagnostics.
        if e.t0.day_of_week==0 and e.t0.day<=7:
            fixed,fr=generate_policies(e,load_models(root,month,e.t0,fixed=True),cfg);sensitivity+=1
            for name in POLICIES:
                z=result[name]["sales"];q=fixed[name]["sales"]
                fixed_rows.append(dict(episode_id=e.episode_id,policy=name,relative_rate_l2=float(np.linalg.norm(z-q)/np.linalg.norm(q)),
                    maximum_inventory_difference_over_initial=float(np.max(np.abs(np.cumsum(z-q,axis=0))/e.initial))))
        if (number+1)%100==0:print(f"Development policies {number+1}/{len(episodes)}",flush=True)
    pd.DataFrame(summary).to_csv(out/f"policy_diagnostics_{suffix}.csv",index=False)
    pd.DataFrame(geometry).to_csv(out/f"schedule_geometry_{suffix}.csv",index=False)
    pd.DataFrame(fixed_rows,columns=["episode_id","policy","relative_rate_l2","maximum_inventory_difference_over_initial"]).to_csv(out/f"fixed_model_sensitivity_{suffix}.csv",index=False)
    if chunks:pd.concat(chunks,ignore_index=True).to_parquet(bulk/f"schedules_{suffix}.parquet",index=False)
    identity=digest.hexdigest();replay=None if old is None else identity==old["schedule_numeric_sha256"]
    result=dict(eligible_episodes=len(episodes),complete_episodes=len(episodes)-len(failures),policy_schedules=len(summary),
        scalar_and_joint_qp_solves=5*(len(episodes)-len(failures)),failures=failures,fixed_model_sensitivity_episodes=sensitivity,
        schedule_numeric_sha256=identity,deterministic_replay_matches_prior=replay,recorded_utc=utcnow(),
        no_future_price_costs=True,evaluators_run=[],test_outcomes_unopened=True)
    save(oldpath,result)
    if replay is False:raise RuntimeError("Deterministic replay changed; inspect before lock")
    return result


def smoke(root):
    prepare_models(root);build(root,True);return policies(root,True)
