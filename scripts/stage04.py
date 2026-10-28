"""Stage 4 development-only episodes/policies; never a historical cost backtest."""
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/"data/tmp/matplotlib"))
os.environ.setdefault("OPENBLAS_NUM_THREADS","1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS","1")
sys.path.insert(0,str(ROOT/"src"))


def main():
    import argparse,resource,time,importlib.metadata,subprocess
    from cryptocrossimpact.episodes import arrivals
    from cryptocrossimpact.stage04 import paths,save,build,policies,smoke,prepare_models
    from cryptocrossimpact.data.storage import sha256,utcnow
    from cryptocrossimpact.data.pipeline import load_config
    from cryptocrossimpact.data.storage import PublicSource
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=["smoke","build","policies","report","lock","all"])
    # Accepted only to make forbidden test-start attempts fail explicitly; the
    # approved full run calendar is immutable rather than arbitrary CLI sampling.
    parser.add_argument("--start",default="2025-07-01T00:00:00Z")
    args=parser.parse_args();arrivals(args.start)
    if args.start!="2025-07-01T00:00:00Z":parser.error("Stage 4 calendar starts July 1; use smoke for a subset")
    out,_=paths(ROOT);clock=time.monotonic();status="FAILED";started=utcnow()
    guard=PublicSource(ROOT,load_config(ROOT));bytes_before=guard.guard(50_000_000)
    try:
        if args.command in ("smoke","all"):smoke(ROOT)
        if args.command in ("build","all"):prepare_models(ROOT);build(ROOT)
        if args.command in ("policies","all"):policies(ROOT)
        if args.command in ("report","all"):
            from cryptocrossimpact.stage04_reporting import report
            report(ROOT)
        if args.command in ("lock","all"):
            from cryptocrossimpact.stage04_reporting import lock
            lock(ROOT)
        status="PASS"
    finally:
        sources=list((ROOT/"src/cryptocrossimpact").rglob("*.py"))+[ROOT/"scripts/stage04.py",ROOT/"tests/test_stage04_policies.py"]
        save(out/f"run_{args.command}.json",dict(stage="Stage 4 development policy construction; no Stage 5",status=status,
            utc=started,command=args.command,elapsed_seconds=time.monotonic()-clock,
            peak_rss_bytes_macos=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            project_bytes_before=bytes_before,project_bytes_after=guard.guard(),
            git_revision=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip(),
            dirty_status=subprocess.check_output(["git","status","--short"],cwd=ROOT,text=True),
            versions={p:importlib.metadata.version(p) for p in ["numpy","pandas","pyarrow","scipy","cvxpy","osqp","clarabel","pytest"]},
            bindings={str(p.relative_to(ROOT)):sha256(p) for p in sources},
            spec_sha256=sha256(ROOT/"CryptoCrossImpact_Research_Specification_v1_2026-10-27.md"),
            config_sha256=sha256(ROOT/"configs/stage04_policies.yaml"),changelog_sha256=sha256(ROOT/"SPEC_CHANGELOG.md"),
            source_manifest_sha256=sha256(ROOT/"data/registry/source_manifest.json"),seed=20261027,
            model_convention="monthly 365 day fixed-family as-of; fixed June sensitivity",evaluator_ids=[],
            test_partitions_opened=0,final_outcome_scoring_performed=False,historical_shortfall_backtest_performed=False))


if __name__=="__main__":main()
