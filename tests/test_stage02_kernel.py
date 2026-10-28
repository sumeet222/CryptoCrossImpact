import json
from pathlib import Path

import cvxpy as cp
import numpy as np
import pandas as pd
import pytest

from cryptocrossimpact.data.pipeline import ROOT
from cryptocrossimpact.kernel.features import (DevelopmentStore,flow_basis,guard_times,construct,feature_names)
from cryptocrossimpact.kernel.fit import (Stats,transforms,normalize,normalized_rows,estimate,loss,
    validate_components,finite_grid_check,level_kernel,predict)


def synthetic(taus=(5,30),cross=-.3,n=10000,seed=17):
    rng=np.random.default_rng(seed)
    f=rng.normal(size=(n,2))
    for t in range(1,n):f[t]+=.35*f[t-1]
    f[:,1]+=.3*f[:,0]
    z=flow_basis(f,taus,60)
    x=rng.normal(size=(n,24));x[:,0]=.4*f[:,0]+rng.normal(size=n)
    matrices=np.array([[[1.,cross],[cross,.8]],[[.3,.1],[.1,.5]]])[:len(taus)]
    y=np.einsum('tkj,kij->ti',np.nan_to_num(z),matrices)+x[:,:2]@np.array([[.1,.2],[-.2,.1]])
    y+=rng.normal(size=y.shape)*.0001
    d=np.column_stack([np.ones(n),x,z.reshape(n,-1)])
    valid=np.isfinite(d).all(axis=1)
    return d[valid],y[valid],matrices


@pytest.mark.parametrize('taus,cross',[((5,),0),((5,),-.3),((5,30),.25)])
def test_known_psd_recovery(taus,cross):
    x,y,truth=synthetic(taus,cross)
    raw=Stats.rows(x,y);norm=transforms(raw)
    m=estimate(normalize(raw,norm),norm,taus,list(taus),'B',0)
    np.testing.assert_allclose(m['matrices'],truth,rtol=.002,atol=.001)
    validate_components(m['matrices']);finite_grid_check(m)


def test_return_equation_and_tail_boundary():
    f=np.zeros((100,2));f[10]=[2,3]
    b=flow_basis(f,[5],60)[:,0]
    assert b[70,0]==pytest.approx(2*(np.exp(-60/5)-np.exp(-59/5)))
    assert b[71,0]==0  # no accidental H+1 term from differencing a truncated level
    f=np.ones((200,2))
    assert flow_basis(f,[5],60)[100,0,0]==pytest.approx(np.exp(-60/5))
    assert (flow_basis(f,[5],60,'lag_only')[100,0]<0).all()


def test_cash_units_and_no_double_difference():
    l=np.array([100.,400.]);q=np.array([200.,-100.]);r=np.array([.001,-.002])
    f=q/np.sqrt(l);y=1e4*np.sqrt(l)*r
    np.testing.assert_allclose(f,[20,-5]);np.testing.assert_allclose(y,[100,-400])
    c=np.array([[2.,-.5],[-.5,1.]])
    log_displacement=(c@f)/(1e4*np.sqrt(l))
    np.testing.assert_allclose(1e4*np.sqrt(l)*log_displacement,c@f)
    assert y[0]==100  # target already a return, no second difference
    validate_components([c])
    with pytest.raises(ValueError,match='indefinite'):validate_components([[[1,2],[2,1]]])


def test_sufficient_stats_direct_design_and_solver_agree():
    x,y,_=synthetic((5,),n=2500)
    raw=Stats.zeros(x.shape[1]).add(Stats.rows(x[:1000],y[:1000])).add(Stats.rows(x[1000:],y[1000:]))
    np.testing.assert_allclose(raw.gram,x.T@x,rtol=1e-12,atol=1e-10)
    norm=transforms(raw);ns=normalize(raw,norm);ridge=.001
    m=estimate(ns,norm,(5,),[5],'B',ridge)
    direct=direct_fit(x,y,norm,ridge)
    np.testing.assert_allclose(m['matrices'][0],direct,rtol=2e-5,atol=2e-5)
    other=estimate(ns,norm,(5,),[5],'B',ridge,solver='SCS')
    np.testing.assert_allclose(m['matrices'],other['matrices'],rtol=1e-4,atol=1e-4)
    # Sufficient-statistic SSE subtracts O(1) terms: absolute float cancellation
    # is the appropriate tolerance for this near-noiseless 1e-6 residual loss.
    np.testing.assert_allclose(loss(ns,np.array(m['theta_standardized'])),np.mean(((y-predict(m,x))/norm['target_scale'])**2,axis=0),rtol=1e-8,atol=1e-12)


def direct_fit(x,y,norm,ridge):
    nc=25;z=normalized_rows(x,norm);ys=np.array(norm['target_scale'])
    c=cp.Variable((2,2),symmetric=True);controls=cp.Variable((nc,2))
    beta=cp.vstack([controls,cp.multiply(c.T,np.array(norm['scale'])[nc:,None]/ys[None,:])])
    problem=cp.Problem(cp.Minimize(cp.sum_squares(y/ys-z@beta)/(2*len(x))+.5*ridge*cp.sum_squares(beta[1:])),[c>>0])
    problem.solve(solver='CLARABEL',tol_gap_abs=1e-9,tol_gap_rel=1e-8,tol_feas=1e-9)
    assert problem.status=='optimal'
    return c.value


def test_diagonal_null_and_asset_permutation():
    x,y,_=synthetic((5,),n=3000)
    norm=transforms(Stats.rows(x,y));stats=normalize(Stats.rows(x,y),norm)
    a=estimate(stats,norm,(5,),[5],'A',.001)
    b=estimate(stats,norm,(5,),[5],'B',.001,force_diagonal=True)
    np.testing.assert_allclose(a['matrices'],b['matrices'],rtol=1e-6,atol=1e-6)
    b=estimate(stats,norm,(5,),[5],'B',.001)
    order=[0]+list(range(11,21))+list(range(1,11))+list(range(21,25))+[26,25]
    swapped=x[:,order];other_norm=transforms(Stats.rows(swapped,y[:,::-1]))
    other=estimate(normalize(Stats.rows(swapped,y[:,::-1]),other_norm),other_norm,(5,),[5],'B',.001)
    np.testing.assert_allclose(np.array(b['matrices'])[:,::-1,::-1],other['matrices'],rtol=2e-5,atol=2e-5)


def test_unconstrained_asymmetry_and_export_block():
    x,y,_=synthetic((5,),n=3000)
    y[:,0]+=.8*x[:,-1]
    norm=transforms(Stats.rows(x,y))
    m=estimate(normalize(Stats.rows(x,y),norm),norm,(5,),[5],'U',0)
    assert abs(m['matrices'][0][0][1]-m['matrices'][0][1][0])>.5
    with pytest.raises(ValueError,match='cannot be exported'):level_kernel(m,[0,1])


def test_firewall_before_file_open(monkeypatch):
    store=DevelopmentStore(ROOT)
    def forbidden(*args,**kwargs):raise AssertionError('Must reject before Parquet access')
    monkeypatch.setattr(pd,'read_parquet',forbidden)
    with pytest.raises(ValueError,match='firewall'):store.read('BTCUSDT','2026-01')
    with pytest.raises(ValueError,match='firewall'):guard_times(pd.DatetimeIndex(['2026-01-01'],tz='UTC'))
    with pytest.raises(ValueError):store.liquidity(end='2026-02-01')


def test_real_train_only_direct_fit_and_timing():
    store=DevelopmentStore(ROOT);frame=store.paired('2024-01').iloc[:5000].copy()
    l=store.liquidity(end='2024-02-01')
    x,y,valid=construct(frame,l,[5])
    assert valid[:1441].sum()==0 and valid[1441:].all()
    k=1600
    assert x[k,1]==pytest.approx(frame.close_to_close_log_return_0.iloc[k-1])
    change=frame.copy()
    for j in range(2):
        change.loc[k:,f'quote_volume_{j}']*=3
        change.loc[k:,f'close_to_close_log_return_{j}']*=2
        change.loc[k:,f'signed_taker_quote_flow_{j}']*=5
    altered,_,_=construct(change,l,[5])
    np.testing.assert_allclose(x[k,:25],altered[k,:25],rtol=0,atol=0)
    np.testing.assert_allclose(x[:k],altered[:k],equal_nan=True)
    raw=Stats.rows(x[valid],y[valid]);norm=transforms(raw)
    m=estimate(normalize(raw,norm),norm,[5],[5],'B',.001)
    np.testing.assert_allclose(m['matrices'][0],direct_fit(x[valid],y[valid],norm,.001),rtol=3e-4,atol=1e-5)
    assert all('2026' not in key for key in store.read_log)


def test_decay_selection_synthetic():
    # Generate the true tau on the same f stream as every competing basis.
    rng=np.random.default_rng(3);f=rng.normal(size=(5000,2));z=flow_basis(f,[2,5,10],60)
    y=z[:,1,:]@np.array([[1,.2],[.2,.8]])
    controls=rng.normal(size=(5000,24))
    x=np.column_stack([np.ones(5000),controls,z.reshape(5000,-1)])
    x,y=x[60:],y[60:]
    raw=Stats.rows(x[:3500],y[:3500]);norm=transforms(raw)
    train=normalize(raw,norm);val=normalize(Stats.rows(x[3500:],y[3500:]),norm)
    scores={}
    for tau in [2,5,10]:
        m=estimate(train,norm,[tau],[2,5,10],'B',0)
        scores[tau]=loss(val.subset(m['indices']),np.array(m['theta_standardized'])).mean()
    assert min(scores,key=scores.get)==5


def test_cross_only_permutation_sufficient_statistics():
    from cryptocrossimpact.kernel.diagnostics import shifted_cross_stats
    x,y,_=synthetic((5,30),n=3000)
    normal=transforms(Stats.rows(x,y));xn=normalized_rows(x,normal);yn=y/normal['target_scale']
    mask=np.ones(len(x),dtype=bool);base=Stats.rows(xn,yn)
    shifted=shifted_cross_stats(xn,yn,mask,base,[5,30],[5,30],1440)
    for i in range(2):
        copy=xn.copy();cc=[25+2*k+1-i for k in range(2)]
        own=[25+2*k+i for k in range(2)]
        copy[:,cc]=np.roll(xn[:,cc],1440,axis=0)
        np.testing.assert_array_equal(copy[:,own],xn[:,own])
        np.testing.assert_allclose(shifted.gram[i],copy.T@copy,atol=2e-10,rtol=1e-12)
        np.testing.assert_allclose(shifted.xy[:,i],copy.T@yn[:,i],atol=2e-10,rtol=1e-12)


def test_resampling_uses_original_rows_not_new_lag_adjacency():
    x,y,_=synthetic((5,),n=3000)
    first=Stats.rows(x[:1440],y[:1440]);second=Stats.rows(x[1440:],y[1440:])
    resampled=Stats.zeros(x.shape[1]).add(second).add(first).add(second)
    expected=Stats.rows(np.vstack([x[1440:],x[:1440],x[1440:]]),np.vstack([y[1440:],y[:1440],y[1440:]]))
    np.testing.assert_allclose(resampled.gram,expected.gram,atol=1e-10)
    np.testing.assert_allclose(resampled.xy,expected.xy,atol=1e-10)


def test_month_and_validation_context_and_fixed_training_scaling():
    store=DevelopmentStore(ROOT)
    june=store.paired('2025-06').iloc[-1441:].copy();july=store.paired('2025-07').iloc[:100].copy()
    frame=pd.concat([june,july],ignore_index=True);l=store.liquidity()
    x,y,valid=construct(frame,l,[5,30]);k=1441
    assert valid[k]
    assert x[k,1]==pytest.approx(june.close_to_close_log_return_0.iloc[-1])
    assert y[k,0]==pytest.approx(1e4*np.sqrt(l[0])*july.close_to_close_log_return_0.iloc[0])
    wrong=frame.copy();wrong.loc[k,'open_time']+=60000
    _,_,bad=construct(wrong,l,[5,30]);assert not bad[k]


def test_zero_volume_nuisances_remain_finite_and_cash_congruence():
    from cryptocrossimpact.kernel.diagnostics import rescale_raw
    store=DevelopmentStore(ROOT);frame=store.paired('2024-01').iloc[:2000].copy()
    for j in range(2):frame[f'quote_volume_{j}']=0.
    x,_,valid=construct(frame,np.array([100.,400.]),[5])
    assert np.isfinite(x[valid]).all()
    assert x[1600,8]==0  # zero previous volume minus zero past median
    d,y,_=synthetic((5,),n=3000);raw=Stats.rows(d,y)
    converted=rescale_raw(raw,[100.,400.],[225.,100.])
    multiplier=np.ones(d.shape[1]);multiplier[25:]=np.sqrt(np.array([100.,400.])/np.array([225.,100.]))
    expected=Stats.rows(d*multiplier,y/np.sqrt(np.array([100.,400.])/np.array([225.,100.])))
    np.testing.assert_allclose(converted.gram,expected.gram,atol=1e-10)
    np.testing.assert_allclose(converted.xy,expected.xy,atol=1e-10)


def test_refit_firewall_no_test_month_invocation():
    from cryptocrossimpact.kernel.diagnostics import refit_historical
    with pytest.raises(ValueError,match='firewall'):refit_historical(ROOT,'2026-02-01')
