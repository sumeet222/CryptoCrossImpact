"""Pre-outcome evidence for approved ex-funding v2; fixtures are 2025/synthetic."""
from dataclasses import replace
import copy
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from cryptocrossimpact.episodes import construct_episode,config as pcfg
from cryptocrossimpact.kernel.features import construct,flow_basis
from cryptocrossimpact.kernel.fit import Stats,transforms,normalize,estimate
from cryptocrossimpact.execution.impact_cost import ASSETS,Kernel,triangular_cash,cash_hessian
from cryptocrossimpact.execution.policies import generate_policies
from cryptocrossimpact.evaluation.preflight import verify_predecessor,preflight,PretestHold
from cryptocrossimpact.evaluation.v2_common import config,digest,SCOPE
from cryptocrossimpact.evaluation.v2_data import HistoricalStore
from cryptocrossimpact.evaluation.v2_features import make_episode,construct_asof
from cryptocrossimpact.evaluation.v2_fit import validate_fit,window,E1_ridge,Fitter,policy_models,fixed_policy_models
from cryptocrossimpact.evaluation.v2_score import worlds,WORLD_IDS,ALIASES,World,score_schedule,evaluation_prices
from cryptocrossimpact.evaluation.v2_inference import block_indices,paired_interval,contrasts
from cryptocrossimpact.evaluation.v2_run import write_decision,verify_receipt,score_decision,snapshot,episode_calendar
from cryptocrossimpact.evaluation.v2_protocol import validate_ready

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports/research/stage05_v2_artifacts"


@pytest.fixture(autouse=True)
def pretest_only(monkeypatch):monkeypatch.setenv("CCI_PRETEST_ONLY","1")


def fit(role="E1",month="2025-09"):
    return json.loads((OUT/"pretest_models"/f"{month}_{role}.json").read_text())


@pytest.fixture
def artificial():
    t=pd.date_range("2025-08-04",periods=28*1440+121,freq="min",tz="UTC");k=np.arange(len(t))
    f=pd.DataFrame(dict(time=t,open_time=t.as_unit("ms").asi8))
    for i in range(2):
        f[f"close_{i}"]=100*np.exp(np.cumsum(.0001*np.sin(k/(7+i))+.0002*np.cos(k/51)))
        f[f"quote_volume_{i}"]=1e6*(1+i+.3*np.sin(k/1227))
        f[f"valid_bar_{i}"]=True;f[f"jump_flag_{i}"]=False;f[f"stale_close_flag_{i}"]=False
    return f


def test_v1_remains_funding_hold_and_preserved_lineage():
    assert verify_predecessor(ROOT)["bindings_verified"]==47
    assert preflight(ROOT)["funding"]["status"]=="PRETEST_FUNDING_HOLD"
    assert config(ROOT)["funding_status"]=="NOT_APPLICABLE_BY_APPROVED_SCOPE_AMENDMENT"


@pytest.mark.parametrize("month",["2025-09","2025-12"])
def test_real_E1_independent_window_units_psd(month):
    m=fit(month=month);origin=pd.Timestamp(month+"-01",tz="UTC");k=validate_fit(m,origin,"E1")
    start,end=window(origin,"E1")
    assert end-start==pd.Timedelta(days=180) and origin-end==pd.Timedelta(days=30)
    assert m["training_rows"]==259200 and m["calendar_days"]==180
    b=fit("B",month)
    assert m["liquidity_usdt"]!=b["liquidity_usdt"] and m["normalization"]!=b["normalization"]
    assert k.matrices.shape==(2,2,2) and list(k.taus_minutes)==[5,30]
    assert all(np.linalg.eigvalsh(c).min()>0 for c in k.matrices)
    assert m["latest_target_available"]==m["training_end_exclusive"]


@pytest.mark.parametrize("mutation",["window","market","assets","U","nonPSD","tau"])
def test_bad_evaluator_identity_rejected(mutation):
    m=fit()
    if mutation=="window":m["training_end_exclusive"]="2025-09-01T00:00:00Z"
    if mutation=="market":m["market"]="spot"
    if mutation=="assets":m["asset_order"]=list(ASSETS[::-1])
    if mutation=="U":m["model"]="U"
    if mutation=="nonPSD":m["matrices"][0]=[[1,2],[2,1]]
    if mutation=="tau":m["taus_minutes"]=[60]
    with pytest.raises(ValueError):validate_fit(m,pd.Timestamp("2025-09-01",tz="UTC"),"E1")


def test_ridge_comes_only_from_fixed_development_family():
    chosen,rows=E1_ridge(ROOT)
    assert chosen==1 and len(rows)==6 and set(rows.taus_minutes)=={"5;30"}


def test_planted_two_component_recovery():
    rng=np.random.default_rng(20261027);n=9000;flow=rng.normal(size=(n,2));control=rng.normal(size=(n,24))
    truth=np.array([[[1,.25],[.25,.8]],[[.4,-.1],[-.1,.5]]]);y=np.zeros((n,2))
    for c,tau in zip(truth,[5,30]):
        weights=np.r_[1,np.diff(np.exp(-np.arange(61)/tau))]
        z=np.column_stack([np.convolve(flow[:,i],weights,mode="full")[:n] for i in range(2)])
        y+=z@c.T
    y+=control[:,:2]@np.array([[.1,.2],[-.1,.1]])
    x=np.column_stack([np.ones(n),control,flow_basis(flow,[5,30]).reshape(n,-1)])[60:]
    raw=Stats.rows(x,y[60:]);normal=transforms(raw)
    m=estimate(normalize(raw,normal),normal,[5,30],[5,30],"B",0)
    np.testing.assert_allclose(m["matrices"],truth,atol=2e-5,rtol=0)


def test_feature_parity_on_real_2025_data():
    s=HistoricalStore(ROOT);f=s.paired(pd.Timestamp("2025-06-30",tz="UTC")-pd.Timedelta(minutes=1),pd.Timestamp("2025-08-01",tz="UTC"),purpose="pretest",asof=pd.Timestamp("2025-08-01",tz="UTC"))
    l=np.array(fit("B")["liquidity_usdt"])
    old=construct(f,l,[2,5,10,30,60]);new=construct_asof(f,l,[2,5,10,30,60])
    for a,b in zip(old,new):np.testing.assert_array_equal(a,b)


def test_forecast_and_policy_parity_future_mutation(artificial):
    cfg=pcfg(ROOT);t0=pd.Timestamp("2025-09-01",tz="UTC")
    old=construct_episode(artificial,t0,cfg);new=make_episode(artificial,t0,cfg)
    assert old.input_hash==new.input_hash
    changed=artificial.copy();future=changed.time>=t0
    changed.loc[future,["close_0","close_1","quote_volume_0","quote_volume_1"]]=np.nan
    after=make_episode(changed,t0,cfg);assert new.input_hash==after.input_hash
    models=policy_models({r:fit(r) for r in ("A","B")},t0)
    a,_=generate_policies(new,models,cfg);b,_=generate_policies(after,models,cfg)
    for name in a:np.testing.assert_array_equal(a[name]["sales"],b[name]["sales"])
    assert new.provenance["latest_open"]=="2025-08-31 23:59:00+00:00"


@pytest.mark.parametrize("purpose",["decision","refit","observed_month","score"])
def test_pretest_2026_refusal_before_parquet(monkeypatch,purpose):
    s=HistoricalStore(ROOT);monkeypatch.setattr(pd,"read_parquet",lambda *a,**k:pytest.fail("Forbidden 2026 I/O"))
    with pytest.raises((ValueError,PretestHold)):
        s.paired(pd.Timestamp("2026-01-01",tz="UTC"),pd.Timestamp("2026-01-02",tz="UTC"),purpose=purpose,asof=pd.Timestamp("2026-01-02",tz="UTC"))


def test_fake_ready_and_changed_config_cannot_unlock(tmp_path):
    o=tmp_path/"reports/research/stage05_v2_artifacts";o.mkdir(parents=True)
    (o/"pretest_ready_v2.json").write_text(json.dumps({"status":"PRETEST_READY_v2"}))
    with pytest.raises(PretestHold):validate_ready(tmp_path)


def test_asof_reader_refuses_own_month_future():
    s=HistoricalStore(ROOT)
    with pytest.raises(ValueError,match="as-of"):
        s.paired(pd.Timestamp("2025-09-01",tz="UTC"),pd.Timestamp("2025-10-01",tz="UTC"),purpose="refit",asof=pd.Timestamp("2025-09-01",tz="UTC"))


@pytest.fixture
def ws():
    origin=pd.Timestamp("2025-09-01",tz="UTC")
    return worlds(validate_fit(fit(),origin,"E1"),validate_fit(fit("B"),origin,"B"),2)


def test_all_worlds_psd_exact_cash_and_aliases(ws):
    assert [w.world_id for w in ws]==WORLD_IDS and ALIASES["E3_rho_0"]=="E2"
    z=np.array([[2000.,1000.],[1000.,2000.]])
    for w in ws:
        assert np.linalg.eigvalsh(w.hessian).min()>=-1e-9*np.linalg.norm(w.hessian,2)
        np.testing.assert_allclose(.5*z.ravel()@w.hessian@z.ravel(),triangular_cash(w.kernel,z),rtol=1e-12,atol=1e-13)
    lookup={w.world_id:w for w in ws}
    np.testing.assert_array_equal(lookup["E2"].kernel.matrices[:,0,1],0)
    np.testing.assert_array_equal(lookup["E3_amplitude_2"].kernel.matrices,lookup["E1"].kernel.matrices*2)
    assert not np.array_equal(lookup["E3_decay_2"].hessian,lookup["E1"].hessian)
    assert lookup["E0"].world_id=="E0"


def test_hand_cash_funding_omitted_negative_shortfall():
    k=Kernel(ASSETS,[np.diag([3,2])],[1e10],[4,9]);world=World("E1",k,.001,2)
    z=np.array([[2.,0],[4.,3.]]);x=z.sum(axis=0);v=np.full((2,2),100.);p=np.array([[110.,200],[90.,220.]])
    args=(z,x,v,np.array([100.,200.]),p,v,world)
    a=score_schedule(*args);b=score_schedule(*args,hypothetical_funding_events=["inside","arrival","endpoint"],funding_rate=-.5)
    assert a==b and a["funding_cashflow_usdt"] is None and a["all_in_cash_cost_usdt"] is None
    assert a["cost_scope"]==SCOPE and a["funding_included"] is False
    np.testing.assert_allclose(a["path_usdt"],-.1,atol=1e-14)
    np.testing.assert_allclose(a["transient_usdt"],.00145,atol=1e-12)
    np.testing.assert_allclose(a["shortfall_ex_funding_usdt"],-.09286,atol=1e-12)


def test_realized_volume_only_changes_diagnostic(ws):
    z=np.array([[2000.,1000.],[1000.,2000.]]);x=z.sum(0);v=np.full_like(z,100000.)
    a=score_schedule(z,x,v,[100,100],np.full_like(z,100.),v,ws[1])
    b=score_schedule(z,x,v,[100,100],np.full_like(z,100.),np.zeros_like(z),ws[1])
    assert a["shortfall_ex_funding_usdt"]==b["shortfall_ex_funding_usdt"]
    assert b["max_realized_participation"]==np.inf and b["zero_realized_volume_cells"]==4


def test_fee_spread_constant_for_equal_totals(ws):
    a=np.array([[2000.,1000.],[1000.,2000.]]);b=a[::-1].copy();x=a.sum(0);v=np.full_like(a,1e5);p=np.full_like(a,100.)
    one=score_schedule(a,x,v,[100,100],p,v,ws[1]);two=score_schedule(b,x,v,[100,100],p,v,ws[1])
    assert one["fee_usdt"]==two["fee_usdt"] and one["spread_usdt"]==two["spread_usdt"]


def test_decision_persisted_and_tamper_rejected(tmp_path):
    r=write_decision(tmp_path/"decisions.jsonl",dict(episode_id="synthetic",t0="2025-09-01T00:00:00Z",horizon_minutes=60))
    assert verify_receipt(r)["episode_id"]=="synthetic"
    with pytest.raises(ValueError):verify_receipt({**r,"sha256":"fake"})


def test_price_qc_retains_valid_adverse_jump():
    t0=pd.Timestamp("2025-09-01",tz="UTC");f=pd.DataFrame(dict(time=pd.date_range(t0,periods=2,freq="min")))
    for i in range(2):f[f"close_{i}"]=[100.,1.];f[f"quote_volume_{i}"]=100.;f[f"valid_bar_{i}"]=True
    p,v=evaluation_prices(f,t0,2);assert p[-1,0]==1.
    with pytest.raises(ValueError,match="EVALUATION_QC"):evaluation_prices(f.iloc[:1],t0,2)


def test_bootstrap_calendar_pairs_exclusions_and_negative_denominator():
    idx=block_indices(21);np.testing.assert_array_equal(idx,block_indices(21))
    for row in idx:
        for k in range(0,21,7):np.testing.assert_array_equal(np.diff(row[k:k+7]),1)
    count=np.ones(21);count[8:11]=0;sums=count*2
    result=paired_interval(np.arange(21),sums,count,-count)
    assert result["mean"]==result["ci_low"]==result["ci_high"]==2
    assert result["relative_reduction"] is None
    empty=paired_interval(np.arange(21),np.zeros(21),np.zeros(21))
    assert empty["mean"] is None and empty["bootstrap_zero_eligible_replicates"]==500


def test_nominal_test_calendar_and_no_funding_exclusion():
    times=episode_calendar(pd.Timestamp("2026-01-01",tz="UTC"),pd.Timestamp("2026-07-01",tz="UTC"))
    assert len(times)==724 and set(times.hour)=={0,6,12,18}
    assert config(ROOT)["funding_episode_exclusions"] is False


def test_paired_contrast_counts_missing_pairs_without_zero_fills():
    rows=[]
    for day in pd.date_range("2026-01-01",periods=21):
        for p,value in [("T3",10.),("T3B",9.),("T4",8.)]:
            if day.day==1 and p=="T4":continue
            rows.append(dict(episode_id=str(day.date()),day=str(day.date()),month="2026-01",world="E1",policy=p,
                W_usdt=10000.,shortfall_ex_funding_usdt=value,shortfall_ex_funding_bps=value))
    table,_=contrasts(pd.DataFrame(rows));row=table[(table.group=="all")&(table.baseline=="T3")].iloc[0]
    assert row.paired_episodes==20 and row.unmatched_episode_count==1 and row.mean_delta_ex_funding_bps==2.


def test_H1_aggregation_on_synthetic_calendar():
    from cryptocrossimpact.evaluation.v2_summary import h1_tables
    rows=[]
    for date in pd.date_range("2026-01-01",periods=21):
        for model,loss in [("A",2.),("B",1.5),("N0",3.)]:
            for asset in ASSETS:rows.append(dict(day=str(date.date()),month="2026-01",model=model,asset=asset,n=1440,
                standardized_sse=1440*loss,error_bps_sse=1440*loss,error_bps_sae=1440,target_bps_sum=0.,target_bps_sumsq=14400.))
    metrics,effects=h1_tables(pd.DataFrame(rows));row=effects[(effects.group=="all")&(effects.asset=="pooled")].iloc[0]
    assert row.delta_fit==.25 and row.mean_paired_standardized_loss_difference==.5


@pytest.mark.parametrize("variant",list(config(ROOT)["decision_sensitivities"]))
def test_locked_decision_sensitivity_paths_on_synthetic_inputs(artificial,tmp_path,variant):
    cfg=pcfg(ROOT);change=config(ROOT)["decision_sensitivities"][variant]
    cfg.update({k:v for k,v in change.items() if k in cfg})
    t0=pd.Timestamp("2025-09-01",tz="UTC");e=make_episode(artificial,t0,cfg)
    if "fixed_notional_per_leg" in change:e=replace(e,initial=np.full(2,change["fixed_notional_per_leg"],dtype=float))
    pm=fixed_policy_models(ROOT) if change.get("frozen_calibration") else policy_models({r:fit(r) for r in ("A","B")},t0)
    p,q=generate_policies(e,pm,cfg)
    world=[w for w in worlds(validate_fit(fit(),t0,"E1"),pm["B"].kernel,len(e.forecast)) if w.world_id in ("E1","E2")]
    data=snapshot(e,p,q,pm,world,cfg,variant);data["decision_key"]=e.episode_id+"_"+variant
    receipt=write_decision(tmp_path/"decisions.jsonl",data)
    price=np.tile(e.p0,(len(e.forecast),1));real=np.array(e.forecast)
    for w in world:
        for policy in p:
            row=score_schedule(p[policy]["sales"],e.initial,e.forecast,e.p0,price,real,w)
            assert row["funding_cashflow_usdt"] is None and np.isfinite(row["shortfall_ex_funding_usdt"])
    assert verify_receipt(receipt)["variant"]==variant


def test_scoring_reader_requires_real_persisted_receipt(monkeypatch):
    s=HistoricalStore(ROOT);monkeypatch.setattr(pd,"read_parquet",lambda *a,**k:pytest.fail("Outcome read before snapshot"))
    with pytest.raises(ValueError,match="receipt"):
        s.paired(pd.Timestamp("2025-09-01",tz="UTC"),pd.Timestamp("2025-09-01T01:00:00Z"),purpose="score")


def test_stale_policy_origin_is_rejected():
    pm=policy_models({r:fit(r) for r in ("A","B")},pd.Timestamp("2025-09-01",tz="UTC"))
    with pytest.raises(ValueError,match="wrong-month"):pm["A"].check(pd.Timestamp("2025-10-01",tz="UTC"))
