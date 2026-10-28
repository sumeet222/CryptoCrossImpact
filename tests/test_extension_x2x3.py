"""Finite-set/CVaR math, causality, X1 parity, resource-safe ready barrier."""
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from cryptocrossimpact.execution.impact_cost import Kernel,ASSETS,cash_hessian,triangular_cash
from cryptocrossimpact.execution.adaptive import AdaptiveQP,historical_linear_state
from cryptocrossimpact.robust.solver import RobustQP
from cryptocrossimpact.robust.scenarios import empirical_cvar,overload,joint_paths,ambiguity,ScenarioSupportError

ROOT=Path(__file__).resolve().parents[1]


def setup(n=10,cross=.3):
    k=Kernel(ASSETS,np.array([[[1.,cross],[cross,1.4]]]),[15],[1e6,2e6])
    v=np.tile([1e6,2e6],(n,1))*(1+.2*np.sin(np.arange(n)[:,None]/3));x=.02*v.sum(axis=0)
    sigma=np.array([[1e-6,4e-7],[4e-7,2e-6]]);beta=1e-6
    return k,v,x,sigma,beta


@pytest.mark.parametrize('values,alpha,answer',[([1,2],.5,2),([1,2,6],1/3,4),([0,0,12],.5,8),([1,2,3],0,2)])
def test_hand_cvar(values,alpha,answer):assert empirical_cvar(values,alpha)==pytest.approx(answer)


def test_overload_zero_volume_units_monotonic():
    v=np.array([[0.,100.],[50.,100.]]);z=np.array([[5.,20.],[5.,10.]])
    assert overload(z,v,40)==pytest.approx(15/40)
    assert overload(2*z,v,40)>=overload(z,v,40)>=0
    assert empirical_cvar(np.ones(12)*.05)*100==pytest.approx(5.)


@pytest.mark.parametrize('cross',[-.5,.5])
@pytest.mark.parametrize('cut',[0,5,9])
def test_singleton_zero_lambda_X1_and_history(cross,cut):
    k,v,x,sigma,beta=setup(cross=cross);old=AdaptiveQP(k,x,.1*v,sigma,beta)
    z,_=old.solve(np.empty((0,2)),1/v);ref,qa=old.solve(z[:cut],1/v[cut:])
    robust=RobustQP([('nominal',k)],x,.1*v,sigma,beta,force_full=True)
    got,d=robust.solve(z[:cut],v[cut:],lam=0)
    np.testing.assert_allclose(got,ref,atol=.1,rtol=5e-5)
    assert d['epigraph_gap']<2e-5 and d['kkt']<2e-5
    h=robust.H[0];offset=cut*2
    np.testing.assert_allclose(h[offset:,:offset]@z[:cut].ravel(),historical_linear_state(k,z[:cut],len(v)-cut).ravel(),rtol=1e-12,atol=1e-16)


def test_cvar_changes_decision_and_second_solver():
    k,v,x,sigma,beta=setup(n=3)
    paths=np.tile(v,(12,1,1));paths[:2,0,:]=0
    qp=RobustQP([('n',k)],x,.1*v,sigma,beta)
    a,qa=qp.solve(np.empty((0,2)),v,paths,25)
    b,qb=qp.solve(np.empty((0,2)),v,paths,25,solver='SCS')
    np.testing.assert_allclose(a,b,rtol=2e-3,atol=10)
    nominal,_=qp.solve(np.empty((0,2)),v,lam=0)
    assert a[0].sum()<nominal[0].sum()
    assert qa['cvar']==pytest.approx(empirical_cvar([overload(a,p,x.sum()) for p in paths]))


def test_multiple_kernel_epigraph_and_no_sunk_constant():
    k,v,x,sigma,beta=setup(n=6,cross=-.6)
    other=Kernel(ASSETS,np.array([[[2.,.1],[.1,.7]]]),[5],[1e6,2e6])
    qp=RobustQP([('n',k),('other',other)],x,.1*v,sigma,beta)
    full,_=qp.solve(np.empty((0,2)),v)
    past=full[:2];future,qa=qp.solve(past,v[2:])
    for H,cost in zip(qp.H,qa['scenario_future_cost_usdt']):
        z=np.vstack([past,future]).ravel();p=past.ravel()
        assert .5*z@H@z-.5*p@H[:4,:4]@p==pytest.approx(cost,rel=1e-11)
    assert qa['epigraph_gap']<2e-5
    # The future cross term must change the conditional optimum.
    reset=RobustQP([('n',k),('other',other)],x-past.sum(axis=0),.1*v[2:],sigma,beta)
    wrong,_=reset.solve(np.empty((0,2)),v[2:])
    assert np.linalg.norm(wrong-future)>.1


def test_cash_hessian_gradient_and_no_indefinite_repair():
    k,v,x,sigma,beta=setup(n=5,cross=-.4);H,_=cash_hessian(k,5)
    z=np.arange(10,dtype=float)*100;cut=4;p=z[:cut];f=z[cut:]
    grad=H[cut:,cut:]@f+H[cut:,:cut]@p
    fun=lambda a:.5*a@H[cut:,cut:]@a+a@H[cut:,:cut]@p
    for i in range(len(f)):
        e=np.eye(len(f))[i]*.01
        assert (fun(f+e)-fun(f-e))/.02==pytest.approx(grad[i],rel=1e-6,abs=1e-13)
    assert triangular_cash(k,z.reshape(5,2))==pytest.approx(.5*z@H@z,rel=1e-12)
    with pytest.raises(ValueError):Kernel(ASSETS,[[[1,2],[2,1]]],[5],[1e6,2e6])


def history(t='2025-08-01T00:00:00Z'):
    t=pd.Timestamp(t);times=pd.date_range(t.normalize()-pd.Timedelta(days=28),t+pd.Timedelta(hours=1),freq='min',inclusive='left')
    f=pd.DataFrame(dict(time=times));v=(1+times.day.to_numpy()/30)*1e6*(1+.4*np.sin(times.minute.to_numpy()/60*2*np.pi))
    for i in range(2):f[f'quote_volume_{i}']=v*(i+1);f[f'valid_bar_{i}']=True
    return f,t


@pytest.mark.parametrize('cut',[0,5,10,15,20,25,30,35,40,45,50,55])
def test_joint_paths_are_past_coherent_deterministic_zero_preserving(cut):
    f,t=history();point=np.tile([1e6,2e6],(60-cut,1));asof=t+pd.Timedelta(minutes=cut)
    a,qa=joint_paths(f,asof,t,point)
    other=f.copy();other.loc[other.time>=asof,['quote_volume_0','quote_volume_1']]=np.nan
    b,qb=joint_paths(other,asof,t,point)
    assert a.tobytes()==b.tobytes() and qa==qb
    assert a.shape==(12,60-cut,2) and len(set(qa['source_hours']))==12
    assert all(pd.Timestamp(s)+pd.Timedelta(hours=1)<=t.normalize() for s in qa['source_hours'])
    # Same historical day for both assets; no artificial independent draws.
    np.testing.assert_allclose(a[:,:,1],2*a[:,:,0])
    source=pd.Timestamp(qa['source_hours'][0]);f.loc[f.time==source+pd.Timedelta(minutes=cut),['quote_volume_0','quote_volume_1']]=0
    z,_=joint_paths(f,asof,t,point);assert (z[0,0]==0).all()


def test_support_hold_and_kernel_diagonal_ambiguity():
    f,t=history();f.loc[f.time<t-pd.Timedelta(days=10),'valid_bar_0']=False
    with pytest.raises(ScenarioSupportError):joint_paths(f,t,t,np.ones((60,2)))
    k,*_=setup();items,qa=ambiguity(k,k,True)
    assert len(items)==1 and all(np.all(a.matrices[:,0,1]==0) for _,a in items)


def test_asset_permutation_conic():
    k,v,x,sigma,beta=setup(n=5)
    q=RobustQP([('n',k)],x,.1*v,sigma,beta,force_full=True);a,_=q.solve(np.empty((0,2)),v)
    kp=Kernel(ASSETS,k.matrices[:,::-1,::-1],k.taus_minutes,k.liquidity_usdt[::-1])
    qp=RobustQP([('n',kp)],x[::-1],.1*v[:,::-1],sigma[::-1,::-1],beta,force_full=True)
    b,_=qp.solve(np.empty((0,2)),v[:,::-1]);np.testing.assert_allclose(a,b[:,::-1],rtol=5e-5,atol=.1)


def test_reader_refuses_without_ready(monkeypatch,tmp_path):
    from cryptocrossimpact.robust.data import Store
    from cryptocrossimpact.robust.protocol import PretestHold
    import shutil
    (tmp_path/'data/registry').mkdir(parents=True)
    shutil.copyfile(ROOT/'data/registry/source_manifest.json',tmp_path/'data/registry/source_manifest.json')
    store=Store(tmp_path);monkeypatch.setattr(pd,'read_parquet',lambda *a,**k:pytest.fail('Premature holdout read'))
    with pytest.raises(PretestHold):store.paired(pd.Timestamp('2026-07-01',tz='UTC'),pd.Timestamp('2026-07-02',tz='UTC'))


def test_manual_ready_flag_cannot_authorize(tmp_path):
    import json
    from cryptocrossimpact.robust.protocol import validate_ready,PretestHold
    out=tmp_path/'reports/research/extension_x2x3_artifacts';out.mkdir(parents=True)
    (out/'PRETEST_READY_X2X3.json').write_text(json.dumps({'status':'PRETEST_READY_X2X3','ready':True}))
    with pytest.raises(PretestHold):validate_ready(tmp_path)


def test_new_time_adapters_match_original():
    from cryptocrossimpact.robust.data import Store,forecast,make_episode
    from cryptocrossimpact.liquidity.forecasts import predict
    from cryptocrossimpact.episodes import construct_episode,config
    t=pd.Timestamp('2025-08-01T00:00:00Z');store=Store(ROOT);h=store.history(t)
    for cut in [0,5,55]:
        clock=t+pd.Timedelta(minutes=cut);h=store.history(clock);targets=pd.date_range(clock,periods=60-cut,freq='min')
        a=forecast(h,clock,targets);b=predict(h,clock,targets)
        for key in ['V0','V1']:np.testing.assert_array_equal(a[key],b[key])
    h=store.history(t);a=make_episode(h,t,ROOT);b=construct_episode(h,t,config(ROOT))
    for key in ['forecast','covariance','initial','p0']:np.testing.assert_array_equal(getattr(a,key),getattr(b,key))


@pytest.mark.parametrize('timestamp',['2025-07-05T00:00:00Z','2025-07-31T18:00:00Z','2025-08-01T00:00:00Z'])
def test_real_three_X1_P2_parity(timestamp):
    import json
    from cryptocrossimpact.robust.data import Store,make_episode
    from cryptocrossimpact.robust.workflow import model_bundle
    from cryptocrossimpact.execution.solver import build_problem
    from cryptocrossimpact.liquidity.workflow import score_schedule
    from cryptocrossimpact.evaluation.v2_score import evaluation_prices
    store=Store(ROOT);t=pd.Timestamp(timestamp);e=make_episode(store.history(t),t,ROOT);b,worlds=model_bundle(ROOT,t.strftime('%Y-%m'),t)
    beta=build_problem(b,e.initial,e.forecast,e.covariance).risk_multiplier;q=AdaptiveQP(b,e.initial,.1*e.forecast,e.covariance,beta)
    past=np.empty((0,2))
    for cut in range(0,60,5):
        clock=t+pd.Timedelta(minutes=cut);p,h=store.forecast(clock,pd.date_range(clock,periods=60-cut,freq='min'))
        future,_=q.solve(past,1/p['V1']);past=np.vstack([past,future[:5]])
    with np.load(ROOT/'results/extension_x1/development'/f'{e.episode_id}.npz') as old:np.testing.assert_allclose(past,old['P2'],rtol=1e-10,atol=1e-6)
    truth=Store(ROOT).paired(t,t+pd.Timedelta(hours=1),purpose='test_parity',asof=t+pd.Timedelta(hours=1))
    prices,v=evaluation_prices(truth,t,60);world=next(w for w in worlds if w.world_id=='E1')
    cost=score_schedule(past,e.initial,e.forecast,e.p0,prices,v,world)['shortfall_ex_funding_bps']
    prior=json.loads((ROOT/'results/extension_x1/development'/f'{e.episode_id}.json').read_text())
    expected=next(x['shortfall_ex_funding_bps'] for x in prior['scores'] if x['policy']=='P2' and x['world']=='E1')
    assert cost==pytest.approx(expected,abs=1e-10)


@pytest.mark.parametrize('cut',range(0,60,5))
def test_causal_prefix_all_replans(cut):
    from cryptocrossimpact.robust.data import forecast
    f,t=history('2025-07-31T23:55:00Z');idx=np.arange(len(f))
    f['open_time']=pd.DatetimeIndex(f.time).as_unit('ms').asi8
    for i in range(2):f[f'close_{i}']=100*np.exp(.0001*np.sin(idx/7+i))
    k,v,x,sigma,beta=setup(n=60);q=RobustQP([('nominal',k)],x,.1*v,sigma,beta)
    p=forecast(f,t,pd.date_range(t,periods=60,freq='min'));initial,_=q.solve(np.empty((0,2)),p['V1'])
    clock=t+pd.Timedelta(minutes=cut);targets=pd.date_range(clock,periods=60-cut,freq='min')
    original=forecast(f,clock,targets);paths,_=joint_paths(f,clock,t,original['V1'])
    # All price/volume/return/flow fields in the current/future tape are poisoned.
    changed=f.copy();future=changed.time>=clock
    for col in ['quote_volume_0','quote_volume_1','close_0','close_1']:changed.loc[future,col]=np.nan
    for col in ['return_0','return_1','cross_flow_0','cross_flow_1']:changed[col]=0.;changed.loc[future,col]=1e20
    revised=forecast(changed,clock,targets);paths2,_=joint_paths(changed,clock,t,revised['V1'])
    assert original['V1'].tobytes()==revised['V1'].tobytes() and paths.tobytes()==paths2.tobytes()
    a,_=q.solve(initial[:cut],original['V1'],paths,25);b,_=q.solve(initial[:cut],revised['V1'],paths2,25)
    np.testing.assert_array_equal(a[:5],b[:5])


def test_asof_fit_windows_and_feature_QC_adapter_parity():
    from cryptocrossimpact.evaluation.v2_fit import window
    from cryptocrossimpact.robust.data import Store
    from cryptocrossimpact.robust.features import construct_asof
    from cryptocrossimpact.evaluation.v2_features import construct_asof as old_construct
    for month in ['2026-07','2026-08','2026-09']:
        origin=pd.Timestamp(month+'-01',tz='UTC');a,b=window(origin,'B');assert b==origin and (b-a).days==365
        a,b=window(origin,'E1');assert (origin-b).days==30 and (b-a).days==180
    store=Store(ROOT);f=store.paired(pd.Timestamp('2025-06-01',tz='UTC'),pd.Timestamp('2025-06-03',tz='UTC'),purpose='pretest',full=True)
    for a,b in zip(construct_asof(f,np.array([1e6,2e6]),[2,5,10,30,60]),old_construct(f,np.array([1e6,2e6]),[2,5,10,30,60])):
        np.testing.assert_array_equal(a,b)


def test_new_canonical_QC_math_same_original_source():
    from cryptocrossimpact.data.schema import canonicalize as original,COLUMNS
    from cryptocrossimpact.robust.canonical import canonicalize
    import yaml
    t=pd.Timestamp('2025-07-01',tz='UTC').value//10**6
    f=pd.DataFrame([[t,100.,101.,99.,100.,1.,t+59999,100.,1,.5,50.,0.]],columns=COLUMNS)
    cfg=yaml.safe_load((ROOT/'configs/core.yaml').read_text())
    a=original(f,'BTCUSDT','2025-07',cfg);b=canonicalize(f,'BTCUSDT','2025-07',cfg)
    pd.testing.assert_frame_equal(a.drop(columns='split'),b.drop(columns='split'))


def test_certified_dominance_reduction_equals_full_QCQP():
    k,v,x,sigma,beta=setup(n=6)
    strong=Kernel(ASSETS,2*k.matrices,k.taus_minutes,k.liquidity_usdt)
    kernels=[('weak',k),('strong',strong)]
    reduced=RobustQP(kernels,x,.1*v,sigma,beta);full=RobustQP(kernels,x,.1*v,sigma,beta,force_full=True)
    z,_=reduced.solve(np.empty((0,2)),v)
    a,qa=reduced.solve(z[:2],v[2:]);b,qb=full.solve(z[:2],v[2:])
    np.testing.assert_allclose(a,b,rtol=1e-4,atol=.2)
    assert qa['active_scenario']=='strong' and qa['dominance_reduction']


def test_independent_enumerated_small_QCQP():
    k,v,x,sigma,beta=setup(n=2,cross=-.5)
    other=Kernel(ASSETS,[[[.6,.2],[.2,2.]]],[5],[1e6,2e6])
    q=RobustQP([('a',k),('b',other)],x,.1*v,sigma,beta,force_full=True)
    z,qa=q.solve(np.empty((0,2)),v)
    def objective(a):
        before=x-np.vstack([np.zeros(2),np.cumsum(a,axis=0)[:-1]])
        return max(triangular_cash(g,a) for g in [k,other])+.001*np.sum(a*a/v)+beta*np.einsum('ki,ij,kj->',before,sigma,before)+.0006*a.sum()
    actual=objective(z);reference=np.inf
    for left in np.linspace(0,x[0],41):
        for right in np.linspace(0,x[1],41):
            candidate=np.array([[left,right],[x[0]-left,x[1]-right]])
            reference=min(reference,objective(candidate))
    assert actual<=reference+1e-5
    assert reference-actual<.002
    assert actual==pytest.approx(qa['conditional_objective_QA_only_usdt'],rel=1e-8)


def test_diagonal_robust_limit_matches_old_diagonal():
    from cryptocrossimpact.execution.policies import without_cross
    k,v,x,sigma,beta=setup(n=6);items,_=ambiguity(k,k,True)
    q=RobustQP(items,x,.1*v,sigma,beta);z,_=q.solve(np.empty((0,2)),v)
    reference=AdaptiveQP(without_cross(k),x,.1*v,sigma,beta).solve(np.empty((0,2)),1/v)[0]
    np.testing.assert_allclose(z,reference,rtol=1e-10,atol=1e-6)


def test_real_asof_refit_adapter_matches_saved_development_models(tmp_path):
    import json
    from cryptocrossimpact.robust.data import Store
    from cryptocrossimpact.robust.fit import Fitter
    fitter=Fitter(ROOT,Store(ROOT));origin=pd.Timestamp('2025-09-01',tz='UTC')
    for role in ['B','E1']:
        fit=fitter.fit(origin,role,tmp_path/role)
        prior=(ROOT/'reports/research/stage04_artifacts/model_B_2025-09.json') if role=='B' else (ROOT/'reports/research/extension_x1_artifacts/models/2025-09_E1.json')
        old=json.loads(prior.read_text());old=old['fit'] if role=='B' else old
        for key in ['matrices','liquidity_usdt','taus_minutes']:
            np.testing.assert_allclose(fit[key],old[key],rtol=1e-10,atol=1e-10)
        assert fit['training_rows']==(525600 if role=='B' else 259200)
        assert pd.Timestamp(fit['training_end_exclusive'])<=origin-pd.Timedelta(days=30 if role=='E1' else 0)


def test_preservation_metadata_exception_cannot_hide_research_change(tmp_path):
    import json
    from cryptocrossimpact.robust.common import preserve,paths
    from cryptocrossimpact.data.storage import sha256
    out,_=paths(tmp_path);meta=tmp_path/'reports/.DS_Store';research=tmp_path/'reports/prior_result.json'
    meta.write_text('Finder original');research.write_text('original research')
    (out/'preservation_initial.json').write_text(json.dumps(dict(files={'reports/.DS_Store':sha256(meta),'reports/prior_result.json':sha256(research)},data_stats={})))
    meta.write_text('Finder updated')
    check=preserve(tmp_path,True)
    assert check['changed']==[] and check['metadata_changed']==['reports/.DS_Store']
    research.write_text('changed result')
    with pytest.raises(ValueError,match='prior_result.json'):preserve(tmp_path,True)
