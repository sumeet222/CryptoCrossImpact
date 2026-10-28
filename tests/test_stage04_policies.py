"""Stage 4 causality/fairness fixtures; never opens final-test market data."""
from dataclasses import replace
from pathlib import Path
import json

import numpy as np
import pandas as pd
import pytest

from cryptocrossimpact.episodes import (EpisodeStore,EpisodeUnavailable,arrivals,config,construct_episode)
from cryptocrossimpact.execution.impact_cost import ASSETS,Kernel,load_stage02
from cryptocrossimpact.execution.policies import (AsOfKernel,generate_policies,without_cross,forecast_vwap,load_models,historical_kernel)
from cryptocrossimpact.execution.solver import build_problem,solve_execution,capped_uniform_reference,InfeasibleCapacity,decompose

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture
def cfg():return config(ROOT)


@pytest.fixture
def frame():
    times=pd.date_range("2025-06-03",periods=28*1440+121,freq="min",tz="UTC");n=len(times);k=np.arange(n)
    f=pd.DataFrame(dict(time=times,open_time=times.as_unit("ms").asi8,available_at_utc=times+pd.Timedelta(minutes=1)))
    for i in range(2):
        f[f"quote_volume_{i}"]=1e6*(1+i+.4*np.sin(k/2300)+.2*np.sin(k/170))
        f[f"close_{i}"]=100*np.exp(np.cumsum(.0002*np.sin(k/(7+i))+.0001*np.cos(k/33)))
        f[f"valid_bar_{i}"]=True;f[f"jump_flag_{i}"]=False;f[f"stale_close_flag_{i}"]=False
    return f


def models(cross=.4):
    start=pd.Timestamp("2024-07-01",tz="UTC");end=pd.Timestamp("2025-07-01",tz="UTC")
    return {name:AsOfKernel(Kernel(ASSETS,[c],[60],[1e6,2e6],name),start,end,name,name)
            for name,c in [("A",[[1,0],[0,1.5]]),("B",[[1,cross],[cross,1.5]])]}


@pytest.fixture
def episode(frame,cfg):return construct_episode(frame,"2025-07-01T00:00:00Z",cfg)


def test_arrival_calendar():
    a=arrivals();assert len(a)==736
    assert list(a[:4].hour)==[0,6,12,18]
    assert a[-1]==pd.Timestamp("2025-12-31T18:00:00Z")


def test_boundary_and_covariance(episode,frame):
    assert episode.provenance["latest_open"]=="2025-06-30 23:59:00+00:00"
    assert episode.provenance["covariance_returns"]==40319
    past=frame[frame.time<episode.t0]
    price=past[["close_0","close_1"]].to_numpy()
    np.testing.assert_array_equal(episode.covariance,np.cov(np.diff(np.log(price),axis=0),rowvar=False,ddof=1))
    assert np.linalg.eigvalsh(episode.covariance).min()>=0
    np.testing.assert_array_equal(episode.p0,price[-1])


def test_future_mutation_all_schedules(frame,episode,cfg):
    changed=frame.copy();mask=changed.time>=episode.t0
    for c in ["close_0","close_1","quote_volume_0","quote_volume_1"]:changed.loc[mask,c]=np.nan
    changed.loc[mask,"valid_bar_0"]=False
    appended=changed.iloc[[-1]].copy()
    appended["time"]=pd.Timestamp("2026-06-01",tz="UTC")
    appended["available_at_utc"]=pd.Timestamp("2026-06-01T00:01:00Z")
    changed=pd.concat([changed,appended],ignore_index=True)
    after=construct_episode(changed,episode.t0,cfg)
    assert after.input_hash==episode.input_hash
    one,_=generate_policies(episode,models(),cfg);two,_=generate_policies(after,models(),cfg)
    for name in one:np.testing.assert_array_equal(one[name]["sales"],two[name]["sales"])


@pytest.mark.parametrize("date",["2026-01-01T00:00:00Z","2026-06-01T00:00:00Z"])
def test_firewall_before_io(date,monkeypatch):
    monkeypatch.setattr(pd,"read_parquet",lambda *a,**k:pytest.fail("Forbidden I/O"))
    with pytest.raises(ValueError):arrivals(date)
    with pytest.raises(ValueError):load_models(ROOT,date[:7],date)
    store=EpisodeStore(ROOT)
    with pytest.raises(ValueError):store.read("BTCUSDT","2026-01")
    with pytest.raises(ValueError):store.history(date)


def test_postarrival_model_before_io(monkeypatch):
    monkeypatch.setattr(Path,"read_text",lambda *a,**k:pytest.fail("Forbidden model read"))
    with pytest.raises(ValueError):load_models(ROOT,"2025-08","2025-07-01T00:00:00Z")


def test_model_asof_guard(episode,cfg):
    m=models();m["A"]=replace(m["A"],training_end=pd.Timestamp("2025-07-02",tz="UTC"))
    with pytest.raises(ValueError,match="Post-arrival"):generate_policies(episode,m,cfg)


def test_reject_realized_forecast(episode):
    with pytest.raises(ValueError,match="not a forecast"):
        replace(episode,provenance={**episode.provenance,"forecast_kind":"realized_future_turnover"})


@pytest.mark.parametrize("problem",["missing","invalid","clock","no_positive"])
def test_bad_history_exclusion(frame,cfg,problem):
    if problem=="missing":frame=frame.iloc[1:]
    if problem=="invalid":frame.loc[0,"valid_bar_0"]=False
    if problem=="clock":frame.loc[0,"open_time"]=1
    if problem=="no_positive":frame["quote_volume_0"]=0
    with pytest.raises(ValueError):construct_episode(frame,"2025-07-01T00:00:00Z",cfg)


def test_verified_zeros_and_floor(frame,cfg):
    frame.loc[:239,"quote_volume_0"]=0
    e=construct_episode(frame,"2025-07-01T00:00:00Z",cfg)
    assert e.provenance["forecast_qa"][0]["zero_turnover_bars"]==240
    assert (e.forecast>0).all()


def test_forecast_fallbacks(frame,cfg):
    fine=construct_episode(frame,"2025-07-01T00:00:00Z",cfg)
    assert fine.provenance["forecast_qa"][0]["minimum_class_count"]==240
    day=construct_episode(frame,"2025-07-01T00:00:00Z",{**cfg,"fine_class_minimum":300})
    overall=construct_episode(frame,"2025-07-01T00:00:00Z",{**cfg,"fine_class_minimum":300,"coarse_class_minimum":2000})
    assert day.provenance["forecast_qa"][0]["class_bins"]["hour_of_day"]==60
    assert overall.provenance["forecast_qa"][0]["class_bins"]["overall"]==60


def test_constant_twap_and_vwap(episode,cfg):
    p,rows=generate_policies(episode,models(),cfg)
    np.testing.assert_allclose(p["T0"]["sales"],np.tile(episode.initial/60,(60,1)),rtol=0,atol=1e-9)
    np.testing.assert_allclose(p["T1"]["sales"],episode.forecast*.02,rtol=1e-14)
    assert all(r["beta"]==rows[0]["beta"] for r in rows)
    assert all(r["normalized_physical_residual"]<1e-9 for r in rows)
    assert all(r["input_hash"]==episode.input_hash for r in rows)


def test_active_twap_projection():
    x=np.array([10.]);caps=np.array([[1.],[9.],[9.]])
    np.testing.assert_allclose(capped_uniform_reference(x,caps).ravel(),[1,4.5,4.5],atol=1e-12)


def test_cap_infeasibility(episode,cfg):
    bad=replace(episode,initial=episode.forecast.sum(axis=0)*.2)
    with pytest.raises(InfeasibleCapacity):generate_policies(bad,models(),cfg)
    with pytest.raises(InfeasibleCapacity):forecast_vwap(bad.initial,bad.forecast,.1)


def test_t2_common_beta_and_diagonal_equivalence(episode,cfg):
    p,rows=generate_policies(episode,models(),cfg);beta=rows[0]["beta"];a=models()["A"].kernel
    joint=solve_execution(a,episode.initial,episode.forecast,np.diag(np.diag(episode.covariance)),risk_multiplier_override=beta)
    np.testing.assert_allclose(joint["schedule_usdt"],p["T2"]["sales"],rtol=1e-7,atol=1e-4)
    assert np.linalg.norm(p["T3"]["sales"]-p["T2"]["sales"])>1
    # Independent own normalization WOULD change the risk preference; prevent it.
    scalar=Kernel((ASSETS[0],),a.matrices[:,:1,:1],a.taus_minutes,a.liquidity_usdt[:1])
    own=build_problem(scalar,episode.initial[:1],episode.forecast[:,:1],episode.covariance[:1,:1],assets=(ASSETS[0],))
    assert not np.isclose(own.risk_multiplier,beta,rtol=.01,atol=0)


def test_t3b_isolation_and_zero_limit(episode,cfg):
    b=models()["B"].kernel;diag=without_cross(b)
    np.testing.assert_array_equal(np.diagonal(diag.matrices,axis1=1,axis2=2),np.diagonal(b.matrices,axis1=1,axis2=2))
    np.testing.assert_array_equal(diag.liquidity_usdt,b.liquidity_usdt)
    np.testing.assert_array_equal(diag.taus_minutes,b.taus_minutes)
    p,_=generate_policies(episode,models(cross=0),cfg)
    np.testing.assert_array_equal(p["T3B"]["sales"],p["T4"]["sales"])
    np.testing.assert_array_equal(p["T3"]["sales"],p["T4"]["sales"])


def test_fee_schedule_invariance(episode,cfg):
    p,_=generate_policies(episode,models(),cfg)
    q,_=generate_policies(episode,models(),{**cfg,"fee_bps":10,"half_spread_bps":2})
    for name in p:np.testing.assert_allclose(p[name]["sales"],q[name]["sales"],rtol=1e-8,atol=1e-5)


def test_objective_identity(episode):
    b=models()["B"].kernel;args=(b,episode.initial,episode.forecast,episode.covariance)
    r=solve_execution(*args);p=build_problem(*args);z=r["schedule_usdt"].ravel()
    np.testing.assert_allclose(.5*z@p.hessian@z+p.linear@z+p.constant,decompose(b,p,r["schedule_usdt"])["objective_usdt"],rtol=1e-12)


def test_override_validation(episode):
    for beta in [-1,np.inf,np.nan]:
        with pytest.raises(ValueError):build_problem(models()["A"].kernel,episode.initial,episode.forecast,episode.covariance,risk_multiplier_override=beta)


def test_asset_permutation(episode):
    b=models()["B"].kernel;r=solve_execution(b,episode.initial,episode.forecast,episode.covariance)
    perm=Kernel(ASSETS[::-1],b.matrices[:,::-1,::-1],b.taus_minutes,b.liquidity_usdt[::-1])
    q=solve_execution(perm,episode.initial[::-1],episode.forecast[:,::-1],episode.covariance[::-1,::-1],assets=ASSETS[::-1])
    np.testing.assert_allclose(r["schedule_usdt"],q["schedule_usdt"][:,::-1],rtol=1e-8,atol=1e-5)


def test_cash_unit_rescaling(episode):
    b=models()["B"].kernel;factor=1000
    r=solve_execution(b,episode.initial,episode.forecast,episode.covariance)
    unit=Kernel(ASSETS,b.matrices,b.taus_minutes,b.liquidity_usdt*factor)
    q=solve_execution(unit,episode.initial*factor,episode.forecast*factor,episode.covariance)
    np.testing.assert_allclose(q["schedule_usdt"]/factor,r["schedule_usdt"],rtol=1e-8,atol=1e-5)


def test_real_source_smoke(cfg):
    store=EpisodeStore(ROOT);e=construct_episode(store.history("2025-07-01T00:00:00Z"),"2025-07-01T00:00:00Z",cfg)
    assert e.forecast.shape==(60,2);assert all(x.split("/")[1]<"2026-01" for x in store.read_log)
    assert e.provenance["history_rows"]==40320


@pytest.mark.parametrize("horizon,cap",[(30,.05),(120,.20)])
def test_alternate_horizon_cap_smoke(frame,cfg,horizon,cap):
    cfg={**cfg,"horizon_minutes":horizon,"cap_fraction":cap}
    e=construct_episode(frame,"2025-07-01T00:00:00Z",cfg);p,r=generate_policies(e,models(),cfg)
    assert e.forecast.shape==(horizon,2)
    assert all(s["sales"].shape==(horizon,2) for s in p.values())
    assert max(row["normalized_physical_residual"] for row in r)<1e-8


def test_availability_identity(frame,cfg):
    frame.loc[0,"available_at_utc"]=pd.Timestamp("2025-07-02",tz="UTC")
    with pytest.raises(ValueError,match="availability"):construct_episode(frame,"2025-07-01T00:00:00Z",cfg)


def test_historical_models_keep_own_units_and_origin():
    # Real development model JSON only, never canonical test data.
    for month in pd.period_range("2025-07","2025-12",freq="M").astype(str):
        loaded=load_models(ROOT,month,month+"-01T00:00:00Z")
        prior=json.loads((ROOT/f"reports/research/stage02_artifacts/model_development_refit_{month}.json").read_text())
        np.testing.assert_array_equal(loaded["B"].kernel.liquidity_usdt,prior["liquidity_usdt"])
        np.testing.assert_array_equal(loaded["B"].kernel.matrices,prior["matrices"])
        for name in ("A","B"):
            assert loaded[name].training_end-loaded[name].training_start==pd.Timedelta(days=365)
            bundle=json.loads((ROOT/f"reports/research/stage04_artifacts/model_{name}_{month}.json").read_text())
            assert bundle["fit"]["training_rows"]==525600


def test_cli_test_start_is_refused():
    import subprocess
    result=subprocess.run([str(ROOT/".venv/bin/python"),str(ROOT/"scripts/stage04.py"),"build","--start","2026-01-01T00:00:00Z"],capture_output=True,text=True)
    assert result.returncode!=0
    assert "firewall" in result.stderr
