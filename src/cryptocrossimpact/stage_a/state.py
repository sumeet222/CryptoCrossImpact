"""Piecewise-constant state congruence and an immutable ex-ante MPC ledger."""
import numpy as np
from ..execution.impact_cost import cash_hessian,psd_diagnostics,exponential_factors
from ..robust.solver import RobustQP


def multipliers(point,reference,eta,floor=1e-8):
    point=np.asarray(point);reference=np.asarray(reference)
    if eta not in [0,.5,1] or not np.isfinite(point).all() or (point<=0).any() or (reference<=0).any():raise ValueError('Invalid forecast/state units')
    if eta==0:return np.ones_like(point)
    return np.clip((reference/np.maximum(point,floor))**(eta/2),.5,2.)


def state_hessian(kernel,a,verify=True):
    a=np.asarray(a);h,_=cash_hessian(kernel,len(a));d=a.ravel()
    if a.shape!=(len(a),len(kernel.assets)) or not np.isfinite(a).all() or (a<=0).any():raise ValueError('State path shape/value')
    result=d[:,None]*h*d[None,:]
    if verify:psd_diagnostics(result)
    return result


def triangle(kernel,z,a):
    """Independent causal cells, transformed signed USDT, same-cell triangle once."""
    z=np.asarray(z)*np.asarray(a);u=z/np.sqrt(kernel.liquidity_usdt);cost=0.
    for c,tau in zip(kernel.matrices,kernel.taus_minutes):
        factors=exponential_factors(len(z),1.,float(tau))
        for k in range(len(z)):
            cost+=factors[0]*(u[k]@c@u[k])
            for s in range(k):cost+=factors[k-s]*(u[k]@c@u[s])
    return float(cost*1e-4)


class StateQP:
    """Same X2 L25 conic QP with ONLY a congruent transient Hessian replaced."""
    def __init__(self,kernel,initial,caps,sigma,beta):
        self.kernel=kernel;self.h0=cash_hessian(kernel,len(caps))[0]
        self.qp=RobustQP([('conditional',kernel)],initial,caps,sigma,beta,force_full=True)
        self.ledger=np.empty((0,len(initial)));self.prefixes=[]

    def composite(self,past,future,claimed_past=None):
        if len(past)!=len(self.ledger):raise ValueError('Past state/trade length disagreement')
        if claimed_past is not None and not np.array_equal(claimed_past,self.ledger):raise ValueError('Immutable past multiplier rewrite rejected')
        a=np.vstack([self.ledger,future])
        if a.shape!=self.qp.base.caps.shape or not np.isfinite(a).all() or (a<=0).any():raise ValueError('Composite state shape')
        return a

    def solve(self,past,point,paths,future,lam=25,solver='CLARABEL',claimed_past=None):
        a=self.composite(past,future,claimed_past);d=a.ravel();h=d[:,None]*self.h0*d[None,:]
        self.qp.base.H=h;self.qp.H=[h]
        z,qa=self.qp.solve(past,point,paths,lam,solver)
        qa['state_hessian_min_eigenvalue']=psd_diagnostics(h)['min_eigenvalue']
        return z,qa

    def commit(self,a):
        a=np.array(a,copy=True);a.setflags(write=False);self.prefixes.append(a);self.ledger=np.vstack([self.ledger,a])
