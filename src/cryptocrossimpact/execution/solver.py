"""CONSTRAINED_SCENARIO_QP: continuous-USDT, hard-terminal, sell-only.

    Accepts declared ex-ante arrays; never loads prices/volume histories. Timing
    provenance of empirical inputs is the future Stage 4 episode builder's job.
"""
from dataclasses import dataclass

import cvxpy as cp
import numpy as np
from scipy.optimize import brentq

from .impact_cost import ASSETS,cash_hessian,psd_diagnostics,triangular_cash


class InfeasibleCapacity(ValueError):
    pass


def capped_uniform_reference(initial,caps):
    """Unique Euclidean projection of equal notional onto box + sum constraints.

    Used only for common risk normalization here, not a historical T0 strategy.
    z_k=clip(X/n+lambda,0,cap_k); bisection in inventory-normalized units.
    """
    x=np.asarray(initial,dtype=float);caps=np.asarray(caps,dtype=float)
    n,assets=caps.shape;answer=np.zeros_like(caps)
    for i in range(assets):
        if x[i]==0:continue
        scaled=caps[:,i]/x[i]
        if scaled.sum()<1-1e-12:raise InfeasibleCapacity("Inventory exceeds forecast participation capacity")
        if np.all(scaled>=1/n):answer[:,i]=x[i]/n;continue
        if scaled.sum()<=1:answer[:,i]=caps[:,i];continue
        fun=lambda shift:np.clip(1/n+shift,0,scaled).sum()-1
        shift=brentq(fun,-1.,max(1.,float(scaled.max())),xtol=1e-14,rtol=1e-14)
        answer[:,i]=np.clip(1/n+shift,0,scaled)*x[i]
    return answer


@dataclass
class QuadraticProblem:
    hessian: np.ndarray
    linear: np.ndarray
    constant: float
    impact_hessian: np.ndarray
    prefix: np.ndarray
    covariance_slice: np.ndarray
    reference_schedule: np.ndarray
    reference_raw_risk: float
    risk_multiplier: float
    effective_theta: float
    zero_risk_fallback: bool
    caps: np.ndarray
    initial: np.ndarray
    forecast: np.ndarray
    drift: np.ndarray
    delta: float
    kappa: float
    fee_bps: float
    spread_bps: float
    convention: str
    hessian_diagnostics: dict
    impact_diagnostics: dict


def build_problem(kernel,initial_inventory_usdt,forecast_turnover_usdt,risk_cov_per_minute,
                  delta_minutes=1.,cap_fraction=.10,kappa=.001,theta=1.,fee_bps=5.,half_spread_bps=1.,
                  expected_price_change=None,assets=ASSETS,convention="exact_exponential_cells",
                  risk_multiplier_override=None):
    """Build .5 z'H z + q'z + c in USDT, time-major total sale notional.

    Sigma_slice=Sigma_per_minute*delta (rate-consistent diffusion). Risk is a
    preference term beta * sum h_before' Sigma_slice h_before, not cash expense.
    beta=theta*(W/1e4)/R(reference); temporary uses bin turnover, so sum
    kappa*z^2/Vhat already accounts for bin duration and receives no extra delta.
    Optional risk_multiplier_override is the caller's common portfolio beta;
    it prevents per-leg normalization from changing independent-policy risk.
    """
    if tuple(assets)!=kernel.assets:raise ValueError("Asset order differs between kernel and inputs")
    x=np.array(initial_inventory_usdt,dtype=float,copy=True);v=np.array(forecast_turnover_usdt,dtype=float,copy=True)
    covariance=np.array(risk_cov_per_minute,dtype=float,copy=True);d=len(assets)
    if x.shape!=(d,) or v.ndim!=2 or v.shape[1]!=d or not len(v) or covariance.shape!=(d,d):
        raise ValueError("Input shapes/asset dimensions disagree")
    if not np.isfinite(x).all() or (x<0).any() or not np.isfinite(v).all() or (v<=0).any():
        raise ValueError("Nonnegative inventory and positive finite ex-ante turnover required")
    if not np.isfinite([delta_minutes,cap_fraction,kappa,theta,fee_bps,half_spread_bps]).all() or delta_minutes<=0 or not 0<cap_fraction<=1 or min(kappa,theta,fee_bps,half_spread_bps)<0:
        raise ValueError("Invalid durations/cap/cost assumption")
    psd_diagnostics(covariance)
    n=len(v);caps=cap_fraction*v
    if np.any(x>caps.sum(axis=0)+1e-12*np.maximum(x,caps.sum(axis=0))):
        raise InfeasibleCapacity("Inventory exceeds forecast participation capacity; no cap relaxation")
    drift=np.zeros_like(v) if expected_price_change is None else np.array(expected_price_change,dtype=float,copy=True)
    if drift.shape!=v.shape or not np.isfinite(drift).all():raise ValueError("Frozen drift must be finite and match forecast bins/assets")
    reference=capped_uniform_reference(x,caps)
    prefix=np.kron(np.tril(np.ones((n,n)),k=-1),np.eye(d))
    b=np.tile(x,n);sigma_slice=covariance*delta_minutes
    risk_matrix=np.kron(np.eye(n),sigma_slice)
    h_ref=(b-prefix@reference.ravel()).reshape(n,d)
    raw_ref=float(np.einsum("ki,ij,kj->",h_ref,sigma_slice,h_ref))
    bound=n*delta_minutes*np.linalg.norm(x)**2*np.linalg.norm(covariance,2)
    fallback=raw_ref<=1e-12*max(bound,np.finfo(float).tiny)
    effective=0. if fallback else theta
    beta=effective*(x.sum()/1e4)/raw_ref if effective else 0.
    # Matched independent policies retain the GLOBAL full-covariance beta even
    # when their decision objective uses only own variance. Default unchanged.
    if risk_multiplier_override is not None:
        if not np.isfinite(risk_multiplier_override) or risk_multiplier_override < 0:
            raise ValueError("Shared risk multiplier must be finite and nonnegative")
        beta=float(risk_multiplier_override)
    impact,impact_diag=cash_hessian(kernel,n,delta_minutes,convention)
    hessian=impact+np.diag((2*kappa/v).ravel())+2*beta*(prefix.T@risk_matrix@prefix)
    linear=-2*beta*(prefix.T@risk_matrix@b)+1e-4*(fee_bps+half_spread_bps)-drift.ravel()
    constant=beta*float(b@risk_matrix@b)
    return QuadraticProblem(hessian,linear,constant,impact,prefix,sigma_slice,reference,raw_ref,beta,effective,fallback,
        caps,x,v,drift,delta_minutes,kappa,fee_bps,half_spread_bps,convention,psd_diagnostics(hessian),impact_diag)


def decompose(kernel,problem,schedule):
    z=np.asarray(schedule,dtype=float);n,d=problem.forecast.shape
    if z.shape!=(n,d) or not np.isfinite(z).all():raise ValueError("Invalid schedule")
    before=problem.initial-np.vstack([np.zeros(d),np.cumsum(z,axis=0)[:-1]])
    raw=float(np.einsum("ki,ij,kj->",before,problem.covariance_slice,before))
    result=dict(transient_usdt=triangular_cash(kernel,z,problem.delta,problem.convention),
        temporary_usdt=float(problem.kappa*np.sum(z*z/problem.forecast)),
        risk_preference_usdt=float(problem.risk_multiplier*raw),
        fee_usdt=float(1e-4*problem.fee_bps*z.sum()),spread_usdt=float(1e-4*problem.spread_bps*z.sum()),
        drift_usdt=float(-np.sum(z*problem.drift)),raw_inventory_risk_usdt_squared=raw)
    result["objective_usdt"]=sum(v for k,v in result.items() if k!="raw_inventory_risk_usdt_squared")
    result["scenario_cash_cost_excluding_risk_usdt"]=result["objective_usdt"]-result["risk_preference_usdt"]
    return result


def solve_execution(kernel,initial_inventory_usdt,forecast_turnover_usdt,risk_cov_per_minute,*,solver="OSQP",**kwargs):
    problem=build_problem(kernel,initial_inventory_usdt,forecast_turnover_usdt,risk_cov_per_minute,**kwargs)
    n,d=problem.forecast.shape
    scales=np.where(problem.initial>0,problem.initial,1.)
    cash_scale=max(float(problem.initial.sum()/1e4),1e-12)
    repeated=np.tile(scales,n)
    h_scaled=problem.hessian*repeated[:,None]*repeated[None,:]/cash_scale
    q_scaled=problem.linear*repeated/cash_scale
    variable=cp.Variable((n,d));flat=cp.vec(variable,order="C")
    constraints=[variable>=0,variable<=problem.caps/scales,cp.sum(variable,axis=0)==problem.initial/scales]
    expression=.5*cp.quad_form(flat,cp.psd_wrap(h_scaled))+q_scaled@flat+problem.constant/cash_scale
    opt=cp.Problem(cp.Minimize(expression),constraints)
    options=dict(eps_abs=1e-9,eps_rel=1e-9,max_iter=100000,polishing=True) if solver=="OSQP" else dict(tol_gap_abs=1e-10,tol_gap_rel=1e-10,tol_feas=1e-10,max_iter=300)
    if solver not in ("OSQP","CLARABEL"):raise ValueError("Unverified QP backend")
    opt.solve(solver=solver,warm_start=False,**options)
    if opt.status!="optimal" or variable.value is None:raise RuntimeError(f"Nonconverged scenario QP: {opt.status}")
    normalized=variable.value;z=normalized*scales
    terminal=problem.initial-z.sum(axis=0)
    tolerance=np.maximum(1e-6*problem.initial,1e-8)
    normalized_primal=max(float(np.max(np.abs(terminal)/scales)),float(np.max(np.maximum(-normalized,0))),
        float(np.max(np.maximum(normalized-problem.caps/scales,0))))
    if np.any(np.abs(terminal)>tolerance) or normalized_primal>1e-7:raise RuntimeError("Material inventory/nonnegative/cap violation")
    lo,hi,eq=[c.dual_value for c in constraints]
    gradient=h_scaled@normalized.ravel()+q_scaled
    stationarity=gradient-lo.ravel()+hi.ravel()+np.tile(eq,n)
    station_scale=max(float(np.max(np.abs(gradient))),float(np.max(np.abs(lo))),float(np.max(np.abs(hi))),float(np.max(np.abs(eq))),np.finfo(float).tiny)
    stationary=float(np.max(np.abs(stationarity))/station_scale)
    complementarity=float(max(np.max(np.abs(lo*normalized)),np.max(np.abs(hi*(problem.caps/scales-normalized)))))
    dual_scale=max(station_scale,1.)
    if stationary>2e-6 or complementarity>2e-6*dual_scale or min(lo.min(),hi.min()) < -1e-8*dual_scale:
        raise RuntimeError("QP KKT diagnostics failed")
    components=decompose(kernel,problem,z)
    quadratic=.5*float(z.ravel()@problem.hessian@z.ravel())+float(problem.linear@z.ravel())+problem.constant
    residual=abs(quadratic-components["objective_usdt"])/max(abs(quadratic),cash_scale)
    solver_objective=float(opt.value*cash_scale)
    if residual>1e-8 or abs(solver_objective-quadratic)>1e-7*max(abs(quadratic),cash_scale):
        raise RuntimeError("Objective decomposition mismatch")
    before=problem.initial-np.vstack([np.zeros(d),np.cumsum(z,axis=0)[:-1]])
    return dict(label="CONSTRAINED_SCENARIO_QP",status=opt.status,solver=solver,asset_order=list(kernel.assets),
        schedule_usdt=z,h_before_usdt=before,h_after_usdt=before-z,starting_inventory_usdt=problem.initial.copy(),
        terminal_inventory_usdt=terminal,caps_usdt=problem.caps.copy(),forecast_turnover_usdt=problem.forecast.copy(),
        reference_schedule_usdt=problem.reference_schedule.copy(),components=components,objective_usdt=components["objective_usdt"],
        diagnostics=dict(terminal_residual_usdt=terminal.tolist(),minimum_sale_usdt=float(z.min()),minimum_cap_slack_usdt=float((problem.caps-z).min()),
            normalized_primal_residual=normalized_primal,relative_stationarity_residual=stationary,
            scaled_complementarity_residual=complementarity,relative_objective_decomposition_residual=residual,
            risk_reference_raw=problem.reference_raw_risk,risk_multiplier=problem.risk_multiplier,
            effective_theta=problem.effective_theta,zero_risk_fallback=problem.zero_risk_fallback,
            impact_hessian=problem.impact_diagnostics,total_hessian=problem.hessian_diagnostics,
            objective_scale_usdt=cash_scale,decision_scale_usdt=scales.tolist(),iterations=opt.solver_stats.num_iters,
            convention=problem.convention,delta_minutes=problem.delta,
            covariance_semantics="per-minute rate multiplied by delta for each bin",input_semantics="declared ex-ante or synthetic; no market-data I/O"))
