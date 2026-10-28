import copy
import json
from pathlib import Path

import cvxpy as cp
import numpy as np
import pandas as pd
import pytest
from scipy.integrate import dblquad

from cryptocrossimpact.data.pipeline import ROOT
from cryptocrossimpact.execution.ajnt_benchmark import (paper_system,nystrom,galerkin,exponential_analytic,integrated_rate_blocks)
from cryptocrossimpact.execution.impact_cost import (ASSETS,Kernel,adapt_stage02,load_stage02,exponential_factors,cash_hessian,triangular_cash,psd_diagnostics)
from cryptocrossimpact.execution.solver import (InfeasibleCapacity,build_problem,capped_uniform_reference,decompose,solve_execution)


def toy(c=None,l=(1e5,2e5),tau=12.,assets=ASSETS):
    c=np.array([[1.,-.2],[-.2,.8]]) if c is None else np.array(c,dtype=float)
    return Kernel(assets,c[None],np.array([tau]),np.array(l))


def test_paper_zero_exact_terminal_penalty_and_endpoint_columns():
    c=np.array([[.06,.05],[.05,.06]])
    t,d,l,u=paper_system(20,'exponential',c)
    assert len(t)==21 and not l[:,-1].any() and not u[:,-1].any()
    step=(1-np.exp(-.5*.5))/.5
    assert l[1,0]==pytest.approx(step)
    assert u[0,0]==pytest.approx(step)
    assert u[0,1]==pytest.approx(step*np.exp(-.5*.5))
    r=nystrom(20,'zero',c)
    np.testing.assert_allclose(r['rates'][:,0],-40/(40+.03),atol=1e-12)
    np.testing.assert_allclose(r['rates'][:,1],0,atol=1e-12)
    assert r['inventory'][-1,0]==pytest.approx(10*.03/(40+.03))
    assert r['inventory'][-1,0]>0  # finite penalty, never hard liquidation
    expected=.5*.03*10*(40/(40+.03))**2+.5*4*(10*.03/(40+.03))**2
    assert r['objective']['total']==pytest.approx(expected)


def test_paper_signed_cross_behavior_and_analytic_grid_convergence():
    c=np.array([[.06,.05],[.05,.06]]);errors=[]
    for n in [40,80,160]:
        r=nystrom(n,'exponential',c);a=exponential_analytic(r['times'],c)
        errors.append(np.max(np.abs(r['inventory']-a['inventory'])))
        assert r['first_order_relative_residual']<1e-11
    assert errors[2]<errors[1]<errors[0]
    assert errors[-1]<.1
    assert r['rates'][0,1]<0 and r['rates'][-1,1]<0 and r['rates'][len(r['rates'])//2,1]>0
    assert r['inventory'][:,1].min()<-.1 and r['inventory'][:,1].max()>.1
    diagonal=nystrom(80,'exponential',np.diag([.06,.06]))
    assert np.max(np.abs(diagonal['rates'][:,1]))<1e-12


@pytest.mark.parametrize('kind',['zero','exponential','fractional'])
def test_paper_independent_galerkin_and_fractional_cells(kind):
    c=np.array([[.06,.05],[.05,.06]])
    coarse=nystrom(40,kind,c);fine=nystrom(80,kind,c);ind=galerkin(80,kind,c)
    assert np.isfinite(fine['rates']).all()
    assert ind['first_order_relative_residual']<1e-10
    # Both schemes converge to the same continuous objective, with distinct cells.
    assert abs(fine['objective']['total']-ind['objective']['total'])<abs(coarse['objective']['total']-ind['objective']['total'])+1e-10
    if kind=='fractional':
        n=4;d=10/n;matrix=integrated_rate_blocks(n,kind)
        expected=2*d**(2-.25)/((1-.25)*(2-.25))
        assert matrix[0,0]==pytest.approx(expected)


@pytest.mark.parametrize('delta,tau',[(1.,60.),(2.,.7),(.5,30.),(1.,1e10)])
def test_exact_exponential_cells_independent_quadrature(delta,tau):
    a=exponential_factors(3,delta,tau)
    same=dblquad(lambda s,t:np.exp(-(t-s)/tau),0,delta,lambda t:0,lambda t:t,epsabs=1e-12,epsrel=1e-12)[0]/delta**2
    across=dblquad(lambda s,t:np.exp(-(t-s)/tau),delta,2*delta,lambda t:0,lambda t:delta,epsabs=1e-12,epsrel=1e-12)[0]/delta**2
    np.testing.assert_allclose(a[:2],[same,across],rtol=2e-11,atol=1e-13)
    assert a[0]>0 and a[0]<=.5


def test_scalar_cash_hand_calculation_and_one_basis_point_conversion():
    k=Kernel(('BTCUSDT',),np.array([[[3.]]]),np.array([1e15]),np.array([4.]))
    one=np.array([[2.]])
    assert triangular_cash(k,one)==pytest.approx(.00015,rel=1e-12)
    two=np.array([[2.],[4.]])
    assert triangular_cash(k,two)==pytest.approx(.00135,rel=1e-12)
    h,_=cash_hessian(k,2)
    assert .5*two.ravel()@h@two.ravel()==pytest.approx(.00135,rel=1e-12)
    # Two assets in one cell, C PSD with negative cross entries.
    k=toy(l=(4.,9.),tau=1e15);z=np.array([[2.,3.]])
    expected=1e-4*.5*np.array([1.,1.])@k.matrices[0]@np.array([1.,1.])
    assert triangular_cash(k,z)==pytest.approx(expected,rel=1e-12)


@pytest.mark.parametrize('c',[[[1,.3],[.3,.8]],[[1,-.3],[-.3,.8]],[[0,0],[0,0]],[[1,0],[0,0]]])
def test_hessian_identity_psd_and_signed_round_trips(c):
    k=toy(c);h,diag=cash_hessian(k,8,.5);rng=np.random.default_rng(3)
    assert diag['relative_min_eigenvalue']>=-1e-9
    for _ in range(5):
        z=rng.normal(size=(8,2))*10000;z-=z.mean(axis=0)
        cash=triangular_cash(k,z,.5)
        assert cash>=-1e-10
        assert cash==pytest.approx(.5*z.ravel()@h@z.ravel(),rel=1e-11,abs=1e-12)
        assert triangular_cash(k,2*z,.5)==pytest.approx(4*cash,rel=1e-12,abs=1e-12)


def test_indefinite_even_tiny_coordinates_rejected():
    for scale in [1.,1e-15]:
        with pytest.raises(ValueError,match='indefinite'):toy(np.array([[1,2],[2,1]])*scale)
    with pytest.raises(ValueError,match='symmetric'):psd_diagnostics([[1,.1],[0,1]])
    with pytest.raises(ValueError):toy(tau=0)
    with pytest.raises(ValueError):toy(l=(0,1))


def test_no_undeclared_sixty_minute_kernel_cutoff_and_half_cell_limit():
    k=load_stage02(ROOT,'B')
    assert k.level([120])[0,0,0]>0
    discrepancies=[]
    for d in [2.,1.,.5]:
        n=round(60/d);z=np.tile([100.,200.],(n,1))*d
        exact=triangular_cash(k,z,d)
        half=triangular_cash(k,z,d,'half_cell_sampled')
        discrepancies.append(abs(exact-half))
    assert discrepancies[2]<discrepancies[1]<discrepancies[0]
    np.testing.assert_allclose(exponential_factors(1,1e-8,60),[.5],atol=1e-10)


@pytest.mark.parametrize('constant',[False,True])
def test_zero_impact_no_risk_volume_proportional_analytic_limit(constant):
    k=toy(np.zeros((2,2)));v=np.tile([1000.,700.],(8,1))
    if not constant:v*=np.linspace(.5,2,8)[:,None]
    x=.04*v.sum(axis=0)
    r=solve_execution(k,x,v,np.zeros((2,2)),theta=0)
    np.testing.assert_allclose(r['schedule_usdt'],v*x/v.sum(axis=0),rtol=1e-7,atol=1e-7)
    assert r['diagnostics']['zero_risk_fallback']
    assert r['diagnostics']['effective_theta']==0


def test_capped_projection_exact_and_infeasible():
    caps=np.array([[.1,2],[2,2],[2,2],[2,2],[2,2.]])
    z=capped_uniform_reference([5.,0.],caps)
    np.testing.assert_allclose(z[:,0],[.1,1.225,1.225,1.225,1.225],atol=1e-12)
    np.testing.assert_allclose(z[:,1],0)
    k=toy()
    with pytest.raises(InfeasibleCapacity):solve_execution(k,[1000,1000],np.ones((4,2)),np.eye(2))


def test_diagonal_joint_equals_independent_scalar_qps_with_common_risk_multiplier():
    k=toy(np.diag([1.,.8]));v=np.tile([1e5,6e4],(12,1));x=.02*v.sum(axis=0)
    sigma=np.diag([1e-6,2e-6]);p=build_problem(k,x,v,sigma)
    r=solve_execution(k,x,v,sigma)
    for i in range(2):
        at=np.arange(i,24,2);h=p.hessian[np.ix_(at,at)];linear=p.linear[at]
        z=cp.Variable(12)
        # Independent scalar solve uses the JOINT reference risk multiplier;
        # renormalizing each leg separately would change the mathematical problem.
        opt=cp.Problem(cp.Minimize((.5*cp.quad_form(z,cp.psd_wrap(h))+linear@z)/(x.sum()/1e4)),[z>=0,z<=p.caps[:,i],cp.sum(z)==x[i]])
        opt.solve(solver='CLARABEL',tol_gap_abs=1e-10,tol_gap_rel=1e-10,tol_feas=1e-10)
        assert opt.status=='optimal'
        np.testing.assert_allclose(r['schedule_usdt'][:,i],z.value,rtol=1e-5,atol=.002)


def test_asset_permutation_and_mismatched_order_rejected():
    k=toy();v=np.tile([1e5,6e4],(12,1));x=.02*v.sum(axis=0);sigma=np.array([[1e-6,.4e-6],[.4e-6,2e-6]])
    a=solve_execution(k,x,v,sigma)
    permuted=Kernel(ASSETS[::-1],k.matrices[:,::-1,::-1],k.taus_minutes,k.liquidity_usdt[::-1])
    with pytest.raises(ValueError,match='Asset order'):solve_execution(permuted,x,v,sigma)
    b=solve_execution(permuted,x[::-1],v[:,::-1],sigma[::-1,::-1],assets=ASSETS[::-1])
    np.testing.assert_allclose(a['schedule_usdt'][:,::-1],b['schedule_usdt'],rtol=1e-7,atol=1e-5)
    assert a['objective_usdt']==pytest.approx(b['objective_usdt'],rel=1e-10)


@pytest.mark.parametrize('cap,kappa,theta',[(.05,.0005,0),(.1,.001,1),(.2,.005,2)])
def test_full_liquidation_caps_monotonic_inventory_and_objective(cap,kappa,theta):
    k=load_stage02(ROOT,'B');v=np.tile([2e6,1.1e6],(20,1));x=.02*v.sum(axis=0);sigma=np.array([[1e-6,.4e-6],[.4e-6,2e-6]])
    r=solve_execution(k,x,v,sigma,cap_fraction=cap,kappa=kappa,theta=theta)
    np.testing.assert_allclose(r['schedule_usdt'].sum(axis=0),x,rtol=1e-9,atol=1e-6)
    assert r['schedule_usdt'].min()>-1e-5
    assert np.max(r['schedule_usdt']-cap*v)<1e-5
    assert np.max(np.diff(np.vstack([x,r['h_after_usdt']]),axis=0))<1e-5
    p=build_problem(k,x,v,sigma,cap_fraction=cap,kappa=kappa,theta=theta)
    c=r['components']
    assert c['objective_usdt']==pytest.approx(c['transient_usdt']+c['temporary_usdt']+c['risk_preference_usdt']+c['fee_usdt']+c['spread_usdt']+c['drift_usdt'])
    expected_risk=np.einsum('ki,ij,kj->',r['h_before_usdt'],sigma,r['h_before_usdt'])
    assert c['raw_inventory_risk_usdt_squared']==pytest.approx(expected_risk)
    assert r['diagnostics']['relative_stationarity_residual']<2e-6


def test_zero_inventory_leg_is_not_a_hedge_round_trip():
    k=toy();v=np.ones((10,2))*1e5
    r=solve_execution(k,[1e4,0],v,np.eye(2)*1e-6)
    assert np.max(np.abs(r['schedule_usdt'][:,1]))<1e-7
    assert abs(r['terminal_inventory_usdt'][0])<1e-6


def test_fee_invariance_and_independent_backend():
    k=toy();v=np.ones((10,2))*1e5;x=.02*v.sum(axis=0);sigma=np.array([[1e-6,.4e-6],[.4e-6,2e-6]])
    no=solve_execution(k,x,v,sigma,fee_bps=0,half_spread_bps=0)
    fees=solve_execution(k,x,v,sigma)
    other=solve_execution(k,x,v,sigma,solver='CLARABEL')
    np.testing.assert_allclose(no['schedule_usdt'],fees['schedule_usdt'],rtol=1e-6,atol=1e-5)
    assert fees['objective_usdt']-no['objective_usdt']==pytest.approx(6e-4*x.sum(),rel=1e-9)
    np.testing.assert_allclose(fees['schedule_usdt'],other['schedule_usdt'],rtol=1e-5,atol=.001)
    assert fees['objective_usdt']==pytest.approx(other['objective_usdt'],rel=1e-8)


@pytest.mark.parametrize('fault',['zero_volume','negative_volume','nan_volume','indefinite_covariance','negative_inventory','delta','drift_shape'])
def test_invalid_inputs_fail_loudly(fault):
    k=toy();v=np.ones((4,2))*1e5;x=np.array([100.,200.]);sigma=np.eye(2);kwargs={}
    if fault=='zero_volume':v[0,0]=0
    elif fault=='negative_volume':v[0,0]=-1
    elif fault=='nan_volume':v[0,0]=np.nan
    elif fault=='indefinite_covariance':sigma=np.array([[1,2],[2,1]])
    elif fault=='negative_inventory':x[0]=-1
    elif fault=='delta':kwargs['delta_minutes']=0
    else:kwargs['expected_price_change']=np.zeros(2)
    with pytest.raises(ValueError):solve_execution(k,x,v,sigma,**kwargs)


@pytest.mark.parametrize('fault',['U','asset_order','unit','schema','cutoff','matrix','source_ids','market'])
def test_adapter_rejects_unverified_schema_market_or_model(fault):
    m=json.loads((ROOT/'reports/research/stage02_artifacts/model_B.json').read_text())
    if fault=='U':m['model']='U'
    elif fault=='asset_order':m['asset_order']=list(reversed(ASSETS))
    elif fault=='unit':m['units']='base coins or seconds'
    elif fault=='schema':m['unidentified_version']=2
    elif fault=='cutoff':m['provenance']['data_latest_open_utc']='2026-01-01T00:00:00Z'
    elif fault=='matrix':m['matrices']=[[[1,2],[2,1]]]
    elif fault=='source_ids':m['provenance']['development_partition_ids']=['SOLUSDT/2025-01']
    else:m['provenance']['market']='spot'
    with pytest.raises(ValueError):adapt_stage02(m)


def test_model_hash_and_no_market_data_read(monkeypatch):
    def forbidden(*args,**kwargs):raise AssertionError('Stage 3 must not read outcome rows')
    monkeypatch.setattr(pd,'read_parquet',forbidden)
    for name in ['A','B']:
        k=load_stage02(ROOT,name)
        r=solve_execution(k,[100.,100.],np.ones((4,2))*1e5,np.eye(2)*1e-6)
        assert r['status']=='optimal'
    with pytest.raises(ValueError):load_stage02(ROOT,'U')
    with pytest.raises(ValueError,match='firewall'):load_stage02(ROOT,'B',ROOT/'data/canonical/BTCUSDT/2026-01.parquet')


def test_continuous_input_grid_convergence_and_risk_time_units():
    k=load_stage02(ROOT,'B');rate=np.array([2e6,1.1e6]);x=.02*rate*60
    sigma=np.array([[1e-6,.4e-6],[.4e-6,2e-6]]);solutions={}
    for delta in [2.,1.,.5,.25]:
        v=np.tile(rate*delta,(round(60/delta),1))
        p=build_problem(k,x,v,sigma,delta_minutes=delta)
        np.testing.assert_array_equal(p.covariance_slice,sigma*delta)
        assert p.risk_multiplier*p.reference_raw_risk==pytest.approx(x.sum()/1e4)
        np.testing.assert_allclose(v.sum(axis=0),rate*60)
        solutions[delta]=solve_execution(k,x,v,sigma,delta_minutes=delta)
    ref=solutions[.25];t=np.linspace(0,60,241);fine=np.vstack([x,ref['h_after_usdt']]);errors=[]
    for delta in [2.,1.,.5]:
        h=np.vstack([x,solutions[delta]['h_after_usdt']])
        interpolated=np.column_stack([np.interp(t,np.linspace(0,60,len(h)),h[:,i]) for i in range(2)])
        errors.append(np.max(np.abs(interpolated-fine)/x))
    assert errors[2]<errors[1]<errors[0] and errors[-1]<.002


def test_risk_reference_capped_normalization_and_preknown_drift_units():
    k=toy();v=np.ones((6,2))*1e5;v[0]=[1.,2.];x=np.array([1e4,2e4])
    sigma=np.array([[1e-6,.4e-6],[.4e-6,2e-6]])
    p=build_problem(k,x,v,sigma,theta=2,delta_minutes=.5,expected_price_change=np.full_like(v,.001))
    assert np.max(p.reference_schedule-p.caps)<1e-7
    np.testing.assert_allclose(p.reference_schedule.sum(axis=0),x,atol=1e-6)
    costs=decompose(k,p,p.reference_schedule)
    assert costs['risk_preference_usdt']==pytest.approx(2*x.sum()/1e4)
    assert costs['drift_usdt']==pytest.approx(-.001*x.sum())
    assert costs['fee_usdt']==pytest.approx(5e-4*x.sum())
    assert costs['spread_usdt']==pytest.approx(1e-4*x.sum())


def test_active_participation_caps_in_the_qp():
    k=toy(np.zeros((2,2)));v=np.ones((8,2))*1000.;x=.09*v.sum(axis=0)
    result=solve_execution(k,x,v,np.eye(2)*1e-6,theta=2,cap_fraction=.1)
    np.testing.assert_allclose(result['schedule_usdt'][0],.1*v[0],atol=1e-6)
    assert np.max(result['schedule_usdt']-.1*v)<1e-6
    np.testing.assert_allclose(result['schedule_usdt'].sum(axis=0),x,atol=1e-6)
    assert result['diagnostics']['relative_stationarity_residual']<1e-7
