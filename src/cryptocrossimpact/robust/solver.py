"""Scaled finite-kernel QCQP + joint-capacity CVaR; no source-data I/O."""
import time
import cvxpy as cp
import numpy as np
from scipy.linalg import eigh
from ..execution.adaptive import AdaptiveQP
from ..execution.impact_cost import cash_hessian,psd_diagnostics
from .scenarios import overload,empirical_cvar


def root_psd(h):
    qa=psd_diagnostics(h);v,u=eigh(h)
    # Only roundoff eigenvalues admitted by the independent PSD check; no
    # material projection/regularizer. Reconstruction error is verified/logged.
    r=np.sqrt(np.maximum(v,0))[:,None]*u.T
    err=np.max(np.abs(r.T@r-h))/max(np.max(np.abs(h)),np.finfo(float).tiny)
    if err>1e-10:raise ValueError('PSD root reconstruction failure')
    return r,dict(**qa,root_relative_reconstruction=err,roundoff_negative_eigenvalues=int((v<0).sum()))


class Template:
    """DPP template shared across episodes of same remaining size/scenario count."""
    def __init__(self,n,d,g,S,liquidity):
        m=n*d;self.w=cp.Variable(m);self.h=cp.Parameter((m,m));self.q=cp.Parameter(m)
        self.cap=cp.Parameter(m);self.remaining=cp.Parameter(d);self.g=g
        self.roots=[cp.Parameter((m,m)) for _ in range(g)];self.states=[cp.Parameter(m) for _ in range(g)]
        w=self.w;self.constraints=[w>=0,w<=self.cap,cp.sum(cp.reshape(w,(n,d),order='C'),axis=0)==self.remaining]
        self.t=cp.Variable();self.epi=[]
        objective=.5*cp.sum_squares(self.h@w)+self.q@w
        if g==1:
            objective+=.5*cp.sum_squares(self.roots[0]@w)+self.states[0]@w
        else:
            for R,s in zip(self.roots,self.states):
                constraint=.5*cp.sum_squares(R@w)+s@w<=self.t;self.constraints.append(constraint);self.epi.append(constraint)
            objective+=self.t
        self.liquidity=liquidity
        if liquidity:
            self.weights=cp.Parameter(m,nonneg=True);self.capacity=cp.Parameter((S,m),nonneg=True);self.lam=cp.Parameter(nonneg=True)
            self.u=cp.Variable((S,m));self.a=cp.Variable();self.b=cp.Variable(S)
            self.liq_constraints=[self.u>=0,cp.multiply(self.weights,w)[None,:]-self.capacity<=self.u,
                cp.sum(self.u,axis=1)-self.a<=self.b,self.b>=0,self.a>=0]
            self.constraints.extend(self.liq_constraints)
            objective+=self.lam*(self.a+cp.sum(self.b)/(.1*S))
        self.problem=cp.Problem(cp.Minimize(objective),self.constraints)
        if not self.problem.is_dpp():raise ValueError('Non-DPP robust template')


class RobustQP:
    templates={}
    def __init__(self,kernels,initial,caps,covariance,beta,force_full=False):
        if not kernels:raise ValueError('Empty ambiguity set')
        self.names=[name for name,_ in kernels];self.kernels=[k for _,k in kernels]
        self.base=AdaptiveQP(self.kernels[0],initial,caps,covariance,beta)
        self.H=[cash_hessian(k,len(caps))[0] for k in self.kernels]
        # Exact elementwise order proves remaining-cost dominance for ALL
        # nonnegative past/future sales. Family is unchanged, only redundant
        # constraints are eliminated; always audit all original scenario costs.
        dominant=next((i for i,h in enumerate(self.H) if all(np.min(h-other)>=0 for other in self.H)),None)
        self.indices=[dominant] if dominant is not None and not force_full else list(range(len(self.H)))
        self.fast=AdaptiveQP(self.kernels[dominant],initial,caps,covariance,beta) if dominant is not None and not force_full else None

    def solve(self,past,point,paths=None,lam=0,solver='CLARABEL',_refinement=0):
        start=time.perf_counter();base=self.base
        if lam<0 or not np.isfinite(lam):raise ValueError('Invalid preference')
        full,q,c,x,_=base.conditional(past,1/point);k=len(past);n=len(point);d=base.d;m=n*d;off=k*d
        original_scale=np.where(base.x>0,base.x,1.);rep=np.tile(original_scale,n);W=float(base.x.sum());cash=max(W/1e4,1e-12)
        if W<=0:
            z,diag=base.solve(past,1/point);return z,dict(**diag,active_scenario='zero_inventory',cvar=0,epigraph_gap=0)
        if lam==0 and self.fast is not None:
            z,qa=self.fast.solve(past,1/point)
            costs=[.5*z.ravel()@H[off:,off:]@z.ravel()+z.ravel()@H[off:,:off]@np.asarray(past).ravel() for H in self.H]
            selected=self.indices[0]
            if max(costs)-costs[selected]>1e-9*max(abs(max(costs)),cash):raise RuntimeError('Dominance certificate failed')
            weights=np.zeros(len(costs));weights[selected]=1
            return z,dict(**qa,active_scenario=self.names[selected],scenario_dual_weights=weights.tolist(),scenario_future_cost_usdt=costs,
                epigraph_gap=0.,cvar=0.,liquidity_preference_usdt=0.,solver='OSQP_certified_singleton',dominance_reduction=True)
        common=full-self.H[0][off:,off:];common_q=q-self.H[0][off:,:off]@np.asarray(past).ravel()
        A=common*rep[:,None]*rep[None,:]/cash;qs=common_q*rep/cash
        root,_=root_psd(A);hg=[];states=[];roots=[]
        for index in self.indices:
            H=self.H[index]
            h=H[off:,off:]*rep[:,None]*rep[None,:]/cash;s=rep*(H[off:,:off]@np.asarray(past).ravel())/cash
            r,_=root_psd(h);hg.append(h);states.append(s);roots.append(r)
        use=lam>0
        if use and (paths is None or np.asarray(paths).shape!=(12,n,d) or not np.isfinite(paths).all() or (paths<0).any()):raise ValueError('Twelve positive-or-zero joint paths required')
        S=12;key=(n,d,len(hg),use)
        if key not in self.templates:self.templates[key]=Template(n,d,len(hg),S,use)
        t=self.templates[key];t.h.value=root;t.q.value=qs;t.cap.value=(base.caps[k:]/original_scale).ravel();t.remaining.value=x/original_scale
        for R,s,r,v in zip(t.roots,t.states,roots,states):R.value=r;s.value=v
        if use:t.weights.value=rep/W;t.capacity.value=.1*np.asarray(paths).reshape(S,m)/W;t.lam.value=lam
        if solver not in ['CLARABEL','SCS']:raise ValueError('QCQP requires verified conic backend')
        attempts=[]
        for step in ([.99,.95,.90] if solver=='CLARABEL' else [None]):
            tolerance=1e-8*(.1**_refinement)
            options=dict(tol_gap_abs=tolerance,tol_gap_rel=tolerance,tol_feas=tolerance,max_iter=300,max_step_fraction=step) if solver=='CLARABEL' else dict(eps=1e-7,max_iters=30000)
            t.problem.solve(solver=solver,warm_start=False,**options)
            attempts.append(dict(max_step_fraction=step,status=t.problem.status))
            if t.problem.status=='optimal':break
        if t.problem.status!='optimal' or t.w.value is None:
            if solver=='CLARABEL' and _refinement<2:
                z,d=self.solve(past,point,paths,lam,solver,_refinement+1)
                d['solver_attempts']=attempts+d['solver_attempts'];d['seconds']=time.perf_counter()-start
                return z,d
            raise RuntimeError('Robust QCQP '+str(t.problem.status))
        w=t.w.value;z=w.reshape(n,d)*original_scale
        costs=np.array([.5*w@h@w+s@w for h,s in zip(hg,states)]);multipliers=np.array([np.asarray(a.dual_value).item() for a in t.epi]) if t.epi else np.ones(1)
        tg=float(t.t.value) if t.epi else float(costs[0]);gradient=A@w+qs
        for a,h,s in zip(multipliers,hg,states):gradient+=a*(h@w+s)
        lo,hi,eq=[a.dual_value for a in t.constraints[:3]];gradient=gradient-lo+hi+np.tile(eq,n)
        station_other=[1-multipliers.sum()];comps=[np.max(np.abs(lo*w)),np.max(np.abs(hi*(t.cap.value-w))),np.max(np.abs(multipliers*(tg-costs)))]
        dual_min=min(float(lo.min()),float(hi.min()),float(multipliers.min()))
        cvar=0.;liq_primal=0.
        if use:
            nu,mu,gamma,delta,eta=[a.dual_value for a in t.liq_constraints]
            gradient+=mu.sum(axis=0)*(rep/W)
            station_other.extend([lam-gamma.sum()-eta,*list(lam/(.1*S)-gamma-delta),*list((-nu-mu+gamma[:,None]).ravel())])
            u=t.u.value;b=t.b.value;a=float(t.a.value);capacity=t.capacity.value
            liq_primal=max(float(np.maximum(-u,0).max()),float(np.maximum(w[None,:]*(rep/W)-capacity-u,0).max()),
                float(np.maximum(u.sum(axis=1)-a-b,0).max()),float(np.maximum(-b,0).max()),max(-a,0.))
            comps.extend([np.max(np.abs(nu*u)),np.max(np.abs(mu*(u-w[None,:]*(rep/W)+capacity))),
                np.max(np.abs(gamma*(b-u.sum(axis=1)+a))),np.max(np.abs(delta*b)),abs(eta*a)])
            dual_min=min(dual_min,float(nu.min()),float(mu.min()),float(gamma.min()),float(delta.min()),float(eta))
            cvar=empirical_cvar([overload(z,v,W) for v in paths])
        den=max(float(np.max(np.abs(A@w+qs))),float(np.max(np.abs(lo))),float(np.max(np.abs(hi))),float(np.max(np.abs(eq))),lam,1.)
        station=max(float(np.max(np.abs(gradient))),float(np.max(np.abs(station_other))))/den
        primal=max(float(np.max(np.abs(z.sum(axis=0)-x)/original_scale)),float(np.maximum(-w,0).max()),
            float(np.maximum(w-t.cap.value,0).max()),float(np.maximum(costs-tg,0).max())/max(abs(tg),1.),liq_primal)
        epigap=abs(tg-costs.max())/max(abs(tg),1.)
        calculated=.5*w@A@w+qs@w+costs.max()+lam*cvar
        decomp=abs(float(t.problem.value)-calculated)/max(abs(calculated),1.)
        complement=float(max(comps))/max(abs(calculated),1.)
        if primal>1e-7 or station>2e-5 or epigap>2e-5 or decomp>2e-5 or complement>2e-5 or dual_min< -1e-7:
            if solver=='CLARABEL' and _refinement<2:
                z,d=self.solve(past,point,paths,lam,solver,_refinement+1)
                d['solver_attempts']=attempts+[dict(refine_after_KKT=station)]+d['solver_attempts'];d['seconds']=time.perf_counter()-start
                return z,d
            raise RuntimeError(f'QCQP QA failed primal={primal} KKT={station} epi={epigap} decomposition={decomp} comp={complement}')
        # Independent physical future-impact expansion, not a local-objective sum.
        physical=[.5*z.ravel()@H[off:,off:]@z.ravel()+z.ravel()@H[off:,:off]@np.asarray(past).ravel() for H in self.H]
        if np.max(np.abs(np.array(physical)[self.indices]/cash-costs))>1e-9*max(abs(costs).max(),1):raise RuntimeError('Impact units/order identity')
        if max(physical)/cash-costs.max()>1e-9*max(abs(costs).max(),1):raise RuntimeError('Dominance certificate failed')
        active=int(np.argmax(physical));all_multipliers=np.zeros(len(self.H));all_multipliers[self.indices]=multipliers
        return z,dict(k=k,seconds=time.perf_counter()-start,primal=primal,kkt=station,complementarity=complement,epigraph_gap=epigap,
            decomposition=decomp,cvar=cvar,liquidity_preference_usdt=cash*lam*cvar,
            active_scenario=self.names[active],scenario_dual_weights=all_multipliers.tolist(),dominance_reduction=len(self.indices)<len(self.H),
            scenario_future_cost_usdt=physical,conditional_objective_QA_only_usdt=float(calculated*cash+c),
            remaining=x.tolist(),history_gradient_usdt_per_usdt=(self.H[active][off:,:off]@np.asarray(past).ravel()).reshape(n,d)[0].tolist(),
            solver=solver,solver_attempts=attempts,iterations=int(t.problem.solver_stats.num_iters))
