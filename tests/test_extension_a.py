"""Stage A frozen-path math, filtration, nesting and matched PSD estimation."""
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from cryptocrossimpact.execution.impact_cost import Kernel,ASSETS,cash_hessian,exponential_factors
from cryptocrossimpact.stage_a.state import multipliers,state_hessian,triangle,StateQP
from cryptocrossimpact.robust.solver import RobustQP
from cryptocrossimpact.stage_a.features import response_design,NC
from cryptocrossimpact.stage_a.fit import rows,estimate,predict


def fixture(n=60,cross=.3):
    k=Kernel(ASSETS,[[[1.,cross],[cross,1.4]]],[60],[1e6,2e6]);v=np.tile([1e6,2e6],(n,1));x=.02*v.sum(axis=0);sigma=np.array([[1e-6,3e-7],[3e-7,2e-6]]);return k,v,x,sigma,1e-6


@pytest.mark.parametrize('n',[1,2,8])
@pytest.mark.parametrize('cross',[-.5,.5])
def test_exact_cell_signed_congruence_triangle_units(n,cross):
    k,v,x,s,b=fixture(n,cross);rng=np.random.default_rng(20261027);a=rng.uniform(.5,2,(n,2));z=rng.normal(size=(n,2))*1e4;h=state_hessian(k,a)
    assert .5*z.ravel()@h@z.ravel()==pytest.approx(triangle(k,z,a),rel=1e-12,abs=1e-12)
    assert triangle(k,2*z,a)==pytest.approx(4*triangle(k,z,a))
    assert np.linalg.eigvalsh(h).min()>0
    h0=cash_hessian(k,n)[0];np.testing.assert_array_equal(state_hessian(k,np.ones((n,2))),h0)
    p=Kernel(ASSETS[::-1],k.matrices[:,::-1,::-1],k.taus_minutes,k.liquidity_usdt[::-1])
    assert triangle(p,z[:,::-1],a[:,::-1])==pytest.approx(triangle(k,z,a))


@pytest.mark.parametrize('cut',[0,5,55,59])
def test_nested_L25_and_immutable_history_gradient(cut):
    k,v,x,s,b=fixture();paths=np.tile(v,(12,1,1));paths[:2,:5]=0
    old=RobustQP([('B',k)],x,.1*v,s,b);z,_=old.solve(np.empty((0,2)),v,paths,25)
    q=StateQP(k,x,.1*v,s,b);q.commit(np.ones((cut,2)))
    got,d=q.solve(z[:cut],v[cut:],paths[:,cut:],np.ones((60-cut,2)))
    expected,_=old.solve(z[:cut],v[cut:],paths[:,cut:],25)
    np.testing.assert_array_equal(got,expected)
    if cut:
        with pytest.raises(ValueError,match='rewrite'):q.solve(z[:cut],v[cut:],paths[:,cut:],np.ones((60-cut,2)),claimed_past=np.ones((cut,2))*1.1)
        old_h=state_hessian(k,np.vstack([q.ledger,np.ones((60-cut,2))]));changed=state_hessian(k,np.ones((60,2))*1.1)
        assert not np.allclose((old_h[cut*2:,:cut*2]@z[:cut].ravel())*1e10,(changed[cut*2:,:cut*2]@z[:cut].ravel())*1e10)
    assert d['kkt']<2e-5


@pytest.mark.parametrize('cut',[5,55,59])
def test_nonconstant_conditional_gradient_and_state_memory(cut):
    k,v,x,s,b=fixture();rng=np.random.default_rng(7);a=rng.uniform(.5,2,(60,2));z=np.tile(x/60,(60,1));h=state_hessian(k,a);n=120-cut*2;p=z[:cut].ravel();w=z[cut:].ravel();fp=h[cut*2:,:cut*2]@p
    direction=rng.normal(size=n);eps=100.
    f=lambda value:.5*value@h[cut*2:,cut*2:]@value+value@fp
    derivative=(f(w+eps*direction)-f(w-eps*direction))/(2*eps)
    assert derivative==pytest.approx(direction@(h[cut*2:,cut*2:]@w+fp),rel=1e-9,abs=1e-10)
    assert np.linalg.norm(fp)>0


def synthetic_frame(n=3000):
    rng=np.random.default_rng(11);t=pd.date_range('2025-01-01',periods=n,freq='min',tz='UTC');f=pd.DataFrame(dict(time=t,open_time=t.as_unit('ms').asi8))
    for i in range(2):
        f[f'quote_volume_{i}']=1e6*(1+.2*np.sin(np.arange(n)/23+i));f[f'signed_taker_quote_flow_{i}']=rng.normal(size=n)*2e5;f[f'close_to_close_log_return_{i}']=rng.normal(size=n)*.0001
        f[f'valid_bar_{i}']=True;f[f'valid_return_{i}']=True
    return f


def test_conditional_return_design_eta0_original_and_direct_formula():
    from cryptocrossimpact.kernel.features import construct
    f=synthetic_frame();l=np.array([1e6,2e6]);a=np.ones((len(f),2));x,y,g=response_design(f,l,a,[60]);old,yo,go=construct(f,l,[60]);np.testing.assert_array_equal(y,yo);np.testing.assert_array_equal(g,go)
    for i in range(2):np.testing.assert_allclose(x[g,i],old[g],rtol=1e-12,atol=1e-10)
    a[:,0]=1+.2*np.sin(np.arange(len(f))/31);a[:,1]=1+.15*np.cos(np.arange(len(f))/17)
    x,_,g=response_design(f,l,a,[60]);t=2000;flow=np.column_stack([f[f'signed_taker_quote_flow_{i}']/np.sqrt(l[i]) for i in range(2)])
    for i in range(2):
        for j in range(2):
            ref=a[t,i]*sum(np.exp(-lag/60)*a[t-lag,j]*flow[t-lag,j] for lag in range(61))-a[t-1,i]*sum(np.exp(-lag/60)*a[t-1-lag,j]*flow[t-1-lag,j] for lag in range(60))
            assert x[t,i,NC+j]==pytest.approx(ref,abs=1e-10)


def test_seeded_PSD_conditional_recovery_and_estimator_nesting():
    from cryptocrossimpact.kernel.fit import Stats,transforms,normalize,estimate as old
    rng=np.random.default_rng(41);n=6000;p=NC+6;raw=rng.normal(size=(n,p));raw[:,0]=1;x=np.repeat(raw[:,None,:],2,axis=1);c=np.array([[1.,-.35],[-.35,1.3]])
    y=raw[:,-2:]@c.T+raw[:,1:3]@np.array([[.1,.2],[-.1,.1]])
    model=estimate(rows(x,y),[60],[1e6,2e6],0,ridge=0)
    np.testing.assert_allclose(model['matrices'][0],c,atol=1e-4)
    s=Stats.rows(raw,y);normal=transforms(s);ref=old(normalize(s,normal),normal,[60],[5,30,60],'B',1)
    got=estimate(rows(x,y),[60],[1e6,2e6],0,1)
    np.testing.assert_allclose(got['matrices'],ref['matrices'],rtol=1e-8,atol=1e-8)
    np.testing.assert_allclose(got['training_mse'],ref['standardized_training_mse'],rtol=1e-10,atol=1e-10)


def test_no_future_read_development_store_and_state_inputs():
    from cryptocrossimpact.kernel.features import DevelopmentStore
    root=Path(__file__).resolve().parents[1];store=DevelopmentStore(root)
    with pytest.raises(ValueError,match='firewall'):store.read('BTCUSDT','2026-10')
    point=np.array([[1e6,2e6]]);a=multipliers(point,[1e6,2e6],.5)
    np.testing.assert_array_equal(a,np.ones_like(point))
    np.testing.assert_array_equal(multipliers(point,[1e6,2e6],0),np.ones_like(point))
    assert (multipliers(point*.0001,[1e6,2e6],1)==2).all()


@pytest.mark.parametrize('cut',[0,5,55,59])
def test_future_mutation_at_all_requested_clocks(cut):
    from cryptocrossimpact.robust.data import forecast
    from cryptocrossimpact.robust.scenarios import joint_paths
    f=synthetic_frame(31*1440);t=pd.Timestamp('2025-01-30',tz='UTC');clock=t+pd.Timedelta(minutes=cut)
    # All price/flow/volume RHS values beyond decision are poisoned.
    altered=f.copy();cols=[n for n in f if n not in ['time','open_time'] and f[n].dtype!=bool];altered.loc[altered.time>=clock,cols]=np.nan
    altered.loc[altered.time>=clock,[n for n in f if f[n].dtype==bool]]=False
    targets=pd.date_range(clock,periods=60-cut,freq='min');p=forecast(f,clock,targets);r=forecast(altered,clock,targets)
    np.testing.assert_array_equal(p['V1'],r['V1']);a=multipliers(p['V1'],[1e6,2e6],.5);b=multipliers(r['V1'],[1e6,2e6],.5);np.testing.assert_array_equal(a,b)
    paths,_=joint_paths(f,clock,t,p['V1']);other,_=joint_paths(altered,clock,t,r['V1']);np.testing.assert_array_equal(paths,other)
    k,v,x,s,beta=fixture();past=np.tile(x/60,(cut,1));q=StateQP(k,x,.1*v,s,beta);q.commit(np.ones((cut,2)))
    z,_=q.solve(past,p['V1'],paths,a);w,_=q.solve(past,r['V1'],other,b);np.testing.assert_array_equal(z[:5],w[:5])


def test_vectorized_minute_V1_matches_original_and_future_mutation():
    from cryptocrossimpact.stage_a.features import monthly_state
    from cryptocrossimpact.robust.data import forecast
    f=synthetic_frame(59*1440);v,ref,qa=monthly_state(f,'2025-02')
    for stamp in ['2025-02-01T00:00Z','2025-02-10T06:05Z','2025-02-28T18:59Z']:
        t=pd.Timestamp(stamp);point=forecast(f,t,pd.date_range(t,periods=1,freq='min'))['V1'][0]
        ix=int((t-pd.Timestamp('2025-02-01',tz='UTC')).total_seconds()/60)
        np.testing.assert_allclose(v[ix],point,rtol=1e-12,atol=1e-7)
    altered=f.copy();t=pd.Timestamp('2025-02-01',tz='UTC');altered.loc[altered.time>=t,['quote_volume_0','quote_volume_1']]*=100
    v2,ref2,_=monthly_state(altered,'2025-02');np.testing.assert_array_equal(ref,ref2);np.testing.assert_array_equal(v[0],v2[0])


def test_receiver_specific_PSD_recovery_and_direct_normal_equations():
    rng=np.random.default_rng(94);n=5000;p=NC+6;x=rng.normal(size=(n,2,p));x[:,1,:NC]=x[:,0,:NC];x[:,:,0]=1
    c=np.array([[1.2,-.4],[-.4,.9]]);y=np.column_stack([x[:,i,-2:]@c[i]+.12*x[:,i,1] for i in range(2)])
    model=estimate(rows(x,y),[60],[1e6,2e6],.5,ridge=0)
    np.testing.assert_allclose(model['matrices'][0],c,atol=2e-4)
    np.testing.assert_allclose(predict(model,x),y,atol=1e-4)


def test_state_solver_asset_permutation_and_diagonal_limit():
    from cryptocrossimpact.execution.policies import without_cross
    k,v,x,s,b=fixture(6,-.3);a=np.array([[.6,1.7],[1.2,.7],[1.,1.],[1.4,.8],[.8,1.3],[1.,.9]]);paths=np.tile(v,(12,1,1));paths[:2,0]=0
    q=StateQP(k,x,.1*v,s,b);z,_=q.solve(np.empty((0,2)),v,paths,a)
    kp=Kernel(ASSETS[::-1],k.matrices[:,::-1,::-1],k.taus_minutes,k.liquidity_usdt[::-1]);r=StateQP(kp,x[::-1],.1*v[:,::-1],s[::-1,::-1],b);zp,_=r.solve(np.empty((0,2)),v[:,::-1],paths[:,:,::-1],a[:,::-1])
    np.testing.assert_allclose(z,zp[:,::-1],atol=.03,rtol=5e-5)
    diag=without_cross(k);d=StateQP(diag,x,.1*v,s,b);got,_=d.solve(np.empty((0,2)),v,paths,np.ones_like(v));ref=RobustQP([('diag',diag)],x,.1*v,s,b).solve(np.empty((0,2)),v,paths,25)[0];np.testing.assert_array_equal(got,ref)


def test_conditional_common_world_cash_and_zero_volume_serialization():
    import json
    from types import SimpleNamespace
    from cryptocrossimpact.liquidity.workflow import score_schedule
    from cryptocrossimpact.evaluation.v2_common import digest
    k,v,x,s,b=fixture(2);a=np.array([[.5,2.],[1.5,.7]]);z=np.tile(x/2,(2,1));h=state_hessian(k,a)
    world=SimpleNamespace(world_id='E_conditional',world_hash=digest(h),hessian=h,kappa=.001,bins=2)
    truth=v.copy();truth[0,0]=0
    row=score_schedule(z,x,v,np.ones(2),np.ones_like(v),truth,world)
    assert row['transient_usdt']==pytest.approx(triangle(k,z,a),rel=1e-12)
    assert row['zero_realized_volume_cells']==1
    json.dumps(row,allow_nan=False)


def test_read_once_stats_loader_exact_equivalence(tmp_path):
    from cryptocrossimpact.kernel.workflow import read_stats,save_stats
    from cryptocrossimpact.evaluation.v2_fit import read_stats_once
    rng=np.random.default_rng(7);records={str(i):rows(rng.normal(size=(30,2,NC+6)),rng.normal(size=(30,2))) for i in range(3)}
    path=tmp_path/'stats.npz';save_stats(path,records);a=read_stats(path);b=read_stats_once(path)
    for key in records:
        assert a[key].n==b[key].n
        for field in ['gram','xy','yy']:np.testing.assert_array_equal(getattr(a[key],field),getattr(b[key],field))


def test_forged_StageA_ready_file_does_not_unlock_October(tmp_path):
    import json
    from cryptocrossimpact.kernel.features import DevelopmentStore
    folder=tmp_path/'data/registry';folder.mkdir(parents=True)
    (folder/'source_manifest.json').write_text(json.dumps(dict(market='futures/um',interval='1m',partitions={})))
    out=tmp_path/'reports/research/extension_a_artifacts';out.mkdir(parents=True)
    (out/'PRETEST_READY_A.json').write_text(json.dumps(dict(status='PRETEST_READY_A',ready=True)))
    store=DevelopmentStore(tmp_path)
    with pytest.raises(ValueError,match='firewall'):store.read('BTCUSDT','2026-10')
    assert store.read_log==[]


def test_reforecasting_only_past_multipliers_changes_state_and_is_rejected():
    k,v,x,s,b=fixture(10);past=np.tile(x/10,(5,1));paths=np.tile(v[5:],(12,1,1));old=np.tile([.7,1.5],(5,1));future=np.tile([1.3,.8],(5,1));q=StateQP(k,x,.1*v,s,b);q.commit(old)
    z,qa=q.solve(past,v[5:],paths,future);h=state_hessian(k,np.vstack([old,future]));expected=(h[10:,:10]@past.ravel()).reshape(5,2)[0]
    np.testing.assert_allclose(qa['history_gradient_usdt_per_usdt'],expected,rtol=1e-12,atol=1e-15)
    rewritten=state_hessian(k,np.vstack([future,future]));wrong=(rewritten[10:,:10]@past.ravel()).reshape(5,2)[0]
    assert np.linalg.norm(expected-wrong)>1e-8
    with pytest.raises(ValueError,match='rewrite'):q.solve(past,v[5:],paths,future,claimed_past=future)


@pytest.mark.skipif(not (Path(__file__).resolve().parents[1]/'reports/research/extension_a_artifacts/feature_manifest.json').exists(),reason='A-G2 artifacts required; pure A-G1 math runs before feature preparation')
def test_StageA_real_asof_eta0_B_E1_matches_saved_models_without_2026_reads(tmp_path):
    import json
    from cryptocrossimpact.stage_a.fit import Fitter
    root=Path(__file__).resolve().parents[1];fitter=Fitter(root);fitter.out=tmp_path
    origin=pd.Timestamp('2025-09-01',tz='UTC')
    for role,days,gap,taus in [('B',365,0,[60]),('E1',180,30,[5,30])]:
        end=origin-pd.Timedelta(days=gap);start=end-pd.Timedelta(days=days)
        m=fitter.fit(start.strftime('%Y-%m-%d'),end.strftime('%Y-%m-%d'),0,taus,role)
        path=root/'reports/research/stage04_artifacts/model_B_2025-09.json' if role=='B' else root/'reports/research/extension_x1_artifacts/models/2025-09_E1.json'
        old=json.loads(path.read_text());old=old['fit'] if role=='B' else old
        for key in ['matrices','liquidity_usdt','taus_minutes']:np.testing.assert_allclose(m[key],old[key],rtol=1e-9,atol=1e-10)
        assert m['training_rows']==days*1440
    assert all(p.split('/')[-1]<'2026-01' for p in fitter.store.read_log)
