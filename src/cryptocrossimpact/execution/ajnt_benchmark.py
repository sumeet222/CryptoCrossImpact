"""AJNT_DETERMINISTIC_BENCHMARK: v2 §§2.2, 3.1, 3.4 only.

Paper units, unrestricted signed rate u=dX/dt, finite terminal penalty.
This is separate from the crypto sell-only, hard-terminal constrained solver.
"""
import numpy as np
from scipy.linalg import solve, svdvals

from .impact_cost import exponential_factors


def paper_system(n,kind,c,horizon=10.,rho=.5,alpha=.25,temporary=.03,penalty=4.):
    """Exact Table 1 cell integrals at n+1 collocation nodes; no inverse.

    Dn=I⊗Lambda+(L+U)⊗C+varrho(L2+U2)⊗Pi for gamma=0,
    Pi=I. g=-varrho Pi X0. U includes its diagonal; the final column
    of every integration matrix is zero (u(T) is not an extra time cell).
    """
    if n<2 or kind not in ("zero","exponential","fractional"):
        raise ValueError("Invalid paper grid/kernel")
    c=np.asarray(c,dtype=float)
    if c.shape!=(2,2) or not np.allclose(c,c.T):raise ValueError("Paper C must be symmetric 2x2")
    d=horizon/n;times=np.linspace(0,horizon,n+1)
    k,j=np.indices((n+1,n+1));lower=(j<k);upper=(j>=k)&(j<n)
    l=np.zeros_like(k,dtype=float);u=np.zeros_like(l)
    if kind=="exponential":
        step=-np.expm1(-rho*d)/rho
        l[lower]=step*np.exp(-rho*(k[lower]-j[lower]-1)*d)
        u[upper]=step*np.exp(-rho*(j[upper]-k[upper])*d)
    elif kind=="fractional":
        if not 0<alpha<.5:raise ValueError("Paper fractional alpha must be square-integrable near zero")
        factor=d**(1-alpha)/(1-alpha)
        m=k[lower]-j[lower]
        l[lower]=factor*(m**(1-alpha)-(m-1)**(1-alpha))
        m=j[upper]-k[upper]
        u[upper]=factor*((m+1)**(1-alpha)-m**(1-alpha))
    l2=lower.astype(float)*d;u2=upper.astype(float)*d
    matrix=np.kron(np.eye(n+1),np.eye(2)*temporary)+np.kron(l+u,c)+penalty*np.kron(l2+u2,np.eye(2))
    return times,matrix,l,u


def integrated_rate_blocks(n,kind,horizon=10.,rho=.5,alpha=.25):
    """Independent Galerkin double-cell integrals, units paper time squared."""
    d=horizon/n;values=np.zeros(n)
    if kind=="exponential":values=d*d*exponential_factors(n,d,1/rho)
    elif kind=="fractional":
        power=2-alpha;factor=d**power/((1-alpha)*(2-alpha))
        values[0]=factor
        m=np.arange(1,n,dtype=float)
        values[1:]=factor*((m+1)**power-2*m**power+(m-1)**power)
    elif kind!="zero":raise ValueError("Unknown paper kernel")
    temporal=values[np.abs(np.arange(n)[:,None]-np.arange(n)[None,:])]
    np.fill_diagonal(temporal,2*values[0])
    return temporal


def paper_objective(rates,c,kind,horizon=10.,rho=.5,alpha=.25,temporary=.03,penalty=4.,initial=(10.,0.)):
    """Minimized cost = transient + .5 Lambda rate^2 + .5 varrho XT Pi XT.

    Pi=I, gamma=0, no signal. No USDT or 1e-4 factors belong in V1.
    """
    u=np.asarray(rates);n=len(u);d=horizon/n
    temporal=integrated_rate_blocks(n,kind,horizon,rho,alpha)
    transient=.5*float(u.ravel()@np.kron(temporal,c)@u.ravel())
    temp=.5*temporary*d*float(np.sum(u*u))
    end=np.array(initial)+d*u.sum(axis=0)
    terminal=.5*penalty*float(end@end)
    return dict(transient=transient,temporary=temp,terminal_penalty=terminal,total=transient+temp+terminal,terminal_inventory=end.tolist())


def nystrom(n,kind,c,horizon=10.,rho=.5,alpha=.25,temporary=.03,penalty=4.,initial=(10.,0.)):
    times,dn,_,_=paper_system(n,kind,c,horizon,rho,alpha,temporary,penalty)
    forcing=np.tile(-penalty*np.array(initial),n+1)
    signed=solve(dn,forcing,assume_a="gen",check_finite=True).reshape(n+1,2)
    residual=float(np.linalg.norm(dn@signed.ravel()-forcing,np.inf)/np.linalg.norm(forcing,np.inf))
    singular=svdvals(dn,check_finite=False)
    inventory=np.vstack([initial,np.array(initial)+(horizon/n)*np.cumsum(signed[:-1],axis=0)])
    return dict(times=times,rates=signed,inventory=inventory,
        first_order_relative_residual=residual,condition_number=float(singular[0]/singular[-1]),
        objective=paper_objective(signed[:-1],c,kind,horizon,rho,alpha,temporary,penalty,initial))


def galerkin(n,kind,c,horizon=10.,rho=.5,alpha=.25,temporary=.03,penalty=4.,initial=(10.,0.)):
    d=horizon/n;temporal=integrated_rate_blocks(n,kind,horizon,rho,alpha)
    hessian=np.eye(2*n)*temporary*d+np.kron(temporal,c)+penalty*d*d*np.kron(np.ones((n,n)),np.eye(2))
    forcing=np.tile(-penalty*d*np.array(initial),n)
    rates=solve(hessian,forcing,assume_a="pos").reshape(n,2)
    inventory=np.vstack([initial,np.array(initial)+d*np.cumsum(rates,axis=0)])
    residual=float(np.linalg.norm(hessian@rates.ravel()-forcing,np.inf)/np.linalg.norm(forcing,np.inf))
    return dict(times=np.linspace(0,horizon,n+1),rates=rates,inventory=inventory,first_order_relative_residual=residual,
                objective=paper_objective(rates,c,kind,horizon,rho,alpha,temporary,penalty,initial))


def exponential_analytic(times,c,horizon=10.,rho=.5,temporary=.03,penalty=4.,initial=(10.,0.)):
    """Independent continuous Fredholm/ODE check, constant Lambda and Pi=I.

    In each C eigenmode, Lambda*v+c*w=k, w''=rho^2*w-2rho*v,
    w'(0)=rho*w(0), w'(T)=-rho*w(T), k=-varrho*XT.
    Boundary conditions yield a constant + cosh rate; finite penalty sets XT.
    This verifies exponential V1 without fitting/digitizing the paper's image.
    """
    values,q=np.linalg.eigh(np.array(c));projections=q.T@np.array(initial)
    times=np.asarray(times);rates=np.empty((len(times),2));inventory=np.empty_like(rates)
    for i,value in enumerate(values):
        omega=np.sqrt(rho*rho+2*rho*value/temporary);half=omega*horizon/2
        denominator=omega*np.sinh(half)+rho*np.cosh(half)
        a=rho*rho/(temporary*omega*omega)
        b=2*value*rho*rho/(temporary**2*omega**2*denominator)
        integral=a*horizon+b*2*np.sinh(half)/omega
        k=-penalty*projections[i]/(1+penalty*integral)
        rates[:,i]=k*(a+b*np.cosh(omega*(times-horizon/2)))
        inventory[:,i]=projections[i]+k*(a*times+b*(np.sinh(omega*(times-horizon/2))+np.sinh(half))/omega)
    return dict(rates=rates@q.T,inventory=inventory@q.T)
