"""Common-world modeled cash shortfall EXCLUDING funding; risk stays separate."""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..execution.impact_cost import Kernel,cash_hessian,ASSETS
from .v2_common import SCOPE,digest


@dataclass(frozen=True)
class World:
    world_id: str
    kernel: Kernel
    kappa: float
    bins: int=60

    def __post_init__(self):
        if self.kernel.assets!=ASSETS or self.kappa<0:raise ValueError("Wrong world units/asset identity")
        h,diagnostic=cash_hessian(self.kernel,self.bins)
        h.setflags(write=False);object.__setattr__(self,"hessian",h);object.__setattr__(self,"hessian_diagnostics",diagnostic)

    @property
    def world_hash(self):
        return digest(dict(id=self.world_id,C=self.kernel.matrices,tau=self.kernel.taus_minutes,L=self.kernel.liquidity_usdt,
                           kappa=self.kappa,bins=self.bins,convention="exact_exponential_cells",cost_scope=SCOPE))


WORLD_IDS=["E0","E1","E2","E3_amplitude_0p5","E3_amplitude_2","E3_decay_0p5","E3_decay_2",
           "E3_kappa_0005","E3_kappa_005","E3_rho_0p5","E3_opposite_sign"]
ALIASES={"E3_amplitude_1":"E1","E3_kappa_001":"E1","E3_rho_1":"E1","E3_rho_0":"E2"}


def worlds(e1,b,bins=60):
    c=e1.matrices;diag=np.array([np.diag(np.diag(a)) for a in c]);d=np.diag([1.,-1.])
    def k(c=c,tau=e1.taus_minutes,label="E1"):
        return Kernel(ASSETS,c,tau,e1.liquidity_usdt,label,e1.source_sha256)
    specs=[("E0",b,.001),("E1",e1,.001),("E2",k(diag,label="E2"),.001),
        ("E3_amplitude_0p5",k(c*.5),.001),("E3_amplitude_2",k(c*2),.001),
        ("E3_decay_0p5",k(tau=e1.taus_minutes*.5),.001),("E3_decay_2",k(tau=e1.taus_minutes*2),.001),
        ("E3_kappa_0005",e1,.0005),("E3_kappa_005",e1,.005),("E3_rho_0p5",k((diag+c)/2),.001),
        ("E3_opposite_sign",k(np.array([d@a@d for a in c])),.001)]
    answer=[World(name,kernel,kap,bins) for name,kernel,kap in specs]
    if [w.world_id for w in answer]!=WORLD_IDS:raise ValueError("Scenario list changed")
    return answer


def evaluation_prices(frame,t0,bins,proxy="close"):
    expected=pd.date_range(t0,periods=bins,freq="min")
    if not pd.DatetimeIndex(frame.time).equals(expected):raise ValueError("EVALUATION_QC: missing/duplicate evaluation minute")
    prices=[];volume=[]
    for i in range(2):
        if not frame[f"valid_bar_{i}"].all():raise ValueError("EVALUATION_QC: invalid evaluation source bar")
        if proxy=="ohlc":p=frame[[f"{c}_{i}" for c in ("open","high","low","close")]].mean(axis=1).to_numpy()
        elif proxy in ("open","close"):p=frame[f"{proxy}_{i}"].to_numpy()
        else:raise ValueError("Unfrozen price proxy")
        v=frame[f"quote_volume_{i}"].to_numpy()
        if not np.isfinite(p).all() or (p<=0).any() or not np.isfinite(v).all() or (v<0).any():raise ValueError("EVALUATION_QC: nonfinite/invalid source")
        prices.append(p);volume.append(v)
    return np.column_stack(prices),np.column_stack(volume)


def score_schedule(z,x,vhat,p0,prices,vreal,world,fee_bps=5.,spread_bps=1.,**irrelevant_funding_metadata):
    """Five cash components only. Hypothetical funding labels have no effect.

    Per-asset transient bookkeeping allocates .5*z_i*(H z)_i. It may be
    negative with valid negative cross terms; only the portfolio PSD form is
    nonnegative. No actual fill or causal intervention interpretation.
    """
    z=np.asarray(z);x=np.asarray(x);vhat=np.asarray(vhat);prices=np.asarray(prices);vreal=np.asarray(vreal);p0=np.asarray(p0)
    if z.shape!=(world.bins,2) or any(a.shape!=z.shape for a in (vhat,prices,vreal)):raise ValueError("Scoring dimensions disagree")
    if not all(np.isfinite(a).all() for a in (z,x,vhat,p0,prices,vreal)) or (vhat<=0).any() or (prices<=0).any() or (p0<=0).any() or (vreal<0).any():raise ValueError("Invalid scoring inputs")
    if (x<=0).any() or np.max(np.abs(x-z.sum(axis=0))/x)>1e-7 or np.max(np.maximum(-z,0)/x)>1e-7:raise ValueError("Invalid sell/liquidation schedule")
    path=np.sum(z*(1-prices/p0),axis=0)
    impact=(.5*z*(world.hessian@z.ravel()).reshape(z.shape)).sum(axis=0)
    temp=world.kappa*np.sum(z*z/vhat,axis=0)
    fee=fee_bps/1e4*z.sum(axis=0);spread=spread_bps/1e4*z.sum(axis=0)
    amount=path+impact+temp+fee+spread
    participation=np.divide(z,vreal,out=np.full_like(z,np.nan),where=vreal>0)
    participation[(vreal==0)&(z>0)]=np.inf
    maximum=float(np.nanmax(participation)) if not np.isnan(participation).all() else None
    result=dict(cost_scope=SCOPE,funding_included=False,funding_observed=False,funding_cashflow_usdt=None,all_in_cash_cost_usdt=None,
        world=world.world_id,world_hash=world.world_hash,evaluator_role="IN_MODEL_ONLY" if world.world_id=="E0" else "ALTERNATIVE_SCENARIO",
        path_usdt=float(path.sum()),transient_usdt=float(impact.sum()),temporary_usdt=float(temp.sum()),fee_usdt=float(fee.sum()),spread_usdt=float(spread.sum()),
        shortfall_ex_funding_usdt=float(amount.sum()),shortfall_ex_funding_bps=float(1e4*amount.sum()/x.sum()),
        max_realized_participation=maximum,realized_participation_over_10pct_cells=int(np.sum(participation>.1)),
        undefined_realized_participation_cells=int(np.sum(np.isnan(participation))),zero_realized_volume_cells=int(np.sum(vreal==0)),W_usdt=float(x.sum()))
    for i,asset in enumerate(("btc","eth")):
        for name,a in [("path",path),("transient",impact),("temporary",temp),("fee",fee),("spread",spread),("shortfall_ex_funding",amount)]:
            result[f"{asset}_{name}_usdt"]=float(a[i])
        result[f"{asset}_initial_usdt"]=float(x[i])
    if not np.isclose(result["shortfall_ex_funding_usdt"],sum(result[k] for k in ["path_usdt","transient_usdt","temporary_usdt","fee_usdt","spread_usdt"]),rtol=1e-12,atol=1e-8):raise ValueError("Ex-funding decomposition mismatch")
    return result
