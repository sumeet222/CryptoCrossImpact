"""Six matched development policies. No future prices, volumes or evaluator API."""
from dataclasses import dataclass
import json
from pathlib import Path
import time

import numpy as np
import pandas as pd

from ..data.storage import sha256
from ..episodes import guard_arrival,utc
from ..kernel.diagnostics import refit_historical
from .impact_cost import ASSETS,UNITS,Kernel,load_stage02
from .solver import build_problem,solve_execution,capped_uniform_reference

POLICIES=("T0","T1","T2","T3","T3B","T4")


@dataclass(frozen=True)
class AsOfKernel:
    kernel: Kernel
    training_start: pd.Timestamp
    training_end: pd.Timestamp
    model_id: str
    model_hash: str

    def check(self,t0):
        if self.training_end>guard_arrival(t0):raise ValueError("Post-arrival fitted model")
        if self.training_start>=self.training_end:raise ValueError("Invalid fitted history")


def historical_kernel(model,month,source_hash):
    """Validate the smaller known Stage 2 refit schema without editing originals."""
    end=pd.Timestamp(month+"-01",tz="UTC");start=end-pd.Timedelta(days=365)
    if (model["model"] not in ("A","B") or model["status"]!="optimal" or model["diagnostic_only"] or
        model["execution_kernel_export_allowed"] is not True or tuple(model["asset_order"])!=ASSETS or model["units"]!=UNITS or
        utc(model["training_start"])!=start or utc(model["training_end_exclusive"])!=end or
        model["taus_minutes"]!=[60] or model["ridge"]!=1 or model["memory_minutes"]!=60):
        raise ValueError("Invalid as-of model identity/window/frozen family")
    kernel=Kernel(ASSETS,model["matrices"],model["taus_minutes"],model["liquidity_usdt"],model["model"],source_hash)
    if model["model"]=="A" and np.any(kernel.matrices[:,0,1]!=0):raise ValueError("A contains cross impact")
    return AsOfKernel(kernel,start,end,f"monthly-{month}-{model['model']}",source_hash)


def prepare_models(root):
    """Reuse six verified B refits; exercise fixed-family API for missing A fits.

    Models retain their OWN L. New artifacts stay in Stage 4; no Stage 2 file is
    rewritten. The June-end frozen models continue through load_stage02.
    """
    root=Path(root);folder=root/"reports/research/stage04_artifacts";folder.mkdir(exist_ok=True)
    prior=root/"reports/research/stage02_artifacts";records=[]
    source_hash=sha256(root/"data/registry/source_manifest.json")
    for month in pd.period_range("2025-07","2025-12",freq="M").astype(str):
        for name in ("A","B"):
            path=folder/f"model_{name}_{month}.json"
            original=prior/f"model_development_refit_{month}.json" if name=="B" else None
            if path.exists():bundle=json.loads(path.read_text());model=bundle["fit"]
            else:
                model=json.loads(original.read_text()) if original else refit_historical(root,month+"-01",model=name)
                bundle=dict(schema="stage04-asof-kernel-v1",fit=model,source_manifest_sha256=source_hash,
                    original_refit_path=str(original.relative_to(root)) if original else None,
                    original_refit_sha256=sha256(original) if original else None,
                    return_basis="G(0) current; G(l)-G(l-1) lags 1..H; no H+1 tail term",
                    selection_sha256=sha256(prior/"selection.json"),refit_api="kernel.diagnostics.refit_historical",
                    final_test_outcomes_unopened=True)
                path.write_text(json.dumps(bundle,indent=2)+"\n")
            if bundle["source_manifest_sha256"]!=source_hash:raise ValueError("Refit manifest changed")
            fit=historical_kernel(model,month,sha256(path))
            records.append(dict(month=month,model=name,path=str(path.relative_to(root)),sha256=sha256(path),
                fit_start=str(fit.training_start),fit_end_exclusive=str(fit.training_end),training_rows=model["training_rows"],
                L_btc=model["liquidity_usdt"][0],L_eth=model["liquidity_usdt"][1],
                C00=model["matrices"][0][0][0],C01=model["matrices"][0][0][1],C11=model["matrices"][0][1][1]))
    pd.DataFrame(records).to_csv(folder/"model_registry.csv",index=False)
    return records


def load_models(root,month,t0,fixed=False):
    t0=guard_arrival(t0)
    # Reject post-arrival origin/test-month paths BEFORE even opening JSON.
    origin=pd.Timestamp(month+"-01",tz="UTC")
    if origin>t0 or not "2025-07"<=month<="2025-12":raise ValueError("Post-arrival/test model refused before I/O")
    root=Path(root);out={}
    if fixed:
        for name in ("A","B"):
            k=load_stage02(root,name)
            out[name]=AsOfKernel(k,pd.Timestamp("2024-01-01",tz="UTC"),pd.Timestamp("2025-07-01",tz="UTC"),f"fixed-June-{name}",k.source_sha256)
    else:
        folder=root/"reports/research/stage04_artifacts"
        registry=pd.read_csv(folder/"model_registry.csv").set_index(["month","model"])
        for name in ("A","B"):
            path=folder/f"model_{name}_{month}.json";digest=sha256(path)
            if digest!=registry.loc[(month,name),"sha256"]:raise ValueError("Monthly kernel hash changed")
            bundle=json.loads(path.read_text())
            if bundle["schema"]!="stage04-asof-kernel-v1" or not bundle["final_test_outcomes_unopened"]:raise ValueError("Unknown refit schema")
            out[name]=historical_kernel(bundle["fit"],month,digest)
    for model in out.values():model.check(t0)
    return out


def without_cross(kernel):
    c=np.array([np.diag(np.diag(c)) for c in kernel.matrices])
    return Kernel(kernel.assets,c,kernel.taus_minutes,kernel.liquidity_usdt,"T3B B self only",kernel.source_sha256)


def forecast_vwap(initial,forecast,cap_fraction):
    """Forecast proportional allocation; if size>cap fraction it is infeasible.

    With common per-bin percentage caps, proportional targets either all satisfy
    caps or total capacity is insufficient. No hindsight denominator or repair.
    """
    z=forecast*(initial/forecast.sum(axis=0))
    if np.any(initial>cap_fraction*forecast.sum(axis=0)+1e-12*initial):
        from .solver import InfeasibleCapacity
        raise InfeasibleCapacity("Forecast VWAP exceeds total forecast capacity")
    return z


def generate_policies(episode,models,cfg):
    """Shared full-covariance beta, ex-ante inputs and complete physical checks.

    T2 solves separate scalar QPs with that GLOBAL beta; full risk for ALL six
    schedules is reported separately from T2's diagonal decision risk.
    Heterogeneous own-model objectives are solver QA, never policy rankings.
    """
    for model in models.values():model.check(episode.t0)
    a,b=models["A"].kernel,models["B"].kernel
    if a.assets!=ASSETS or b.assets!=ASSETS:raise ValueError("Wrong ordered instrument identity")
    x,v,sigma=episode.initial,episode.forecast,episode.covariance
    kwargs=dict(delta_minutes=cfg["delta_minutes"],cap_fraction=cfg["cap_fraction"],kappa=cfg["kappa"],theta=cfg["theta"],
                fee_bps=cfg["fee_bps"],half_spread_bps=cfg["half_spread_bps"])
    if cfg["alpha"]!=0:raise ValueError("Core has no alpha")
    reference=build_problem(a,x,v,sigma,**kwargs);beta=reference.risk_multiplier;caps=reference.caps
    kwargs["risk_multiplier_override"]=beta
    schedules={"T0":reference.reference_schedule,"T1":forecast_vwap(x,v,cfg["cap_fraction"])}
    solves={};start=time.monotonic();legs=[]
    for i,asset in enumerate(ASSETS):
        scalar=Kernel((asset,),a.matrices[:,i:i+1,i:i+1],a.taus_minutes,a.liquidity_usdt[i:i+1],"T2 independent",a.source_sha256)
        legs.append(solve_execution(scalar,x[i:i+1],v[:,i:i+1],sigma[i:i+1,i:i+1],assets=(asset,),**kwargs))
    schedules["T2"]=np.column_stack([leg["schedule_usdt"][:,0] for leg in legs])
    solves["T2"]=dict(diagnostics={
        "relative_stationarity_residual":max(q["diagnostics"]["relative_stationarity_residual"] for q in legs),
        "relative_objective_decomposition_residual":max(q["diagnostics"]["relative_objective_decomposition_residual"] for q in legs),
        "iterations":sum(q["diagnostics"]["iterations"] for q in legs)},
        objective_usdt=sum(q["objective_usdt"] for q in legs),seconds=time.monotonic()-start)
    for policy,kernel in [("T3",a),("T3B",without_cross(b)),("T4",b)]:
        start=time.monotonic();result=solve_execution(kernel,x,v,sigma,**kwargs)
        solves[policy]=result;result["seconds"]=time.monotonic()-start;schedules[policy]=result["schedule_usdt"]
    rows=[];paths={}
    for policy in POLICIES:
        z=schedules[policy];h=x-np.vstack([np.zeros(2),np.cumsum(z,axis=0)[:-1]])
        terminal=x-z.sum(axis=0);scale=np.maximum(x,1.)
        physical=max(float(np.max(np.abs(terminal)/scale)),float(np.max(np.maximum(-z,0)/scale)),float(np.max(np.maximum(z-caps,0)/scale)))
        if physical>1e-7:raise RuntimeError(f"{policy} invalid physical schedule; preserve whole-episode failure")
        raw=float(np.einsum("ki,ij,kj->",h,sigma*cfg["delta_minutes"],h))
        paths[policy]=dict(sales=z,before=h,after=h-z)
        model=models["B" if policy in ("T3B","T4") else "A"]
        diagnostic=solves.get(policy,{}).get("diagnostics",{})
        rows.append(dict(episode_id=episode.episode_id,policy=policy,status="PASS",input_hash=episode.input_hash,
            model_id=model.model_id if policy not in ("T0","T1") else "no_kernel",model_hash=model.model_hash if policy not in ("T0","T1") else "none",
            fit_end_exclusive=str(model.training_end),beta=beta,full_cov_raw_risk_usdt_squared=raw,full_cov_risk_preference_usdt=beta*raw,
            terminal_max_usdt=float(np.max(np.abs(terminal))),normalized_physical_residual=physical,minimum_sale_usdt=float(z.min()),
            minimum_cap_slack_usdt=float((caps-z).min()),cap_binding_cells=int(np.sum((caps-z)/scale<1e-8)),
            twap_adjusted_cells=int(np.sum(np.abs(z-x/len(z))/scale>1e-10)) if policy=="T0" else 0,
            solver="OSQP" if policy in solves else "deterministic_projection" if policy=="T0" else "forecast_formula",
            stationarity=diagnostic.get("relative_stationarity_residual",0.),decomposition_residual=diagnostic.get("relative_objective_decomposition_residual",0.),
            iterations=diagnostic.get("iterations",0),solve_seconds=solves.get(policy,{}).get("seconds",0.),
            own_model_objective_QA_only_usdt=solves.get(policy,{}).get("objective_usdt"),zero_risk_fallback=reference.zero_risk_fallback))
    return paths,rows
