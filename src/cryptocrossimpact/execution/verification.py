"""Stage 3 numerical harness; JSON models + synthetic arrays only."""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from scipy.integrate import dblquad

from ..data.storage import write_json,sha256,utcnow
from .impact_cost import Kernel,load_stage02,exponential_factors,cash_hessian,triangular_cash
from .solver import solve_execution,build_problem,decompose
from .ajnt_benchmark import nystrom,galerkin,exponential_analytic


def config(root):return yaml.safe_load((Path(root)/"configs/stage03_execution.yaml").read_text())


def location(root):
    out=Path(root)/config(root)["output"];out.mkdir(parents=True,exist_ok=True)
    return out


def clean(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,dict):return {k:clean(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [clean(v) for v in value]
    return value


def save(path,value):write_json(path,clean(value))


def paper(root):
    cfg=config(root)["paper"];out=location(root);rows=[];curves=[];case_status=[]
    params=dict(horizon=cfg["horizon"],rho=cfg["exponential_rho"],alpha=cfg["fractional_alpha"],
        temporary=cfg["temporary_lambda"],penalty=cfg["terminal_penalty"],initial=cfg["initial_inventory"])
    for matrix in ("diagonal","cross"):
        c=np.array(cfg[f"{matrix}_matrix"])
        for kind in ("zero","exponential","fractional"):
            errors=[]
            for n in cfg["grids"]:
                result=nystrom(n,kind,c,**params);independent=galerkin(n,kind,c,**params)
                reference=None
                if kind in ("zero","exponential"):
                    reference=exponential_analytic(result["times"],np.zeros((2,2)) if kind=="zero" else c,
                        horizon=params["horizon"],rho=params["rho"],temporary=params["temporary"],penalty=params["penalty"],initial=params["initial"])
                inventory_error=float(np.max(np.abs(result["inventory"]-(reference or independent)["inventory"])))
                errors.append(inventory_error)
                row=dict(matrix=matrix,kernel=kind,n=n,delta=cfg["horizon"]/n,
                    first_order_relative_residual=result["first_order_relative_residual"],condition_number=result["condition_number"],
                    objective=result["objective"]["total"],independent_galerkin_objective=independent["objective"]["total"],
                    inventory_reference="continuous closed form" if reference else "exact-cell Galerkin on same grid",
                    maximum_inventory_reference_error=inventory_error,
                    maximum_rate_reference_error=float(np.max(np.abs(result["rates"]-reference["rates"]))) if reference else None,
                    galerkin_midcell_rate_difference=float(np.max(np.abs((result["rates"][:-1]+result["rates"][1:])/2-independent["rates"]))),
                    asset2_rate_min=float(result["rates"][:,1].min()),asset2_rate_max=float(result["rates"][:,1].max()),
                    asset2_inventory_min=float(result["inventory"][:,1].min()),asset2_inventory_max=float(result["inventory"][:,1].max()),
                    endpoint_rate_asymmetry=float(np.max(np.abs(result["rates"][0]-result["rates"][-1]))),
                    terminal_asset1=float(result["inventory"][-1,0]),terminal_asset2=float(result["inventory"][-1,1]))
                if row["first_order_relative_residual"]>1e-10:raise ValueError("Paper Fredholm residual failed")
                rows.append(row)
                if n==max(cfg["grids"]):
                    for i,time in enumerate(result["times"]):
                        curves.append(dict(matrix=matrix,kernel=kind,time=time,u1=result["rates"][i,0],u2=result["rates"][i,1],
                            x1=result["inventory"][i,0],x2=result["inventory"][i,1],
                            analytic_u1=reference["rates"][i,0] if reference else None,analytic_u2=reference["rates"][i,1] if reference else None,
                            analytic_x1=reference["inventory"][i,0] if reference else None,analytic_x2=reference["inventory"][i,1] if reference else None))
                print(f"AJNT {matrix}/{kind} n={n}: residual={row['first_order_relative_residual']:.2g}; inventory error={inventory_error:.6g}",flush=True)
            if matrix=="diagonal" and max(abs(row["asset2_rate_min"]),abs(row["asset2_rate_max"]))>1e-10:
                raise ValueError("Unexpected asset-2 trading in paper diagonal null")
            if matrix=="cross" and kind!="zero" and not (row["asset2_rate_min"]<0<row["asset2_rate_max"] and row["asset2_inventory_min"]<0<row["asset2_inventory_max"]):
                raise ValueError("Paper cross signed round-trip pattern not reproduced")
            if kind!="zero" and not errors[-1]<errors[1]<errors[0]:raise ValueError("Paper discretization did not converge")
            case_status.append(dict(matrix=matrix,kernel=kind,status="QUALIFIED" if kind=="fractional" else "REPRODUCED",inventory_reference_errors=errors,
                qualification="Table1/first-order/inventory convergence pass; finite-grid terminal nodal rate and pointwise published-figure agreement unresolved" if kind=="fractional" else None))
    pd.DataFrame(rows).to_csv(out/"paper_convergence.csv",index=False)
    pd.DataFrame(curves).to_csv(out/"paper_curves.csv",index=False)
    save(out/"paper_summary.json",dict(label="AJNT_DETERMINISTIC_BENCHMARK",status="REPRODUCED",params=cfg,cases=case_status,
        status_scope="Required zero/exponential deterministic examples reproduced. Optional fractional pointwise figure agreement QUALIFIED; no endpoint convention altered.",
        reference="Local arXiv v2 (2026-02-20), Cor 2.9 / Remark 2.10 eq(2.15), sec3.1 eqs(3.1)-(3.4), sec3.4 Table1 pp20-21",
        sign="u=dX/dt; unrestricted signed rates; finite terminal penalty, not hard equality",
        pixel_match="NOT CLAIMED: published grid size/digitized points unavailable; qualitative Figures 1-2 plus equation/analytic/Galerkin checks",
        stochastic_theorem_implemented=False))


def scenario_inputs(cfg,delta=None,varying=False):
    s=cfg["scenario"];d=s["delta_minutes"] if delta is None else delta;n=round(s["horizon_minutes"]/d)
    rates=np.array(s["turnover_rate_usdt_per_minute"])
    v=np.tile(rates*d,(n,1))
    if varying:
        # Exact integral of a predetermined sinusoidal TURNOVER RATE, not data.
        edges=np.linspace(0,s["horizon_minutes"],n+1);omega=2*np.pi/s["horizon_minutes"]
        for i,phase in enumerate([0.,1.]):
            v[:,i]=rates[i]*(d+.25*(np.cos(omega*edges[:-1]+phase)-np.cos(omega*edges[1:]+phase))/omega)
    x=s["start_fraction_of_forecast"]*rates*s["horizon_minutes"]
    sigma=np.array(s["covariance_per_minute"])
    kwargs=dict(delta_minutes=d,cap_fraction=s["cap_fraction"],kappa=s["kappa"],theta=s["theta"],fee_bps=s["fee_bps"],half_spread_bps=s["half_spread_bps"],convention=s["convention"])
    return x,v,sigma,kwargs


def models_smoke(root):
    cfg=config(root);out=location(root);x,v,sigma,kwargs=scenario_inputs(cfg)
    records=[]
    for name in ("A","B"):
        kernel=load_stage02(root,name);result=solve_execution(kernel,x,v,sigma,**kwargs)
        records.append(dict(model=name,source_sha256=kernel.source_sha256,asset_order=kernel.assets,
            identified_schema="stage02-kernel-implicit-v1 (known complete key set, hash-bound)",status=result["status"],diagnostics=result["diagnostics"]))
    rejected=False
    try:load_stage02(root,"U")
    except ValueError:rejected=True
    if not rejected:raise ValueError("U export was not blocked")
    save(out/"models_smoke.json",dict(status="PASS",models=records,U_rejected=True,market_data_rows_loaded=0,synthetic_inputs=clean(dict(initial=x,forecast=v,covariance_per_minute=sigma,kwargs=kwargs))))


def synthetic(root):
    cfg=config(root);out=location(root);x,v,sigma,kwargs=scenario_inputs(cfg,varying=True)
    schedules=[];summaries=[];backend=[]
    kernels={name:load_stage02(root,name) for name in ("A","B")}
    b=kernels["B"]
    controlled=b.matrices.copy();controlled[:,0,1]=0;controlled[:,1,0]=0
    kernels["B_same_self_zero_cross_synthetic"]=Kernel(b.assets,controlled,b.taus_minutes,b.liquidity_usdt,"B same-self diagonal mathematical limit")
    for name,kernel in kernels.items():
        result=solve_execution(kernel,x,v,sigma,**kwargs)
        other=solve_execution(kernel,x,v,sigma,solver="CLARABEL",**kwargs)
        normalized_error=float(np.max(np.abs(result["schedule_usdt"]-other["schedule_usdt"])/x))
        objective_error=abs(result["objective_usdt"]-other["objective_usdt"])/result["objective_usdt"]
        if normalized_error>1e-5 or objective_error>1e-7:raise ValueError("Independent QP backends disagree")
        summaries.append(dict(model=name,components=result["components"],diagnostics=result["diagnostics"]))
        backend.append(dict(model=name,primary="OSQP",independent="CLARABEL",max_schedule_error_over_inventory=normalized_error,relative_objective_difference=objective_error))
        for k in range(len(v)):
            for i,asset in enumerate(b.assets):schedules.append(dict(model=name,interval=k,minute_start=k,asset=asset,sell_usdt=result["schedule_usdt"][k,i],h_before_usdt=result["h_before_usdt"][k,i],h_after_usdt=result["h_after_usdt"][k,i],forecast_turnover_usdt=v[k,i],cap_usdt=result["caps_usdt"][k,i]))
    pd.DataFrame(schedules).to_csv(out/"synthetic_schedules.csv",index=False)
    pd.DataFrame(backend).to_csv(out/"independent_solver_comparison.csv",index=False)
    save(out/"synthetic_summary.json",dict(label="CONSTRAINED_SCENARIO_QP",status="PASS",cases=summaries,
        input_kind="entirely synthetic ex-ante rate/covariance arrays; development A/B model JSON only",
        same_inputs=True,interpretation="Each row uses its own assumed objective; no cost-saving/policy claim or cross-scored replay",
        self_coefficient_note="Calibrated A/B self diagonals differ. The extra B-diagonal synthetic limit holds B self terms fixed; not a Stage 4 strategy."))
    hessian_verification(root,kernels)
    convergence(root)


def hessian_verification(root,kernels):
    cfg=config(root);out=location(root);rng=np.random.default_rng(cfg["seed"]);records=[];b=kernels["B"]
    checks=dict(kernels)
    checks["zero"]=Kernel(b.assets,np.zeros((1,2,2)),[60.],b.liquidity_usdt)
    checks["negative_cross_PSD"]=Kernel(b.assets,[[[1.,-.3],[-.3,.8]]],[12.],b.liquidity_usdt)
    checks["two_components"]=Kernel(b.assets,[[[1.,.2],[.2,.7]],[[.3,-.1],[-.1,.4]]],[5.,30.],b.liquidity_usdt)
    for name,kernel in checks.items():
        h,diagnostics=cash_hessian(kernel,60)
        signed=rng.normal(size=(100,60,2))*1e5;signed-=signed.mean(axis=1,keepdims=True)
        flat=signed.reshape(100,-1);cost=.5*np.einsum("bi,ij,bj->b",flat,h,flat)
        identity=max(abs(triangular_cash(kernel,signed[i])-.5*flat[i]@h@flat[i]) for i in range(5))
        scale=max(float(np.max(np.abs(cost))),1e-30)
        if cost.min()<-1e-9*scale or identity>1e-9*scale:raise ValueError("Hessian/signed cost verification failed")
        records.append(dict(model=name,**diagnostics,round_trips=100,min_round_trip_cash_usdt=float(cost.min()),maximum_triangular_identity_error_usdt=identity))
    pd.DataFrame(records).to_csv(out/"hessian_diagnostics.csv",index=False)
    quadrature=[]
    for d,tau in [(1.,60.),(2.,.7),(.5,30.),(1.,1e10)]:
        actual=exponential_factors(2,d,tau)
        same=dblquad(lambda s,t:np.exp(-(t-s)/tau),0,d,lambda t:0,lambda t:t,epsabs=1e-12)[0]/d**2
        across=dblquad(lambda s,t:np.exp(-(t-s)/tau),d,2*d,lambda t:0,lambda t:d,epsabs=1e-12)[0]/d**2
        err=max(abs(actual[0]-same),abs(actual[1]-across))
        if err>1e-10:raise ValueError("Cell factor quadrature failed")
        quadrature.append(dict(delta_minutes=d,tau_minutes=tau,a0=actual[0],a1=actual[1],quadrature_a0=same,quadrature_a1=across,max_absolute_error=err))
    pd.DataFrame(quadrature).to_csv(out/"cell_quadrature.csv",index=False)


def convergence(root):
    cfg=config(root);out=location(root);kernel=load_stage02(root,"B");solutions={};rows=[]
    grids=cfg["convergence"]["delta_minutes"]
    for d in grids:
        x,v,sigma,kwargs=scenario_inputs(cfg,delta=d)
        result=solve_execution(kernel,x,v,sigma,**kwargs)
        solutions[d]=result
        half=triangular_cash(kernel,result["schedule_usdt"],d,"half_cell_sampled")
        rows.append(dict(delta_minutes=d,intervals=len(v),initial_btc_usdt=x[0],initial_eth_usdt=x[1],
            forecast_total_btc_usdt=v[:,0].sum(),covariance_slice_btc=sigma[0,0]*d,objective_usdt=result["objective_usdt"],
            impact_exact_usdt=result["components"]["transient_usdt"],impact_half_cell_usdt=half,
            half_minus_exact_impact_usdt=half-result["components"]["transient_usdt"],relative_stationarity_residual=result["diagnostics"]["relative_stationarity_residual"]))
    fine=min(grids);reference=solutions[fine];t_fine=np.linspace(0,60,len(reference["schedule_usdt"])+1)
    x,v,sigma,kwargs=scenario_inputs(cfg,delta=fine);problem=build_problem(kernel,x,v,sigma,**kwargs)
    fine_inventory=np.vstack([x,reference["h_after_usdt"]]);curves=[]
    for row in rows:
        d=row["delta_minutes"];result=solutions[d];trajectory=np.vstack([x,result["h_after_usdt"]]);times=np.linspace(0,60,len(trajectory))
        interpolated=np.column_stack([np.interp(t_fine,times,trajectory[:,i]) for i in range(2)])
        error=float(np.max(np.abs(interpolated-fine_inventory)/x))
        copies=round(d/fine);embedded=np.repeat(result["schedule_usdt"]/copies,copies,axis=0)
        rates=embedded/fine;fine_rates=reference["schedule_usdt"]/fine
        row.update(max_inventory_error_over_initial=error,relative_rate_L2_error=float(np.linalg.norm(rates-fine_rates)/np.linalg.norm(fine_rates)),
            objective_on_common_fine_grid_usdt=decompose(kernel,problem,embedded)["objective_usdt"])
        for i,time in enumerate(times):curves.append(dict(delta_minutes=d,time_minutes=time,btc_remaining=trajectory[i,0]/x[0],eth_remaining=trajectory[i,1]/x[1]))
    errors=[row["max_inventory_error_over_initial"] for row in rows]
    if not errors[2]<errors[1]<errors[0]:raise ValueError("Continuous-input inventory convergence failed")
    if not abs(rows[2]["half_minus_exact_impact_usdt"])<abs(rows[1]["half_minus_exact_impact_usdt"])<abs(rows[0]["half_minus_exact_impact_usdt"]):
        raise ValueError("Half-cell comparison did not converge")
    pd.DataFrame(rows).to_csv(out/"scenario_grid_convergence.csv",index=False)
    pd.DataFrame(curves).to_csv(out/"scenario_grid_trajectories.csv",index=False)
    save(out/"scenario_convergence.json",dict(status="PASS",grids_minutes=grids,constant_continuous_inputs=True,
        turnover_rule="Vhat_delta=turnover_rate*delta",covariance_rule="Sigma_delta=Sigma_per_minute*delta; applied internally once",
        reference_delta_minutes=fine,inventory_relative_errors=errors,
        convention="exact_exponential_cells; half-cell/sample-lag evaluated only as a controlled comparison"))
