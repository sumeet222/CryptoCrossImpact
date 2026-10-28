"""Chronological immutable decisions → shared-world ex-funding scoring."""
from dataclasses import replace
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd

from ..data.storage import sha256,utcnow
from ..episodes import EpisodeUnavailable
from ..execution.policies import generate_policies,POLICIES
from .v2_common import locations,config,policy_config,digest,save,clean,SCOPE
from .v2_data import HistoricalStore,utc
from .v2_features import make_episode,EpisodeV2
from .v2_fit import Fitter,policy_models,validate_fit,fixed_policy_models
from .v2_score import worlds,evaluation_prices,score_schedule


def episode_calendar(start,end):
    return pd.date_range(start,end,freq="6h",inclusive="left")


def write_decision(path,record,existing=None):
    path=Path(path);data=clean(record);payload=json.dumps(data,sort_keys=True,separators=(",",":"),allow_nan=False).encode()+b"\n"
    identity=digest(data)
    key=record.get("decision_key",record["episode_id"])
    if existing and key in existing:
        receipt=existing[key]
        if digest(verify_receipt(receipt))!=identity:raise RuntimeError("Immutable decision replay changed; do not overwrite")
        return receipt
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("ab") as f:
        offset=f.tell();f.write(payload);f.flush();os.fsync(f.fileno())
    return dict(path=str(path),offset=offset,bytes=len(payload),sha256=identity)


def verify_receipt(receipt):
    if not isinstance(receipt,dict) or not {"path","offset","bytes","sha256"}<=receipt.keys():raise ValueError("Persisted decision receipt required")
    with Path(receipt["path"]).open("rb") as f:f.seek(receipt["offset"]);raw=f.read(receipt["bytes"])
    data=json.loads(raw)
    if digest(data)!=receipt["sha256"]:raise ValueError("Decision receipt hash mismatch")
    return data


def receipts(path):
    result={};path=Path(path)
    if path.exists():
        with path.open("rb") as f:
            while True:
                offset=f.tell();line=f.readline()
                if not line:break
                data=json.loads(line);receipt=dict(path=str(path),offset=offset,bytes=len(line),sha256=digest(data))
                key=data.get("decision_key",data["episode_id"])
                if key in result:raise ValueError("Duplicate immutable decision")
                result[key]=receipt
    return result


def verify_closed_month(root,end):
    end=utc(end);month=(end-pd.Timedelta(days=1)).strftime("%Y-%m")
    _,bulk=locations(root);folder=bulk/"primary"/month
    record=json.loads((folder/"decisions_closed.json").read_text())
    if record["decision_file_sha256"]!=sha256(folder/"decisions.jsonl") or record["nominal"]!=pd.Period(month).days_in_month*4:
        raise ValueError("Month outcome-feature read before all immutable decisions")


def protocol_ids(root):
    root=Path(root);out,_=locations(root)
    ids=dict(spec_sha256=sha256(root/"CryptoCrossImpact_Research_Specification_v1_2026-10-27.md"),
        config_sha256=sha256(root/"configs/stage05_evaluation_v2.yaml"),source_manifest_sha256=sha256(root/"data/registry/source_manifest.json"),
        source_id="Binance/futures/um/BTCUSDT+ETHUSDT/1m")
    if (out/"pretest_ready_v2.json").exists():
        ids.update(pretest_ready_sha256=sha256(out/"pretest_ready_v2.json"),pretest_lock_sha256=sha256(root/"configs/stage05_pretest_lock_v2.yaml"))
        import yaml
        locked=yaml.safe_load((root/"configs/stage05_pretest_lock_v2.yaml").read_text())
        ids["code_binding_sha256"]=digest({k:v for k,v in locked["bindings"].items() if k.startswith("src/") or k.startswith("scripts/")})
    return ids


def snapshot(e,paths,qa,models,world_list,cfg,variant,bindings=None):
    return dict(episode_id=e.episode_id,t0=str(e.t0),horizon_minutes=len(e.forecast),variant=variant,status="DECISIONS_FROZEN",
        forecast=e.forecast,initial=e.initial,p0=e.p0,covariance=e.covariance,input_provenance=e.provenance,input_hash=e.input_hash,
        caps=e.forecast*cfg["cap_fraction"],policy_config=cfg,schedules={p:d["sales"] for p,d in paths.items()},policy_qa=qa,
        models={p:dict(id=m.model_id,hash=m.model_hash,fit_end_exclusive=str(m.training_end)) for p,m in models.items()},
        world_hashes={w.world_id:w.world_hash for w in world_list},cost_scope=SCOPE,provenance_hashes=bindings or {})


def reconstruct(data):
    return EpisodeV2(data["episode_id"],utc(data["t0"]),data["forecast"],data["covariance"],data["initial"],data["p0"],data["input_provenance"])


def score_decision(data,frame,world_list,receipt_hash,proxy="close"):
    e=reconstruct(data);prices,real=evaluation_prices(frame,e.t0,len(e.forecast),proxy)
    qa={r["policy"]:r for r in data["policy_qa"]};rows=[]
    for world in world_list:
        if data["world_hashes"][world.world_id]!=world.world_hash:raise ValueError("Wrong common evaluator identity")
        for p in POLICIES:
            z=np.array(data["schedules"][p]);q=qa[p]
            row=score_schedule(z,e.initial,e.forecast,e.p0,prices,real,world,data["policy_config"]["fee_bps"],data["policy_config"]["half_spread_bps"])
            row.update(episode_id=e.episode_id,t0=str(e.t0),day=str(e.t0.date()),month=e.t0.strftime("%Y-%m"),policy=p,variant=data["variant"],
                status="PASS",decision_hash=receipt_hash,input_hash=e.input_hash,model_id=q["model_id"],model_hash=q["model_hash"],
                fit_end_exclusive=q["fit_end_exclusive"],full_cov_raw_risk_usdt_squared=q["full_cov_raw_risk_usdt_squared"],
                full_cov_risk_preference_usdt=q["full_cov_risk_preference_usdt"],beta=q["beta"],price_proxy=proxy,
                past_liquidity_usdt=float(e.forecast.sum()*.02),
                past_volatility=float(np.sqrt(np.array(e.covariance).sum())),weekend=e.t0.day_of_week>=5,
                terminal_max_usdt=q["terminal_max_usdt"],normalized_physical_residual=q["normalized_physical_residual"],
                stationarity=q["stationarity"],decomposition_residual=q["decomposition_residual"])
            row.update(data.get("provenance_hashes",{}));row["canonical_ids"]=f"BTCUSDT/{e.t0.strftime('%Y-%m')};ETHUSDT/{e.t0.strftime('%Y-%m')}"
            rows.append(row)
    return rows


def run_month(root,month,fitter,store,pretest=False):
    out,bulk=locations(root);folder=bulk/("development_smoke_v2_final" if pretest else "primary")/month;folder.mkdir(parents=True,exist_ok=True)
    checkpoint=folder/"checkpoint.json";start=pd.Timestamp(month+"-01",tz="UTC");end=start+pd.offsets.MonthBegin(1)
    if checkpoint.exists():
        saved=json.loads(checkpoint.read_text())
        for name,h in saved["output_sha256"].items():
            if sha256(folder/name)!=h:raise RuntimeError("Completed month changed")
        if not pretest:fitter.restore_month(month)
        return saved
    models={role:fitter.fit(start,role,out/("pretest_models" if pretest else "models")) for role in ("A","B","N0","E1")}
    pm=policy_models(models,start);e1=validate_fit(models["E1"],start,"E1");world_list=worlds(e1,pm["B"].kernel)
    save(folder/"asof_registry.json",dict(origin=str(start),fit_hashes={r:digest(m) for r,m in models.items()},
        world_hashes={w.world_id:w.world_hash for w in world_list},all_fits_saved_before_scoring=True))
    existing=receipts(folder/"decisions.jsonl");rows=[];coverage=[];cfg=policy_config(root);bindings=protocol_ids(root)
    times=episode_calendar(start,start+pd.Timedelta(days=2) if pretest else end)
    for index,t0 in enumerate(times):
        episode_id=t0.strftime("%Y%m%dT%H%MZ");base=dict(episode_id=episode_id,t0=str(t0),horizon_minutes=60,variant="primary",cost_scope=SCOPE)
        try:
            history=store.paired(t0-pd.Timedelta(days=28),t0,purpose="decision",asof=t0)
            e=make_episode(history,t0,cfg)
        except EpisodeUnavailable as exc:
            data={**base,"status":"INPUT_QC_EXCLUDED","reason":str(exc)};write_decision(folder/"decisions.jsonl",data,existing)
            coverage.append({**base,"status":data["status"],"reason":str(exc)});continue
        try:p,qa=generate_policies(e,pm,cfg)
        except (ValueError,RuntimeError) as exc:
            data={**base,"status":"POLICY_SET_FAILURE","reason":str(exc)};write_decision(folder/"decisions.jsonl",data,existing)
            coverage.append({**base,"status":data["status"],"reason":str(exc)});continue
        data=snapshot(e,p,qa,pm,world_list,cfg,"primary",bindings);receipt=write_decision(folder/"decisions.jsonl",data,existing)
        try:
            future=store.paired(t0,t0+pd.Timedelta(minutes=60),purpose="score",receipt=receipt)
            scored=score_decision(verify_receipt(receipt),future,world_list,receipt["sha256"])
        except ValueError as exc:
            if not str(exc).startswith("EVALUATION_QC"):raise
            coverage.append({**base,"status":"STRUCTURAL_EVALUATION_QC_EXCLUDED","reason":str(exc)});continue
        rows.extend(scored);coverage.append({**base,"status":"SCORED","reason":""})
        if (index+1)%40==0:print(f"Primary {month}: {index+1}/{len(times)} immutable episode sets",flush=True)
    pd.DataFrame(coverage).to_csv(folder/"coverage.csv",index=False)
    pd.DataFrame(rows).to_parquet(folder/"scores.parquet",index=False)
    save(folder/"decisions_closed.json",dict(nominal=len(times),decision_file_sha256=sha256(folder/"decisions.jsonl"),closed_utc=utcnow()))
    frame,x,y,valid=fitter.observe_month(month)
    daily=fitter.h1(frame,x,y,valid,models)
    for row in daily:row.update(bindings)
    pd.DataFrame(daily).to_csv(folder/"h1_daily.csv",index=False)
    save(folder/"io_audit.json",store.read_log);store.read_log.clear()
    result=dict(month=month,nominal=len(times),scored=sum(c["status"]=="SCORED" for c in coverage),
        statuses=pd.Series([c["status"] for c in coverage]).value_counts().to_dict(),score_rows=len(rows),cost_scope=SCOPE,
        output_sha256={n:sha256(folder/n) for n in ["scores.parquet","decisions.jsonl","decisions_closed.json","h1_daily.csv","coverage.csv","asof_registry.json"]})
    save(checkpoint,result);return result


def primary(root,pretest=False):
    store=HistoricalStore(root);fitter=Fitter(root,store)
    months=["2025-09"] if pretest else list(pd.period_range("2026-01","2026-06",freq="M").astype(str))
    if not pretest:
        from .v2_protocol import validate_ready
        validate_ready(root)
    results=[run_month(root,m,fitter,store,pretest) for m in months]
    out,bulk=locations(root)
    if not pretest:
        save(out/"primary_index.json",dict(status="PRIMARY_FROZEN",months=results,cost_scope=SCOPE,
            ready_sha256=sha256(out/"pretest_ready_v2.json"),indexed_utc=utcnow()))
    return results


def robustness(root):
    """Predeclared OFAT decisions; common E1/E2 only, after primary index."""
    from .v2_protocol import validate_ready
    validate_ready(root);out,bulk=locations(root)
    index=json.loads((out/"primary_index.json").read_text())
    if index["status"]!="PRIMARY_FROZEN":raise ValueError("Freeze primary before sensitivities")
    store=HistoricalStore(root);cfg0=policy_config(root);variants=config(root)["decision_sensitivities"];bindings=protocol_ids(root)
    fixed=fixed_policy_models(root)
    for entry in index["months"]:
        month=entry["month"];folder=bulk/"robustness"/month;folder.mkdir(parents=True,exist_ok=True)
        checkpoint=folder/"checkpoint.json"
        if checkpoint.exists():
            saved=json.loads(checkpoint.read_text())
            for n,h in saved["output_sha256"].items():
                if sha256(folder/n)!=h:raise RuntimeError("Robustness checkpoint changed")
            continue
        origin=pd.Timestamp(month+"-01",tz="UTC");models={r:json.loads((out/"models"/f"{month}_{r}.json").read_text()) for r in ("A","B","E1")}
        pm=policy_models(models,origin);e1=validate_fit(models["E1"],origin,"E1")
        world_cache={n:[w for w in worlds(e1,pm["B"].kernel,n) if w.world_id in ("E1","E2")] for n in (30,60,120)}
        original=receipts(bulk/"primary"/month/"decisions.jsonl");existing=receipts(folder/"decisions.jsonl")
        rows=[];fails=[]
        for i,(eid,receipt0) in enumerate(original.items()):
            original_data=verify_receipt(receipt0)
            if original_data["status"]!="DECISIONS_FROZEN":continue
            e0=reconstruct(original_data);t0=e0.t0;history=None
            for variant,change in variants.items():
                cfg={**cfg0,**{k:v for k,v in change.items() if k in cfg0}};n=cfg["horizon_minutes"]
                if n!=60:
                    if history is None:history=store.paired(t0-pd.Timedelta(days=28),t0,purpose="decision",asof=t0)
                    e=make_episode(history,t0,cfg)
                else:e=replace(e0,initial=e0.forecast.sum(axis=0)*cfg["initial_fraction"])
                if "fixed_notional_per_leg" in change:e=replace(e,initial=np.full(2,change["fixed_notional_per_leg"],dtype=float))
                selected=fixed if change.get("frozen_calibration") else pm
                try:p,qa=generate_policies(e,selected,cfg)
                except (ValueError,RuntimeError) as exc:
                    fails.append(dict(episode_id=eid,variant=variant,status="INFEASIBLE_OR_POLICY_FAILURE",reason=str(exc)));continue
                data=snapshot(e,p,qa,selected,world_cache[n],cfg,variant,bindings)
                # Use a variant-qualified key for one shared monthly log.
                data["decision_key"]=eid+"_"+variant
                receipt=write_decision(folder/"decisions.jsonl",data,existing)
                future=store.paired(t0,t0+pd.Timedelta(minutes=n),purpose="score",receipt=receipt)
                rows.extend(score_decision(verify_receipt(receipt),future,world_cache[n],receipt["sha256"]))
            # Score-only proxy/linear-cost sensitivities keep primary schedules.
            ws=world_cache[60];f=store.paired(t0,t0+pd.Timedelta(minutes=60),purpose="score",receipt=receipt0)
            for proxy in ("open","ohlc"):
                data={**original_data,"variant":"price_"+proxy,"world_hashes":{w.world_id:w.world_hash for w in ws}}
                rows.extend(score_decision(data,f,ws,receipt0["sha256"],proxy))
            for parameter,values in [("fee_bps",[2,10]),("half_spread_bps",[0,2])]:
                for value in values:
                    data={**original_data,"variant":f"{parameter}_{value}","policy_config":{**cfg0,parameter:value},"world_hashes":{w.world_id:w.world_hash for w in ws}}
                    rows.extend(score_decision(data,f,ws,receipt0["sha256"]))
            if (i+1)%40==0:print(f"Robustness {month}: {i+1}/{len(original)} arrivals, all fixed OFAT variants",flush=True)
        pd.DataFrame(rows).to_parquet(folder/"scores.parquet",index=False)
        save(folder/"failures.json",fails);save(folder/"io_audit.json",store.read_log);store.read_log.clear()
        save(checkpoint,dict(month=month,rows=len(rows),failures=len(fails),output_sha256={n:sha256(folder/n) for n in ["scores.parquet","decisions.jsonl","failures.json"]}))
    save(out/"robustness_index.json",dict(status="COMPLETE",primary_index_sha256=sha256(out/"primary_index.json"),variants=list(variants),cost_scope=SCOPE))
