"""X1 deterministic conditional QP with carried exact-cell transient state.

Time-major USDT amounts. No market-data I/O. Original solver remains untouched.
"""
import time
import numpy as np
import osqp
from scipy import sparse

from .impact_cost import cash_hessian,psd_diagnostics,exponential_factors


def historical_linear_state(kernel,past,future_bins):
    """Independent exponential sum equivalent to H_fp z_p, cash/USDT units."""
    past=np.asarray(past);k=len(past);out=np.zeros((future_bins,len(kernel.assets)))
    units=1/np.sqrt(kernel.liquidity_usdt)
    for c,tau in zip(kernel.matrices,kernel.taus_minutes):
        a=exponential_factors(k+future_bins,1.,float(tau))
        for j in range(k):
            out+=a[k+np.arange(future_bins)-j,None]*(1e-4*(c*units[:,None]*units[None,:])@past[j])
    return out


class AdaptiveQP:
    def __init__(self,kernel,initial,caps,covariance,beta,kappa=.001):
        self.kernel=kernel;self.x=np.array(initial,copy=True);self.caps=np.array(caps,copy=True)
        self.sigma=np.array(covariance,copy=True);self.beta=float(beta);self.kappa=float(kappa)
        self.n,self.d=self.caps.shape
        if self.x.shape!=(self.d,) or self.sigma.shape!=(self.d,self.d) or (self.x<0).any() or (self.caps<=0).any() or min(beta,kappa)<0:
            raise ValueError('Invalid fixed episode inputs')
        if not all(np.isfinite(a).all() for a in (self.x,self.caps,self.sigma)) or not np.isfinite([beta,kappa]).all():raise ValueError('Nonfinite fixed inputs')
        psd_diagnostics(self.sigma);self.H,self.psd=cash_hessian(kernel,self.n)

    def conditional(self,past,inverse_volume):
        """Return H,q,c for future cash+risk. Past-only constants excluded."""
        past=np.asarray(past,dtype=float);inv=np.asarray(inverse_volume,dtype=float)
        if past.ndim!=2 or past.shape[1]!=self.d:raise ValueError('Past shape')
        k=len(past);n=self.n-k
        if n<1 or inv.shape!=(n,self.d) or (inv<=0).any() or not np.isfinite(inv).all() or not np.isfinite(past).all():raise ValueError('Invalid remaining problem')
        x=self.x-past.sum(axis=0);scales=np.maximum(self.x,1.)
        if (x < -1e-8*scales).any() or (past < -1e-8*scales).any() or (past-self.caps[:k]>1e-8*scales).any():raise ValueError('Invalid past state')
        if (x>self.caps[k:].sum(axis=0)+1e-8*scales).any():raise ValueError('Infeasible remaining fixed caps')
        A=np.kron(np.tril(np.ones((n,n)),k=-1),np.eye(self.d))
        R=np.kron(np.eye(n),self.sigma);b=np.tile(x,n);offset=k*self.d
        H=self.H[offset:,offset:]+np.diag((2*self.kappa*inv).ravel())+2*self.beta*A.T@R@A
        impact_linear=self.H[offset:,:offset]@past.ravel()
        q=impact_linear-2*self.beta*A.T@R@b+6e-4
        c=self.beta*float(b@R@b)
        return H,q,c,x,impact_linear

    def solve(self,past,inverse_volume):
        start=time.perf_counter();H,q,c,x,state=self.conditional(past,inverse_volume)
        n=len(inverse_volume);k=self.n-n;d=self.d
        scale=np.where(self.x>0,self.x,1.);rep=np.tile(scale,n);cash=max(self.x.sum()/1e4,1e-12)
        hs=H*rep[:,None]*rep[None,:]/cash;qs=q*rep/cash
        psd_diagnostics(hs)
        equality=sparse.kron(np.ones((1,n)),sparse.eye(d),format='csc')
        constraint=sparse.vstack([sparse.eye(n*d),equality],format='csc')
        lower=np.r_[np.zeros(n*d),x/scale];upper=np.r_[(self.caps[k:]/scale).ravel(),x/scale]
        opt=osqp.OSQP();opt.setup(P=sparse.csc_matrix(np.triu(hs)),q=qs,A=constraint,l=lower,u=upper,
            eps_abs=1e-9,eps_rel=1e-9,max_iter=100000,polishing=True,verbose=False)
        result=opt.solve(raise_error=True)
        if result.info.status!='solved':raise RuntimeError('Nonconverged conditional QP: '+result.info.status)
        w=result.x;z=w.reshape(n,d)*scale;dual=result.y
        primal=max(float(np.max(np.abs(z.sum(axis=0)-x)/scale)),float(np.max(np.maximum(-z,0)/scale)),float(np.max(np.maximum(z-self.caps[k:],0)/scale)))
        g=hs@w+qs;station=g+constraint.T@dual
        den=max(float(np.max(np.abs(g))),float(np.max(np.abs(dual))),np.finfo(float).tiny)
        kkt=float(np.max(np.abs(station))/den)
        db=dual[:n*d];comp=max(float(np.max(np.abs(np.minimum(db,0)*w))),float(np.max(np.abs(np.maximum(db,0)*(upper[:n*d]-w)))))
        if primal>1e-7 or kkt>2e-6 or comp>2e-6*max(den,1.):raise RuntimeError(f'Conditional KKT/feasibility failure {primal} {kkt} {comp}')
        before=x-np.vstack([np.zeros(d),np.cumsum(z,axis=0)[:-1]])
        decomposition=(.5*z.ravel()@self.H[k*d:,k*d:]@z.ravel()+state@z.ravel()+self.kappa*np.sum(z*z*inverse_volume)
                       +self.beta*np.einsum('ki,ij,kj->',before,self.sigma,before)+6e-4*z.sum())
        quadratic=.5*z.ravel()@H@z.ravel()+q@z.ravel()+c
        residual=abs(decomposition-quadratic)/max(abs(quadratic),cash)
        if residual>1e-8:raise RuntimeError('Conditional objective decomposition')
        return z,dict(k=k,seconds=time.perf_counter()-start,iterations=result.info.iter,
            primal=primal,kkt=kkt,complementarity=comp,decomposition=residual,
            remaining=x.tolist(),history_gradient_usdt_per_usdt=state.reshape(n,d)[0].tolist(),
            conditional_objective_QA_only_usdt=float(quadratic))


def replay(qp,forecast,adaptive=True,scenario=False,median=False,factors=None,cadence=5):
    """Callback(k) supplies as-of point volume; commit immutable trade prefixes."""
    from ..liquidity.forecasts import bands
    past=np.empty((0,qp.d));records=[];forecasts=[]
    for k in range(0,qp.n,cadence if adaptive else qp.n):
        point=forecast(k);b=bands(point,factors) if scenario or median else None
        inv=(np.sum(np.array([.25,.5,.25])[None,:,None]/b,axis=1) if scenario else 1/b[:,1,:] if median else 1/point)
        z,diagnostic=qp.solve(past,inv);count=min(cadence if adaptive else qp.n,len(z))
        prefix=z[:count].copy();prefix.setflags(write=False)
        records.append(dict(**diagnostic,prefix=prefix.tolist(),point_forecast=point.tolist()))
        past=np.vstack([past,prefix]);forecasts.append(point[:count])
    if np.max(np.abs(past.sum(axis=0)-qp.x)/np.maximum(qp.x,1.))>1e-7:raise RuntimeError('Terminal liquidation failure')
    return past,records,np.vstack(forecasts)
