"""Post-outcome QA only: frozen outputs/models, no canonical outcome reads.

This independent audit was written after opening outcomes. It cannot establish
pretest readiness, choose parameters, change scores, or replace frozen tests.
Run from the repository root after `scripts/stage05_v2.py all` completes.
"""
import os
from pathlib import Path
import sys
import json
import datetime
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd

root=Path.cwd();sys.path.insert(0,str(root/"src"))
os.environ.setdefault("MPLCONFIGDIR",str(root/"data/tmp/matplotlib"))
from cryptocrossimpact.data.storage import sha256,utcnow
from cryptocrossimpact.evaluation.v2_common import locations,save,digest,SCOPE
from cryptocrossimpact.evaluation.v2_protocol import validate_ready
from cryptocrossimpact.evaluation.preflight import verify_predecessor
from cryptocrossimpact.evaluation.v2_fit import validate_fit,policy_models
from cryptocrossimpact.evaluation.v2_score import worlds
from cryptocrossimpact.evaluation.v2_run import receipts,verify_receipt,reconstruct
from cryptocrossimpact.execution.impact_cost import triangular_cash

out,bulk=locations(root);ready=validate_ready(root);verify_predecessor(root)
index=json.loads((out/"primary_index.json").read_text());allscore=[];casherrors=[];nominal=0;decisions=0;maximum_twap_vwap_error=0.
for entry in index["months"]:
    month=entry["month"];folder=bulk/"primary"/month;cp=json.loads((folder/"checkpoint.json").read_text())
    for name,h in cp["output_sha256"].items():assert sha256(folder/name)==h,(month,name)
    rs=receipts(folder/"decisions.jsonl");origin=pd.Timestamp(month+"-01",tz="UTC")
    models={r:json.loads((out/"models"/f"{month}_{r}.json").read_text()) for r in ("A","B","N0","E1")}
    for role,m in models.items():validate_fit(m,origin,role)
    ws=worlds(validate_fit(models["E1"],origin,"E1"),validate_fit(models["B"],origin,"B"))
    scores=pd.read_parquet(folder/"scores.parquet");allscore.append(scores)
    assert len(rs)==cp["nominal"]==pd.Period(month).days_in_month*4
    for eid,receipt in rs.items():
        d=verify_receipt(receipt)
        if d["status"]!="DECISIONS_FROZEN":continue
        e=reconstruct(d);assert e.input_hash==d["input_hash"]
        assert pd.Timestamp(e.provenance["latest_open"])==e.t0-pd.Timedelta(minutes=1)
        assert pd.Timestamp(e.provenance["latest_available_at"])==e.t0
        assert len({q["beta"] for q in d["policy_qa"]})==1
        for name,z in d["schedules"].items():
            z=np.array(z);x=np.array(d["initial"]);cap=np.array(d["caps"])
            assert np.max(np.abs(z.sum(0)-x)/x)<1e-7
            assert np.max(np.maximum(z-cap,0)/x)<1e-7 and np.max(np.maximum(-z,0)/x)<1e-7
        maximum_twap_vwap_error=max(maximum_twap_vwap_error,float(np.max(np.abs(np.array(d["schedules"]["T0"])-np.array(d["schedules"]["T1"]))/e.initial)))
        assert set(scores[scores.episode_id==eid].decision_hash)=={receipt["sha256"]}
        decisions+=1
    # Independent direct triangular cash audit of the first episode, every world.
    first=verify_receipt(next(iter(rs.values())));z=np.array(first["schedules"]["T4"])
    for w in ws:
        actual=float(scores[(scores.episode_id==first["episode_id"])&(scores.policy=="T4")&(scores.world==w.world_id)].transient_usdt.iloc[0])
        direct=triangular_cash(w.kernel,z);casherrors.append(abs(actual-direct))
        assert np.isclose(actual,direct,rtol=1e-11,atol=1e-8)
    for event in json.loads((folder/"io_audit.json").read_text()):
        if event["purpose"] in ("refit","decision","pretest"):
            assert pd.Timestamp(event["end_exclusive"])<=pd.Timestamp(event["asof"])
    nominal+=cp["nominal"]
s=pd.concat(allscore,ignore_index=True)
assert nominal==decisions==724 and len(s)==47784 and s.world.nunique()==11 and s.policy.nunique()==6
assert s.funding_cashflow_usdt.isna().all() and s.all_in_cash_cost_usdt.isna().all()
assert set(s.cost_scope)=={SCOPE} and not s.funding_included.any() and not s.funding_observed.any()
assert (s.groupby("episode_id").input_hash.nunique()==1).all() and (s.groupby("episode_id").beta.nunique()==1).all()
first_open=json.loads((out/"first_outcome_open_v2.json").read_text())
assert pd.Timestamp(first_open["utc"])>pd.Timestamp(ready["utc"])
assert first_open["ready_sha256"]==sha256(out/"pretest_ready_v2.json") and first_open["purpose"]=="score"
frozen=json.loads((out/"primary_statistics_index.json").read_text())
for name,h in frozen["sha256"].items():assert sha256(out/name)==h

initial=json.loads((out/"preservation_start.json").read_text());changed=[];archived={
    "SPEC_CHANGELOG.md":"docs/stage05_v1_preserved/SPEC_CHANGELOG.md",
    "src/cryptocrossimpact/evaluation/preflight.py":"docs/stage05_v1_preserved/preflight.py",
    "README.md":"docs/stage05_v1_preserved/README.md"}
for name,h in initial["protected_sha256"].items():
    if sha256(root/name)!=h:
        assert name in archived and sha256(root/archived[name])==h,name
        changed.append(dict(active_path=name,original_preserved_as=archived[name]))
for name,value in initial["canonical_stat_only"].items():
    st=(root/name).stat();assert dict(bytes=st.st_size,mtime_ns=st.st_mtime_ns)==value,name
save(out/"preservation_end_v2.json",dict(status="PASS",unchanged_live_prior_files=len(initial["protected_sha256"])-len(changed),
    authorized_edits_with_exact_originals_preserved=changed,canonical_stat_only_partitions=60))

# Prespecified adverse/outlier diagnostics, not filters or alternate hypotheses.
extremes=[]
for world,g in s.groupby("world"):
    p=g.pivot(index="episode_id",columns="policy",values="shortfall_ex_funding_bps")
    for baseline in ("T3","T3B"):
        delta=p[baseline]-p.T4;eid=delta.idxmin()
        extremes.append(dict(world=world,baseline=baseline,worst_episode_id=eid,worst_delta_ex_funding_bps=float(delta.loc[eid])))
pd.DataFrame(extremes).to_csv(out/"worst_episode_diagnostics.csv",index=False)
participation=s[s.world=="E1"].groupby("policy").agg(maximum_realized_participation=("max_realized_participation","max"),
    over10pct_cells=("realized_participation_over_10pct_cells","sum"),zero_volume_cells=("zero_realized_volume_cells","sum"))
participation["total_asset_minute_cells"]=724*60*2
participation["over10pct_share"]=participation.over10pct_cells/participation.total_asset_minute_cells
participation.to_csv(out/"realized_participation_by_policy.csv")
post=list(ET.parse(out/"post_ready_pytest.xml").getroot().iter("testsuite"))
assert sum(int(x.attrib["tests"]) for x in post)==166
assert sum(int(x.attrib.get("errors",0))+int(x.attrib.get("failures",0)) for x in post)==0
save(out/"post_ready_checks_v2.json",dict(utc=utcnow(),status="PASS",tests_passed=166,tests_failed=0,
    audited_immutable_decisions=decisions,primary_score_rows=len(s),independent_triangular_cash_checks=len(casherrors),
    maximum_triangular_cash_discrepancy_usdt=max(casherrors),maximum_T0_T1_difference_over_initial=maximum_twap_vwap_error,
    full_calendar_and_shared_beta=True,first_outcome_open_after_ready=True,primary_statistics_unchanged=True,
    negative_cash_rows_retained=int((s.shortfall_ex_funding_usdt<0).sum()),funding_and_all_in_unestimated=True,stage6_started=False))
print(dict(status="PASS",decisions=decisions,scores=len(s),cash_error=max(casherrors),preserved_changed_originals=changed))

robust_index=json.loads((out/"robustness_index.json").read_text())
assert robust_index["status"]=="COMPLETE"
assert robust_index["primary_index_sha256"]==sha256(out/"primary_index.json")
robust_scores=[];robust_decisions=0;max_fee_error=0.;max_spread_error=0.
expected_variants=set(robust_index["variants"])|{"price_open","price_ohlc","fee_bps_2","fee_bps_10","half_spread_bps_0","half_spread_bps_2"}
assert len(expected_variants)==17
for entry in index["months"]:
    month=entry["month"];folder=bulk/"robustness"/month
    cp=json.loads((folder/"checkpoint.json").read_text())
    for name,h in cp["output_sha256"].items():assert sha256(folder/name)==h,(month,name)
    assert cp["failures"]==0 and json.loads((folder/"failures.json").read_text())==[]
    r=pd.read_parquet(folder/"scores.parquet");assert len(r)==cp["rows"]
    assert set(r.variant)==expected_variants and set(r.world)=={"E1","E2"}
    counts=r.groupby(["variant","world","policy"]).size()
    assert len(counts)==17*2*6 and (counts==pd.Period(month).days_in_month*4).all()
    rs=receipts(folder/"decisions.jsonl")
    assert len(rs)==pd.Period(month).days_in_month*4*11
    for receipt in rs.values():
        d=verify_receipt(receipt);e=reconstruct(d)
        assert e.input_hash==d["input_hash"]
        q=r[(r.episode_id==d["episode_id"])&(r.variant==d["variant"])]
        assert set(q.decision_hash)=={receipt["sha256"]}
        assert len({a["beta"] for a in d["policy_qa"]})==1
        for z in d["schedules"].values():
            z=np.asarray(z);initial=np.asarray(d["initial"]);caps=np.asarray(d["caps"])
            assert np.max(np.abs(z.sum(0)-initial)/initial)<1e-7
            assert np.max(np.maximum(z-caps,0)/initial)<1e-7
            assert np.max(np.maximum(-z,0)/initial)<1e-7
        robust_decisions+=1
    primary=pd.read_parquet(bulk/"primary"/month/"scores.parquet")
    primary=primary[primary.world.isin(["E1","E2"])].set_index(["episode_id","world","policy"])
    for variant,delta in [("fee_bps_2",-3),("fee_bps_10",5),("half_spread_bps_0",-1),("half_spread_bps_2",1)]:
        g=r[r.variant==variant].set_index(["episode_id","world","policy"]).reindex(primary.index)
        assert (g.decision_hash==primary.decision_hash).all()
        error=float(np.max(np.abs((g.shortfall_ex_funding_bps-primary.shortfall_ex_funding_bps)-delta)))
        assert error<1e-8,(variant,error)
        if variant.startswith("fee"):max_fee_error=max(max_fee_error,error)
        else:max_spread_error=max(max_spread_error,error)
    for variant in ("price_open","price_ohlc"):
        g=r[r.variant==variant].set_index(["episode_id","world","policy"]).reindex(primary.index)
        assert (g.decision_hash==primary.decision_hash).all()
    robust_scores.append(r)
r=pd.concat(robust_scores,ignore_index=True)
assert robust_decisions==724*11 and len(r)==724*17*2*6
assert r.funding_cashflow_usdt.isna().all() and r.all_in_cash_cost_usdt.isna().all()
assert not r.funding_observed.any() and not r.funding_included.any()
verdict=json.loads((out/"verdict_v2.json").read_text())
assert verdict["stage"]=="G4 OOS COMPLETE" and verdict["implementation"]=="PASS"
save(out/"robustness_output_audit_v2.json",dict(utc=utcnow(),status="PASS",origin="post_outcome_independent_QA_not_pretest_evidence",
    variants=17,monthly_checkpoints=6,score_rows=len(r),immutable_reoptimized_decisions=robust_decisions,failures=0,
    maximum_linear_fee_shift_error_bps=max_fee_error,maximum_linear_spread_shift_error_bps=max_spread_error,
    source_sha256=sha256(Path(__file__)),funding_and_all_in_unestimated=True,stage6_started=False))
print(dict(status="PASS",robustness_rows=len(r),robustness_decisions=robust_decisions,variants=17))
