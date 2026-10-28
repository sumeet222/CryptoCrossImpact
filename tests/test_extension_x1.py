"""Focused X1 chronology, continuation, units, scenario and preservation tests."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from cryptocrossimpact.liquidity.forecasts import predict,seasonal,calibrate,bands
from cryptocrossimpact.liquidity.workflow import X1Store,beta_for,episode_policies
from cryptocrossimpact.episodes import construct_episode,config
from cryptocrossimpact.execution.impact_cost import Kernel,cash_hessian,ASSETS
from cryptocrossimpact.execution.adaptive import AdaptiveQP,replay,historical_linear_state
from cryptocrossimpact.execution.solver import solve_execution
from cryptocrossimpact.execution.policies import load_models
from cryptocrossimpact.evaluation.v2_score import World,score_schedule

ROOT=Path(__file__).resolve().parents[1]


def fake(t='2025-08-01T00:00:00Z'):
    t=pd.Timestamp(t);times=pd.date_range(t.normalize()-pd.Timedelta(days=28),t+pd.Timedelta(hours=1),freq='min',inclusive='left')
    n=len(times);v=1e6*(1+.4*np.sin(times.minute.to_numpy()/60*2*np.pi))
    frame=pd.DataFrame(dict(time=times,open_time=times.as_unit('ms').asi8,available_at_utc=times+pd.Timedelta(minutes=1)))
    for i in range(2):
        frame[f'quote_volume_{i}']=v*(i+1);frame[f'valid_bar_{i}']=True
        frame[f'close_{i}']=100*np.exp(.0001*np.sin(np.arange(n)/7+i))
        frame[f'jump_flag_{i}']=False;frame[f'stale_close_flag_{i}']=False
    return frame,t


def kernel(cross=.3):
    return Kernel(ASSETS,np.array([[[1.,cross],[cross,1.4]]]),[15],[1e6,2e6])


def qp_fixture(cross=.3,n=60,zero=False):
    k=kernel(cross);v=np.tile([1e6,2e6],(n,1))*(1+.2*np.sin(np.arange(n)[:,None]/3))
    x=.02*v.sum(axis=0);sigma=np.array([[1e-6,4e-7],[4e-7,2e-6]])
    if zero:x*=0
    return k,v,x,sigma,AdaptiveQP(k,x,.1*v,sigma,1e-6)


@pytest.mark.parametrize('cut',[0,5,55,59])
@pytest.mark.parametrize('cross',[-.5,.5])
def test_conditional_cash_gradient_and_state(cut,cross):
    k,v,x,sigma,qp=qp_fixture(cross)
    rng=np.random.default_rng(12);z=rng.uniform(20,300,(60,2));past=z[:cut];future=z[cut:].ravel();H=qp.H;o=2*cut
    conditional=.5*future@H[o:,o:]@future+future@H[o:,:o]@past.ravel()
    full=.5*z.ravel()@H@z.ravel();constant=.5*past.ravel()@H[:o,:o]@past.ravel()
    assert full-constant==pytest.approx(conditional,rel=1e-12)
    np.testing.assert_allclose(H[o:,:o]@past.ravel(),historical_linear_state(k,past,60-cut).ravel(),rtol=2e-13,atol=1e-18)
    gradient=H[o:,o:]@future+H[o:,:o]@past.ravel()
    for index in [0,len(future)-1]:
        eps=.01;plus=future.copy();minus=future.copy();plus[index]+=eps;minus[index]-=eps
        fun=lambda f:.5*f@H[o:,o:]@f+f@H[o:,:o]@past.ravel()
        assert (fun(plus)-fun(minus))/(2*eps)==pytest.approx(gradient[index],rel=2e-7,abs=1e-12)


@pytest.mark.parametrize('cut',[0,5,55,59])
@pytest.mark.parametrize('cross',[-.5,.5])
def test_unchanged_tail_time_consistency(cut,cross):
    k,v,x,sigma,qp=qp_fixture(cross)
    z,_=qp.solve(np.empty((0,2)),1/v)
    tail,qa=qp.solve(z[:cut],1/v[cut:])
    np.testing.assert_allclose(tail,z[cut:],rtol=1e-6,atol=1e-4)
    assert qa['kkt']<2e-6 and qa['primal']<1e-7
    if cut==5:
        wrong=AdaptiveQP(k,x-z[:cut].sum(axis=0),.1*v[cut:],sigma,qp.beta)
        reset,_=wrong.solve(np.empty((0,2)),1/v[cut:])
        assert np.linalg.norm(reset-tail)>1e-3


def test_prior_solver_parity_and_independent_solver():
    k,v,x,sigma,qp=qp_fixture()
    z,_=qp.solve(np.empty((0,2)),1/v)
    for backend in ['OSQP','CLARABEL']:
        old=solve_execution(k,x,v,sigma,risk_multiplier_override=qp.beta,solver=backend)
        np.testing.assert_allclose(z,old['schedule_usdt'],rtol=2e-7,atol=1e-3)


@pytest.mark.parametrize('n',[1,5,60])
def test_zero_inventory_zero_kernel(n):
    k,v,x,sigma,qp=qp_fixture(n=n,zero=True)
    z,_=qp.solve(np.empty((0,2)),1/v);np.testing.assert_allclose(z,0,atol=1e-12)
    zero=Kernel(ASSETS,np.zeros((1,2,2)),[15],[1e6,2e6]);x=.02*v.sum(axis=0)
    q=AdaptiveQP(zero,x,.1*v,np.zeros((2,2)),0)
    z,_=q.solve(np.empty((0,2)),1/v)
    np.testing.assert_allclose(z,v*(x/v.sum(axis=0)),rtol=1e-7,atol=1e-6)


@pytest.mark.parametrize('date',['2025-07-31T23:55:00Z','2025-08-01T00:00:00Z','2025-12-01T06:00:00Z'])
def test_forecast_future_mutation_and_profile(date):
    f,t=fake(date);target=pd.date_range(t,periods=60,freq='min');p=predict(f,t,target)
    changed=f.copy();mask=changed.time>=t
    for name in changed.columns:
        if name.startswith(('quote_volume','close')):changed.loc[mask,name]=np.nan
    changed.loc[mask,'valid_bar_0']=False
    q=predict(changed,t,target)
    for m in ['V0','V1','V2']:assert p[m].tobytes()==q[m].tobytes()
    profile,qa=seasonal(f,t)
    np.testing.assert_allclose(profile.mean(axis=0),1,rtol=1e-14)
    assert (profile>0).all() and np.ptp(profile[:,0])>.1
    assert np.ptp(p['V1'][:,0])>1e4


def test_zero_volume_partial_hour_and_scenarios():
    f,t=fake();f.loc[(f.time<t)&(f.time.dt.minute==3),'quote_volume_0']=0
    profile,qa=seasonal(f,t);assert (profile>0).all()
    f=f.drop(f.index[0]);_,qa=seasonal(f,t);assert qa['excluded_hours'][0]==1
    actual=np.ones((20,60,2))*100;actual[:,0]=0;point=np.ones_like(actual)*120
    dates=pd.date_range('2024-03-01',periods=20,freq='6h',tz='UTC')
    s=calibrate(point,actual,np.ones((20,2)),np.arange(1,61),dates,minimum=1000)
    b=bands(point[0],s['factors']);assert (b>0).all() and (np.diff(b,axis=1)>=0).all()
    assert all(s['pooled'])
    with pytest.raises(ValueError,match='training'):
        calibrate(point,actual,np.ones((20,2)),np.arange(1,61),dates+pd.Timedelta(days=600))


def test_immutable_prefix_completed_bar_changes_later():
    f,t=fake();k,v,x,sigma,qp=qp_fixture()
    def path(frame):
        return replay(qp,lambda cut:predict(frame,t+pd.Timedelta(minutes=cut),pd.date_range(t+pd.Timedelta(minutes=cut),periods=60-cut,freq='min'))['V2'])[0]
    z=path(f);q=f.copy();q.loc[q.time==t+pd.Timedelta(minutes=4),'quote_volume_0']*=100
    altered=path(q);assert z[:5].tobytes()==altered[:5].tobytes()
    assert np.linalg.norm(z[5:]-altered[5:])>1


def test_real_V0_and_static_T4_parity():
    store=X1Store(ROOT);t=pd.Timestamp('2025-08-01T00:00:00Z');pc=config(ROOT)
    e=construct_episode(store.history(t),t,pc);p=store.forecast(t,pd.date_range(t,periods=60,freq='min'))
    np.testing.assert_array_equal(e.forecast,p['V0'])
    b=load_models(ROOT,'2025-08',t)['B'].kernel;beta=beta_for(e,b,pc)
    q=AdaptiveQP(b,e.initial,.1*e.forecast,e.covariance,beta);z,_=q.solve(np.empty((0,2)),1/e.forecast)
    old=pd.read_parquet(ROOT/'results/stage04_development/schedules_development.parquet')
    old=old[(old.episode_id==e.episode_id)&(old.policy=='T4')].sort_values('minute')
    np.testing.assert_allclose(z,old[['btc_sales_usdt','eth_sales_usdt']],rtol=1e-7,atol=1e-3)
    assert all('/2026-' not in s for s in store.read_log)


def test_reader_refuses_final_before_parquet(monkeypatch):
    store=X1Store(ROOT)
    monkeypatch.setattr(pd,'read_parquet',lambda *a,**kw:pytest.fail('Opened forbidden partition'))
    with pytest.raises(ValueError):store.paired(pd.Timestamp('2026-01-01',tz='UTC'),pd.Timestamp('2026-01-02',tz='UTC'))
    with pytest.raises(ValueError):store.paired(pd.Timestamp('2025-08-01',tz='UTC'),pd.Timestamp('2025-08-02',tz='UTC'),asof=pd.Timestamp('2025-08-01',tz='UTC'))


def test_evaluator_independence_future_price_volume_only_scores():
    k,v,x,sigma,qp=qp_fixture();z,records,used=replay(qp,lambda cut:v[cut:])
    w=World('E1',kernel(-.2),.001);wh=w.world_hash
    p0=np.array([100.,200.]);prices=np.tile(p0,(60,1));truth=v.copy()
    a=score_schedule(z,x,v,p0,prices,truth,w)
    b=score_schedule(z,x,v,p0,prices*1.01,truth*.1,w)
    assert a['path_usdt']!=b['path_usdt'] and a['max_realized_participation']!=b['max_realized_participation']
    other=AdaptiveQP(kernel(-.6),x,.1*v,sigma,qp.beta);replay(other,lambda cut:v[cut:])
    assert w.world_hash==wh
    np.testing.assert_array_equal(z[:5],np.array(records[0]['prefix']))


def test_scenario_curvature_is_weighted_inverse():
    k,v,x,sigma,qp=qp_fixture();f=np.ones((3,3,2));f[:,0]*=.5;f[:,2]*=2
    z,_,_=replay(qp,lambda cut:v[cut:],scenario=True,factors=f)
    # .25/(.5V)+.5/V+.25/(2V)=1.125/V; static forecasts => consistent tail.
    ref,_=qp.solve(np.empty((0,2)),1.125/v)
    np.testing.assert_allclose(z,ref,rtol=1e-6,atol=1e-3)


@pytest.mark.parametrize('date',['2025-07-31T23:55:00Z','2025-08-01T00:00:00Z'])
@pytest.mark.parametrize('cut',[0,5])
def test_issued_prefix_byte_identity_all_current_future_fields(date,cut):
    f,t=fake(date);k,v,x,sigma,qp=qp_fixture()
    initial=predict(f,t,pd.date_range(t,periods=60,freq='min'))['V1']
    z,_=qp.solve(np.empty((0,2)),1/initial);past=z[:cut]
    decision=t+pd.Timedelta(minutes=cut);targets=pd.date_range(decision,periods=60-cut,freq='min')
    known=predict(f,decision,targets)['V2'];prefix=qp.solve(past,1/known)[0][:5]
    other=f.copy();future=other.time>=decision
    for col in other:
        if col.startswith(('quote_volume','close')):other.loc[future,col]=np.nan
        if col.startswith('valid_bar'):other.loc[future,col]=False
    revised=predict(other,decision,targets)['V2'];prefix2=qp.solve(past,1/revised)[0][:5]
    assert prefix.tobytes()==prefix2.tobytes()
    # Merely having future rows is also unavailable at decision time.
    absent=other.loc[other.time<decision]
    assert np.array_equal(predict(absent,decision,targets)['V2'],known)


def test_conditional_full_risk_expansion_no_double_counting():
    k,v,x,sigma,qp=qp_fixture();z,_=qp.solve(np.empty((0,2)),1/v);cut=5
    H,q,c,remaining,state=qp.conditional(z[:cut],1/v[cut:])
    f=z[cut:].ravel();conditional=.5*f@H@f+q@f+c
    before=x-np.vstack([np.zeros(2),np.cumsum(z,axis=0)[:-1]])
    full=.5*z.ravel()@qp.H@z.ravel()+qp.kappa*np.sum(z*z/v)+qp.beta*np.einsum('ki,ij,kj->',before,sigma,before)+.0006*z.sum()
    past=z[:cut].ravel()
    past_cost=.5*past@qp.H[:2*cut,:2*cut]@past+qp.kappa*np.sum(z[:cut]**2/v[:cut])+qp.beta*np.einsum('ki,ij,kj->',before[:cut],sigma,before[:cut])+.0006*z[:cut].sum()
    assert full-past_cost==pytest.approx(conditional,rel=1e-12)
    np.testing.assert_allclose(remaining,x-z[:cut].sum(axis=0))


def test_fixed_caps_unchanged_when_objective_volume_revised():
    k,v,x,sigma,qp=qp_fixture();caps=qp.caps.copy()
    z,_=qp.solve(np.empty((0,2)),1/(v*.01))
    np.testing.assert_array_equal(qp.caps,caps)
    assert (z<=caps+1e-7*x).all()
    np.testing.assert_allclose(z.sum(axis=0),x,rtol=1e-7)
    with pytest.raises(ValueError):qp.solve(np.ones((5,2))*1e20,1/v[5:])


def test_zero_realized_volume_retained_json_safe_with_explicit_infeasibility():
    from cryptocrossimpact.liquidity.workflow import score_schedule as json_score
    k,v,x,sigma,qp=qp_fixture();z,_=qp.solve(np.empty((0,2)),1/v)
    truth=v.copy();truth[0,0]=0;p0=np.array([100.,200.]);prices=np.tile(p0,(60,1))
    value=json_score(z,x,v,p0,prices,truth,World('E1',k,.001))
    assert value['max_realized_participation'] is None
    assert value['max_realized_participation_status']=='INFEASIBLE_POSITIVE_SALE_ZERO_VOLUME'
    assert value['zero_realized_volume_cells']==1
    json.dumps(value,allow_nan=False)
    ordinary=score_schedule(z,x,v,p0,prices,v,World('E1',k,.001))
    for key in ['path_usdt','transient_usdt','temporary_usdt','shortfall_ex_funding_bps']:
        assert value[key]==ordinary[key]
