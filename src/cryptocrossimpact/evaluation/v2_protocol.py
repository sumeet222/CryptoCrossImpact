"""Evidence-linked v2 readiness; marker/config flags alone grant no access."""
import json
import os
from pathlib import Path
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import yaml

from ..data.storage import sha256,utcnow
from .preflight import verify_predecessor,PretestHold
from .v2_common import locations,config,save,digest,numerical_sources,SCOPE
from .v2_fit import Fitter,validate_fit,E1_ridge
from .v2_data import HistoricalStore
from .v2_score import worlds,WORLD_IDS,ALIASES

_cache={}


def prepare(root):
    root=Path(root);out,bulk=locations(root);verify_predecessor(root)
    if (out/"first_outcome_open_v2.json").exists():raise PretestHold("Pretest evidence cannot be regenerated after opening outcomes")
    os.environ["CCI_PRETEST_ONLY"]="1"
    store=HistoricalStore(root);fitter=Fitter(root,store);records=[]
    ridge,candidates=E1_ridge(root);candidates.to_csv(out/"E1_ridge_selection_v2.csv",index=False)
    for date in config(root)["E1_development_origins"]:
        origin=pd.Timestamp(date,tz="UTC")
        e1=fitter.fit(origin,"E1",out/"pretest_models");b=fitter.fit(origin,"B",out/"pretest_models")
        replay=fitter.fit(origin,"E1",out/"pretest_replay_models")
        if digest(e1)!=digest(replay):raise PretestHold("Independent E1 repeat differs")
        k=validate_fit(e1,origin,"E1");kb=validate_fit(b,origin,"B")
        if e1["liquidity_usdt"]==b["liquidity_usdt"] or e1["normalization"]==b["normalization"]:
            raise PretestHold("E1 appears to reuse optimizer coordinates")
        ws=worlds(k,kb)
        records.append(dict(origin=str(origin),training_start=e1["training_start"],training_end_exclusive=e1["training_end_exclusive"],
            rows=e1["training_rows"],calendar_days=e1["calendar_days"],gap_days=30,tau=e1["taus_minutes"],ridge=ridge,
            L=e1["liquidity_usdt"],E1_model_sha256=sha256(out/"pretest_models"/f"{date[:7]}_E1.json"),
            B_model_sha256=sha256(out/"pretest_models"/f"{date[:7]}_B.json"),reproducible=True,
            components=e1["component_diagnostics"],world_min_relative_eigenvalue=min(w.hessian_diagnostics["relative_min_eigenvalue"] for w in ws)))
    from .v2_run import primary
    smoke=primary(root,pretest=True)
    if smoke[0]["scored"]!=8:raise PretestHold("Development decision/scorer smoke incomplete")
    sources=[root/"src/cryptocrossimpact/evaluation"/n for n in ["v2_fit.py","v2_features.py","v2_data.py","v2_score.py","v2_run.py"]]
    evidence=dict(status="PRETEST_EVIDENCE_PASS",utc=utcnow(),outcomes_unopened=True,E1_origins=records,development_smoke=smoke,
        worlds=WORLD_IDS,aliases=ALIASES,funding_status="NOT_APPLICABLE_BY_APPROVED_SCOPE_AMENDMENT",cost_scope=SCOPE,
        source_bindings={str(p.relative_to(root)):sha256(p) for p in sources},source_manifest_sha256=sha256(root/"data/registry/source_manifest.json"))
    save(out/"pretest_evidence_v2.json",evidence)
    os.environ.pop("CCI_PRETEST_ONLY",None)
    return evidence


def check_evidence(root):
    root=Path(root);out,_=locations(root);verify_predecessor(root)
    e=json.loads((out/"pretest_evidence_v2.json").read_text())
    if e["status"]!="PRETEST_EVIDENCE_PASS" or e["worlds"]!=WORLD_IDS or e["cost_scope"]!=SCOPE or len(e["E1_origins"])!=2:
        raise PretestHold("Incomplete/changed pretest evidence")
    for name,h in e["source_bindings"].items():
        if sha256(root/name)!=h:raise PretestHold(f"Pretest implementation changed: {name}")
    for row in e["E1_origins"]:
        origin=pd.Timestamp(row["origin"]);path=out/"pretest_models"/f"{origin.strftime('%Y-%m')}_E1.json"
        if sha256(path)!=row["E1_model_sha256"]:raise PretestHold("E1 development artifact changed")
        m=json.loads(path.read_text());validate_fit(m,origin,"E1")
        if m["training_rows"]!=259200 or not row["reproducible"]:raise PretestHold("E1 calendar/replay check failed")
    tests=json.loads((out/"test_results_v2.json").read_text())
    if tests["failed"] or tests["passed"]<100:raise PretestHold("Required pretest suite not passed")
    for name,h in tests["bindings"].items():
        if sha256(root/name)!=h:raise PretestHold(f"Code/tests changed after pretests: {name}")
    suites=list(ET.parse(out/"pretest_pytest.xml").getroot().iter("testsuite"))
    if sum(int(s.attrib.get("failures",0))+int(s.attrib.get("errors",0)) for s in suites):raise PretestHold("JUnit contains failures")
    if sum(int(s.attrib["tests"]) for s in suites)!=tests["passed"]:raise PretestHold("Test evidence counts disagree")
    return dict(E1=digest(e),tests=sha256(out/"test_results_v2.json"),scope=SCOPE,worlds=WORLD_IDS)


def freeze(root):
    root=Path(root);out,_=locations(root)
    if (out/"first_outcome_open_v2.json").exists():raise PretestHold("Cannot refreeze after outcome access")
    evidence=check_evidence(root);oldpath=root/"configs/stage05_pretest_lock.yaml"
    original=yaml.safe_load(oldpath.read_text());cfg=config(root)
    bind=numerical_sources(root)+[root/"tests/test_stage05_v2.py",root/"SPEC_CHANGELOG.md",root/"CryptoCrossImpact_Research_Specification_v1_2026-10-27.md",
        root/"configs/stage04_policies.yaml",root/"data/registry/source_manifest.json",root/"docs/stage05_pretest_amendment_v2_funding_excluded.md",
        root/"docs/stage05_pretest_policy_evaluator_lock_v2.md",out/"pretest_evidence_v2.json",out/"test_results_v2.json",out/"pretest_pytest.xml",
        root/"reports/research/stage05_artifacts/final_verification.json",root/"reports/research/stage05_artifacts/funding_source_probes.json",
        root/"results/kernel_development/daily.npz",root/"reports/research/stage02_artifacts/features.json",
        root/"prompts/CryptoCrossImpact_Codex_Stage05_Recovery_Funding_Excluded_2026-10-27.md",
        root/"prompts/CryptoCrossImpact_Codex_Stage05_OOS_Evaluation_and_Robustness_Prompt_2026-10-27.md"]
    bind+=list((out/"pretest_models").glob("*.json"))+list((root/"docs/stage05_v1_preserved").glob("*"))
    lock=dict(version="stage05-ex-funding-v2",status="FROZEN_PRETEST_PROTOCOL",previous_lock_sha256=sha256(oldpath),
        previous_lock_path=str(oldpath.relative_to(root)),approval_basis="Explicit user funding-excluded recovery amendment before 2026 outcome opening",
        cost_scope=SCOPE,funding_status="NOT_APPLICABLE_BY_APPROVED_SCOPE_AMENDMENT",funding_included=False,
        original_funding_HOLD_preserved=True,settings=cfg,unchanged_predecessor_settings={k:v for k,v in original.items() if k not in ("bindings","status","holds")},
        worlds=WORLD_IDS,world_aliases=ALIASES,regime_thresholds=original["development_regime_tercile_thresholds"],
        gate_evidence=evidence,bindings={str(p.relative_to(root)):sha256(p) for p in bind})
    lockpath=root/"configs/stage05_pretest_lock_v2.yaml"
    lockpath.write_text(yaml.safe_dump(lock,sort_keys=False));lockhash=sha256(lockpath)
    (root/"configs/stage05_pretest_lock_v2.sha256").write_text(f"{lockhash}  stage05_pretest_lock_v2.yaml\n")
    ready=dict(status="PRETEST_READY_v2",utc=utcnow(),previous_lock_sha256=sha256(oldpath),amended_lock_sha256=lockhash,
        config_sha256=sha256(root/"configs/stage05_evaluation_v2.yaml"),funding_status=lock["funding_status"],cost_scope=SCOPE,
        gate_evidence_digest=digest(evidence),outcomes_unopened_at_approval=True)
    ready["receipt_digest"]=digest(ready);save(out/"pretest_ready_v2.json",ready)
    validate_ready(root);return ready


def validate_ready(root):
    root=Path(root);out,_=locations(root)
    try:
        prior=_cache.get(str(root))
        if prior is not None:
            current=tuple((str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in prior["files"])
            if current==prior["stats"]:return prior["ready"]
        path=out/"pretest_ready_v2.json";ready=json.loads(path.read_text());lockpath=root/"configs/stage05_pretest_lock_v2.yaml"
        lock=yaml.safe_load(lockpath.read_text())
        files=[path,lockpath]+[root/n for n in lock["bindings"]]
        stats=tuple((str(p),p.stat().st_size,p.stat().st_mtime_ns) for p in files)
        check={k:v for k,v in ready.items() if k!="receipt_digest"}
        if ready["status"]!="PRETEST_READY_v2" or digest(check)!=ready["receipt_digest"] or sha256(lockpath)!=ready["amended_lock_sha256"]:
            raise PretestHold("Invalid readiness receipt/hash")
        if ready["cost_scope"]!=SCOPE or lock["settings"]["funding_episode_exclusions"] or lock["funding_status"]!="NOT_APPLICABLE_BY_APPROVED_SCOPE_AMENDMENT":
            raise PretestHold("Wrong amendment/scope")
        for name,h in lock["bindings"].items():
            if sha256(root/name)!=h:raise PretestHold(f"Frozen protocol/code/evidence changed: {name}")
        evidence=check_evidence(root)
        if digest(evidence)!=ready["gate_evidence_digest"]:raise PretestHold("Underlying pretest evidence changed")
        _cache[str(root)]=dict(stats=stats,files=files,ready=ready);return ready
    except (OSError,KeyError,ValueError,TypeError) as exc:
        raise PretestHold(f"PRETEST_HOLD_v2: no verified readiness ({exc})") from exc
